from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from typing import Dict, Any
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, date

from pydantic import BaseModel, EmailStr
from typing import List, Optional

from src.core.config import settings
from src.core.logger import logger
from src.services.whatsapp_service import whatsapp_service
from src.services.knowledge_base import knowledge_base
from src.services.session_manager import session_manager
from src.agents.lunia_agent_enhanced import lunia_agent
from src.models.schemas import AgentState, MessageType, ConversationRole
from src.services.email_service import EmailService
from src.services.calendar_service import CalendarService
from src.services.supabase_service import SupabaseService
from src.services.agent_service_integration import AgentServiceIntegration
from src.utils.http_client import AsyncHttpClient
from src.security.middleware import SecurityMiddleware, get_api_key_auth, verify_webhook
from src.services.performance_monitor import PerformanceMonitor

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Lunia WhatsApp Agent API...")
    
    # Store startup time for uptime calculation
    import time
    app.state.start_time = time.time()
    
    # Initialize performance monitor
    if settings.ENABLE_METRICS:
        app.state.performance_monitor = PerformanceMonitor()
        await app.state.performance_monitor.start()
    
    # Validate configuration
    if not hasattr(settings, 'OPENAI_API_KEY') or not settings.OPENAI_API_KEY:
        logger.error("Configuration validation failed")
        raise RuntimeError("Invalid configuration")
    
    # Initialize services
    app.state.whatsapp_service = whatsapp_service
    app.state.email_service = EmailService()
    app.state.calendar_service = CalendarService()
    app.state.supabase_service = SupabaseService()
    
    # Initialize service integration
    app.state.service_integration = AgentServiceIntegration(
        email_service=app.state.email_service,
        calendar_service=app.state.calendar_service,
        supabase_service=app.state.supabase_service
    )
    
    # Set service integration in the agent
    lunia_agent.set_service_integration(app.state.service_integration)

    # Initialize knowledge base
    if not knowledge_base.initialize():
        logger.warning("Knowledge base initialization failed")
    
    logger.info("API startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Lunia WhatsApp Agent API...")
    # Close HTTP client sessions
    await AsyncHttpClient.close()
    await app.state.whatsapp_service.close()

# Create FastAPI app
app = FastAPI(
    title="Lunia WhatsApp Agent API",
    description="""
    ## Lunia WhatsApp Agent - AI Conversational Assistant

    A comprehensive AI-powered WhatsApp agent with integrated services including:
    - **Intelligent Conversations**: Natural language processing with context awareness
    - **Email Integration**: Send emails through natural language commands
    - **Calendar Management**: Create and manage calendar events
    - **Knowledge Base**: Query and retrieve information from documents
    - **Session Management**: Persistent conversation history
    - **Service Integration**: Automated service actions based on user requests

    ### Key Features
    - Multi-language support (English/Spanish)
    - Automatic service action detection and execution
    - Real-time monitoring and metrics
    - Comprehensive API documentation
    - Production-ready deployment

    ### Authentication
    API key authentication required for protected endpoints.
    Include `X-API-Key` header with your API key.

    ### Rate Limits
    - Webhook endpoints: 50 requests/second
    - API endpoints: 10 requests/second
    - Burst limits apply with delayed processing

    ### Support
    For technical support, please contact the development team.
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else ["https://your-domain.com"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security middleware
security_middleware = SecurityMiddleware()
app.add_middleware(SecurityMiddleware)

# Security dependency
security = HTTPBearer(auto_error=False)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Lunia WhatsApp Agent API",
        "version": settings.VERSION,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint"""
    try:
        # Check Evolution API status
        whatsapp_status = False
        instance_status = None
        
        if whatsapp_service._validate_api_config():
            instance_status = await whatsapp_service.get_instance_status()
            whatsapp_status = instance_status is not None
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "whatsapp": {
                    "configured": whatsapp_service._validate_api_config(),
                    "connected": whatsapp_status,
                    "instance_status": instance_status
                },
                "knowledge_base": {
                    "initialized": knowledge_base._initialized,
                    "document_count": getattr(knowledge_base, '_document_count', 0)
                },                "openai": {
                    "configured": bool(settings.OPENAI_API_KEY),
                    "transcription_available": whatsapp_service.openai_client is not None
                },
                "session_manager": {
                    "active_sessions": len(getattr(session_manager, '_sessions', {}))
                }
            }
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(
    request: Request, 
    background_tasks: BackgroundTasks,
    verified: bool = Depends(verify_webhook)
):
    """
    WhatsApp webhook endpoint
    
    Receives messages from Evolution API and processes them
    """
    try:
        payload = await request.json()
        logger.info(f"Received webhook: {payload.get('event', 'unknown')}")
        
        # Parse the message
        message = whatsapp_service.parse_webhook_message(payload)
        
        if not message:
            logger.warning("Failed to parse webhook message")
            return JSONResponse(
                status_code=200,
                content={"status": "ignored", "reason": "invalid_message"}
            )
        
        # Process message in background
        background_tasks.add_task(process_message_background, message)
        
        return JSONResponse(
            status_code=200,
            content={"status": "accepted"}
        )
    
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

