import pytest
from unittest.mock import Mock, patch
from src.services.whatsapp_service import WhatsAppService
from src.models.schemas import MessageType
from datetime import datetime

@pytest.fixture
def whatsapp_service():
    """Create WhatsApp service instance for testing"""
    return WhatsAppService()

def test_parse_text_message(whatsapp_service):
    """Test parsing text message from webhook"""
    payload = {
        "event": "messages.upsert",
        "data": {
            "key": {"remoteJid": "1234567890@s.whatsapp.net"},
            "message": {"conversation": "Hello, how can you help me?"}
        }
    }
    
    message = whatsapp_service.parse_webhook_message(payload)
    
    assert message is not None
    assert message.sender == "1234567890"
    assert message.content == "Hello, how can you help me?"
    assert message.message_type == MessageType.TEXT
    assert isinstance(message.timestamp, datetime)

def test_parse_audio_message(whatsapp_service):
    """Test parsing audio message from webhook"""
    payload = {
        "event": "messages.upsert",
        "data": {
            "key": {"remoteJid": "1234567890@s.whatsapp.net"},
            "message": {"audioMessage": {"url": "use_sample_audio.mp3"}}
        }
    }
    
    message = whatsapp_service.parse_webhook_message(payload)
    
    assert message is not None
    assert message.sender == "1234567890"
    assert message.message_type == MessageType.AUDIO
    assert message.audio_url == "use_sample_audio.mp3"
    # Should contain transcribed text (simulated)
    assert "simulated transcription" in message.content.lower()

def test_parse_invalid_message(whatsapp_service):
    """Test parsing invalid message"""
    payload = {
        "event": "some.other.event",
        "data": {}
    }
    
    message = whatsapp_service.parse_webhook_message(payload)
    assert message is None

def test_parse_message_no_sender(whatsapp_service):
    """Test parsing message without sender"""
    payload = {
        "event": "messages.upsert",
        "data": {
            "key": {},
            "message": {"conversation": "Hello"}
        }
    }
    
    message = whatsapp_service.parse_webhook_message(payload)
    assert message is None

@patch('requests.post')
def test_send_message_success(mock_post, whatsapp_service):
    """Test successful message sending"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response
    
    # Mock configuration
    with patch.object(whatsapp_service, 'api_url', 'https://test-api.com'):
        with patch.object(whatsapp_service, 'api_key', 'test-key'):
            with patch.object(whatsapp_service, 'instance_name', 'test-instance'):
                result = whatsapp_service.send_message("1234567890", "Test message")
    
    assert result is True
    mock_post.assert_called_once()

@patch('requests.post')
def test_send_message_failure(mock_post, whatsapp_service):
    """Test failed message sending"""
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = "Bad request"
    mock_post.return_value = mock_response
    
    # Mock configuration
    with patch.object(whatsapp_service, 'api_url', 'https://test-api.com'):
        with patch.object(whatsapp_service, 'api_key', 'test-key'):
            with patch.object(whatsapp_service, 'instance_name', 'test-instance'):
                result = whatsapp_service.send_message("1234567890", "Test message")
    
    assert result is False

def test_send_message_placeholder_url(whatsapp_service):
    """Test sending message with placeholder URL"""
    # Should return True but not actually send
    result = whatsapp_service.send_message("1234567890", "Test message")
    assert result is True

def test_validate_api_config(whatsapp_service):
    """Test API configuration validation"""
    # Test with default (invalid) config
    assert whatsapp_service._validate_api_config() is False
    
    # Test with valid config
    whatsapp_service.api_url = "https://test-api.com"
    whatsapp_service.api_key = "test-key"
    whatsapp_service.instance_name = "test-instance"
    
    assert whatsapp_service._validate_api_config() is True

def test_transcribe_audio_simulation(whatsapp_service):
    """Test audio transcription simulation"""
    # Test successful simulation
    result = whatsapp_service._transcribe_audio("use_sample_audio.mp3")
    assert result is not None
    assert "simulated transcription" in result.lower()
    
    # Test failed simulation
    result = whatsapp_service._transcribe_audio("some_other_audio.ogg")
    assert result is None
    
    # Test with empty URL
    result = whatsapp_service._transcribe_audio("")
    assert result is None
