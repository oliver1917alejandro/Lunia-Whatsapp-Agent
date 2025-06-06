# Enhanced Lunia WhatsApp Agent with Service Integration
from typing import Optional, Dict, Any, List
import asyncio
from langgraph.graph import StateGraph, END
from src.models.schemas import AgentState, ConversationRole, MessageType
from src.services.knowledge_base import knowledge_base
from src.services.session_manager import session_manager
from src.services.whatsapp_service import whatsapp_service
from src.core.logger import logger
from src.core.config import Config
from src.services.agent_service_integration import AgentServiceIntegration


class LuniaAgent:
    """Enhanced Lunia WhatsApp Agent using LangGraph with robust error handling and conversation flow"""
    
    def __init__(self, service_integration: Optional[AgentServiceIntegration] = None):
        self.graph = self._create_graph()
        self.compiled_graph = self.graph.compile()
        self._max_message_length = 4000  # WhatsApp limit
        self._conversation_timeout = 1800  # 30 minutes
        self.service_integration = service_integration
        
    def set_service_integration(self, service_integration: AgentServiceIntegration):
        """Set the service integration layer"""
        self.service_integration = service_integration

    def _create_graph(self) -> StateGraph:
        """Create the enhanced LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("validate_input", self._validate_input_node)
        workflow.add_node("process_message", self._process_message_node)
        workflow.add_node("generate_response", self._generate_response_node)
        workflow.add_node("send_response", self._send_response_node)
        workflow.add_node("handle_error", self._handle_error_node)
        
        # Set entry point
        workflow.set_entry_point("validate_input")
        
        # Add edges
        workflow.add_conditional_edges(
            "validate_input",
            self._should_continue_after_validation,
            {
                "continue": "process_message",
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("process_message", "generate_response")
        workflow.add_edge("generate_response", "send_response")
        workflow.add_edge("send_response", END)
        workflow.add_edge("handle_error", END)
        
        return workflow

    async def process_message(self, state: AgentState) -> AgentState:
        """Process incoming message through the enhanced agent workflow"""
        try:
            logger.info(f"Processing message from {state.sender_phone}: {state.input_message[:100]}")
            
            # Add processing timestamp
            state.timestamp = asyncio.get_event_loop().time()
            
            # Run through the graph
            result = await asyncio.wait_for(
                self._run_graph_async(state),
                timeout=60.0
            )
            
            # Handle knowledge base query if needed
            if not result.response and result.intent not in ["greeting", "goodbye"]:
                kb_response = await self._query_knowledge_base_async(result.input_message, result)
                if kb_response:
                    result.response = kb_response
                else:
                    result.response = self._generate_fallback_response()
                
                # Send the response if not already sent
                if not result.response_sent and result.response:
                    success = whatsapp_service.send_message(result.sender_phone, result.response)
                    result.response_sent = success
            
            # Update session with conversation data
            await self._update_session_async(result)
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Message processing timed out for {state.sender_phone}")
            return await self._create_error_response(state, "Request timed out. Please try again.")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return await self._create_error_response(state, "I encountered an error processing your request. Please try again.")

    async def _run_graph_async(self, state: AgentState) -> AgentState:
        """Run the graph asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.compiled_graph.invoke, state)

    async def _create_error_response(self, state: AgentState, error_message: str) -> AgentState:
        """Create a standardized error response"""
        state.response = error_message
        state.message_type = MessageType.ERROR
        
        # Try to send error message
        try:
            success = whatsapp_service.send_message(state.sender_phone, error_message)
            state.response_sent = success
        except Exception as send_error:
            logger.error(f"Failed to send error message: {send_error}")
        
        return state

    async def _query_knowledge_base_async(self, message: str, state: AgentState) -> Optional[str]:
        """Query knowledge base asynchronously with context"""
        try:
            # Prepare context from conversation history
            context = ""
            if state.conversation_history:
                recent_turns = state.conversation_history[-3:]  # Last 3 turns
                context = " ".join([f"{role}: {content}" for role, content in recent_turns])
            
            # Query knowledge base
            response = await knowledge_base.query(message, context)
            
            if response:
                logger.debug(f"Knowledge base response: {response[:100]}...")
                return response
            
            return None
            
        except Exception as e:
            logger.error(f"Knowledge base query error: {e}")
            return None

    async def _update_session_async(self, state: AgentState):
        """Update session with conversation data asynchronously"""
        try:
            # Add user message
            await session_manager.add_message(
                state.sender_phone,
                ConversationRole.USER,
                state.input_message
            )
            
            # Add assistant response if available
            if state.response:
                await session_manager.add_message(
                    state.sender_phone,
                    ConversationRole.ASSISTANT,
                    state.response
                )
            
            state.session_updated = True
            logger.debug(f"Session updated for {state.sender_phone}")
            
        except Exception as e:
            logger.error(f"Session update error: {e}")
            if hasattr(state, 'processing_errors'):
                state.processing_errors.append(f"Session update error: {str(e)}")

    # Workflow Nodes
    def _validate_input_node(self, state: AgentState) -> AgentState:
        """Validate and sanitize input message"""
        try:
            message = state.input_message.strip()
            
            # Basic validation
            if not message:
                state.validation_error = "Empty message received"
                return state
            
            if len(message) > self._max_message_length * 2:
                state.validation_error = "Message too long"
                return state
            
            # Sanitize message
            state.input_message = message
            state.message_length = len(message)
            
            logger.debug(f"Input validated for {state.sender_phone}")
            return state
            
        except Exception as e:
            logger.error(f"Input validation error: {e}")
            state.validation_error = "Validation failed"
            return state

    async def _process_message_node(self, state: AgentState) -> AgentState:
        """Enhanced message processing with intent detection, analysis, and service integration"""
        try:
            logger.debug(f"Processing message node for {state.sender_phone}")
            
            message = state.input_message.lower().strip()
            
            # Check for service intents first if integration is available
            if self.service_integration:
                logger.debug("Checking for service intents...")
                service_result = await self.service_integration.process_service_intent(
                    state.input_message,
                    state.sender_phone,
                    context={"conversation_history": state.conversation_history}
                )
                
                if service_result and service_result.get("success"):
                    # Service action was executed successfully
                    state.service_action_taken = True
                    state.service_action_result = service_result
                    state.response = service_result.get("message", "Acción completada exitosamente.")
                    state.intent = f"service_{service_result.get('action', 'unknown')}"
                    state.confidence = 0.95
                    logger.info(f"Service action executed: {service_result.get('action')}")
                    return state
                elif service_result and not service_result.get("success"):
                    # Service action failed
                    state.service_action_taken = True
                    state.service_action_result = service_result
                    state.service_error = service_result.get("message", "Error en la acción de servicio.")
                    logger.warning(f"Service action failed: {service_result.get('message')}")
                    # Continue with normal processing to provide fallback response
            
            # Enhanced message analysis
            state.is_greeting = any(word in message for word in [
                'hello', 'hi', 'hola', 'hey', 'good morning', 'good afternoon', 'good evening'
            ])
            
            state.is_goodbye = any(word in message for word in [
                'bye', 'adios', 'goodbye', 'see you', 'hasta luego', 'chau', 'thanks bye'
            ])
            
            state.is_question = '?' in state.input_message or any(
                state.input_message.lower().startswith(word) for word in [
                    'what', 'how', 'why', 'when', 'where', 'who', 'which', 'can you', 'do you'
                ]
            )
            
            # Intent detection
            if state.is_greeting:
                state.intent = "greeting"
            elif state.is_goodbye:
                state.intent = "goodbye"
            elif any(word in message for word in ['price', 'cost', 'budget', 'pricing']):
                state.intent = "pricing_inquiry"
            elif any(word in message for word in ['service', 'services', 'what do you', 'what can you']):
                state.intent = "service_inquiry"
            elif any(word in message for word in ['schedule', 'appointment', 'meeting', 'call']):
                state.intent = "scheduling"
            elif any(word in message for word in ['email', 'send', 'enviar', 'correo']):
                state.intent = "email_request"
            elif any(word in message for word in ['calendar', 'evento', 'cita', 'recordatorio']):
                state.intent = "calendar_request"
            elif any(word in message for word in ['ai', 'artificial intelligence', 'machine learning', 'ml']):
                state.intent = "ai_consultation"
            else:
                state.intent = "general_inquiry"
            
            # Set confidence based on intent clarity
            state.confidence = 0.9 if state.intent in ["greeting", "goodbye"] else 0.7
            
            logger.debug(f"Message analysis - Intent: {state.intent}, Confidence: {state.confidence}")
            return state
            
        except Exception as e:
            logger.error(f"Message processing error: {e}")
            if hasattr(state, 'processing_errors'):
                state.processing_errors.append(f"Processing error: {str(e)}")
            return state

    def _generate_response_node(self, state: AgentState) -> AgentState:
        """Enhanced response generation with context-aware replies"""
        try:
            logger.debug(f"Generating response for {state.sender_phone} - Intent: {state.intent}")
            
            message = state.input_message
            intent = state.intent
            
            # Skip response generation if service action was already taken
            if getattr(state, 'service_action_taken', False) and state.response:
                logger.debug("Service action response already set, skipping generation")
                return state
            
            # Generate response based on intent
            if intent == "greeting":
                state.response = self._generate_greeting_response()
            elif intent == "goodbye":
                state.response = self._generate_goodbye_response()
            elif self._is_error_message(message):
                state.response = self._generate_error_handling_response()
            elif intent == "pricing_inquiry":
                state.response = self._generate_pricing_response()
            elif intent == "service_inquiry":
                state.response = self._generate_service_response()
            elif intent == "scheduling":
                state.response = self._generate_scheduling_response()
            elif intent in ["email_request", "calendar_request"] and not self.service_integration:
                state.response = self._generate_service_unavailable_response(intent)
            else:
                # Use knowledge base for general inquiries - will be handled in main process_message
                pass
            
            # Post-process response if available
            if state.response:
                state.response = self._post_process_response(state.response, state)
            
            logger.info(f"Generated response for {state.sender_phone}: {state.response[:100] if state.response else 'KB query needed'}...")
            return state
            
        except Exception as e:
            logger.error(f"Response generation error: {e}")
            if hasattr(state, 'processing_errors'):
                state.processing_errors.append(f"Response generation error: {str(e)}")
            state.response = "I apologize, but I encountered an error. Please try again."
            return state

    def _send_response_node(self, state: AgentState) -> AgentState:
        """Send response via WhatsApp with error handling"""
        try:
            if state.response and state.sender_phone:
                success = whatsapp_service.send_message(
                    state.sender_phone,
                    state.response
                )
                
                state.response_sent = success
                
                if not success:
                    logger.error(f"Failed to send response to {state.sender_phone}")
                    if hasattr(state, 'processing_errors'):
                        state.processing_errors.append("Failed to send response")
                else:
                    logger.info(f"Response sent successfully to {state.sender_phone}")
            
            return state
            
        except Exception as e:
            logger.error(f"Send response error: {e}")
            if hasattr(state, 'processing_errors'):
                state.processing_errors.append(f"Send error: {str(e)}")
            return state

    def _handle_error_node(self, state: AgentState) -> AgentState:
        """Handle errors and provide fallback response"""
        try:
            error_msg = state.validation_error or "An error occurred processing your message."
            
            state.response = f"I apologize, but {error_msg.lower()} Please try again with a shorter message."
            state.message_type = MessageType.ERROR
            
            # Try to send error response
            if state.sender_phone:
                success = whatsapp_service.send_message(state.sender_phone, state.response)
                state.response_sent = success
            
            logger.error(f"Error handled for {state.sender_phone}: {error_msg}")
            return state
            
        except Exception as e:
            logger.error(f"Error handling failed: {e}")
            return state

    # Response generation methods
    def _generate_greeting_response(self) -> str:
        """Generate a greeting response"""
        return ("¡Hola! Soy el Asistente AI de Lunia Soluciones. Estoy aquí para ayudarte con consultoría en IA, "
                "desarrollo de soluciones, programación de citas y más. ¿En qué puedo asistirte hoy?\n\n"
                "Puedo ayudarte con:\n"
                "📧 Enviar emails\n"
                "📅 Programar eventos y recordatorios\n"
                "🤖 Consultoría en IA\n"
                "💼 Información sobre nuestros servicios")

    def _generate_goodbye_response(self) -> str:
        """Generate a goodbye response"""
        return ("¡Hasta luego! Gracias por contactar a Lunia Soluciones. "
                "Esperamos poder ayudarte con tus necesidades de IA en el futuro. ¡Que tengas un excelente día!")

    def _generate_error_handling_response(self) -> str:
        """Generate response for error messages"""
        return ("Recibí un mensaje de audio, pero hubo un problema al procesarlo. "
                "¿Podrías intentar enviar un mensaje de texto, o asegurarte de que el audio sea claro?")

    def _generate_pricing_response(self) -> str:
        """Generate pricing inquiry response"""
        return ("Nuestros servicios de consultoría en IA están adaptados a las necesidades específicas de cada cliente. "
                "Los precios dependen del alcance y la complejidad de tu proyecto. "
                "¿Te gustaría programar una consulta para discutir tus requerimientos y obtener una cotización personalizada?")

    def _generate_service_response(self) -> str:
        """Generate service inquiry response"""
        return ("Lunia Soluciones ofrece servicios integrales de consultoría en IA:\n\n"
                "🎯 Desarrollo de Estrategia en IA\n"
                "🤖 Soluciones de Machine Learning\n"
                "📊 Análisis de Datos e Insights\n"
                "⚙️ Automatización de Procesos\n"
                "🔧 Servicios de Integración de IA\n\n"
                "¿Cuál de estas áreas te interesa más?")

    def _generate_scheduling_response(self) -> str:
        """Generate scheduling response"""
        return ("¡Estaré encantado de ayudarte a programar una consulta! "
                "Por favor déjame saber tu horario preferido y podemos organizar una reunión "
                "para discutir tus necesidades de IA en detalle.\n\n"
                "También puedo crear recordatorios y eventos en calendario. "
                "Solo dime qué necesitas programar.")

    def _generate_service_unavailable_response(self, intent: str) -> str:
        """Generate response when service integration is unavailable"""
        if intent == "email_request":
            return ("Entiendo que quieres enviar un email. Esta funcionalidad requiere configuración adicional. "
                    "Por favor contacta directamente a nuestro equipo para asistencia con emails.")
        elif intent == "calendar_request":
            return ("Entiendo que quieres programar algo en calendario. Esta funcionalidad requiere configuración adicional. "
                    "Por favor contacta directamente a nuestro equipo para programar citas.")
        else:
            return ("Esta funcionalidad no está disponible en este momento. "
                    "Por favor contacta directamente a nuestro equipo.")

    def _generate_fallback_response(self) -> str:
        """Generate fallback response"""
        return ("Entiendo que estás preguntando sobre eso, pero no tengo información específica disponible. "
                "¿Podrías reformular tu pregunta o preguntar sobre nuestros servicios de consultoría en IA? "
                "Estoy aquí para ayudar con información sobre las soluciones y servicios de Lunia.")

    def _post_process_response(self, response: str, state: AgentState) -> str:
        """Post-process the response for quality and length"""
        try:
            # Ensure response is not too long for WhatsApp
            if len(response) > self._max_message_length:
                # Try to truncate at sentence boundary
                sentences = response.split('.')
                truncated = ""
                for sentence in sentences:
                    if len(truncated + sentence + ".") <= self._max_message_length - 50:
                        truncated += sentence + "."
                    else:
                        break
                
                if truncated:
                    response = truncated + "\n\n(Mensaje truncado por longitud)"
                else:
                    response = response[:self._max_message_length - 50] + "..."
            
            # Add personalization if available
            if state.sender_phone and not state.is_goodbye and not getattr(state, 'service_action_taken', False):
                if len(response) + 50 < self._max_message_length:
                    response += "\n\n¿Hay algo más en lo que pueda ayudarte?"
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Post-processing error: {e}")
            return response

    # Flow control methods
    def _should_continue_after_validation(self, state: AgentState) -> str:
        """Determine next step after validation"""
        if state.validation_error:
            return "error"
        return "continue"

    def _is_error_message(self, message: str) -> bool:
        """Check if message indicates a processing error"""
        error_indicators = [
            "[Audio transcription failed]",
            "[Audio file not found for transcription]", 
            "[Audio file was a placeholder, not transcribed]",
            "[OpenAI client not available for transcription]",
            "[Audio message URL received, but live download/processing is not part of this simulation step]",
            "[Transcription resulted in empty text]",
            "[Audio transcription failed or unavailable]"
        ]
        
        return message.strip() in error_indicators


# Global agent instance
lunia_agent = LuniaAgent()
