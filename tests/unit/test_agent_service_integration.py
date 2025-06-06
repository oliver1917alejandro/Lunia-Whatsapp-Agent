"""
Tests for Agent Service Integration
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta

from src.services.agent_service_integration import AgentServiceIntegration
from src.services.email_service import EmailService
from src.services.calendar_service import CalendarService
from src.services.supabase_service import SupabaseService


class TestAgentServiceIntegration:
    """Test Agent Service Integration functionality"""
    
    @pytest.fixture
    def mock_email_service(self):
        """Create mock email service"""
        service = Mock(spec=EmailService)
        service.send_email = AsyncMock(return_value=True)
        return service
    
    @pytest.fixture
    def mock_calendar_service(self):
        """Create mock calendar service"""
        service = Mock(spec=CalendarService)
        service.create_event = AsyncMock(return_value="event_123")
        return service
    
    @pytest.fixture
    def mock_supabase_service(self):
        """Create mock Supabase service"""
        service = Mock(spec=SupabaseService)
        service.insert = AsyncMock(return_value={"id": 1, "created_at": datetime.now().isoformat()})
        service.select = AsyncMock(return_value=[])
        service.delete = AsyncMock(return_value=True)
        return service
    
    @pytest.fixture
    def service_integration(self, mock_email_service, mock_calendar_service, mock_supabase_service):
        """Create service integration instance"""
        return AgentServiceIntegration(
            email_service=mock_email_service,
            calendar_service=mock_calendar_service,
            supabase_service=mock_supabase_service
        )
    
    @pytest.mark.asyncio
    async def test_email_intent_detection_and_execution(self, service_integration):
        """Test email intent detection and execution"""
        message = "Send email to test@example.com about meeting tomorrow"
        user_id = "user123"
        
        result = await service_integration.process_service_intent(message, user_id)
        
        assert result["action"] == "email_sent"
        assert result["success"] is True
        assert "test@example.com" in result["message"]
        
        # Verify email service was called
        service_integration.email_service.send_email.assert_called_once()
        call_args = service_integration.email_service.send_email.call_args
        assert call_args[1]["to_email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_email_intent_no_email_address(self, service_integration):
        """Test email intent without valid email address"""
        message = "Send email to someone about something"
        user_id = "user123"
        
        result = await service_integration.process_service_intent(message, user_id)
        
        assert result["action"] == "email_error"
        assert result["success"] is False
        assert "dirección de email válida" in result["message"]
    
    @pytest.mark.asyncio
    async def test_calendar_intent_detection_and_execution(self, service_integration):
        """Test calendar intent detection and execution"""
        message = "Schedule meeting with team tomorrow at 3pm"
        user_id = "user123"
        
        with patch.object(service_integration, '_extract_event_details') as mock_extract:
            mock_extract.return_value = {
                "summary": "Meeting with team",
                "start_datetime": datetime.now() + timedelta(days=1),
                "end_datetime": datetime.now() + timedelta(days=1, hours=1)
            }
            
            result = await service_integration.process_service_intent(message, user_id)
            
            assert result["action"] == "calendar_event_created"
            assert result["success"] is True
            assert "event_123" in result["details"]["event_id"]
            
            # Verify calendar service was called
            service_integration.calendar_service.create_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_reminder_intent_detection_and_execution(self, service_integration):
        """Test reminder intent detection and execution"""
        message = "Remind me to call John in 1 hour"
        user_id = "user123"
        
        with patch.object(service_integration, '_extract_reminder_time') as mock_extract:
            mock_extract.return_value = datetime.now() + timedelta(hours=1)
            
            result = await service_integration.process_service_intent(message, user_id)
            
            assert result["action"] == "reminder_created"
            assert result["success"] is True
            
            # Verify both calendar and database services were called
            service_integration.calendar_service.create_event.assert_called_once()
            service_integration.supabase_service.insert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_data_intent_detection_and_logging(self, service_integration):
        """Test data query intent detection and logging"""
        message = "Show me my recent orders"
        user_id = "user123"
        
        result = await service_integration.process_service_intent(message, user_id)
        
        assert result["action"] == "data_query_logged"
        assert result["success"] is True
        
        # Verify database logging was called
        service_integration.supabase_service.insert.assert_called_once()
        call_args = service_integration.supabase_service.insert.call_args
        assert call_args[0][0] == "user_queries"
        assert call_args[0][1]["user_id"] == user_id
    
    @pytest.mark.asyncio
    async def test_no_intent_detected(self, service_integration):
        """Test when no service intent is detected"""
        message = "Hello, how are you?"
        user_id = "user123"
        
        result = await service_integration.process_service_intent(message, user_id)
        
        assert result["action"] == "none"
        assert result["success"] is False
    
    def test_extract_email_subject(self, service_integration):
        """Test email subject extraction"""
        # Test with subject keyword
        message = "Send email to test@example.com subject: Important Meeting"
        subject = service_integration._extract_email_subject(message)
        assert subject == "Important Meeting"
        
        # Test with Spanish keywords
        message = "Enviar correo a test@example.com asunto: Reunión Importante"
        subject = service_integration._extract_email_subject(message)
        assert subject == "Reunión Importante"
        
        # Test without subject
        message = "Send email to test@example.com about something"
        subject = service_integration._extract_email_subject(message)
        assert subject is None
    
    def test_extract_email_body(self, service_integration):
        """Test email body extraction"""
        message = "Send email to test@example.com about the meeting tomorrow"
        recipient = "test@example.com"
        
        body = service_integration._extract_email_body(message, recipient)
        
        assert "meeting tomorrow" in body.lower()
        assert recipient not in body  # Should be removed
        assert "send email" not in body.lower()  # Should be removed
    
    def test_extract_datetime_from_message(self, service_integration):
        """Test datetime extraction from messages"""
        # Test tomorrow
        message = "Schedule meeting tomorrow"
        dt = service_integration._extract_datetime_from_message(message)
        assert dt is not None
        assert dt.date() == (datetime.now() + timedelta(days=1)).date()
        
        # Test specific time
        message = "Schedule meeting at 3pm"
        dt = service_integration._extract_datetime_from_message(message)
        assert dt is not None
        assert dt.hour == 15
        
        # Test Spanish
        message = "Programar reunión mañana"
        dt = service_integration._extract_datetime_from_message(message)
        assert dt is not None
    
    def test_extract_event_details(self, service_integration):
        """Test event details extraction"""
        message = "Schedule team meeting tomorrow at 2pm"
        
        with patch.object(service_integration, '_extract_datetime_from_message') as mock_extract:
            tomorrow_2pm = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0) + timedelta(days=1)
            mock_extract.return_value = tomorrow_2pm
            
            details = service_integration._extract_event_details(message)
            
            assert details is not None
            assert "team meeting" in details["summary"].lower()
            assert details["start_datetime"] == tomorrow_2pm
            assert details["end_datetime"] == tomorrow_2pm + timedelta(hours=1)
    
    @pytest.mark.asyncio
    async def test_get_user_service_history(self, service_integration):
        """Test getting user service history"""
        user_id = "user123"
        mock_history = [
            {"action_type": "email_sent", "timestamp": datetime.now().isoformat()},
            {"action_type": "calendar_event_created", "timestamp": datetime.now().isoformat()}
        ]
        
        service_integration.supabase_service.select.return_value = mock_history
        
        history = await service_integration.get_user_service_history(user_id)
        
        assert len(history) == 2
        assert history[0]["action_type"] == "email_sent"
        
        # Verify correct database query
        service_integration.supabase_service.select.assert_called_once_with(
            table="service_actions",
            filters={"user_id": user_id},
            limit=10
        )
    
    @pytest.mark.asyncio
    async def test_get_service_statistics(self, service_integration):
        """Test getting service statistics"""
        mock_actions = [
            {"action_type": "email_sent"},
            {"action_type": "email_sent"},
            {"action_type": "calendar_event_created"}
        ]
        
        service_integration.supabase_service.select.return_value = mock_actions
        
        stats = await service_integration.get_service_statistics()
        
        assert stats["total_actions"] == 3
        assert stats["action_types"]["email_sent"] == 2
        assert stats["action_types"]["calendar_event_created"] == 1
    
    @pytest.mark.asyncio
    async def test_service_action_logging(self, service_integration):
        """Test service action logging"""
        user_id = "user123"
        action_type = "test_action"
        details = {"test": "data"}
        
        await service_integration._log_service_action(user_id, action_type, details)
        
        # Verify database insert was called with correct data
        service_integration.supabase_service.insert.assert_called_once()
        call_args = service_integration.supabase_service.insert.call_args
        
        assert call_args[0][0] == "service_actions"
        inserted_data = call_args[0][1]
        assert inserted_data["user_id"] == user_id
        assert inserted_data["action_type"] == action_type
        assert inserted_data["details"] == details
        assert inserted_data["success"] is True
    
    @pytest.mark.asyncio
    async def test_email_service_failure(self, service_integration):
        """Test handling of email service failure"""
        service_integration.email_service.send_email.return_value = False
        
        message = "Send email to test@example.com about something"
        user_id = "user123"
        
        result = await service_integration.process_service_intent(message, user_id)
        
        assert result["action"] == "email_error"
        assert result["success"] is False
        assert "Error al enviar" in result["message"]
    
    @pytest.mark.asyncio
    async def test_calendar_service_failure(self, service_integration):
        """Test handling of calendar service failure"""
        service_integration.calendar_service.create_event.return_value = None
        
        message = "Schedule meeting tomorrow"
        user_id = "user123"
        
        with patch.object(service_integration, '_extract_event_details') as mock_extract:
            mock_extract.return_value = {
                "summary": "Meeting",
                "start_datetime": datetime.now() + timedelta(days=1),
                "end_datetime": datetime.now() + timedelta(days=1, hours=1)
            }
            
            result = await service_integration.process_service_intent(message, user_id)
            
            assert result["action"] == "calendar_error"
            assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_exception_handling(self, service_integration):
        """Test exception handling in service integration"""
        service_integration.email_service.send_email.side_effect = Exception("Service error")
        
        message = "Send email to test@example.com"
        user_id = "user123"
        
        result = await service_integration.process_service_intent(message, user_id)
        
        assert result["action"] == "email_error"
        assert result["success"] is False
        assert "Error procesando" in result["message"]
    
    def test_multiple_pattern_matching(self, service_integration):
        """Test multiple pattern matching for different languages"""
        # English patterns
        assert any(service_integration.email_patterns[i] for i in range(len(service_integration.email_patterns)) 
                  if "send email to" in "send email to test@example.com")
        
        # Spanish patterns
        assert any(service_integration.email_patterns[i] for i in range(len(service_integration.email_patterns)) 
                  if "enviar correo a" in "enviar correo a test@example.com")
        
        # Calendar patterns
        assert any(service_integration.calendar_patterns[i] for i in range(len(service_integration.calendar_patterns)) 
                  if "schedule meeting" in "schedule meeting tomorrow")
    
    @pytest.mark.asyncio
    async def test_context_usage(self, service_integration):
        """Test usage of context in service intent processing"""
        message = "Send that to John"
        user_id = "user123"
        context = {
            "conversation_history": [
                {"role": "user", "content": "I need to email john@example.com about the meeting"},
                {"role": "assistant", "content": "I can help you with that"}
            ]
        }
        
        # The integration should potentially use context to understand "that" and "John"
        result = await service_integration.process_service_intent(message, user_id, context)
        
        # For now, this would not match email patterns, but context could be used in future enhancements
        assert result["action"] == "none"
        assert result["success"] is False