async def process_message_background(message):
    """Process message in background with enhanced error handling"""
    try:
        logger.info(f"Processing message from {message.sender}: {message.content[:50]}...")
        
        # Handle audio transcription if needed
        if message.message_type == MessageType.AUDIO and message.audio_url:
            logger.info("Transcribing audio message...")
            transcription = await whatsapp_service.transcribe_audio_async(message.audio_url)
            if transcription:
                message.content = transcription
                logger.info(f"Audio transcribed: {transcription[:50]}...")
            else:
                message.content = "Lo siento, no pude procesar el mensaje de audio. ¿Podrías escribir tu pregunta?"
        
        # Create agent state with enhanced metadata
        state = AgentState(
            input_message=message.content,
            sender_phone=message.sender,
            message_type=message.message_type,
            conversation_history=[],
            session_id=f"session_{message.sender}",
            processing_start_time=datetime.now(),
            raw_message_data=message.raw_data
        )
        
        # Add conversation history from session manager
        session = await session_manager.get_session(message.sender)
        if session:
            state.conversation_history = [
                {"role": turn.role.value, "content": turn.content, "timestamp": turn.timestamp}
                for turn in session.get_recent_history(10)
            ]
        
        # Send typing indicator
        await whatsapp_service.send_typing(message.sender)
        
        # Process through agent
        result_state = await lunia_agent.process_message(state)
        
        # Send response if generated
        if result_state.response and result_state.response.strip():
            success = await whatsapp_service.send_message(
                message.sender, 
                result_state.response
            )
            
            if success:
                # Save conversation to session
                await session_manager.add_message(
                    message.sender, 
                    ConversationRole.USER, 
                    message.content,
                    {"message_type": message.message_type.value}
                )
                await session_manager.add_message(
                    message.sender, 
                    ConversationRole.ASSISTANT, 
                    result_state.response,
                    {
                        "intent": result_state.detected_intent,
                        "processing_time": result_state.processing_time,
                        "confidence": result_state.confidence_level
                    }
                )
                logger.info(f"Response sent successfully to {message.sender}")
            else:
                logger.error(f"Failed to send response to {message.sender}")
        else:
            logger.warning(f"No response generated for message from {message.sender}")
        
    except Exception as e:
        logger.error(f"Background message processing error: {e}")
        
        # Send error message to user
        try:
            error_message = "Lo siento, hubo un error procesando tu mensaje. Por favor intenta de nuevo."
            await whatsapp_service.send_message(message.sender, error_message)
        except Exception as send_error:
            logger.error(f"Failed to send error message: {send_error}")

