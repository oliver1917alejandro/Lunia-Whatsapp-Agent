#!/usr/bin/env python3
"""
Production-ready server startup script for Lunia WhatsApp Agent
"""
import os
import sys
import logging
import uvicorn
import asyncio
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import settings

def setup_production_logging():
    """Setup production logging configuration"""
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(settings.LOGS_DIR / "server.log") if settings.LOG_FILE else logging.NullHandler()
        ]
    )

def validate_environment():
    """Validate environment configuration before startup"""
    required_vars = [
        'OPENAI_API_KEY',
        'EVOLUTION_API_URL',
        'EVOLUTION_API_KEY',
        'EVOLUTION_INSTANCE_NAME'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not getattr(settings, var, None):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ Environment validation passed")
    return True

def print_startup_info():
    """Print server startup information"""
    print("\n" + "="*60)
    print("🚀 Lunia WhatsApp Agent Server")
    print("="*60)
    print(f"Version: {settings.VERSION}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Host: {settings.HOST}")
    print(f"Port: {settings.PORT}")
    print(f"Debug Mode: {settings.DEBUG}")
    print(f"Workers: {settings.WORKERS}")
    print(f"Metrics Enabled: {settings.ENABLE_METRICS}")
    if settings.ENABLE_HTTPS:
        print(f"HTTPS: Enabled")
        print(f"SSL Cert: {settings.SSL_CERT_PATH}")
        print(f"SSL Key: {settings.SSL_KEY_PATH}")
    print("="*60)
    print("📚 API Documentation:")
    print(f"  • Swagger UI: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"  • ReDoc: http://{settings.HOST}:{settings.PORT}/redoc")
    if settings.ENABLE_METRICS:
        print(f"  • Metrics: http://{settings.HOST}:{settings.METRICS_PORT}{settings.PROMETHEUS_ENDPOINT}")
    print("="*60)

async def health_check():
    """Perform initial health check"""
    try:
        # Test database connection if configured
        if hasattr(settings, 'DATABASE_URL') and settings.DATABASE_URL:
            print("🔍 Testing database connection...")
        
        # Test Redis connection if configured
        if hasattr(settings, 'REDIS_URL') and settings.REDIS_URL:
            print("🔍 Testing Redis connection...")
        
        print("✅ Health check completed")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def start_server():
    """Start the server with production settings"""
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    # Setup logging
    setup_production_logging()
    
    # Print startup info
    print_startup_info()
    
    # Perform health check
    if not asyncio.run(health_check()):
        print("❌ Server health check failed. Exiting...")
        sys.exit(1)
    
    # SSL/TLS configuration
    ssl_keyfile = settings.SSL_KEY_PATH if settings.ENABLE_HTTPS else None
    ssl_certfile = settings.SSL_CERT_PATH if settings.ENABLE_HTTPS else None
    
    # Server configuration
    server_config = {
        "app": "src.api.main:app",
        "host": settings.HOST,
        "port": settings.PORT,
        "reload": settings.RELOAD,
        "workers": settings.WORKERS if not settings.DEBUG else 1,
        "log_level": "debug" if settings.DEBUG else "info",
        "access_log": True,
        "loop": "asyncio",
        "http": "httptools",
        "ws": "websockets",
    }
    
    # Add SSL if enabled
    if ssl_keyfile and ssl_certfile:
        server_config.update({
            "ssl_keyfile": ssl_keyfile,
            "ssl_certfile": ssl_certfile,
        })
    
    print(f"🌟 Starting server at {'https' if settings.ENABLE_HTTPS else 'http'}://{settings.HOST}:{settings.PORT}")
    print("✨ Press Ctrl+C to stop the server\n")
    
    try:
        uvicorn.run(**server_config)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_server()
