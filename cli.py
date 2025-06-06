#!/usr/bin/env python3
"""
CLI utilities for Lunia WhatsApp Agent
Provides command-line tools for testing, management, and monitoring
"""

import asyncio
import argparse
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Add project root to path
sys.path.append('.')

from src.core.config import Config
from src.core.logger import logger
from src.services.email_service import EmailService
from src.services.calendar_service import CalendarService
from src.services.supabase_service import SupabaseService
from src.services.agent_service_integration import AgentServiceIntegration
from src.agents.lunia_agent_enhanced import LuniaAgent
from src.models.schemas import AgentState, MessageType


class LuniaCLI:
    """Command Line Interface for Lunia WhatsApp Agent"""
    
    def __init__(self):
        self.email_service = None
        self.calendar_service = None
        self.supabase_service = None
        self.service_integration = None
        self.agent = None
    
    async def initialize_services(self):
        """Initialize all services"""
        try:
            self.email_service = EmailService()
            self.calendar_service = CalendarService()
            self.supabase_service = SupabaseService()
            
            self.service_integration = AgentServiceIntegration(
                email_service=self.email_service,
                calendar_service=self.calendar_service,
                supabase_service=self.supabase_service
            )
            
            self.agent = LuniaAgent(service_integration=self.service_integration)
            
            print("✅ Services initialized successfully")
            
        except Exception as e:
            print(f"❌ Error initializing services: {e}")
            return False
        
        return True
    
    async def test_email(self, to_email: str, subject: str = None, body: str = None):
        """Test email functionality"""
        if not self.email_service:
            await self.initialize_services()
        
        subject = subject or f"Test Email from Lunia CLI - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        body = body or "This is a test email sent from the Lunia WhatsApp Agent CLI tool."
        
        try:
            print(f"📧 Sending test email to {to_email}...")
            success = await self.email_service.send_email(
                to_email=to_email,
                subject=subject,
                body=body
            )
            
            if success:
                print("✅ Email sent successfully!")
                return True
            else:
                print("❌ Failed to send email")
                return False
                
        except Exception as e:
            print(f"❌ Email test error: {e}")
            return False
    
    async def test_calendar(self, summary: str = None, minutes_from_now: int = 60):
        """Test calendar functionality"""
        if not self.calendar_service:
            await self.initialize_services()
        
        summary = summary or f"Test Event from Lunia CLI - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        start_time = datetime.now() + timedelta(minutes=minutes_from_now)
        end_time = start_time + timedelta(hours=1)
        
        try:
            print(f"📅 Creating test calendar event: {summary}")
            print(f"⏰ Scheduled for: {start_time.strftime('%Y-%m-%d %H:%M')}")
            
            event_id = await self.calendar_service.create_event(
                summary=summary,
                description="Test event created from Lunia WhatsApp Agent CLI tool",
                start_datetime=start_time,
                end_datetime=end_time
            )
            
            if event_id:
                print(f"✅ Calendar event created successfully! Event ID: {event_id}")
                return event_id
            else:
                print("❌ Failed to create calendar event")
                return None
                
        except Exception as e:
            print(f"❌ Calendar test error: {e}")
            return None
    
    async def test_database(self, table: str = "test_table"):
        """Test database functionality"""
        if not self.supabase_service:
            await self.initialize_services()
        
        test_data = {
            "test_field": f"CLI Test - {datetime.now().isoformat()}",
            "user": "lunia_cli",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            print(f"🗄️ Testing database operations on table: {table}")
            
            # Test insert
            print("📝 Inserting test record...")
            result = await self.supabase_service.insert(table, test_data)
            
            if result:
                print("✅ Database insert successful!")
                
                # Test select
                print("🔍 Querying test records...")
                records = await self.supabase_service.select(
                    table=table,
                    filters={"user": "lunia_cli"},
                    limit=5
                )
                
                if records:
                    print(f"✅ Database query successful! Found {len(records)} records")
                    return True
                else:
                    print("⚠️ No records found")
                    return True
            else:
                print("❌ Database insert failed")
                return False
                
        except Exception as e:
            print(f"❌ Database test error: {e}")
            return False
    
    async def test_agent_message(self, message: str, phone: str = "test_user"):
        """Test agent message processing"""
        if not self.agent:
            await self.initialize_services()
        
        try:
            print(f"🤖 Testing agent with message: '{message}'")
            print(f"👤 From user: {phone}")
            
            # Create agent state
            state = AgentState(
                input_message=message,
                sender_phone=phone,
                message_type=MessageType.TEXT,
                conversation_history=[],
                session_id=f"cli_test_{phone}",
                processing_start_time=datetime.now()
            )
            
            # Process message
            result = await self.agent.process_message(state)
            
            print(f"\n📥 Input: {result.input_message}")
            print(f"🎯 Intent: {result.intent}")
            print(f"🎲 Confidence: {result.confidence}")
            print(f"📤 Response: {result.response}")
            
            if hasattr(result, 'service_action_taken') and result.service_action_taken:
                print(f"⚙️ Service Action: {result.service_action_result}")
            
            return result
            
        except Exception as e:
            print(f"❌ Agent test error: {e}")
            return None
    
    async def check_service_status(self):
        """Check status of all services"""
        if not await self.initialize_services():
            return
        
        print("🔍 Checking service status...\n")
        
        # Check email service
        try:
            email_status = await self.email_service.test_connection()
            print(f"📧 Email Service: {'✅ Connected' if email_status else '❌ Not configured'}")
        except Exception as e:
            print(f"📧 Email Service: ❌ Error - {e}")
        
        # Check calendar service
        try:
            calendar_status = await self.calendar_service.test_connection()
            print(f"📅 Calendar Service: {'✅ Authenticated' if calendar_status else '❌ Not authenticated'}")
        except Exception as e:
            print(f"📅 Calendar Service: ❌ Error - {e}")
        
        # Check database service
        try:
            db_status = await self.supabase_service.test_connection()
            print(f"🗄️ Database Service: {'✅ Connected' if db_status else '❌ Not connected'}")
        except Exception as e:
            print(f"🗄️ Database Service: ❌ Error - {e}")
        
        print(f"\n📋 Configuration Status:")
        print(f"   - Environment: {getattr(Config, 'ENVIRONMENT', 'development')}")
        print(f"   - Debug Mode: {getattr(Config, 'DEBUG', False)}")
        print(f"   - App Version: {getattr(Config, 'VERSION', 'unknown')}")
    
    async def get_service_statistics(self):
        """Get service usage statistics"""
        if not self.service_integration:
            await self.initialize_services()
        
        try:
            print("📊 Fetching service statistics...\n")
            
            stats = await self.service_integration.get_service_statistics()
            
            if "error" in stats:
                print(f"❌ Error getting statistics: {stats['error']}")
                return
            
            print(f"📈 Total Service Actions: {stats.get('total_actions', 0)}")
            
            action_types = stats.get('action_types', {})
            if action_types:
                print("\n🎯 Action Types:")
                for action, count in action_types.items():
                    print(f"   - {action}: {count}")
            
            print(f"\n🕒 Last Updated: {stats.get('last_updated', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ Statistics error: {e}")
    
    async def cleanup_test_data(self):
        """Clean up test data from database"""
        if not self.supabase_service:
            await self.initialize_services()
        
        try:
            print("🧹 Cleaning up test data...")
            
            # Delete test records
            success = await self.supabase_service.delete(
                table="test_table",
                filters={"user": "lunia_cli"}
            )
            
            if success:
                print("✅ Test data cleaned up successfully")
            else:
                print("⚠️ No test data found to clean up")
                
        except Exception as e:
            print(f"❌ Cleanup error: {e}")


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Lunia WhatsApp Agent CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Check service status")
    
    # Test commands
    test_parser = subparsers.add_parser("test", help="Test services")
    test_subparsers = test_parser.add_subparsers(dest="test_type", help="Test types")
    
    # Test email
    email_parser = test_subparsers.add_parser("email", help="Test email service")
    email_parser.add_argument("to_email", help="Recipient email address")
    email_parser.add_argument("--subject", help="Email subject")
    email_parser.add_argument("--body", help="Email body")
    
    # Test calendar
    calendar_parser = test_subparsers.add_parser("calendar", help="Test calendar service")
    calendar_parser.add_argument("--summary", help="Event summary")
    calendar_parser.add_argument("--minutes", type=int, default=60, help="Minutes from now")
    
    # Test database
    db_parser = test_subparsers.add_parser("database", help="Test database service")
    db_parser.add_argument("--table", default="test_table", help="Table name")
    
    # Test agent
    agent_parser = test_subparsers.add_parser("agent", help="Test agent message processing")
    agent_parser.add_argument("message", help="Message to process")
    agent_parser.add_argument("--phone", default="test_user", help="Phone number")
    
    # Statistics command
    stats_parser = subparsers.add_parser("stats", help="Get service statistics")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up test data")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = LuniaCLI()
    
    try:
        if args.command == "status":
            await cli.check_service_status()
        
        elif args.command == "test":
            if args.test_type == "email":
                await cli.test_email(args.to_email, args.subject, args.body)
            elif args.test_type == "calendar":
                await cli.test_calendar(args.summary, args.minutes)
            elif args.test_type == "database":
                await cli.test_database(args.table)
            elif args.test_type == "agent":
                await cli.test_agent_message(args.message, args.phone)
            else:
                test_parser.print_help()
        
        elif args.command == "stats":
            await cli.get_service_statistics()
        
        elif args.command == "cleanup":
            await cli.cleanup_test_data()
        
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\n⏸️ Operation cancelled by user")
    except Exception as e:
        print(f"❌ CLI Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
