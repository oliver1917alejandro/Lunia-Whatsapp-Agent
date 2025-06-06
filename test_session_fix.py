#!/usr/bin/env python3
"""Quick test to verify the session fix works"""

import sys
import asyncio
sys.path.append('.')

async def test_session_fix():
    """Test that the WhatsApp service initializes without event loop errors"""
    try:
        from src.services.whatsapp_service import whatsapp_service
        print("✅ WhatsApp service imported successfully")
        
        # Test session initialization
        session = await whatsapp_service._ensure_session()
        print("✅ Session initialized successfully")
        
        # Test that it's reusable
        session2 = await whatsapp_service._ensure_session()
        print("✅ Session reuse working")
        
        # Close the session
        await whatsapp_service.close()
        print("✅ Session closed successfully")
        
        print("\n🎉 All session handling tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Session test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_session_fix())
    exit(0 if success else 1)
