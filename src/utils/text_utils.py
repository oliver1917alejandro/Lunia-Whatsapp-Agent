from typing import Any, Dict, Optional, List
import re
import json
from datetime import datetime
import hashlib

def clean_phone_number(phone: str) -> str:
    """
    Clean and normalize phone number
    
    Args:
        phone: Raw phone number
        
    Returns:
        Cleaned phone number
    """
    if not phone:
        return ""
    
    # Remove WhatsApp suffix if present
    phone = phone.replace("@s.whatsapp.net", "")
    
    # Remove all non-digit characters except +
    phone = re.sub(r'[^\d+]', '', phone)
    
    # Ensure it starts with + if it's an international number
    if phone and not phone.startswith('+') and len(phone) > 10:
        phone = '+' + phone
    
    return phone

def sanitize_text(text: str, max_length: int = 1000) -> str:
    """
    Sanitize text input
    
    Args:
        text: Input text
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text

def is_valid_phone_number(phone: str) -> bool:
    """
    Validate phone number format
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not phone:
        return False
    
    cleaned = clean_phone_number(phone)
    
    # Basic validation: should be 10-15 digits
    if cleaned.startswith('+'):
        digits = cleaned[1:]
    else:
        digits = cleaned
    
    return digits.isdigit() and 10 <= len(digits) <= 15

def generate_message_id(sender: str, content: str, timestamp: datetime = None) -> str:
    """
    Generate unique message ID
    
    Args:
        sender: Message sender
        content: Message content
        timestamp: Message timestamp
        
    Returns:
        Unique message ID
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    data = f"{sender}|{content}|{timestamp.isoformat()}"
    return hashlib.md5(data.encode()).hexdigest()[:12]

def format_response_for_whatsapp(text: str) -> str:
    """
    Format response text for WhatsApp
    
    Args:
        text: Raw response text
        
    Returns:
        Formatted text
    """
    if not text:
        return ""
    
    # Basic formatting for WhatsApp
    text = text.strip()
    
    # Convert markdown-style formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'*\1*', text)  # Bold
    text = re.sub(r'__(.*?)__', r'_\1_', text)      # Italic
    
    # Limit line length for better mobile display
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        if len(line) > 100:
            words = line.split()
            current_line = []
            current_length = 0
            
            for word in words:
                if current_length + len(word) + 1 > 100:
                    if current_line:
                        formatted_lines.append(' '.join(current_line))
                        current_line = [word]
                        current_length = len(word)
                    else:
                        formatted_lines.append(word)
                        current_length = 0
                else:
                    current_line.append(word)
                    current_length += len(word) + 1
            
            if current_line:
                formatted_lines.append(' '.join(current_line))
        else:
            formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)

def extract_keywords(text: str) -> List[str]:
    """
    Extract keywords from text
    
    Args:
        text: Input text
        
    Returns:
        List of keywords
    """
    if not text:
        return []
    
    # Simple keyword extraction
    # Remove common stop words
    stop_words = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
        'to', 'was', 'will', 'with', 'you', 'your', 'el', 'la', 'en', 'de',
        'un', 'una', 'y', 'que', 'es', 'por', 'para', 'con', 'se', 'su'
    }
    
    # Extract words
    words = re.findall(r'\b[a-zA-ZáéíóúÁÉÍÓÚñÑ]{3,}\b', text.lower())
    
    # Filter stop words and duplicates
    keywords = list(set(word for word in words if word not in stop_words))
    
    return keywords[:10]  # Return top 10 keywords

def safe_json_loads(json_str: str) -> Optional[Dict[str, Any]]:
    """
    Safely parse JSON string
    
    Args:
        json_str: JSON string
        
    Returns:
        Parsed dictionary or None if invalid
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return None

def safe_json_dumps(data: Any) -> str:
    """
    Safely serialize data to JSON
    
    Args:
        data: Data to serialize
        
    Returns:
        JSON string or empty string if error
    """
    try:
        return json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    except (TypeError, ValueError):
        return ""

def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def is_greeting(text: str) -> bool:
    """Check if text is a greeting"""
    if not text:
        return False
    
    greetings = {
        'hello', 'hi', 'hey', 'hola', 'buenos', 'buenas', 'good morning',
        'good afternoon', 'good evening', 'saludos', 'saludo'
    }
    
    text_lower = text.lower()
    return any(greeting in text_lower for greeting in greetings)

def is_goodbye(text: str) -> bool:
    """Check if text is a goodbye"""
    if not text:
        return False
    
    goodbyes = {
        'bye', 'goodbye', 'see you', 'adios', 'adiós', 'hasta luego',
        'hasta la vista', 'nos vemos', 'chau', 'hasta pronto'
    }
    
    text_lower = text.lower()
    return any(goodbye in text_lower for goodbye in goodbyes)
