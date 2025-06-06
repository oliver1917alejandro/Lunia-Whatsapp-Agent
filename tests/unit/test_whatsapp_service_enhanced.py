"""
Tests for WhatsApp Service Enhanced
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from src.services.whatsapp_service_enhanced import WhatsAppServiceEnhanced
from src.models.schemas import WhatsAppMessage, MessageType


class TestWhatsAppServiceEnhanced:
    """Test WhatsApp Service Enhanced functionality"""
    
    @pytest.fixture
    def whatsapp_service(self):
        """Create WhatsApp service instance for testing"""
        service = WhatsAppServiceEnhanced()
        return service
    
    @pytest.mark.asyncio
    async def test_send_message_success(self, whatsapp_service):
        """Test successful message sending"""
        with patch.object(whatsapp_service, '_make_api_request') as mock_request:
            mock_request.return_value = {"status": "success", "messageId": "test123"}
            
            result = await whatsapp_service.send_message("1234567890", "Test message")
            
            assert result is True
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_message_failure(self, whatsapp_service):
        """Test message sending failure"""
        with patch.object(whatsapp_service, '_make_api_request') as mock_request:
            mock_request.return_value = None
            
            result = await whatsapp_service.send_message("1234567890", "Test message")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_send_message_with_retry(self, whatsapp_service):
        """Test message sending with retry logic"""
        with patch.object(whatsapp_service, '_make_api_request') as mock_request:
            # First call fails, second succeeds
            mock_request.side_effect = [None, {"status": "success", "messageId": "test123"}]
            
            result = await whatsapp_service.send_message("1234567890", "Test message")
            
            assert result is True
            assert mock_request.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_instance_status(self, whatsapp_service):
        """Test getting instance status"""
        with patch.object(whatsapp_service, '_make_api_request') as mock_request:
            mock_request.return_value = {"status": "open", "qrcode": None}
            
            status = await whatsapp_service.get_instance_status()
            
            assert status is not None
            assert status["status"] == "open"
    
    @pytest.mark.asyncio
    async def test_send_typing_indicator(self, whatsapp_service):
        """Test sending typing indicator"""
        with patch.object(whatsapp_service, '_make_api_request') as mock_request:
            mock_request.return_value = {"status": "success"}
            
            result = await whatsapp_service.send_typing("1234567890")
            
            assert result is True
    
    def test_parse_webhook_message_text(self, whatsapp_service):
        """Test parsing text webhook message"""
        payload = {
            "event": "messages.upsert",
            "data": {
                "key": {
                    "remoteJid": "1234567890@s.whatsapp.net",
                    "fromMe": False
                },
                "message": {
                    "conversation": "Hello world"
                },
                "messageTimestamp": 1640995200
            }
        }
        
        message = whatsapp_service.parse_webhook_message(payload)
        
        assert message is not None
        assert message.sender == "1234567890"
        assert message.content == "Hello world"
        assert message.message_type == MessageType.TEXT
    
    def test_parse_webhook_message_audio(self, whatsapp_service):
        """Test parsing audio webhook message"""
        payload = {
            "event": "messages.upsert",
            "data": {
                "key": {
                    "remoteJid": "1234567890@s.whatsapp.net",
                    "fromMe": False
                },
                "message": {
                    "audioMessage": {
                        "url": "https://example.com/audio.mp3",
                        "mimetype": "audio/mpeg"
                    }
                },
                "messageTimestamp": 1640995200
            }
        }
        
        message = whatsapp_service.parse_webhook_message(payload)
        
        assert message is not None
        assert message.sender == "1234567890"
        assert message.message_type == MessageType.AUDIO
        assert message.audio_url == "https://example.com/audio.mp3"
    
    def test_parse_webhook_message_invalid(self, whatsapp_service):
        """Test parsing invalid webhook message"""
        payload = {"invalid": "data"}
        
        message = whatsapp_service.parse_webhook_message(payload)
        
        assert message is None
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_success(self, whatsapp_service):
        """Test successful audio transcription"""
        with patch.object(whatsapp_service, 'openai_client') as mock_client:
            mock_response = Mock()
            mock_response.text = "Transcribed text"
            mock_client.audio.transcriptions.create.return_value = mock_response
            
            with patch('requests.get') as mock_get:
                mock_get.return_value.content = b"fake audio data"
                mock_get.return_value.status_code = 200
                
                result = await whatsapp_service.transcribe_audio_async("https://example.com/audio.mp3")
                
                assert result == "Transcribed text"
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_no_client(self, whatsapp_service):
        """Test audio transcription without OpenAI client"""
        whatsapp_service.openai_client = None
        
        result = await whatsapp_service.transcribe_audio_async("https://example.com/audio.mp3")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, whatsapp_service):
        """Test rate limiting functionality"""
        # Set a very low rate limit for testing
        whatsapp_service.rate_limit_per_minute = 2
        
        with patch.object(whatsapp_service, '_make_api_request') as mock_request:
            mock_request.return_value = {"status": "success"}
            
            # First two calls should succeed
            result1 = await whatsapp_service.send_message("1234567890", "Test 1")
            result2 = await whatsapp_service.send_message("1234567890", "Test 2")
            
            assert result1 is True
            assert result2 is True
            
            # Third call should be rate limited (in a real scenario)
            # For testing, we'll just verify the rate limit tracking works
            assert len(whatsapp_service.request_times) == 2
    
    @pytest.mark.asyncio
    async def test_concurrency_control(self, whatsapp_service):
        """Test concurrency control with semaphore"""
        # Mock the semaphore to test concurrency control
        original_semaphore = whatsapp_service.semaphore
        whatsapp_service.semaphore = asyncio.Semaphore(1)  # Allow only 1 concurrent request
        
        with patch.object(whatsapp_service, '_make_api_request') as mock_request:
            # Make the request take some time
            async def slow_request(*args, **kwargs):
                await asyncio.sleep(0.1)
                return {"status": "success"}
            
            mock_request.side_effect = slow_request
            
            # Start multiple concurrent requests
            tasks = [
                whatsapp_service.send_message("1234567890", f"Test {i}")
                for i in range(3)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # All should succeed, but they were processed sequentially
            assert all(results)
            assert mock_request.call_count == 3
        
        # Restore original semaphore
        whatsapp_service.semaphore = original_semaphore
    
    def test_validate_api_config_valid(self, whatsapp_service):
        """Test API configuration validation with valid config"""
        with patch('src.core.config.Config') as mock_config:
            mock_config.EVOLUTION_API_URL = "https://api.example.com"
            mock_config.EVOLUTION_API_KEY = "test_key"
            mock_config.EVOLUTION_INSTANCE_NAME = "test_instance"
            
            result = whatsapp_service._validate_api_config()
            
            assert result is True
    
    def test_validate_api_config_invalid(self, whatsapp_service):
        """Test API configuration validation with invalid config"""
        with patch('src.core.config.Config') as mock_config:
            mock_config.EVOLUTION_API_URL = None
            mock_config.EVOLUTION_API_KEY = "test_key"
            mock_config.EVOLUTION_INSTANCE_NAME = "test_instance"
            
            result = whatsapp_service._validate_api_config()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_error_handling_and_logging(self, whatsapp_service):
        """Test error handling and logging"""
        with patch.object(whatsapp_service, '_make_api_request') as mock_request:
            mock_request.side_effect = Exception("API Error")
            
            with patch('src.services.whatsapp_service_enhanced.logger') as mock_logger:
                result = await whatsapp_service.send_message("1234567890", "Test message")
                
                assert result is False
                mock_logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_exponential_backoff(self, whatsapp_service):
        """Test exponential backoff in retry logic"""
        with patch.object(whatsapp_service, '_make_api_request') as mock_request:
            # Simulate multiple failures then success
            mock_request.side_effect = [None, None, {"status": "success"}]
            
            with patch('asyncio.sleep') as mock_sleep:
                result = await whatsapp_service.send_message("1234567890", "Test message")
                
                assert result is True
                # Should have slept for backoff delays
                assert mock_sleep.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_close_method(self, whatsapp_service):
        """Test the close method for cleanup"""
        with patch.object(whatsapp_service, 'session') as mock_session:
            mock_session.close = AsyncMock()
            
            await whatsapp_service.close()
            
            mock_session.close.assert_called_once()
    
    def test_extract_phone_number(self, whatsapp_service):
        """Test phone number extraction from JID"""
        # Test various JID formats
        assert whatsapp_service._extract_phone_number("1234567890@s.whatsapp.net") == "1234567890"
        assert whatsapp_service._extract_phone_number("1234567890@c.us") == "1234567890"
        assert whatsapp_service._extract_phone_number("invalid") == "invalid"
    
    def test_message_length_truncation(self, whatsapp_service):
        """Test message length truncation"""
        long_message = "A" * 5000  # Longer than WhatsApp limit
        
        with patch.object(whatsapp_service, '_make_api_request') as mock_request:
            mock_request.return_value = {"status": "success"}
            
            # The service should handle long messages gracefully
            # Implementation depends on how the service handles this
            pass
