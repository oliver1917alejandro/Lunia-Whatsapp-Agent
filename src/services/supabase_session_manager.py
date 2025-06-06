"""
SupabaseSessionManager: Session persistence in Supabase database
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json
from src.services.session_manager import SessionManagerInterface
from src.services.supabase_service import SupabaseService
from src.models.schemas import UserSession, ConversationRole, ConversationTurn
from src.core.config import Config
from src.core.logger import logger


class SupabaseSessionManager(SessionManagerInterface):
    """Session manager with Supabase persistence"""

    def __init__(self):
        self.supabase = SupabaseService()
        self.table_name = "user_sessions"
        self.turns_table = "conversation_turns"

    async def get_session(self, user_id: str) -> Optional[UserSession]:
        """Retrieve session from Supabase"""
        try:
            response = self.supabase.client.table(self.table_name).select("*").eq("user_id", user_id).execute()
            
            if not response.data:
                return None
            
            session_data = response.data[0]
            
            # Check if session is expired
            last_activity = datetime.fromisoformat(session_data["last_activity"])
            if self._is_session_expired_time(last_activity):
                await self.delete_session(user_id)
                return None
            
            # Load conversation history
            turns_response = self.supabase.client.table(self.turns_table).select("*").eq("session_id", session_data["id"]).order("created_at").execute()
            
            conversation_history = []
            for turn_data in turns_response.data:
                turn = ConversationTurn(
                    role=ConversationRole(turn_data["role"]),
                    content=turn_data["content"],
                    timestamp=datetime.fromisoformat(turn_data["created_at"]),
                    metadata=json.loads(turn_data["metadata"]) if turn_data["metadata"] else {}
                )
                conversation_history.append(turn)
            
            return UserSession(
                user_id=user_id,
                conversation_history=conversation_history,
                created_at=datetime.fromisoformat(session_data["created_at"]),
                last_activity=last_activity,
                metadata=json.loads(session_data["metadata"]) if session_data["metadata"] else {}
            )
            
        except Exception as e:
            logger.error(f"Error retrieving session for {user_id}: {e}")
            return None

    async def save_session(self, session: UserSession) -> bool:
        """Save session to Supabase"""
        try:
            session.last_activity = datetime.now()
            
            # Upsert session data
            session_data = {
                "user_id": session.user_id,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "metadata": json.dumps(session.metadata) if session.metadata else None
            }
            
            response = self.supabase.client.table(self.table_name).upsert(session_data, on_conflict="user_id").execute()
            
            if not response.data:
                return False
            
            session_id = response.data[0]["id"]
            
            # Save recent conversation turns (limit to avoid bloat)
            recent_turns = session.conversation_history[-Config.MAX_CONVERSATION_HISTORY:]
            
            # Delete old turns first
            self.supabase.client.table(self.turns_table).delete().eq("session_id", session_id).execute()
            
            # Insert new turns
            for turn in recent_turns:
                turn_data = {
                    "session_id": session_id,
                    "role": turn.role.value,
                    "content": turn.content,
                    "created_at": turn.timestamp.isoformat(),
                    "metadata": json.dumps(turn.metadata) if turn.metadata else None
                }
                self.supabase.client.table(self.turns_table).insert(turn_data).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving session for {session.user_id}: {e}")
            return False

    async def delete_session(self, user_id: str) -> bool:
        """Delete session from Supabase"""
        try:
            # Get session ID first
            response = self.supabase.client.table(self.table_name).select("id").eq("user_id", user_id).execute()
            
            if response.data:
                session_id = response.data[0]["id"]
                
                # Delete conversation turns first
                self.supabase.client.table(self.turns_table).delete().eq("session_id", session_id).execute()
                
                # Delete session
                self.supabase.client.table(self.table_name).delete().eq("user_id", user_id).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting session for {user_id}: {e}")
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
        await self.save_session(session)

    def _is_session_expired_time(self, last_activity: datetime) -> bool:
        """Check if session is expired based on timestamp"""
        timeout = timedelta(minutes=Config.SESSION_TIMEOUT_MINUTES)
        return datetime.now() - last_activity > timeout

    async def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            cutoff_time = datetime.now() - timedelta(minutes=Config.SESSION_TIMEOUT_MINUTES)
            
            # Get expired sessions
            response = self.supabase.client.table(self.table_name).select("user_id").lt("last_activity", cutoff_time.isoformat()).execute()
            
            for session_data in response.data:
                await self.delete_session(session_data["user_id"])
                
            logger.info(f"Cleaned up {len(response.data)} expired sessions")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")

    async def get_all_active_sessions(self) -> List[UserSession]:
        """Get all non-expired sessions"""
        try:
            cutoff_time = datetime.now() - timedelta(minutes=Config.SESSION_TIMEOUT_MINUTES)
            
            response = self.supabase.client.table(self.table_name).select("*").gte("last_activity", cutoff_time.isoformat()).execute()
            
            sessions = []
            for session_data in response.data:
                session = await self.get_session(session_data["user_id"])
                if session:
                    sessions.append(session)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return []
