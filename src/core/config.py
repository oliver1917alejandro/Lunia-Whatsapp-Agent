import os
import secrets
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from pydantic import Field, validator
from pydantic_settings import BaseSettings

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment"""
    # App settings
    APP_NAME: str = "Lunia WhatsApp Agent"
    VERSION: str = "2.0.0"
    DEBUG: bool = Field(False, env="DEBUG")
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    
    # Security settings
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32), env="SECRET_KEY")
    JWT_SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32), env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field("HS256", env="JWT_ALGORITHM")
    JWT_EXPIRATION_MINUTES: int = Field(1440, env="JWT_EXPIRATION_MINUTES")  # 24 hours
    API_KEYS: List[str] = Field([], env="API_KEYS")
    WEBHOOK_SECRET: str = Field(default_factory=lambda: secrets.token_urlsafe(32), env="WEBHOOK_SECRET")
    
    # Server settings
    HOST: str = Field("0.0.0.0", env="HOST")
    PORT: int = Field(8000, env="PORT")
    WORKERS: int = Field(1, env="WORKERS")
    RELOAD: bool = Field(False, env="RELOAD")
    
    # Database settings
    DATABASE_URL: str = Field("sqlite:///./lunia_agent.db", env="DATABASE_URL")
    DATABASE_POOL_SIZE: int = Field(5, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(10, env="DATABASE_MAX_OVERFLOW")
    
    # Redis settings
    REDIS_URL: str = Field("redis://localhost:6379", env="REDIS_URL")
    REDIS_PASSWORD: Optional[str] = Field(None, env="REDIS_PASSWORD")
    REDIS_DB: int = Field(0, env="REDIS_DB")
    CACHE_TTL_SECONDS: int = Field(3600, env="CACHE_TTL_SECONDS")  # 1 hour    # API Keys
    OPENAI_API_KEY: str = Field("", env="OPENAI_API_KEY")

    # WhatsApp/Evolution API
    EVOLUTION_API_URL: str = Field("", env="EVOLUTION_API_URL")
    EVOLUTION_API_KEY: str = Field("", env="EVOLUTION_API_KEY")
    EVOLUTION_INSTANCE_NAME: str = Field("", env="EVOLUTION_INSTANCE_NAME")

    # Paths (computed at runtime)
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    STORAGE_DIR: Path = BASE_DIR / "storage"
    VECTOR_STORE_DIR: Path = STORAGE_DIR / "vector_store"
    CACHE_DIR: Path = STORAGE_DIR / "cache"
    LOGS_DIR: Path = STORAGE_DIR / "logs"

    # LlamaIndex settings
    LLAMA_DATA_DIR: Path = DATA_DIR / "lunia_info"
    SIMILARITY_TOP_K: int = Field(3, env="SIMILARITY_TOP_K")

    # OpenAI Models
    OPENAI_MODEL: str = Field("gpt-3.5-turbo", env="OPENAI_MODEL")
    OPENAI_EMBEDDING_MODEL: str = Field("text-embedding-ada-002", env="OPENAI_EMBEDDING_MODEL")

    # Audio processing
    MAX_AUDIO_SIZE_MB: int = Field(25, env="MAX_AUDIO_SIZE_MB")
    SUPPORTED_AUDIO_FORMATS: List[str] = ["mp3", "wav", "ogg", "m4a", "flac"]

    # Rate limiting
    MAX_REQUESTS_PER_MINUTE: int = Field(20, env="MAX_REQUESTS_PER_MINUTE")

    # Session management
    SESSION_TIMEOUT_MINUTES: int = Field(30, env="SESSION_TIMEOUT_MINUTES")
    MAX_CONVERSATION_HISTORY: int = Field(10, env="MAX_CONVERSATION_HISTORY")    # Gmail SMTP settings
    SMTP_SERVER: str = Field("", env="SMTP_SERVER")
    SMTP_PORT: int = Field(587, env="SMTP_PORT")
    SMTP_USER: str = Field("", env="SMTP_USER")
    SMTP_PASSWORD: str = Field("", env="SMTP_PASSWORD")

    # Google Calendar service account file
    GOOGLE_SERVICE_ACCOUNT_FILE: str = Field("", env="GOOGLE_SERVICE_ACCOUNT_FILE")

    # Supabase configuration
    SUPABASE_URL: str = Field("", env="SUPABASE_URL")
    SUPABASE_KEY: str = Field("", env="SUPABASE_KEY")# HTTP client timeout seconds
    HTTP_TIMEOUT: int = Field(30, env="HTTP_TIMEOUT")
    
    # Monitoring and metrics
    ENABLE_METRICS: bool = Field(True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(8001, env="METRICS_PORT")
    PROMETHEUS_ENDPOINT: str = Field("/metrics", env="PROMETHEUS_ENDPOINT")
    HEALTH_CHECK_TIMEOUT: int = Field(30, env="HEALTH_CHECK_TIMEOUT")
    
    # Logging settings
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field("%(asctime)s - %(name)s - %(levelname)s - %(message)s", env="LOG_FORMAT")
    LOG_FILE: Optional[str] = Field(None, env="LOG_FILE")
    LOG_MAX_SIZE: int = Field(10485760, env="LOG_MAX_SIZE")  # 10MB
    LOG_BACKUP_COUNT: int = Field(5, env="LOG_BACKUP_COUNT")
    
    # Performance settings
    MAX_CONCURRENT_REQUESTS: int = Field(100, env="MAX_CONCURRENT_REQUESTS")
    REQUEST_TIMEOUT_SECONDS: int = Field(300, env="REQUEST_TIMEOUT_SECONDS")  # 5 minutes
    BACKGROUND_TASK_TIMEOUT: int = Field(600, env="BACKGROUND_TASK_TIMEOUT")  # 10 minutes
    
    # SSL/TLS settings
    SSL_CERT_PATH: Optional[str] = Field(None, env="SSL_CERT_PATH")
    SSL_KEY_PATH: Optional[str] = Field(None, env="SSL_KEY_PATH")
    ENABLE_HTTPS: bool = Field(False, env="ENABLE_HTTPS")
    
    # Validation methods
    @validator('LOG_LEVEL')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'LOG_LEVEL must be one of {valid_levels}')
        return v.upper()
    
    @validator('ENVIRONMENT')
    def validate_environment(cls, v):
        valid_envs = ['development', 'staging', 'production']
        if v.lower() not in valid_envs:
            raise ValueError(f'ENVIRONMENT must be one of {valid_envs}')
        return v.lower()
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT.lower() == 'production'
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.ENVIRONMENT.lower() == 'development'

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Initialize settings instance and directory setup
settings = Settings()

# Replace legacy Config name for backwards compatibility
Config = settings

# Create directories
os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
os.makedirs(settings.VECTOR_STORE_DIR, exist_ok=True)
os.makedirs(settings.CACHE_DIR, exist_ok=True)
os.makedirs(settings.LOGS_DIR, exist_ok=True)

# Configure logging
def setup_logging():
    """Setup application logging"""
    log_level = getattr(logging, settings.LOG_LEVEL)
    logging.basicConfig(
        level=log_level,
        format=settings.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(),
            *([logging.FileHandler(settings.LOG_FILE)] if settings.LOG_FILE else [])
        ]
    )

# Initialize logging
setup_logging()
