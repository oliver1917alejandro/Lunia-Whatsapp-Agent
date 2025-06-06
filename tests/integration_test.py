#!/usr/bin/env python3
"""
Integration test script for Lunia WhatsApp Agent

This script tests the complete workflow of the enhanced agent system,
including all major components and their interactions.
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.core.config import Config
    from src.core.logger import logger
    from src.services.whatsapp_service import whatsapp_service
    from src.services.knowledge_base import knowledge_base
    from src.services.session_manager import session_manager
    from src.agents.lunia_agent import lunia_agent
    from src.models.schemas import AgentState, MessageType, WhatsAppMessage
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure to run this script from the project root directory")
    sys.exit(1)


class IntegrationTester:
    """Integration test suite for the enhanced agent system"""
    
    def __init__(self):
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        self.test_phone = "1234567890"
        
    async def run_all_tests(self):
        """Run complete integration test suite"""
        print("🚀 Starting Lunia WhatsApp Agent Integration Tests")
        print("=" * 60)
        
        # Configuration tests
        await self.test_configuration()
        
        # Service initialization tests
        await self.test_service_initialization()
        
        # Knowledge base tests
        await self.test_knowledge_base()
        
        # WhatsApp service tests
        await self.test_whatsapp_service()
        
        # Session management tests
        await self.test_session_management()
        
        # Agent workflow tests
        await self.test_agent_workflow()
        
        # Message processing tests
        await self.test_message_processing()
        
        # Error handling tests
        await self.test_error_handling()
        
        # Performance tests
        await self.test_performance()
        
        # Print results
        self.print_results()
        
    async def test_configuration(self):
        """Test configuration validation"""
        print("\n📋 Testing Configuration...")
        
        try:
            # Test config validation
            is_valid = Config.validate()
            self.assert_test(is_valid, "Configuration validation")
            
            # Test required environment variables
            required_vars = ['OPENAI_API_KEY', 'EVOLUTION_API_URL', 'EVOLUTION_API_KEY']
            for var in required_vars:
                value = getattr(Config, var, None)
                self.assert_test(value is not None, f"Environment variable {var}")
                
        except Exception as e:
            self.record_error("Configuration test", e)
    
    async def test_service_initialization(self):
        """Test service initialization"""
        print("\n🔧 Testing Service Initialization...")
        
        try:
            # Test knowledge base initialization
            if not knowledge_base._initialized:
                init_success = await knowledge_base.initialize_async()
                self.assert_test(init_success, "Knowledge base initialization")
            else:
                self.assert_test(True, "Knowledge base already initialized")
            
            # Test WhatsApp service config
            whatsapp_valid = whatsapp_service._validate_api_config()
            self.assert_test(whatsapp_valid, "WhatsApp service configuration")
            
            # Test session manager
            test_session = await session_manager.create_session("test_user")
            self.assert_test(test_session is not None, "Session manager initialization")
            
        except Exception as e:
            self.record_error("Service initialization test", e)
    
    async def test_knowledge_base(self):
        """Test knowledge base functionality"""
        print("\n📚 Testing Knowledge Base...")
        
        try:
            # Test document addition
            test_doc = "Lunia Soluciones ofrece servicios de inteligencia artificial y desarrollo de software."
            add_success = await knowledge_base.add_document_async(test_doc)
            self.assert_test(add_success, "Document addition")
            
            # Test query functionality
            test_query = "¿Qué servicios ofrece Lunia?"
            answer = await knowledge_base.query_async(test_query)
            self.assert_test(answer is not None, "Knowledge base query")
            print(f"   Query: {test_query}")
            print(f"   Answer: {answer[:100]}..." if answer else "   Answer: None")
            
            # Test query with context
            context = "Usuario pregunta sobre servicios"
            answer_with_context = await knowledge_base.query_async(test_query, context=context)
            self.assert_test(answer_with_context is not None, "Knowledge base query with context")
            
        except Exception as e:
            self.record_error("Knowledge base test", e)
    
    async def test_whatsapp_service(self):
        """Test WhatsApp service functionality"""
        print("\n📱 Testing WhatsApp Service...")
        
        try:
            # Test message parsing
            test_payload = {
                "event": "messages.upsert",
                "data": {
                    "key": {"remoteJid": "1234567890@s.whatsapp.net"},
                    "message": {"conversation": "Hola, ¿cómo están?"}
                }
            }
            
            parsed_message = whatsapp_service.parse_webhook_message(test_payload)
            self.assert_test(parsed_message is not None, "Message parsing")
            self.assert_test(parsed_message.sender == "1234567890", "Sender extraction")
            self.assert_test(parsed_message.content == "Hola, ¿cómo están?", "Content extraction")
            
            # Test audio message parsing
            audio_payload = {
                "event": "messages.upsert",
                "data": {
                    "key": {"remoteJid": "1234567890@s.whatsapp.net"},
                    "message": {"audioMessage": {"url": "use_sample_audio.mp3"}}
                }
            }
            
            audio_message = whatsapp_service.parse_webhook_message(audio_payload)
            self.assert_test(audio_message is not None, "Audio message parsing")
            self.assert_test(audio_message.message_type == MessageType.AUDIO, "Audio message type")
            
            # Test message sending (simulation)
            send_success = await whatsapp_service.send_message(
                self.test_phone, 
                "Test message from integration test"
            )
            self.assert_test(send_success, "Message sending")
            
            # Test long message splitting
            long_message = "A" * 5000  # Very long message
            messages = whatsapp_service._split_message(long_message)
            self.assert_test(len(messages) > 1, "Long message splitting")
            
        except Exception as e:
            self.record_error("WhatsApp service test", e)
    
    async def test_session_management(self):
        """Test session management functionality"""
        print("\n👤 Testing Session Management...")
        
        try:
            test_user = "integration_test_user"
            
            # Test session creation
            session = await session_manager.create_session(test_user)
            self.assert_test(session is not None, "Session creation")
            self.assert_test(session.user_id == test_user, "Session user ID")
            
            # Test message addition
            from src.models.schemas import ConversationRole
            await session_manager.add_message(
                test_user, 
                ConversationRole.USER, 
                "Test message"
            )
            
            # Test session retrieval
            retrieved_session = await session_manager.get_session(test_user)
            self.assert_test(retrieved_session is not None, "Session retrieval")
            self.assert_test(len(retrieved_session.conversation_history) == 1, "Message storage")
            
            # Test session cleanup
            await session_manager.delete_session(test_user)
            deleted_session = await session_manager.get_session(test_user)
            self.assert_test(deleted_session is None, "Session deletion")
            
        except Exception as e:
            self.record_error("Session management test", e)
    
    async def test_agent_workflow(self):
        """Test agent workflow functionality"""
        print("\n🤖 Testing Agent Workflow...")
        
        try:
            # Test greeting intent
            greeting_state = AgentState(
                input_message="Hola, buenos días",
                sender_phone=self.test_phone,
                message_type=MessageType.TEXT,
                conversation_history=[],
                session_id=f"test_session_{self.test_phone}",
                processing_start_time=datetime.now()
            )
            
            result_state = await lunia_agent.process_message(greeting_state)
            self.assert_test(result_state.response is not None, "Greeting response generation")
            self.assert_test(result_state.detected_intent is not None, "Intent detection")
            print(f"   Intent: {result_state.detected_intent}")
            print(f"   Response: {result_state.response[:100]}...")
            
            # Test service inquiry
            service_state = AgentState(
                input_message="¿Qué servicios ofrecen?",
                sender_phone=self.test_phone,
                message_type=MessageType.TEXT,
                conversation_history=[],
                session_id=f"test_session_{self.test_phone}",
                processing_start_time=datetime.now()
            )
            
            service_result = await lunia_agent.process_message(service_state)
            self.assert_test(service_result.response is not None, "Service inquiry response")
            self.assert_test("service_inquiry" in service_result.detected_intent, "Service intent detection")
            
            # Test AI consultation inquiry
            ai_state = AgentState(
                input_message="Necesito ayuda con inteligencia artificial",
                sender_phone=self.test_phone,
                message_type=MessageType.TEXT,
                conversation_history=[],
                session_id=f"test_session_{self.test_phone}",
                processing_start_time=datetime.now()
            )
            
            ai_result = await lunia_agent.process_message(ai_state)
            self.assert_test(ai_result.response is not None, "AI consultation response")
            
        except Exception as e:
            self.record_error("Agent workflow test", e)
    
    async def test_message_processing(self):
        """Test complete message processing pipeline"""
        print("\n🔄 Testing Message Processing Pipeline...")
        
        try:
            # Create a realistic webhook message
            webhook_payload = {
                "event": "messages.upsert",
                "data": {
                    "key": {"remoteJid": f"{self.test_phone}@s.whatsapp.net"},
                    "message": {"conversation": "Hola, quiero información sobre sus servicios de IA"}
                }
            }
            
            # Parse message
            message = whatsapp_service.parse_webhook_message(webhook_payload)
            self.assert_test(message is not None, "Webhook message parsing")
            
            # Create agent state
            state = AgentState(
                input_message=message.content,
                sender_phone=message.sender,
                message_type=message.message_type,
                conversation_history=[],
                session_id=f"session_{message.sender}",
                processing_start_time=datetime.now(),
                raw_message_data=message.raw_data
            )
            
            # Process through agent
            result_state = await lunia_agent.process_message(state)
            self.assert_test(result_state.response is not None, "End-to-end processing")
            self.assert_test(result_state.processing_time > 0, "Processing time tracking")
            
            print(f"   Processing time: {result_state.processing_time:.2f}s")
            print(f"   Confidence: {result_state.confidence_level:.2f}")
            
        except Exception as e:
            self.record_error("Message processing test", e)
    
    async def test_error_handling(self):
        """Test error handling capabilities"""
        print("\n⚠️  Testing Error Handling...")
        
        try:
            # Test invalid message parsing
            invalid_payload = {"invalid": "payload"}
            parsed = whatsapp_service.parse_webhook_message(invalid_payload)
            self.assert_test(parsed is None, "Invalid payload handling")
            
            # Test empty message processing
            empty_state = AgentState(
                input_message="",
                sender_phone=self.test_phone,
                message_type=MessageType.TEXT,
                conversation_history=[],
                session_id=f"test_session_{self.test_phone}",
                processing_start_time=datetime.now()
            )
            
            empty_result = await lunia_agent.process_message(empty_state)
            self.assert_test(empty_result.response is not None, "Empty message handling")
            
            # Test very long message
            long_message = "A" * 10000
            long_state = AgentState(
                input_message=long_message,
                sender_phone=self.test_phone,
                message_type=MessageType.TEXT,
                conversation_history=[],
                session_id=f"test_session_{self.test_phone}",
                processing_start_time=datetime.now()
            )
            
            long_result = await lunia_agent.process_message(long_state)
            self.assert_test(long_result.response is not None, "Long message handling")
            
        except Exception as e:
            self.record_error("Error handling test", e)
    
    async def test_performance(self):
        """Test performance characteristics"""
        print("\n⚡ Testing Performance...")
        
        try:
            # Test response time for multiple queries
            test_messages = [
                "Hola",
                "¿Qué servicios ofrecen?",
                "Necesito ayuda con IA",
                "¿Cuánto cuesta?",
                "Gracias"
            ]
            
            total_time = 0
            for i, message in enumerate(test_messages):
                start_time = datetime.now()
                
                state = AgentState(
                    input_message=message,
                    sender_phone=f"perf_test_{i}",
                    message_type=MessageType.TEXT,
                    conversation_history=[],
                    session_id=f"perf_session_{i}",
                    processing_start_time=start_time
                )
                
                result = await lunia_agent.process_message(state)
                processing_time = (datetime.now() - start_time).total_seconds()
                total_time += processing_time
                
                self.assert_test(result.response is not None, f"Performance test {i+1}")
                self.assert_test(processing_time < 30.0, f"Response time {i+1} (<30s)")
            
            avg_time = total_time / len(test_messages)
            print(f"   Average response time: {avg_time:.2f}s")
            self.assert_test(avg_time < 10.0, "Average response time (<10s)")
            
        except Exception as e:
            self.record_error("Performance test", e)
    
    def assert_test(self, condition: bool, test_name: str):
        """Assert a test condition and record result"""
        if condition:
            print(f"   ✅ {test_name}")
            self.test_results["passed"] += 1
        else:
            print(f"   ❌ {test_name}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Assertion failed: {test_name}")
    
    def record_error(self, test_name: str, error: Exception):
        """Record a test error"""
        print(f"   ❌ {test_name}: {str(error)}")
        self.test_results["failed"] += 1
        self.test_results["errors"].append(f"{test_name}: {str(error)}")
        logger.error(f"Integration test error in {test_name}: {error}")
    
    def print_results(self):
        """Print final test results"""
        print("\n" + "=" * 60)
        print("🏁 INTEGRATION TEST RESULTS")
        print("=" * 60)
        
        total_tests = self.test_results["passed"] + self.test_results["failed"]
        pass_rate = (self.test_results["passed"] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {self.test_results['passed']} ✅")
        print(f"Failed: {self.test_results['failed']} ❌")
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        if self.test_results["errors"]:
            print("\n🔍 ERROR DETAILS:")
            for error in self.test_results["errors"]:
                print(f"   • {error}")
        
        if pass_rate >= 80:
            print("\n🎉 Integration tests PASSED! System is ready for deployment.")
        else:
            print("\n⚠️  Integration tests FAILED! Please fix issues before deployment.")
        
        return pass_rate >= 80


async def main():
    """Main test execution"""
    tester = IntegrationTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
