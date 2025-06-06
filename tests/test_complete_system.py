#!/usr/bin/env python3
"""
Comprehensive test script for Lunia WhatsApp Agent
Tests all components, services, and integrations
"""
import asyncio
import aiohttp
import json
import time
import sys
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import settings

class LuniaAgentTester:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or f"http://{settings.HOST}:{settings.PORT}"
        self.session = None
        self.test_results = []
        self.api_key = "test-api-key"  # You should configure this
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, success: bool, message: str = "", duration: float = 0):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name} ({duration:.2f}s)")
        if message:
            print(f"    {message}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        })
    
    async def test_server_startup(self):
        """Test if server is running and responding"""
        start_time = time.time()
        try:
            async with self.session.get(f"{self.base_url}/") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test(
                        "Server Startup", 
                        True, 
                        f"Version: {data.get('version', 'unknown')}", 
                        time.time() - start_time
                    )
                    return True
                else:
                    self.log_test("Server Startup", False, f"HTTP {response.status}", time.time() - start_time)
                    return False
        except Exception as e:
            self.log_test("Server Startup", False, str(e), time.time() - start_time)
            return False
    
    async def test_health_check(self):
        """Test health check endpoint"""
        start_time = time.time()
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    services = data.get('services', {})
                    healthy_services = sum(1 for s in services.values() if s.get('configured', False))
                    self.log_test(
                        "Health Check", 
                        True, 
                        f"Services configured: {healthy_services}/{len(services)}", 
                        time.time() - start_time
                    )
                    return True
                else:
                    self.log_test("Health Check", False, f"HTTP {response.status}", time.time() - start_time)
                    return False
        except Exception as e:
            self.log_test("Health Check", False, str(e), time.time() - start_time)
            return False
    
    async def test_knowledge_base(self):
        """Test knowledge base functionality"""
        start_time = time.time()
        test_query = {
            "question": "What services do you offer?",
            "context": "Testing knowledge base"
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/knowledge-base/query",
                json=test_query,
                headers={"X-API-Key": self.api_key}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    answer = data.get('answer', '')
                    self.log_test(
                        "Knowledge Base Query", 
                        bool(answer), 
                        f"Answer length: {len(answer)} chars" if answer else "No answer returned", 
                        time.time() - start_time
                    )
                    return bool(answer)
                else:
                    self.log_test("Knowledge Base Query", False, f"HTTP {response.status}", time.time() - start_time)
                    return False
        except Exception as e:
            self.log_test("Knowledge Base Query", False, str(e), time.time() - start_time)
            return False
    
    async def test_message_processing(self):
        """Test message processing endpoint"""
        start_time = time.time()
        test_message = {
            "message": "Hello, can you help me with information about your services?",
            "sender": "test_user_12345"
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/test/message",
                json=test_message,
                headers={"X-API-Key": self.api_key}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    response_text = data.get('response', '')
                    intent = data.get('intent', '')
                    confidence = data.get('confidence', 0)
                    
                    self.log_test(
                        "Message Processing", 
                        bool(response_text), 
                        f"Intent: {intent}, Confidence: {confidence:.2f}, Response: {len(response_text)} chars", 
                        time.time() - start_time
                    )
                    return bool(response_text)
                else:
                    self.log_test("Message Processing", False, f"HTTP {response.status}", time.time() - start_time)
                    return False
        except Exception as e:
            self.log_test("Message Processing", False, str(e), time.time() - start_time)
            return False
    
    async def test_session_management(self):
        """Test session management"""
        start_time = time.time()
        test_user = "test_session_user"
        
        try:
            # First, try to get session (should not exist)
            async with self.session.get(
                f"{self.base_url}/api/sessions/{test_user}",
                headers={"X-API-Key": self.api_key}
            ) as response:
                session_exists = response.status == 200
            
            # Create a session by sending a message
            test_message = {
                "message": "Create session test",
                "sender": test_user
            }
            
            async with self.session.post(
                f"{self.base_url}/api/test/message",
                json=test_message,
                headers={"X-API-Key": self.api_key}
            ) as response:
                message_processed = response.status == 200
            
            # Now try to get session again
            async with self.session.get(
                f"{self.base_url}/api/sessions/{test_user}",
                headers={"X-API-Key": self.api_key}
            ) as response:
                session_created = response.status == 200
                if session_created:
                    data = await response.json()
                    turns = data.get('conversation_turns', 0)
            
            # Clean up - delete session
            async with self.session.delete(
                f"{self.base_url}/api/sessions/{test_user}",
                headers={"X-API-Key": self.api_key}
            ) as response:
                cleanup_success = response.status == 200
            
            success = message_processed and session_created and cleanup_success
            message = f"Session lifecycle: {'✓' if success else '✗'}"
            if session_created:
                message += f", Turns: {turns}"
            
            self.log_test("Session Management", success, message, time.time() - start_time)
            return success
            
        except Exception as e:
            self.log_test("Session Management", False, str(e), time.time() - start_time)
            return False
    
    async def test_stats_endpoint(self):
        """Test statistics endpoint"""
        start_time = time.time()
        try:
            async with self.session.get(
                f"{self.base_url}/api/stats",
                headers={"X-API-Key": self.api_key}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    stats = data.get('stats', {})
                    system_info = stats.get('system', {})
                    version = system_info.get('version', 'unknown')
                    
                    self.log_test(
                        "Statistics Endpoint", 
                        True, 
                        f"Version: {version}, Categories: {len(stats)}", 
                        time.time() - start_time
                    )
                    return True
                else:
                    self.log_test("Statistics Endpoint", False, f"HTTP {response.status}", time.time() - start_time)
                    return False
        except Exception as e:
            self.log_test("Statistics Endpoint", False, str(e), time.time() - start_time)
            return False
    
    async def test_metrics_endpoint(self):
        """Test metrics endpoint"""
        start_time = time.time()
        try:
            async with self.session.get(f"{self.base_url}/api/metrics") as response:
                if response.status == 200:
                    data = await response.json()
                    metrics = data.get('system', {})
                    cpu_info = metrics.get('cpu_percent', 'N/A')
                    
                    self.log_test(
                        "Metrics Endpoint", 
                        True, 
                        f"CPU: {cpu_info}%, Categories: {len(data)}", 
                        time.time() - start_time
                    )
                    return True
                else:
                    self.log_test("Metrics Endpoint", False, f"HTTP {response.status}", time.time() - start_time)
                    return False
        except Exception as e:
            self.log_test("Metrics Endpoint", False, str(e), time.time() - start_time)
            return False
    
    async def test_email_service(self):
        """Test email service status"""
        start_time = time.time()
        try:
            async with self.session.get(
                f"{self.base_url}/api/email/status",
                headers={"X-API-Key": self.api_key}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    configured = data.get('configured', False)
                    
                    self.log_test(
                        "Email Service", 
                        True, 
                        f"Configured: {'✓' if configured else '✗'}", 
                        time.time() - start_time
                    )
                    return True
                else:
                    self.log_test("Email Service", False, f"HTTP {response.status}", time.time() - start_time)
                    return False
        except Exception as e:
            self.log_test("Email Service", False, str(e), time.time() - start_time)
            return False
    
    async def test_calendar_service(self):
        """Test calendar service status"""
        start_time = time.time()
        try:
            async with self.session.get(
                f"{self.base_url}/api/calendar/status",
                headers={"X-API-Key": self.api_key}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    authenticated = data.get('authenticated', False)
                    
                    self.log_test(
                        "Calendar Service", 
                        True, 
                        f"Authenticated: {'✓' if authenticated else '✗'}", 
                        time.time() - start_time
                    )
                    return True
                else:
                    self.log_test("Calendar Service", False, f"HTTP {response.status}", time.time() - start_time)
                    return False
        except Exception as e:
            self.log_test("Calendar Service", False, str(e), time.time() - start_time)
            return False
    
    async def test_database_service(self):
        """Test database service status"""
        start_time = time.time()
        try:
            async with self.session.get(
                f"{self.base_url}/api/database/status",
                headers={"X-API-Key": self.api_key}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    connected = data.get('connected', False)
                    
                    self.log_test(
                        "Database Service", 
                        True, 
                        f"Connected: {'✓' if connected else '✗'}", 
                        time.time() - start_time
                    )
                    return True
                else:
                    self.log_test("Database Service", False, f"HTTP {response.status}", time.time() - start_time)
                    return False
        except Exception as e:
            self.log_test("Database Service", False, str(e), time.time() - start_time)
            return False
    
    async def test_performance_load(self):
        """Test performance under load"""
        start_time = time.time()
        try:
            # Send multiple concurrent requests
            tasks = []
            for i in range(10):
                test_message = {
                    "message": f"Performance test message {i}",
                    "sender": f"perf_test_user_{i}"
                }
                task = self.session.post(
                    f"{self.base_url}/api/test/message",
                    json=test_message,
                    headers={"X-API-Key": self.api_key}
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            successful_responses = sum(1 for r in responses if not isinstance(r, Exception) and r.status == 200)
            
            self.log_test(
                "Performance Load Test", 
                successful_responses >= 8,  # At least 80% success rate
                f"Successful: {successful_responses}/10 requests", 
                time.time() - start_time
            )
            return successful_responses >= 8
            
        except Exception as e:
            self.log_test("Performance Load Test", False, str(e), time.time() - start_time)
            return False
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🧪 Starting Lunia WhatsApp Agent Comprehensive Test Suite")
        print("=" * 60)
        
        # Core functionality tests
        tests = [
            self.test_server_startup,
            self.test_health_check,
            self.test_knowledge_base,
            self.test_message_processing,
            self.test_session_management,
            self.test_stats_endpoint,
            self.test_metrics_endpoint,
        ]
        
        # Service integration tests
        service_tests = [
            self.test_email_service,
            self.test_calendar_service,
            self.test_database_service,
        ]
        
        # Performance tests
        performance_tests = [
            self.test_performance_load,
        ]
        
        all_tests = tests + service_tests + performance_tests
        
        # Run tests
        for test_func in all_tests:
            await test_func()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Failed tests details
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print("\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"  • {test['test']}: {test['message']}")
        
        # Save results to file
        results_file = Path(project_root) / "test_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": total - passed,
                    "success_rate": success_rate
                },
                "results": self.test_results
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        return success_rate >= 80  # Consider 80%+ success rate as overall pass

async def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Lunia WhatsApp Agent Test Suite")
    parser.add_argument("--url", default=None, help="Base URL for testing (default: from config)")
    parser.add_argument("--api-key", default="test-api-key", help="API key for authenticated endpoints")
    
    args = parser.parse_args()
    
    async with LuniaAgentTester(base_url=args.url) as tester:
        tester.api_key = args.api_key
        success = await tester.run_all_tests()
        
        if success:
            print("\n🎉 Overall test suite: PASSED")
            sys.exit(0)
        else:
            print("\n💥 Overall test suite: FAILED")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
