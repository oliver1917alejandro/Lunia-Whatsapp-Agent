#!/usr/bin/env python3
"""
Test simulation script for Lunia WhatsApp Agent
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.services.whatsapp_service import whatsapp_service
from src.agents.lunia_agent import lunia_agent
from src.models.schemas import AgentState
from src.core.logger import logger

async def run_simulation():
    """Run test simulation"""
    print("🧪 Running Lunia WhatsApp Agent Simulation")
    print("=" * 50)
    
    # Test message payloads
    test_messages = [
        {
            "event": "messages.upsert",
            "data": {
                "key": {"remoteJid": "test_user_1@s.whatsapp.net"},
                "message": {"conversation": "Hola"}
            }
        },
        {
            "event": "messages.upsert", 
            "data": {
                "key": {"remoteJid": "test_user_1@s.whatsapp.net"},
                "message": {"conversation": "What services do you offer?"}
            }
        },
        {
            "event": "messages.upsert",
            "data": {
                "key": {"remoteJid": "test_user_2@s.whatsapp.net"},
                "message": {"audioMessage": {"url": "use_sample_audio.mp3"}}
            }
        },
        {
            "event": "messages.upsert",
            "data": {
                "key": {"remoteJid": "test_user_1@s.whatsapp.net"},
                "message": {"conversation": "How much do your AI consulting services cost?"}
            }
        },
        {
            "event": "messages.upsert",
            "data": {
                "key": {"remoteJid": "test_user_1@s.whatsapp.net"},
                "message": {"conversation": "Goodbye"}
            }
        }
    ]
    
    for i, payload in enumerate(test_messages, 1):
        print(f"\n📨 Test Message {i}")
        print("-" * 30)
        
        # Parse the message
        message = whatsapp_service.parse_webhook_message(payload)
        
        if not message:
            print("❌ Failed to parse message")
            continue
        
        print(f"👤 From: {message.sender}")
        print(f"💬 Message: {message.content}")
        print(f"📱 Type: {message.message_type.value}")
        
        # Create agent state
        state = AgentState(
            input_message=message.content,
            sender_phone=message.sender,
            response="",
            conversation_history=[]
        )
        
        # Process through agent
        try:
            result = await lunia_agent.process_message(state)
            print(f"🤖 Response: {result['response']}")
        except Exception as e:
            print(f"❌ Error processing message: {e}")
        
        print()
    
    print("✅ Simulation complete!")

def main():
    """Main function"""
    asyncio.run(run_simulation())

if __name__ == "__main__":
    main()