@app.post("/api/send-message")
async def send_message_api(
    payload: Dict[str, Any],
    api_key: str = Depends(get_api_key_auth)
):
    """
    Send message via API with enhanced validation
    
    Body:
    {
        "phone": "+1234567890",
        "message": "Hello world",  
        "options": {  # Optional
            "delay": 1200,
            "presence": "composing"
        }
    }
    """
    try:
        phone = payload.get("phone")
        message = payload.get("message")
        options = payload.get("options")
        
        if not phone or not message:
            raise HTTPException(status_code=400, detail="Phone and message are required")
        
        # Validate phone number format
        if not phone.startswith('+'):
            raise HTTPException(status_code=400, detail="Phone number must include country code (e.g., +1234567890)")
        
        # Clean phone number
        clean_phone = phone.replace('+', '').replace('-', '').replace(' ', '')
        if not clean_phone.isdigit() or len(clean_phone) < 10:
            raise HTTPException(status_code=400, detail="Invalid phone number format")
        
        success = await whatsapp_service.send_message(clean_phone, message, options)
        
        if success:
            return {
                "status": "sent", 
                "phone": phone,
                "message_length": len(message),
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send message")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send message API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/knowledge-base/query")
async def query_knowledge_base(
    payload: Dict[str, Any],
    api_key: str = Depends(get_api_key_auth)
):
    """
    Query knowledge base directly with enhanced context
    
    Body:
    {
        "question": "What services do you offer?",
        "context": "Optional context for the query"
    }
    """
    try:
        question = payload.get("question")
        context = payload.get("context", "")
        
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        # Use async query method
        answer = await knowledge_base.query_async(question, context=context)
        
        return {
            "question": question,
            "answer": answer,
            "context_provided": bool(context),
            "status": "success" if answer else "no_answer",
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Knowledge base query API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/knowledge-base/rebuild")
async def rebuild_knowledge_base(api_key: str = Depends(get_api_key_auth)):
    """Rebuild knowledge base index asynchronously"""
    try:
        success = await knowledge_base.rebuild_index_async()
        
        if success:
            return {
                "status": "rebuilt", 
                "message": "Knowledge base index rebuilt successfully",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to rebuild knowledge base")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Knowledge base rebuild API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions/{user_id}")
async def get_user_session(
    user_id: str,
    api_key: str = Depends(get_api_key_auth)
):
    """Get user session information"""
    try:
        session = await session_manager.get_session(user_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "user_id": session.user_id,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "conversation_turns": len(session.conversation_history),
            "recent_history": [
                {
                    "role": turn.role.value,
                    "content": turn.content[:100] + "..." if len(turn.content) > 100 else turn.content,
                    "timestamp": turn.timestamp.isoformat()
                }
                for turn in session.get_recent_history(5)
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get session API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/sessions/{user_id}")
async def delete_user_session(
    user_id: str,
    api_key: str = Depends(get_api_key_auth)
):
    """Delete user session"""
    try:
        success = await session_manager.delete_session(user_id)
        
        return {
            "status": "deleted" if success else "not_found",
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Delete session API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sessions/cleanup")
async def cleanup_expired_sessions(api_key: str = Depends(get_api_key_auth)):
    """Clean up expired sessions"""
    try:
        await session_manager.cleanup_expired_sessions()
        
        return {
            "status": "cleanup_completed",
            "message": "Expired sessions cleaned up successfully",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Session cleanup API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    try:
        stats = {
            "system": {
                "uptime": "N/A",  # Could be implemented with startup time tracking
                "version": settings.VERSION,
                "environment": settings.ENVIRONMENT
            },
            "sessions": {
                "active_count": len(getattr(session_manager, '_sessions', {})),
                "total_conversations": sum(
                    len(session.conversation_history) 
                    for session in getattr(session_manager, '_sessions', {}).values()
                )
            },
            "knowledge_base": {
                "initialized": knowledge_base._initialized,
                "document_count": getattr(knowledge_base, '_document_count', 0),
                "query_count": getattr(knowledge_base, '_query_count', 0)
            },
            "whatsapp": {
                "configured": whatsapp_service._validate_api_config(),
                "last_message_time": whatsapp_service.last_message_time
            }
        }
        
        return {
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Stats API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test/message")
async def test_message_processing(
    payload: Dict[str, Any],
    api_key: str = Depends(get_api_key_auth)
):
    """Test message processing without sending via WhatsApp"""
    try:
        message_content = payload.get("message", "")
        sender = payload.get("sender", "test_user") 
        
        if not message_content:
            raise HTTPException(status_code=400, detail="Message content is required")
        
        # Create test agent state
        state = AgentState(
            input_message=message_content,
            sender_phone=sender,
            message_type=MessageType.TEXT,
            conversation_history=[],
            session_id=f"test_session_{sender}",
            processing_start_time=datetime.now()
        )
        
        # Process through agent
        result_state = await lunia_agent.process_message(state)
        
        return {
            "input": message_content,
            "response": result_state.response,
            "intent": result_state.detected_intent,
            "confidence": result_state.confidence_level,
            "processing_time": result_state.processing_time,
            "status": "processed",
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test message processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== EMAIL ENDPOINTS ====================

class EmailRequest(BaseModel):
    to_email: EmailStr
    subject: str
    body: str
    cc: Optional[List[EmailStr]] = None
    bcc: Optional[List[EmailStr]] = None
    html_body: Optional[str] = None

@app.post("/api/email/send")
async def send_email_api(
    email_request: EmailRequest,
    api_key: str = Depends(get_api_key_auth)
):
    """Send email via Gmail SMTP"""
    try:
        success = await app.state.email_service.send_email(
            to_email=email_request.to_email,
            subject=email_request.subject,
            body=email_request.body,
            cc=email_request.cc,
            bcc=email_request.bcc,
            html_body=email_request.html_body
        )
        
        if success:
            return {
                "status": "sent",
                "to": email_request.to_email,
                "subject": email_request.subject,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send email")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send email API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/email/status")
async def email_service_status():
    """Check email service configuration status"""
    try:
        status = await app.state.email_service.test_connection()
        return {
            "configured": status,
            "service": "Gmail SMTP",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Email status check error: {e}")
        return {
            "configured": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ==================== CALENDAR ENDPOINTS ====================

class EventRequest(BaseModel):
    summary: str
    description: Optional[str] = None
    start_datetime: datetime
    end_datetime: datetime
    attendees: Optional[List[EmailStr]] = None
    location: Optional[str] = None

class EventUpdateRequest(BaseModel):
    summary: Optional[str] = None
    description: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    attendees: Optional[List[EmailStr]] = None
    location: Optional[str] = None

@app.post("/api/calendar/events")
async def create_calendar_event(
    event_request: EventRequest,
    api_key: str = Depends(get_api_key_auth)
):
    """Create a new calendar event"""
    try:
        event_id = await app.state.calendar_service.create_event(
            summary=event_request.summary,
            description=event_request.description,
            start_datetime=event_request.start_datetime,
            end_datetime=event_request.end_datetime,
            attendees=event_request.attendees,
            location=event_request.location
        )
        
        if event_id:
            return {
                "status": "created",
                "event_id": event_id,
                "summary": event_request.summary,
                "start_time": event_request.start_datetime.isoformat(),
                "end_time": event_request.end_datetime.isoformat(),
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create calendar event")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create calendar event API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/calendar/events")
async def list_calendar_events(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    max_results: int = 50
):
    """List calendar events within date range"""
    try:
        events = await app.state.calendar_service.list_events(
            start_date=start_date,
            end_date=end_date,
            max_results=max_results
        )
        
        return {
            "events": events,
            "count": len(events),
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"List calendar events API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/calendar/events/{event_id}")
async def get_calendar_event(event_id: str):
    """Get specific calendar event by ID"""
    try:
        event = await app.state.calendar_service.get_event(event_id)
        
        if event:
            return {
                "event": event,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="Event not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get calendar event API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/calendar/events/{event_id}")
async def update_calendar_event(
    event_id: str, 
    event_update: EventUpdateRequest,
    api_key: str = Depends(get_api_key_auth)
):
    """Update existing calendar event"""
    try:
        # Convert None values to exclude them from update
        update_data = {k: v for k, v in event_update.dict().items() if v is not None}
        
        success = await app.state.calendar_service.update_event(event_id, **update_data)
        
        if success:
            return {
                "status": "updated",
                "event_id": event_id,
                "updated_fields": list(update_data.keys()),
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="Event not found or update failed")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update calendar event API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/calendar/events/{event_id}")
async def delete_calendar_event(
    event_id: str,
    api_key: str = Depends(get_api_key_auth)
):
    """Delete calendar event"""
    try:
        success = await app.state.calendar_service.delete_event(event_id)
        
        if success:
            return {
                "status": "deleted",
                "event_id": event_id,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="Event not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete calendar event API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/calendar/status")
async def calendar_service_status():
    """Check calendar service authentication status"""
    try:
        status = await app.state.calendar_service.test_connection()
        return {
            "authenticated": status,
            "service": "Google Calendar API",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Calendar status check error: {e}")
        return {
            "authenticated": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ==================== DATABASE ENDPOINTS ====================

class DatabaseRecord(BaseModel):
    table: str
    data: Dict[str, Any]

class DatabaseQuery(BaseModel):
    table: str
    filters: Optional[Dict[str, Any]] = None
    columns: Optional[List[str]] = None
    limit: Optional[int] = 100
    offset: Optional[int] = 0

@app.post("/api/database/insert")
async def insert_database_record(
    record: DatabaseRecord,
    api_key: str = Depends(get_api_key_auth)
):
    """Insert new record into Supabase table"""
    try:
        result = await app.state.supabase_service.insert(record.table, record.data)
        
        if result:
            return {
                "status": "inserted",
                "table": record.table,
                "data": result,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to insert record")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database insert API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/database/query")
async def query_database(
    query: DatabaseQuery,
    api_key: str = Depends(get_api_key_auth)
):
    """Query records from Supabase table"""
    try:
        results = await app.state.supabase_service.select(
            table=query.table,
            columns=query.columns,
            filters=query.filters,
            limit=query.limit,
            offset=query.offset
        )
        
        return {
            "results": results,
            "table": query.table,
            "count": len(results) if results else 0,
            "filters": query.filters,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Database query API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/database/update/{table_name}")
async def update_database_record(
    table_name: str,
    filters: Dict[str, Any],
    updates: Dict[str, Any],
    api_key: str = Depends(get_api_key_auth)
):
    """Update records in Supabase table"""
    try:
        result = await app.state.supabase_service.update(
            table=table_name,
            filters=filters,
            updates=updates
        )
        
        if result:
            return {
                "status": "updated",
                "table": table_name,
                "filters": filters,
                "updates": updates,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="No records found to update")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database update API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/database/delete/{table_name}")
async def delete_database_record(
    table_name: str, 
    filters: Dict[str, Any],
    api_key: str = Depends(get_api_key_auth)
):
    """Delete records from Supabase table"""
    try:
        success = await app.state.supabase_service.delete(
            table=table_name,
            filters=filters
        )
        
        if success:
            return {
                "status": "deleted",
                "table": table_name,
                "filters": filters,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="No records found to delete")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database delete API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/database/status")
async def database_service_status():
    """Check Supabase database connection status"""
    try:
        status = await app.state.supabase_service.test_connection()
        return {
            "connected": status,
            "service": "Supabase",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Database status check error: {e}")
        return {
            "connected": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ==================== METRICS & MONITORING ====================

@app.get("/api/metrics")
async def get_system_metrics():
    """Get comprehensive system metrics for monitoring"""
    try:
        import psutil
        import time
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Application metrics
        uptime_seconds = time.time() - getattr(app.state, 'start_time', time.time())
        
        metrics = {
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                }
            },            "application": {
                "uptime_seconds": uptime_seconds,
                "version": settings.VERSION,
                "environment": settings.ENVIRONMENT
            },
            "services": {
                "whatsapp": {
                    "configured": whatsapp_service._validate_api_config(),
                    "last_message_time": getattr(whatsapp_service, 'last_message_time', None)
                },                "email": {
                    "configured": bool(getattr(settings, 'SMTP_USER', None))
                },
                "calendar": {
                    "configured": bool(getattr(settings, 'GOOGLE_SERVICE_ACCOUNT_FILE', None))
                },
                "database": {
                    "configured": bool(getattr(settings, 'SUPABASE_URL', None))
                }
            },
            "sessions": {
                "active_count": len(getattr(session_manager, '_sessions', {})),
                "total_conversations": sum(
                    len(session.conversation_history) 
                    for session in getattr(session_manager, '_sessions', {}).values()
                )
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return metrics
    
    except ImportError:
        # psutil not available, return basic metrics
        return {
            "system": {"status": "metrics_limited"},            "application": {
                "version": settings.VERSION,
                "environment": settings.ENVIRONMENT
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Metrics API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )
