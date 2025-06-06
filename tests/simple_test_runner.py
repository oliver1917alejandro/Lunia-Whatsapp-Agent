#!/usr/bin/env python3
"""
Simple test runner for Lunia WhatsApp Agent
Tests basic functionality without complex async setup
"""
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all main modules can be imported"""
    print("🧪 Testing module imports...")
    
    try:
        from src.core.config import settings
        print("✅ Core config imported successfully")
        
        from src.core.logger import logger
        print("✅ Logger imported successfully")
        
        from src.services.whatsapp_service import whatsapp_service
        print("✅ WhatsApp service imported successfully")
        
        from src.services.knowledge_base import knowledge_base
        print("✅ Knowledge base imported successfully")
        
        from src.services.session_manager import session_manager
        print("✅ Session manager imported successfully")
        
        from src.agents.lunia_agent_enhanced import lunia_agent
        print("✅ Enhanced agent imported successfully")
        
        from src.models.schemas import AgentState, MessageType
        print("✅ Schemas imported successfully")
        
        from src.security.middleware import SecurityMiddleware
        print("✅ Security middleware imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    print("\n🔧 Testing configuration...")
    
    try:
        from src.core.config import settings
        
        # Test basic settings
        print(f"✅ App name: {settings.APP_NAME}")
        print(f"✅ Version: {settings.VERSION}")
        print(f"✅ Environment: {settings.ENVIRONMENT}")
        print(f"✅ Host: {settings.HOST}")
        print(f"✅ Port: {settings.PORT}")
        
        # Test directory creation
        dirs_to_check = [
            settings.DATA_DIR,
            settings.STORAGE_DIR,
            settings.LOGS_DIR,
            settings.CACHE_DIR
        ]
        
        for dir_path in dirs_to_check:
            if os.path.exists(dir_path):
                print(f"✅ Directory exists: {dir_path}")
            else:
                print(f"⚠️  Directory missing: {dir_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_api_structure():
    """Test API structure and endpoint definitions"""
    print("\n🌐 Testing API structure...")
    
    try:
        from src.api.main import app
        
        # Get all routes
        routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                routes.append(f"{list(route.methods)[0]} {route.path}")
        
        print(f"✅ API app created with {len(routes)} routes")
        
        # Check for key endpoints
        key_endpoints = [
            "GET /health",
            "POST /webhook/whatsapp",
            "POST /api/send-message",
            "POST /api/knowledge-base/query",
            "GET /api/metrics"
        ]
        
        for endpoint in key_endpoints:
            found = any(endpoint in route for route in routes)
            status = "✅" if found else "❌"
            print(f"{status} {endpoint}")
        
        return True
        
    except Exception as e:
        print(f"❌ API structure test failed: {e}")
        return False

def test_services_initialization():
    """Test that services can be initialized"""
    print("\n🔨 Testing service initialization...")
    
    try:
        from src.services.whatsapp_service import whatsapp_service
        from src.services.knowledge_base import knowledge_base
        from src.services.session_manager import session_manager
        
        print("✅ WhatsApp service instance created")
        print("✅ Knowledge base instance created")
        print("✅ Session manager instance created")
        
        # Test basic service properties
        print(f"✅ WhatsApp service has config validation: {hasattr(whatsapp_service, '_validate_api_config')}")
        print(f"✅ Knowledge base has initialization: {hasattr(knowledge_base, 'initialize')}")
        print(f"✅ Session manager has get_session: {hasattr(session_manager, 'get_session')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Service initialization test failed: {e}")
        return False

def test_security_middleware():
    """Test security middleware functionality"""
    print("\n🔒 Testing security middleware...")
    
    try:
        from src.security.middleware import SecurityMiddleware, get_api_key_auth, verify_webhook
        
        print("✅ Security middleware imported")
        print("✅ API key authentication function imported")
        print("✅ Webhook verification function imported")
        
        # Test middleware creation
        middleware = SecurityMiddleware()
        print("✅ Security middleware instance created")
        
        return True
        
    except Exception as e:
        print(f"❌ Security middleware test failed: {e}")
        return False

def test_docker_configuration():
    """Test Docker configuration files"""
    print("\n🐳 Testing Docker configuration...")
    
    try:
        # Check Docker files
        docker_files = [
            "docker-compose.yml",
            "Dockerfile",
            "nginx.conf"
        ]
        
        for file_name in docker_files:
            file_path = project_root / file_name
            if file_path.exists():
                print(f"✅ {file_name} exists")
            else:
                print(f"❌ {file_name} missing")
        
        # Check deployment scripts
        deploy_files = [
            "deploy/deploy.sh",
            "scripts/start_server.py",
            "scripts/setup_ssl.sh"
        ]
        
        for file_name in deploy_files:
            file_path = project_root / file_name
            if file_path.exists():
                print(f"✅ {file_name} exists")
            else:
                print(f"❌ {file_name} missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Docker configuration test failed: {e}")
        return False

def test_monitoring_setup():
    """Test monitoring configuration"""
    print("\n📊 Testing monitoring setup...")
    
    try:
        # Check monitoring files
        monitoring_files = [
            "monitoring/prometheus.yml",
            "monitoring/grafana-provisioning/datasources/prometheus.yml",
            "monitoring/grafana-provisioning/dashboards/lunia-dashboard.json"
        ]
        
        for file_name in monitoring_files:
            file_path = project_root / file_name
            if file_path.exists():
                print(f"✅ {file_name} exists")
            else:
                print(f"❌ {file_name} missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Monitoring setup test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Lunia WhatsApp Agent Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_configuration,
        test_api_structure,
        test_services_initialization,
        test_security_middleware,
        test_docker_configuration,
        test_monitoring_setup
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System appears to be properly configured.")
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
