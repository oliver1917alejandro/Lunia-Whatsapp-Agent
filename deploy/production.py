#!/usr/bin/env python3
"""
Production deployment and monitoring script for Lunia WhatsApp Agent

This script handles:
- Environment validation
- Service health checks  
- Graceful startup and shutdown
- Monitoring and logging
- Error recovery
"""

import asyncio
import signal
import sys
import os
from datetime import datetime
from typing import Optional
import json
import logging
from contextlib import asynccontextmanager

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.core.config import Config
    from src.core.logger import logger
    from src.services.whatsapp_service import whatsapp_service
    from src.services.knowledge_base import knowledge_base
    from src.services.session_manager import session_manager
    from src.agents.lunia_agent import lunia_agent
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure to run this script from the project root directory")
    sys.exit(1)


class ProductionManager:
    """Production deployment and monitoring manager"""
    
    def __init__(self):
        self.is_running = False
        self.startup_time = None
        self.shutdown_requested = False
        self.health_check_interval = 60  # seconds
        self.session_cleanup_interval = 300  # 5 minutes
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True
    
    async def start_production_server(self):
        """Start the production server with full monitoring"""
        logger.info("🚀 Starting Lunia WhatsApp Agent in Production Mode")
        logger.info("=" * 60)
        
        try:
            # Validate environment
            await self._validate_production_environment()
            
            # Initialize services
            await self._initialize_services()
            
            # Start monitoring tasks
            await self._start_monitoring()
            
            # Keep running until shutdown requested
            await self._run_main_loop()
            
        except Exception as e:
            logger.error(f"❌ Production startup failed: {e}")
            sys.exit(1)
        finally:
            await self._graceful_shutdown()
    
    async def _validate_production_environment(self):
        """Validate production environment setup"""
        logger.info("🔍 Validating Production Environment...")
        
        # Check configuration
        if not Config.validate():
            raise RuntimeError("Configuration validation failed")
        
        # Check required environment variables
        required_vars = {
            'OPENAI_API_KEY': Config.OPENAI_API_KEY,
            'EVOLUTION_API_URL': Config.EVOLUTION_API_URL,
            'EVOLUTION_API_KEY': Config.EVOLUTION_API_KEY,
            'EVOLUTION_INSTANCE_NAME': Config.EVOLUTION_INSTANCE_NAME
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        if missing_vars:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Check API endpoints
        try:
            status = await whatsapp_service.get_instance_status()
            if not status:
                logger.warning("⚠️  WhatsApp API instance may not be ready")
            else:
                logger.info("✅ WhatsApp API instance is accessible")
        except Exception as e:
            logger.warning(f"⚠️  WhatsApp API check failed: {e}")
        
        logger.info("✅ Environment validation completed")
    
    async def _initialize_services(self):
        """Initialize all services with error handling"""
        logger.info("🔧 Initializing Services...")
        
        # Initialize knowledge base
        try:
            if not knowledge_base._initialized:
                success = await knowledge_base.initialize_async()
                if success:
                    logger.info("✅ Knowledge base initialized")
                else:
                    logger.error("❌ Knowledge base initialization failed")
                    raise RuntimeError("Knowledge base initialization failed")
            else:
                logger.info("✅ Knowledge base already initialized")
        except Exception as e:
            logger.error(f"❌ Knowledge base error: {e}")
            raise
        
        # Test agent functionality
        try:
            from src.models.schemas import AgentState, MessageType
            test_state = AgentState(
                input_message="Test initialization",
                sender_phone="system_test",
                message_type=MessageType.TEXT,
                conversation_history=[],
                session_id="init_test",
                processing_start_time=datetime.now()
            )
            
            result = await lunia_agent.process_message(test_state)
            if result.response:
                logger.info("✅ Agent system is ready")
            else:
                logger.warning("⚠️  Agent system may have issues")
        except Exception as e:
            logger.error(f"❌ Agent initialization test failed: {e}")
            raise
        
        logger.info("✅ All services initialized successfully")
    
    async def _start_monitoring(self):
        """Start background monitoring tasks"""
        logger.info("📊 Starting Monitoring Tasks...")
        
        # Start health check task
        asyncio.create_task(self._health_check_loop())
        
        # Start session cleanup task
        asyncio.create_task(self._session_cleanup_loop())
        
        # Start metrics collection task
        asyncio.create_task(self._metrics_collection_loop())
        
        self.startup_time = datetime.now()
        self.is_running = True
        
        logger.info("✅ Monitoring tasks started")
    
    async def _run_main_loop(self):
        """Main application loop"""
        logger.info("🎯 Application is running in production mode")
        logger.info("   Press Ctrl+C to shutdown gracefully")
        
        # Import and start FastAPI server
        try:
            import uvicorn
            from src.api.main import app
            
            # Configure uvicorn for production
            config = uvicorn.Config(
                app=app,
                host="0.0.0.0",
                port=int(os.getenv("PORT", 8000)),
                log_level="info",
                access_log=True,
                loop="asyncio"
            )
            
            server = uvicorn.Server(config)
            
            # Start server in background
            server_task = asyncio.create_task(server.serve())
            
            # Wait for shutdown signal
            while not self.shutdown_requested:
                await asyncio.sleep(1)
            
            # Stop server
            server.should_exit = True
            await server_task
            
        except Exception as e:
            logger.error(f"❌ Server error: {e}")
            raise
    
    async def _health_check_loop(self):
        """Periodic health checks"""
        while not self.shutdown_requested:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(self.health_check_interval)
    
    async def _perform_health_check(self):
        """Perform comprehensive health check"""
        checks = {
            "whatsapp_api": False,
            "knowledge_base": False,
            "session_manager": False,
            "agent_system": False
        }
        
        # Check WhatsApp API
        try:
            status = await whatsapp_service.get_instance_status()
            checks["whatsapp_api"] = status is not None
        except:
            pass
        
        # Check knowledge base
        try:
            test_query = await knowledge_base.query_async("test", timeout=5.0)
            checks["knowledge_base"] = True
        except:
            pass
        
        # Check session manager
        try:
            test_session = await session_manager.get_session("health_check")
            checks["session_manager"] = True
        except:
            pass
        
        # Check agent system
        try:
            from src.models.schemas import AgentState, MessageType
            test_state = AgentState(
                input_message="Health check",
                sender_phone="health_check",
                message_type=MessageType.TEXT,
                conversation_history=[],
                session_id="health_check",
                processing_start_time=datetime.now()
            )
            result = await asyncio.wait_for(
                lunia_agent.process_message(test_state), 
                timeout=10.0
            )
            checks["agent_system"] = result.response is not None
        except:
            pass
        
        # Log health status
        failed_checks = [name for name, status in checks.items() if not status]
        if failed_checks:
            logger.warning(f"⚠️  Health check failed for: {', '.join(failed_checks)}")
        else:
            logger.debug("✅ All health checks passed")
    
    async def _session_cleanup_loop(self):
        """Periodic session cleanup"""
        while not self.shutdown_requested:
            try:
                await session_manager.cleanup_expired_sessions()
                logger.debug("Session cleanup completed")
                await asyncio.sleep(self.session_cleanup_interval)
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
                await asyncio.sleep(self.session_cleanup_interval)
    
    async def _metrics_collection_loop(self):
        """Collect and log system metrics"""
        while not self.shutdown_requested:
            try:
                await self._log_system_metrics()
                await asyncio.sleep(300)  # Every 5 minutes
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(300)
    
    async def _log_system_metrics(self):
        """Log system performance metrics"""
        try:
            uptime = (datetime.now() - self.startup_time).total_seconds() if self.startup_time else 0
            
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": uptime,
                "active_sessions": len(getattr(session_manager, '_sessions', {})),
                "knowledge_base_queries": getattr(knowledge_base, '_query_count', 0),
                "whatsapp_last_message": whatsapp_service.last_message_time,
                "memory_usage": "N/A"  # Could add psutil for memory monitoring
            }
            
            logger.info(f"📊 System Metrics: {json.dumps(metrics, indent=2)}")
            
        except Exception as e:
            logger.error(f"Metrics logging error: {e}")
    
    async def _graceful_shutdown(self):
        """Perform graceful shutdown"""
        logger.info("🛑 Initiating graceful shutdown...")
        
        try:
            # Clean up sessions
            await session_manager.cleanup_expired_sessions()
            logger.info("✅ Session cleanup completed")
            
            # Save any pending data
            # (Add any necessary cleanup here)
            
            # Final metrics log
            if self.startup_time:
                uptime = (datetime.now() - self.startup_time).total_seconds()
                logger.info(f"📊 Final uptime: {uptime:.1f} seconds")
            
            logger.info("✅ Graceful shutdown completed")
            
        except Exception as e:
            logger.error(f"❌ Shutdown error: {e}")
        
        self.is_running = False


async def main():
    """Main entry point for production deployment"""
    manager = ProductionManager()
    await manager.start_production_server()


if __name__ == "__main__":
    print("🏭 Lunia WhatsApp Agent - Production Mode")
    print("=" * 50)
    
    # Set production logging level
    logging.getLogger().setLevel(logging.INFO)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
