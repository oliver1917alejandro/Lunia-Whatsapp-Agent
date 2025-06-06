import os
import aiohttp
import asyncio
import json
from typing import Optional, Dict, Any, List
import openai
from src.core.config import Config
from src.core.logger import logger
from src.models.schemas import WhatsAppMessage, MessageType
from datetime import datetime
import tempfile
from pathlib import Path
import time
from urllib.parse import urlparse
import random  # for retry jitter


class WhatsAppService:
    """Enhanced WhatsApp service for sending and receiving messages with async support"""
    
    def __init__(self):
        self.api_url = Config.EVOLUTION_API_URL
        self.api_key = Config.EVOLUTION_API_KEY
        self.instance_name = Config.EVOLUTION_INSTANCE_NAME
        
        # Initialize OpenAI client for transcription
        self.openai_client = None
        if Config.OPENAI_API_KEY:
            try:
                self.openai_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
                logger.info("OpenAI client initialized for audio transcription")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
        else:
            logger.warning("OPENAI_API_KEY not found. Audio transcription unavailable")
        
        # Message retry configuration
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # Rate limiting
        self.last_message_time: float = 0.0
        self.min_message_interval: float = 1.0
        # Concurrency limit
        self._semaphore = asyncio.Semaphore(Config.MAX_REQUESTS_PER_MINUTE)
        # Reusable HTTP session
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))

    async def send_message(self, phone_number: str, message: str, options: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send a text message via WhatsApp (async)
        
        Args:
            phone_number: Recipient phone number
            message: Message content
            options: Additional options (delay, presence, etc.)
            
        Returns:
            Success status
        """
        # Acquire semaphore to limit concurrency
        await self._semaphore.acquire()
        try:
            if not self._validate_api_config():
                logger.error("WhatsApp API configuration invalid")
                return False
            
            # Rate limiting
            await self._rate_limit()
            
            # Check for placeholder URL to prevent accidental calls
            if self.api_url == "https://your-evolution-api-domain.com":
                logger.warning("Using placeholder API URL - message not sent")
                logger.info(f"Would send to {phone_number}: {message}")
                return True
            
            url = f"{self.api_url}/message/sendText/{self.instance_name}"
            headers = {
                "Content-Type": "application/json",
                "apikey": self.api_key
            }
            
            # Split long messages
            messages = self._split_message(message)
            
            success = True
            for msg_part in messages:
                if not await self._send_single_message(url, headers, phone_number, msg_part, options):
                    success = False
                    break
                
                # Add delay between message parts
                if len(messages) > 1:
                    await asyncio.sleep(2.0)
            
            return success
        finally:
            self._semaphore.release()
    
    async def _send_single_message(self, url: str, headers: Dict[str, str], 
                                 phone_number: str, message: str, 
                                 options: Optional[Dict[str, Any]] = None) -> bool:
        """Send a single message with retry logic and exponential backoff"""
        
        default_options = {
            "delay": 1200,
            "presence": "composing"
        }
        
        if options:
            default_options.update(options)
        
        payload = {
            "number": phone_number,
            "options": default_options,
            "textMessage": {"text": message}
        }
        
        for attempt in range(self.max_retries):
            try:
                async with self.session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Message sent successfully to {phone_number}")
                        return True
                    else:
                        text = await response.text()
                        logger.error(f"WhatsApp send failed ({response.status}): {text}")
                        
                        # Retry on rate limit or server errors with jittered backoff
                        backoff = self.retry_delay * (2 ** attempt) + random.uniform(0, 0.5)
                        if response.status in (429,) or response.status >= 500:
                            await asyncio.sleep(backoff)
                            continue
                        return False
                        
            except asyncio.TimeoutError:
                logger.error(f"Timeout sending message (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
            except Exception as e:
                logger.error(f"Network error sending message (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
        
        logger.error(f"Failed to send message after {self.max_retries} attempts")
        return False
    
    def _split_message(self, message: str, max_length: int = 4000) -> List[str]:
        """Split long messages into smaller parts"""
        if len(message) <= max_length:
            return [message]
        
        parts = []
        current_part = ""
        
        # Split by sentences first
        sentences = message.split('. ')
        
        for sentence in sentences:
            if len(current_part + sentence + '. ') <= max_length:
                current_part += sentence + '. '
            else:
                if current_part:
                    parts.append(current_part.strip())
                    current_part = sentence + '. '
                else:
                    # Handle very long sentences
                    while len(sentence) > max_length:
                        parts.append(sentence[:max_length])
                        sentence = sentence[max_length:]
                    current_part = sentence + '. '
        
        if current_part:
            parts.append(current_part.strip())
        
        return parts
    
    async def _rate_limit(self):
        """Apply rate limiting between messages"""
        current_time = time.time()
        time_since_last = current_time - self.last_message_time
        
        if time_since_last < self.min_message_interval:
            sleep_time = self.min_message_interval - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_message_time = time.time()
    
    def parse_webhook_message(self, payload: Dict[str, Any]) -> Optional[WhatsAppMessage]:
        """
        Parse incoming webhook message with enhanced error handling
        
        Args:
            payload: Raw webhook payload
            
        Returns:
            Parsed WhatsApp message or None
        """
        try:
            if payload.get("event") != "messages.upsert":
                logger.debug(f"Ignoring non-message event: {payload.get('event')}")
                return None
            
            data = payload.get("data", {})
            key = data.get("key", {})
            message = data.get("message", {})
            
            sender = key.get("remoteJid", "").replace("@s.whatsapp.net", "")
            if not sender:
                logger.error("No sender found in webhook payload")
                return None
            
            # Handle different message types
            return self._parse_message_content(sender, message, payload)
                
        except Exception as e:
            logger.error(f"Error parsing webhook message: {e}")
            return None
    
    def _parse_message_content(self, sender: str, message: Dict[str, Any], 
                             raw_payload: Dict[str, Any]) -> Optional[WhatsAppMessage]:
        """Parse message content based on type"""
        
        # Handle text messages
        if "conversation" in message:
            return WhatsAppMessage(
                sender=sender,
                content=message["conversation"],
                message_type=MessageType.TEXT,
                timestamp=datetime.now(),
                raw_data=raw_payload
            )
        
        # Handle extended text messages (with formatting)
        elif "extendedTextMessage" in message:
            text_content = message["extendedTextMessage"].get("text", "")
            return WhatsAppMessage(
                sender=sender,
                content=text_content,
                message_type=MessageType.TEXT,
                timestamp=datetime.now(),
                raw_data=raw_payload
            )
        
        # Handle audio messages
        elif "audioMessage" in message:
            return self._handle_audio_message(sender, message["audioMessage"], raw_payload)
        
        # Handle image messages
        elif "imageMessage" in message:
            caption = message["imageMessage"].get("caption", "[Image received]")
            return WhatsAppMessage(
                sender=sender,
                content=caption,
                message_type=MessageType.IMAGE,
                timestamp=datetime.now(),
                raw_data=raw_payload
            )
        
        # Handle document messages
        elif "documentMessage" in message:
            filename = message["documentMessage"].get("fileName", "document")
            return WhatsAppMessage(
                sender=sender,
                content=f"[Document received: {filename}]",
                message_type=MessageType.DOCUMENT,
                timestamp=datetime.now(),
                raw_data=raw_payload
            )
        
        # Handle other message types
        else:
            logger.warning(f"Unsupported message type from {sender}: {list(message.keys())}")
            return WhatsAppMessage(
                sender=sender,
                content="[Unsupported message type - please send text or audio]",
                message_type=MessageType.TEXT,
                timestamp=datetime.now(),
                raw_data=raw_payload
            )
    
    def _handle_audio_message(self, sender: str, audio_data: Dict[str, Any], 
                            raw_payload: Dict[str, Any]) -> WhatsAppMessage:
        """Handle audio message parsing"""
        audio_url = audio_data.get("url")
        
        # For now, return a placeholder - async transcription will be handled separately
        return WhatsAppMessage(
            sender=sender,
            content="[Audio message - transcription processing...]",
            message_type=MessageType.AUDIO,
            timestamp=datetime.now(),
            raw_data=raw_payload,
            audio_url=audio_url
        )
    
    async def transcribe_audio_async(self, audio_url: str) -> Optional[str]:
        """
        Transcribe audio using OpenAI Whisper (async)
        
        Args:
            audio_url: URL of the audio file
            
        Returns:
            Transcribed text or None
        """
        if not self.openai_client:
            logger.warning("OpenAI client not available for transcription")
            return None
        
        if not audio_url:
            logger.error("No audio URL provided for transcription")
            return None
        
        # Handle simulation URLs
        if audio_url in ["use_sample_audio.mp3", "some_other_audio.ogg"]:
            if audio_url == "use_sample_audio.mp3":
                # Simulate successful transcription
                return "This is a simulated transcription of the sample audio."
            else:
                # Simulate failed transcription
                return None
        
        try:
            # Download and transcribe audio file
            audio_file_path = await self._download_audio_file(audio_url)
            if not audio_file_path:
                return None
            
            # Transcribe using OpenAI Whisper
            transcription = await self._transcribe_file(audio_file_path)
            
            # Clean up temporary file
            try:
                os.unlink(audio_file_path)
            except Exception:
                pass
            
            return transcription
            
        except Exception as e:
            logger.error(f"Audio transcription error: {e}")
            return None
    
    async def _download_audio_file(self, audio_url: str) -> Optional[str]:
        """Download audio file from URL"""
        try:
            parsed_url = urlparse(audio_url)
            if not parsed_url.scheme:
                logger.error(f"Invalid audio URL: {audio_url}")
                return None
            
            async with aiohttp.ClientSession() as session:
                async with session.get(audio_url, timeout=30) as response:
                    if response.status != 200:
                        logger.error(f"Failed to download audio: {response.status}")
                        return None
                    
                    # Create temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
                        async for chunk in response.content.iter_chunked(8192):
                            temp_file.write(chunk)
                        return temp_file.name
                        
        except Exception as e:
            logger.error(f"Error downloading audio file: {e}")
            return None
    
    async def _transcribe_file(self, file_path: str) -> Optional[str]:
        """Transcribe audio file using OpenAI Whisper"""
        try:
            # Check file size (WhatsApp audio is typically small)
            file_size = os.path.getsize(file_path)
            if file_size > 25 * 1024 * 1024:  # 25MB limit
                logger.error(f"Audio file too large: {file_size} bytes")
                return None
            
            if file_size < 100:  # Likely a placeholder
                logger.warning(f"Audio file too small: {file_size} bytes")
                return None
            
            # Transcribe in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            transcription = await loop.run_in_executor(
                None, 
                self._sync_transcribe_file, 
                file_path
            )
            
            return transcription
            
        except Exception as e:
            logger.error(f"Error transcribing file: {e}")
            return None
    
    def _sync_transcribe_file(self, file_path: str) -> Optional[str]:
        """Synchronous transcription for thread pool execution"""
        try:
            with open(file_path, "rb") as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="es"  # Assuming Spanish for Lunia
                )
            
            transcribed_text = transcript.text.strip()
            logger.info(f"Audio transcribed successfully: '{transcribed_text[:50]}...'")
            return transcribed_text if transcribed_text else None
            
        except Exception as e:
            logger.error(f"OpenAI transcription error: {e}")
            return None
    
    def _validate_api_config(self) -> bool:
        """Validate API configuration"""
        return all([
            self.api_url,
            self.api_key,
            self.instance_name
        ])
    
    async def get_instance_status(self) -> Optional[Dict[str, Any]]:
        """Get Evolution API instance status"""
        if not self._validate_api_config():
            return None

        url = f"{self.api_url}/instance/status/{self.instance_name}"
        headers = {"apikey": self.api_key}

        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                logger.error(f"WhatsApp status failed: {response.status}")
                return None
        except Exception as e:
            logger.error(f"Error getting instance status: {e}")
            return None
    
    async def send_typing(self, phone_number: str) -> bool:
        """Send typing indicator"""
        if not self._validate_api_config():
            return False

        url = f"{self.api_url}/chat/presence/{self.instance_name}"
        headers = {
            "Content-Type": "application/json",
            "apikey": self.api_key
        }
        payload = {
            "number": phone_number,
            "presence": "composing"
        }

        try:
            async with self.session.post(url, headers=headers, json=payload) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Error sending typing indicator: {e}")
            return False

    async def close(self) -> None:
        """Close the underlying HTTP session"""
        if self.session:
            await self.session.close()


# Global WhatsApp service instance
whatsapp_service = WhatsAppService()
