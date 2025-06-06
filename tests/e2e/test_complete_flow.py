"""
End-to-end test suite for Lunia WhatsApp Agent
Tests the complete flow from webhook to response
"""
import pytest
import asyncio
import json
from typing import Dict, Any
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

import httpx
from fastapi.testclient import TestClient

from src.api.main import app
from src.core.config import Config


class TestE2EFlow:
    """End-to-end test scenarios"""
    
    @pytest.fixture
    def client(self):
        """Test client fixture"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_services(self):
        """Mock all external services"""
        with patch('src.services.whatsapp_service.whatsapp_service') as mock_whatsapp, \
             patch('src.services.email_service.EmailService') as mock_email, \
             patch('src.services.calendar_service.CalendarService') as mock_calendar, \
             patch('src.services.supabase_service.SupabaseService') as mock_supabase, \
             patch('src.services.knowledge_base.knowledge_base') as mock_kb:
            
            # Configure WhatsApp service mock
            mock_whatsapp._validate_api_config.return_value = True
            mock_whatsapp.send_message = AsyncMock(return_value=True)
            mock_whatsapp.parse_webhook_message.return_value = MagicMock(
                sender="1234567890",
                content="Hello",
                message_type="TEXT",
                audio_url=None,
                raw_data={}
            )
            
            # Configure other service mocks
            mock_email.return_value.send_email = AsyncMock(return_value=True)
            mock_email.return_value.test_connection = AsyncMock(return_value=True)
            
            mock_calendar.return_value.create_event = AsyncMock(return_value="event_123")
            mock_calendar.return_value.test_connection = AsyncMock(return_value=True)
            
            mock_supabase.return_value.insert = AsyncMock(return_value={"id": "123"})
            mock_supabase.return_value.test_connection = AsyncMock(return_value=True)
            
            mock_kb._initialized = True
            mock_kb.query_async = AsyncMock(return_value="Knowledge base response")
            
            yield {
                'whatsapp': mock_whatsapp,
                'email': mock_email,
                'calendar': mock_calendar,
                'supabase': mock_supabase,
                'knowledge_base': mock_kb
            }
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "services" in data
    
    def test_basic_webhook_flow(self, client, mock_services):
        """Test basic WhatsApp webhook processing"""
        webhook_payload = {
            "event": "message.received",
            "data": {
                "key": {
                    "remoteJid": "1234567890@s.whatsapp.net"
                },
                "message": {
                    "conversation": "Hello, how are you?"
                }
            }
        }
        
        response = client.post("/webhook/whatsapp", json=webhook_payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "accepted"
    
    def test_send_message_api(self, client, mock_services):
        """Test send message API endpoint"""
        payload = {
            "phone": "+1234567890",
            "message": "Test message"
        }
        
        response = client.post("/api/send-message", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "sent"
        assert data["phone"] == "+1234567890"
    
    def test_knowledge_base_query(self, client, mock_services):
        """Test knowledge base query endpoint"""
        payload = {
            "question": "What services do you offer?",
            "context": "Business inquiry"
        }
        
        response = client.post("/api/knowledge-base/query", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["answer"] == "Knowledge base response"
    
    def test_email_service_integration(self, client, mock_services):
        """Test email service endpoint"""
        payload = {
            "to_email": "test@example.com",
            "subject": "Test Email",
            "body": "This is a test email"
        }
        
        response = client.post("/api/email/send", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "sent"
        assert data["to"] == "test@example.com"
    
    def test_calendar_event_creation(self, client, mock_services):
        """Test calendar event creation endpoint"""
        payload = {
            "summary": "Test Meeting",
            "description": "A test meeting",
            "start_datetime": "2024-01-15T10:00:00",
            "end_datetime": "2024-01-15T11:00:00",
            "attendees": ["attendee@example.com"]
        }
        
        response = client.post("/api/calendar/events", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "created"
        assert data["event_id"] == "event_123"
    
    def test_database_operations(self, client, mock_services):
        """Test database operations endpoints"""
        # Test insert
        insert_payload = {
            "table": "test_table",
            "data": {"name": "Test", "value": 123}
        }
        
        response = client.post("/api/database/insert", json=insert_payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "inserted"
        
        # Test query
        query_payload = {
            "table": "test_table",
            "filters": {"name": "Test"},
            "limit": 10
        }
        
        response = client.post("/api/database/query", json=query_payload)
        assert response.status_code == 200
    
    def test_service_status_endpoints(self, client, mock_services):
        """Test all service status endpoints"""
        status_endpoints = [
            "/api/email/status",
            "/api/calendar/status", 
            "/api/database/status"
        ]
        
        for endpoint in status_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            
            data = response.json()
            assert "timestamp" in data
    
    def test_metrics_endpoint(self, client, mock_services):
        """Test metrics endpoint"""
        response = client.get("/api/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert "system" in data or "application" in data
        assert "timestamp" in data
    
    def test_stats_endpoint(self, client, mock_services):
        """Test stats endpoint"""
        response = client.get("/api/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "stats" in data
        assert "timestamp" in data
    
    def test_session_management(self, client, mock_services):
        """Test session management endpoints"""
        user_id = "test_user_123"
        
        # Test session cleanup
        response = client.post("/api/sessions/cleanup")
        assert response.status_code == 200
        
        # Test session deletion (might return 404 if not exists)
        response = client.delete(f"/api/sessions/{user_id}")
        assert response.status_code in [200, 404]
    
    def test_message_processing_simulation(self, client, mock_services):
        """Test message processing without WhatsApp"""
        payload = {
            "message": "Envía un email a test@example.com sobre reunión",
            "sender": "test_user"
        }
        
        response = client.post("/api/test/message", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "processed"
        assert "response" in data
        assert "processing_time" in data
    
    def test_error_handling(self, client):
        """Test API error handling"""
        # Test invalid payload
        response = client.post("/api/send-message", json={})
        assert response.status_code == 400
        
        # Test invalid phone number
        response = client.post("/api/send-message", json={
            "phone": "invalid",
            "message": "test"
        })
        assert response.status_code == 400
        
        # Test missing required fields
        response = client.post("/api/knowledge-base/query", json={})
        assert response.status_code == 400
    
    def test_validation_errors(self, client):
        """Test input validation"""
        # Test invalid email format
        response = client.post("/api/email/send", json={
            "to_email": "invalid-email",
            "subject": "Test",
            "body": "Test body"
        })
        assert response.status_code == 422  # Validation error
        
        # Test invalid datetime format
        response = client.post("/api/calendar/events", json={
            "summary": "Test",
            "start_datetime": "invalid-date",
            "end_datetime": "invalid-date"
        })
        assert response.status_code == 422


class TestServiceIntegration:
    """Test service integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_natural_language_email_processing(self):
        """Test natural language email command processing"""
        from src.services.agent_service_integration import AgentServiceIntegration
        from src.services.email_service import EmailService
        
        # Mock email service
        mock_email = AsyncMock(spec=EmailService)
        mock_email.send_email = AsyncMock(return_value=True)
        
        integration = AgentServiceIntegration(
            email_service=mock_email,
            calendar_service=None,
            supabase_service=None
        )
        
        # Test email command detection and execution
        result = await integration.process_service_actions(
            "Send email to john@example.com about meeting tomorrow",
            "user123"
        )
        
        assert result is not None
        assert "email" in result.get("actions_executed", [])
    
    @pytest.mark.asyncio
    async def test_calendar_event_natural_language(self):
        """Test natural language calendar command processing"""
        from src.services.agent_service_integration import AgentServiceIntegration
        from src.services.calendar_service import CalendarService
        
        # Mock calendar service
        mock_calendar = AsyncMock(spec=CalendarService)
        mock_calendar.create_event = AsyncMock(return_value="event_123")
        
        integration = AgentServiceIntegration(
            email_service=None,
            calendar_service=mock_calendar,
            supabase_service=None
        )
        
        # Test calendar command detection and execution
        result = await integration.process_service_actions(
            "Schedule meeting tomorrow at 3pm with John",
            "user123"
        )
        
        assert result is not None
        assert "calendar" in result.get("actions_executed", [])
    
    @pytest.mark.asyncio
    async def test_error_recovery(self):
        """Test error recovery in service integration"""
        from src.services.agent_service_integration import AgentServiceIntegration
        from src.services.email_service import EmailService
        
        # Mock email service with failure
        mock_email = AsyncMock(spec=EmailService)
        mock_email.send_email = AsyncMock(side_effect=Exception("Email failed"))
        
        integration = AgentServiceIntegration(
            email_service=mock_email,
            calendar_service=None,
            supabase_service=None
        )
        
        # Should handle error gracefully
        result = await integration.process_service_actions(
            "Send email to john@example.com",
            "user123"
        )
        
        assert result is not None
        assert "errors" in result


class TestPerformanceScenarios:
    """Test performance and load scenarios"""
    
    def test_concurrent_requests(self, client):
        """Test handling concurrent API requests"""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = client.get("/health")
            results.append(response.status_code)
        
        # Create 10 concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 10
    
    def test_large_payload_handling(self, client, mock_services):
        """Test handling of large message payloads"""
        large_message = "x" * 10000  # 10KB message
        
        payload = {
            "message": large_message,
            "sender": "test_user"
        }
        
        response = client.post("/api/test/message", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "processed"
    
    def test_rate_limiting_simulation(self, client):
        """Simulate rate limiting behavior"""
        # Make multiple rapid requests to health endpoint
        responses = []
        for _ in range(20):
            response = client.get("/health")
            responses.append(response.status_code)
        
        # Should handle all requests (basic endpoint)
        success_count = sum(1 for status in responses if status == 200)
        assert success_count > 15  # Most should succeed


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
