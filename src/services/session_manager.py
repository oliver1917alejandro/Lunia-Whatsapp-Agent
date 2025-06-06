from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from src.models.schemas import UserSession, ConversationRole
from src.core.config import Config

class SessionManagerInterface(ABC):
    """Interface for session management"""
    
    @abstractmethod
    async def get_session(self, user_id: str) -> Optional[UserSession]:
        pass
    
    @abstractmethod
    async def save_session(self, session: UserSession) -> bool:
        pass
    
    @abstractmethod
    async def delete_session(self, user_id: str) -> bool:
        pass

class InMemorySessionManager(SessionManagerInterface):
    """In-memory session manager"""
    
    def __init__(self):
        self._sessions: Dict[str, UserSession] = {}
    
    async def get_session(self, user_id: str) -> Optional[UserSession]:
        session = self._sessions.get(user_id)
        
        if session:
            # Check if session is expired
            if self._is_session_expired(session):
                await self.delete_session(user_id)
                return None
                
        return session
    
    async def save_session(self, session: UserSession) -> bool:
        try:
            session.last_activity = datetime.now()
            self._sessions[session.user_id] = session
            return True
        except Exception:
            return False
    
    async def delete_session(self, user_id: str) -> bool:
        try:
            if user_id in self._sessions:
                del self._sessions[user_id]
            return True
        except Exception:
            return False
    
    async def create_session(self, user_id: str) -> UserSession:
        """Create a new session"""
        session = UserSession(
            user_id=user_id,
            conversation_history=[],
            created_at=datetime.now(),
            last_activity=datetime.now()
        )
        await self.save_session(session)
        return session
    
    async def add_message(self, user_id: str, role: ConversationRole, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a message to the session"""
        session = await self.get_session(user_id)
        if not session:
            session = await self.create_session(user_id)
        
        session.add_turn(role, content, metadata)
        
        # Limit conversation history
        if len(session.conversation_history) > Config.MAX_CONVERSATION_HISTORY:
            session.conversation_history = session.conversation_history[-Config.MAX_CONVERSATION_HISTORY:]
        
        await self.save_session(session)
    
    def _is_session_expired(self, session: UserSession) -> bool:
        """Check if session is expired"""
        timeout = timedelta(minutes=Config.SESSION_TIMEOUT_MINUTES)
        return datetime.now() - session.last_activity > timeout
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        expired_users = []
        for user_id, session in self._sessions.items():
            if self._is_session_expired(session):
                expired_users.append(user_id)
        
        for user_id in expired_users:
            await self.delete_session(user_id)

# Global session manager instance
session_manager = InMemorySessionManager()
