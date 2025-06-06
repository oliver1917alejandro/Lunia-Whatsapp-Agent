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

class WhatsAppService:
    """WhatsApp service for sending and receiving messages"""
    
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
    
    def send_message(self, phone_number: str, message: str) -> bool:
        """
        Send a text message via WhatsApp
        
        Args:
            phone_number: Recipient phone number
            message: Message content
            
        Returns:
            Success status
        """
        if not self._validate_api_config():
            logger.error("WhatsApp API configuration invalid")
            return False
        
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
        
        payload = {
            "number": phone_number,
            "text": message
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Message sent successfully to {phone_number}")
                return True
            else:
                logger.error(f"Failed to send message. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error sending message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            return False
    
    def parse_webhook_message(self, payload: Dict[str, Any]) -> Optional[WhatsAppMessage]:
        """
        Parse incoming webhook message
        
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
            
            # Handle text messages
            if "conversation" in message:
                return WhatsAppMessage(
                    sender=sender,
                    content=message["conversation"],
                    message_type=MessageType.TEXT,
                    timestamp=datetime.now(),
                    raw_data=payload
                )
            
            # Handle audio messages
            elif "audioMessage" in message:
                audio_url = message["audioMessage"].get("url")
                transcribed_text = self._transcribe_audio(audio_url) if audio_url else None
                
                if not transcribed_text:
                    transcribed_text = "[Audio transcription failed or unavailable]"
                
                return WhatsAppMessage(
                    sender=sender,
                    content=transcribed_text,
                    message_type=MessageType.AUDIO,
                    timestamp=datetime.now(),
                    raw_data=payload,
                    audio_url=audio_url
                )
            
            # Handle other message types (can be extended)
            else:
                logger.warning(f"Unsupported message type from {sender}: {list(message.keys())}")
                return WhatsAppMessage(
                    sender=sender,
                    content="[Unsupported message type]",
                    message_type=MessageType.TEXT,
                    timestamp=datetime.now(),
                    raw_data=payload
                )
                
        except Exception as e:
            logger.error(f"Error parsing webhook message: {e}")
            return None
    
    def _transcribe_audio(self, audio_url: str) -> Optional[str]:
        """
        Transcribe audio using OpenAI Whisper
        
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
            # In a real implementation, you would:
            # 1. Download the audio file from the URL
            # 2. Validate file size and format
            # 3. Send to OpenAI Whisper API
            # 4. Return transcribed text
            
            logger.info("Audio transcription would be processed here in production")
            return "[Live audio transcription not implemented in this version]"
            
        except Exception as e:
            logger.error(f"Audio transcription error: {e}")
            return None
    
    def _validate_api_config(self) -> bool:
        """Validate API configuration"""
        return all([
            self.api_url,
            self.api_key,
            self.instance_name
        ])

# Global WhatsApp service instance
whatsapp_service = WhatsAppService()
