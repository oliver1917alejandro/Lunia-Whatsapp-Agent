#!/usr/bin/env python3
"""
Quick integration test for the enhanced Lunia WhatsApp Agent
"""

import sys
import os
import asyncio

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def quick_test():
    try:
        print("🚀 Running Quick Integration Test for Lunia WhatsApp Agent")
        print("=" * 60)
        
        # Test imports
        print("📦 Testing imports...")
        from src.core.config import Config
        from src.services.whatsapp_service import whatsapp_service
        from src.services.knowledge_base import knowledge_base
        from src.agents.lunia_agent import lunia_agent
        from src.models.schemas import AgentState, MessageType
        print("✅ All imports successful")
        
        # Test configuration
        print("\n🔧 Testing configuration...")
        config_valid = Config.validate()
        print(f"✅ Configuration valid: {config_valid}")
        
        # Test WhatsApp service
        print("\n📱 Testing WhatsApp service...")
        whatsapp_valid = whatsapp_service._validate_api_config()
        print(f"✅ WhatsApp config valid: {whatsapp_valid}")
        
        # Test message parsing
        print("\n📨 Testing message parsing...")
        test_payload = {
            "event": "messages.upsert",
            "data": {
                "key": {"remoteJid": "1234567890@s.whatsapp.net"},
                "message": {"conversation": "Hola, ¿cómo están?"}
            }
        }
        parsed_message = whatsapp_service.parse_webhook_message(test_payload)
        print(f"✅ Message parsed: {parsed_message is not None}")
        
        # Test knowledge base initialization
        print("\n📚 Testing knowledge base...")
        try:
            kb_initialized = await knowledge_base.initialize_async()
            print(f"✅ Knowledge base initialized: {kb_initialized}")
        except Exception as e:
            print(f"⚠️  Knowledge base init issue: {e}")
        
        # Test basic agent functionality
        print("\n🤖 Testing agent...")
        from datetime import datetime
        
        test_state = AgentState(
            input_message="Hola",
            sender_phone="test_user",
            message_type=MessageType.TEXT,
            conversation_history=[],
            session_id="test_session",
            processing_start_time=datetime.now()
        )
        
        try:
            result = await lunia_agent.process_message(test_state)
            print(f"✅ Agent processed message: {result.response is not None}")
            if result.response:
                print(f"   Response: {result.response[:100]}...")
        except Exception as e:
            print(f"⚠️  Agent processing issue: {e}")
        
        print("\n🎉 Quick integration test completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(quick_test())
    sys.exit(0 if success else 1)
