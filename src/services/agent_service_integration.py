# Business Logic Integration
# This module provides the integration layer between the AI agent and external services

import re
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from email.utils import parseaddr

from src.core.logger import logger
from src.services.email_service import EmailService
from src.services.calendar_service import CalendarService
from src.services.supabase_service import SupabaseService


class AgentServiceIntegration:
    """
    Business logic integration for AI agent to interact with external services
    """
    
    def __init__(
        self,
        email_service: EmailService,
        calendar_service: CalendarService,
        supabase_service: SupabaseService
    ):
        self.email_service = email_service
        self.calendar_service = calendar_service
        self.supabase_service = supabase_service
        
        # Intent patterns for service actions
        self.email_patterns = [
            r'send\s+email\s+to\s+([^\s]+)',
            r'email\s+([^\s]+)\s+about\s+(.+)',
            r'enviar\s+correo\s+a\s+([^\s]+)',
            r'mandar\s+email\s+a\s+([^\s]+)'
        ]
        
        self.calendar_patterns = [
            r'schedule\s+meeting\s+(.+)',
            r'create\s+appointment\s+(.+)',
            r'book\s+(.+)\s+on\s+(.+)',
            r'programar\s+cita\s+(.+)',
            r'agendar\s+(.+)\s+para\s+(.+)'
        ]
        
        self.reminder_patterns = [
            r'remind\s+me\s+(.+)',
            r'set\s+reminder\s+(.+)',
            r'recordarme\s+(.+)',
            r'crear\s+recordatorio\s+(.+)'
        ]

    async def process_service_intent(
        self, 
        message: str, 
        user_id: str, 
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process message to detect and execute service-related intents
        
        Returns:
            Dict with action taken, success status, and response message
        """
        message_lower = message.lower()
        context = context or {}
        
        # Check for email intent
        email_action = await self._check_email_intent(message, message_lower, user_id, context)
        if email_action:
            return email_action
        
        # Check for calendar intent
        calendar_action = await self._check_calendar_intent(message, message_lower, user_id, context)
        if calendar_action:
            return calendar_action
        
        # Check for reminder intent
        reminder_action = await self._check_reminder_intent(message, message_lower, user_id, context)
        if reminder_action:
            return reminder_action
        
        # Check for data query intent
        data_action = await self._check_data_intent(message, message_lower, user_id, context)
        if data_action:
            return data_action
        
        return {
            "action": "none",
            "success": False,
            "message": "No service action detected"
        }

    async def _check_email_intent(
        self, 
        message: str, 
        message_lower: str, 
        user_id: str, 
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check and process email-related intents"""
        
        for pattern in self.email_patterns:
            match = re.search(pattern, message_lower)
            if match:
                try:
                    # Extract email and content
                    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', message)
                    if not email_match:
                        return {
                            "action": "email_error",
                            "success": False,
                            "message": "No se encontró una dirección de email válida en el mensaje."
                        }
                    
                    recipient_email = email_match.group()
                    
                    # Extract subject and body from context or generate
                    subject = self._extract_email_subject(message) or f"Mensaje de {user_id}"
                    body = self._extract_email_body(message, recipient_email)
                    
                    # Send email
                    success = await self.email_service.send_email(
                        to_email=recipient_email,
                        subject=subject,
                        body=body
                    )
                    
                    if success:
                        # Log the action
                        await self._log_service_action(
                            user_id=user_id,
                            action_type="email_sent",
                            details={
                                "recipient": recipient_email,
                                "subject": subject,
                                "body_length": len(body)
                            }
                        )
                        
                        return {
                            "action": "email_sent",
                            "success": True,
                            "message": f"✅ Email enviado exitosamente a {recipient_email}",
                            "details": {
                                "recipient": recipient_email,
                                "subject": subject
                            }
                        }
                    else:
                        return {
                            "action": "email_error",
                            "success": False,
                            "message": "❌ Error al enviar el email. Verifica la configuración."
                        }
                        
                except Exception as e:
                    logger.error(f"Email intent processing error: {e}")
                    return {
                        "action": "email_error",
                        "success": False,
                        "message": f"❌ Error procesando el email: {str(e)}"
                    }
        
        return None

    async def _check_calendar_intent(
        self, 
        message: str, 
        message_lower: str, 
        user_id: str, 
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check and process calendar-related intents"""
        
        for pattern in self.calendar_patterns:
            match = re.search(pattern, message_lower)
            if match:
                try:
                    # Extract event details
                    event_details = self._extract_event_details(message)
                    
                    if not event_details:
                        return {
                            "action": "calendar_error",
                            "success": False,
                            "message": "No pude extraer los detalles del evento. Por favor proporciona más información."
                        }
                    
                    # Create calendar event
                    event_id = await self.calendar_service.create_event(
                        summary=event_details["summary"],
                        description=event_details.get("description", ""),
                        start_datetime=event_details["start_datetime"],
                        end_datetime=event_details["end_datetime"],
                        attendees=event_details.get("attendees"),
                        location=event_details.get("location")
                    )
                    
                    if event_id:
                        # Log the action
                        await self._log_service_action(
                            user_id=user_id,
                            action_type="calendar_event_created",
                            details={
                                "event_id": event_id,
                                "summary": event_details["summary"],
                                "start_time": event_details["start_datetime"].isoformat()
                            }
                        )
                        
                        return {
                            "action": "calendar_event_created",
                            "success": True,
                            "message": f"📅 Evento creado: {event_details['summary']} para {event_details['start_datetime'].strftime('%Y-%m-%d %H:%M')}",
                            "details": {
                                "event_id": event_id,
                                "summary": event_details["summary"],
                                "start_time": event_details["start_datetime"].isoformat()
                            }
                        }
                    else:
                        return {
                            "action": "calendar_error",
                            "success": False,
                            "message": "❌ Error al crear el evento en el calendario."
                        }
                        
                except Exception as e:
                    logger.error(f"Calendar intent processing error: {e}")
                    return {
                        "action": "calendar_error",
                        "success": False,
                        "message": f"❌ Error procesando el evento: {str(e)}"
                    }
        
        return None

    async def _check_reminder_intent(
        self, 
        message: str, 
        message_lower: str, 
        user_id: str, 
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check and process reminder-related intents"""
        
        for pattern in self.reminder_patterns:
            match = re.search(pattern, message_lower)
            if match:
                try:
                    # Extract reminder details
                    reminder_text = match.group(1)
                    reminder_time = self._extract_reminder_time(message)
                    
                    if not reminder_time:
                        # Default to 1 hour from now
                        reminder_time = datetime.now() + timedelta(hours=1)
                    
                    # Create calendar event as reminder
                    event_id = await self.calendar_service.create_event(
                        summary=f"🔔 Recordatorio: {reminder_text}",
                        description=f"Recordatorio solicitado por usuario {user_id}",
                        start_datetime=reminder_time,
                        end_datetime=reminder_time + timedelta(minutes=15)
                    )
                    
                    if event_id:
                        # Also store in database for additional tracking
                        await self.supabase_service.insert("reminders", {
                            "user_id": user_id,
                            "reminder_text": reminder_text,
                            "reminder_time": reminder_time.isoformat(),
                            "event_id": event_id,
                            "status": "active",
                            "created_at": datetime.now().isoformat()
                        })
                        
                        return {
                            "action": "reminder_created",
                            "success": True,
                            "message": f"⏰ Recordatorio creado: {reminder_text} para {reminder_time.strftime('%Y-%m-%d %H:%M')}",
                            "details": {
                                "event_id": event_id,
                                "reminder_text": reminder_text,
                                "reminder_time": reminder_time.isoformat()
                            }
                        }
                    else:
                        return {
                            "action": "reminder_error",
                            "success": False,
                            "message": "❌ Error al crear el recordatorio."
                        }
                        
                except Exception as e:
                    logger.error(f"Reminder intent processing error: {e}")
                    return {
                        "action": "reminder_error",
                        "success": False,
                        "message": f"❌ Error procesando el recordatorio: {str(e)}"
                    }
        
        return None

    async def _check_data_intent(
        self, 
        message: str, 
        message_lower: str, 
        user_id: str, 
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check and process data query intents"""
        
        data_keywords = [
            "show me", "get", "find", "search", "list", "query",
            "muestra", "busca", "encuentra", "lista", "consulta"
        ]
        
        if any(keyword in message_lower for keyword in data_keywords):
            try:
                # Store the query for later analysis
                await self.supabase_service.insert("user_queries", {
                    "user_id": user_id,
                    "query": message,
                    "query_type": "data_request",
                    "timestamp": datetime.now().isoformat(),
                    "processed": False
                })
                
                return {
                    "action": "data_query_logged",
                    "success": True,
                    "message": "📊 Tu consulta ha sido registrada para procesamiento.",
                    "details": {
                        "query": message,
                        "user_id": user_id
                    }
                }
                
            except Exception as e:
                logger.error(f"Data intent processing error: {e}")
                return {
                    "action": "data_error",
                    "success": False,
                    "message": f"❌ Error procesando la consulta: {str(e)}"
                }
        
        return None

    def _extract_email_subject(self, message: str) -> Optional[str]:
        """Extract email subject from message"""
        subject_patterns = [
            r'subject[:\s]+(.+)',
            r'asunto[:\s]+(.+)',
            r'titulo[:\s]+(.+)'
        ]
        
        for pattern in subject_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None

    def _extract_email_body(self, message: str, recipient: str) -> str:
        """Extract or generate email body from message"""
        # Remove email address and common patterns
        body = message
        body = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '', body)
        body = re.sub(r'send\s+email\s+to', '', body, flags=re.IGNORECASE)
        body = re.sub(r'enviar\s+correo\s+a', '', body, flags=re.IGNORECASE)
        body = body.strip()
        
        if len(body) < 10:
            return f"Mensaje enviado desde el asistente WhatsApp de Lunia Soluciones.\n\nContenido: {message}"
        
        return body

    def _extract_event_details(self, message: str) -> Optional[Dict[str, Any]]:
        """Extract event details from message"""
        try:
            # Simple extraction - in production, use more sophisticated NLP
            event_details = {}
            
            # Extract summary (first part before time/date info)
            summary_match = re.search(r'(schedule|create|book|programar|agendar)\s+([^0-9]+)', message, re.IGNORECASE)
            if summary_match:
                event_details["summary"] = summary_match.group(2).strip()
            else:
                event_details["summary"] = "Reunión programada desde WhatsApp"
            
            # Extract date/time - simplified version
            time_info = self._extract_datetime_from_message(message)
            if time_info:
                event_details["start_datetime"] = time_info
                event_details["end_datetime"] = time_info + timedelta(hours=1)
            else:
                # Default to next hour
                next_hour = datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
                event_details["start_datetime"] = next_hour
                event_details["end_datetime"] = next_hour + timedelta(hours=1)
            
            # Extract emails for attendees
            attendee_emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', message)
            if attendee_emails:
                event_details["attendees"] = attendee_emails
            
            return event_details
            
        except Exception as e:
            logger.error(f"Event details extraction error: {e}")
            return None

    def _extract_datetime_from_message(self, message: str) -> Optional[datetime]:
        """Extract datetime from message - simplified version"""
        # This is a basic implementation - in production, use proper datetime parsing
        now = datetime.now()
        
        if "tomorrow" in message.lower() or "mañana" in message.lower():
            return now + timedelta(days=1)
        elif "next week" in message.lower() or "próxima semana" in message.lower():
            return now + timedelta(weeks=1)
        elif "today" in message.lower() or "hoy" in message.lower():
            return now + timedelta(hours=1)
        
        # Try to extract time patterns like "at 3pm", "a las 15:00"
        time_patterns = [
            r'at\s+(\d{1,2}):?(\d{2})?\s*(pm|am)?',
            r'a\s+las\s+(\d{1,2}):?(\d{2})?'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, message.lower())
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2)) if match.group(2) else 0
                
                if match.group(3) and match.group(3).lower() == 'pm' and hour < 12:
                    hour += 12
                
                target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if target_time < now:
                    target_time += timedelta(days=1)
                
                return target_time
        
        return None

    def _extract_reminder_time(self, message: str) -> Optional[datetime]:
        """Extract reminder time from message"""
        now = datetime.now()
        
        # Time-based patterns
        if "in 1 hour" in message.lower() or "en 1 hora" in message.lower():
            return now + timedelta(hours=1)
        elif "in 30 minutes" in message.lower() or "en 30 minutos" in message.lower():
            return now + timedelta(minutes=30)
        elif "tomorrow" in message.lower() or "mañana" in message.lower():
            return now + timedelta(days=1)
        
        # Use same datetime extraction as events
        return self._extract_datetime_from_message(message)

    async def _log_service_action(
        self, 
        user_id: str, 
        action_type: str, 
        details: Dict[str, Any]
    ):
        """Log service actions to database for analytics"""
        try:
            await self.supabase_service.insert("service_actions", {
                "user_id": user_id,
                "action_type": action_type,
                "details": details,
                "timestamp": datetime.now().isoformat(),
                "success": True
            })
        except Exception as e:
            logger.error(f"Failed to log service action: {e}")

    async def get_user_service_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's service action history"""
        try:
            history = await self.supabase_service.select(
                table="service_actions",
                filters={"user_id": user_id},
                limit=limit
            )
            return history or []
        except Exception as e:
            logger.error(f"Failed to get user service history: {e}")
            return []

    async def get_service_statistics(self) -> Dict[str, Any]:
        """Get service usage statistics"""
        try:
            # Get action counts by type
            actions = await self.supabase_service.select("service_actions")
            
            if not actions:
                return {"total_actions": 0, "action_types": {}}
            
            action_counts = {}
            for action in actions:
                action_type = action.get("action_type", "unknown")
                action_counts[action_type] = action_counts.get(action_type, 0) + 1
            
            return {
                "total_actions": len(actions),
                "action_types": action_counts,
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get service statistics: {e}")
            return {"error": str(e)}
