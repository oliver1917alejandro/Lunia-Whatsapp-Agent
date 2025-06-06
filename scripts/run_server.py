#!/usr/bin/env python3
"""
Development server script for Lunia WhatsApp Agent
"""

import uvicorn
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.core.config import Config

def main():
    """Run the development server"""
    print(f"🚀 Starting {Config.APP_NAME} v{Config.VERSION}")
    print(f"📍 Server will be available at: http://localhost:8000")
    print(f"📚 API docs at: http://localhost:8000/docs")
    print(f"🔧 Debug mode: {Config.DEBUG}")
    
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=Config.DEBUG,
        log_level="debug" if Config.DEBUG else "info",
        access_log=True
    )

if __name__ == "__main__":
    main()
