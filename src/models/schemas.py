from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class MessageType(Enum):
    TEXT = "text"
    AUDIO = "audio"
    IMAGE = "image"
    DOCUMENT = "document"
    ERROR = "error"
    SYSTEM = "system"

class ConversationRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

@dataclass
class WhatsAppMessage:
    """WhatsApp message model"""
    sender: str
    content: str
    message_type: MessageType
    timestamp: datetime
    raw_data: Optional[Dict[str, Any]] = None
    audio_url: Optional[str] = None
    media_url: Optional[str] = None

@dataclass 
class ConversationTurn:
    """Single conversation turn"""
    role: ConversationRole
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class UserSession:
    """User session data"""
    user_id: str
    conversation_history: List[ConversationTurn]
    created_at: datetime
    last_activity: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def add_turn(self, role: ConversationRole, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a conversation turn"""
        turn = ConversationTurn(
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata
        )
        self.conversation_history.append(turn)
        self.last_activity = datetime.now()
    
    def get_recent_history(self, max_turns: int = 10) -> List[ConversationTurn]:
        """Get recent conversation history"""
        return self.conversation_history[-max_turns:]
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history.clear()

@dataclass
class AgentResponse:
    """Agent response model"""
    content: str
    confidence: float
    source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
@dataclass
class AgentState:
    """Enhanced Agent state for LangGraph with comprehensive tracking"""
    # Core message data
    input_message: str = ""
    sender_phone: str = ""
    response: str = ""
    message_type: MessageType = MessageType.TEXT
    
    # Conversation context
    conversation_history: List[Tuple[str, str]] = field(default_factory=list)
    session_context: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    # Processing metadata
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    processing_errors: List[str] = field(default_factory=list)
    
    # Validation and flow control
    validation_error: Optional[str] = None
    context_error: Optional[str] = None
    context_loaded: bool = False
    
    # Timing and performance
    timestamp: Optional[float] = None
    processing_time: Optional[float] = None
    
    # Message analysis
    message_length: int = 0
    is_greeting: bool = False
    is_goodbye: bool = False
    is_question: bool = False
    intent: Optional[str] = None
    confidence: float = 0.0
    
    # Response control
    response_sent: bool = False
    session_updated: bool = False
