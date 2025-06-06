import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.services.session_manager import InMemorySessionManager
from src.models.schemas import ConversationRole
from datetime import datetime, timedelta

@pytest.fixture
def session_manager():
    """Create a fresh session manager for each test"""
    return InMemorySessionManager()

@pytest.mark.asyncio
async def test_create_session(session_manager):
    """Test session creation"""
    user_id = "test_user_123"
    
    session = await session_manager.create_session(user_id)
    
    assert session.user_id == user_id
    assert len(session.conversation_history) == 0
    assert isinstance(session.created_at, datetime)
    assert isinstance(session.last_activity, datetime)

@pytest.mark.asyncio
async def test_get_nonexistent_session(session_manager):
    """Test getting a session that doesn't exist"""
    session = await session_manager.get_session("nonexistent_user")
    assert session is None

@pytest.mark.asyncio
async def test_save_and_get_session(session_manager):
    """Test saving and retrieving a session"""
    user_id = "test_user_456"
    
    # Create and save session
    original_session = await session_manager.create_session(user_id)
    
    # Retrieve session
    retrieved_session = await session_manager.get_session(user_id)
    
    assert retrieved_session is not None
    assert retrieved_session.user_id == user_id
    assert retrieved_session.created_at == original_session.created_at

@pytest.mark.asyncio
async def test_add_message_to_session(session_manager):
    """Test adding messages to a session"""
    user_id = "test_user_789"
    
    # Add user message
    await session_manager.add_message(
        user_id, 
        ConversationRole.USER, 
        "Hello, how are you?"
    )
    
    # Add assistant message
    await session_manager.add_message(
        user_id,
        ConversationRole.ASSISTANT,
        "I'm doing well, thank you!"
    )
    
    session = await session_manager.get_session(user_id)
    
    assert len(session.conversation_history) == 2
    assert session.conversation_history[0].role == ConversationRole.USER
    assert session.conversation_history[0].content == "Hello, how are you?"
    assert session.conversation_history[1].role == ConversationRole.ASSISTANT
    assert session.conversation_history[1].content == "I'm doing well, thank you!"

@pytest.mark.asyncio
async def test_session_expiration(session_manager):
    """Test session expiration"""
    with patch('src.core.config.Config.SESSION_TIMEOUT_MINUTES', 1):  # 1 minute timeout
        user_id = "test_user_expire"
        
        # Create session
        session = await session_manager.create_session(user_id)
        
        # Mock last activity to be in the past
        session.last_activity = datetime.now() - timedelta(minutes=2)
        await session_manager.save_session(session)
        
        # Try to get expired session
        retrieved_session = await session_manager.get_session(user_id)
        
        assert retrieved_session is None

@pytest.mark.asyncio
async def test_delete_session(session_manager):
    """Test session deletion"""
    user_id = "test_user_delete"
    
    # Create session
    await session_manager.create_session(user_id)
    
    # Verify session exists
    session = await session_manager.get_session(user_id)
    assert session is not None
    
    # Delete session
    success = await session_manager.delete_session(user_id)
    assert success is True
    
    # Verify session is deleted
    session = await session_manager.get_session(user_id)
    assert session is None

@pytest.mark.asyncio
async def test_conversation_history_limit(session_manager):
    """Test conversation history limit"""
    with patch('src.core.config.Config.MAX_CONVERSATION_HISTORY', 3):
        user_id = "test_user_limit"
        
        # Add more messages than the limit
        for i in range(5):
            await session_manager.add_message(
                user_id,
                ConversationRole.USER,
                f"Message {i}"
            )
        
        session = await session_manager.get_session(user_id)
        
        # Should only keep the last 3 messages
        assert len(session.conversation_history) == 3
        assert session.conversation_history[0].content == "Message 2"
        assert session.conversation_history[2].content == "Message 4"

@pytest.mark.asyncio
async def test_cleanup_expired_sessions(session_manager):
    """Test cleanup of expired sessions"""
    with patch('src.core.config.Config.SESSION_TIMEOUT_MINUTES', 1):
        # Create multiple sessions
        active_user = "active_user"
        expired_user1 = "expired_user1"
        expired_user2 = "expired_user2"
        
        # Create sessions
        active_session = await session_manager.create_session(active_user)
        expired_session1 = await session_manager.create_session(expired_user1)
        expired_session2 = await session_manager.create_session(expired_user2)
        
        # Make some sessions expired
        expired_time = datetime.now() - timedelta(minutes=2)
        expired_session1.last_activity = expired_time
        expired_session2.last_activity = expired_time
        
        await session_manager.save_session(expired_session1)
        await session_manager.save_session(expired_session2)
        
        # Cleanup expired sessions
        await session_manager.cleanup_expired_sessions()
        
        # Check results
        assert await session_manager.get_session(active_user) is not None
        assert await session_manager.get_session(expired_user1) is None
        assert await session_manager.get_session(expired_user2) is None
