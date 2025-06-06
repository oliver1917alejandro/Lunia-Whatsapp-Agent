"""
Security hardening and authentication middleware for production
"""
import hashlib
import hmac
import time
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import jwt
from datetime import datetime, timedelta

from src.core.config import Config
from src.core.logger import logger


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for request validation and rate limiting"""
    
    def __init__(self, app, rate_limit_per_minute: int = 60):
        super().__init__(app)
        self.rate_limit = rate_limit_per_minute
        self.request_history: Dict[str, list] = {}
        
    async def dispatch(self, request: Request, call_next):
        # Security headers
        start_time = time.time()
        
        try:
            # Rate limiting
            client_ip = self.get_client_ip(request)
            if not self.check_rate_limit(client_ip):
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded", "retry_after": 60}
                )
            
            # Content length validation
            if request.method in ["POST", "PUT", "PATCH"]:
                content_length = request.headers.get("content-length")
                if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
                    return JSONResponse(
                        status_code=413,
                        content={"error": "Payload too large"}
                    )
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            
            # Log request
            processing_time = time.time() - start_time
            logger.info(f"{request.method} {request.url.path} - {response.status_code} - {processing_time:.3f}s")
            
            return response
            
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"}
            )
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        # Check for forwarded headers (when behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def check_rate_limit(self, client_ip: str) -> bool:
        """Check if client is within rate limit"""
        now = time.time()
        minute_ago = now - 60
        
        # Initialize or clean old requests
        if client_ip not in self.request_history:
            self.request_history[client_ip] = []
        
        # Remove old requests
        self.request_history[client_ip] = [
            req_time for req_time in self.request_history[client_ip]
            if req_time > minute_ago
        ]
        
        # Check rate limit
        if len(self.request_history[client_ip]) >= self.rate_limit:
            return False
        
        # Add current request
        self.request_history[client_ip].append(now)
        return True


class APIKeyAuth:
    """API key authentication"""
    
    def __init__(self):
        self.api_keys = self._load_api_keys()
    
    def _load_api_keys(self) -> Dict[str, Dict[str, Any]]:
        """Load API keys from configuration"""
        # In production, load from secure storage
        api_keys = {}
        
        # Default admin key from config
        if hasattr(Config, 'API_KEY') and Config.API_KEY:
            api_keys[Config.API_KEY] = {
                "name": "admin",
                "permissions": ["admin"],
                "created_at": datetime.now().isoformat()
            }
        
        return api_keys
    
    async def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Verify API key and return key info"""
        if api_key in self.api_keys:
            return self.api_keys[api_key]
        return None


class WebhookAuth:
    """Webhook signature verification"""
    
    @staticmethod
    def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
        """Verify webhook signature"""
        if not signature or not secret:
            return False
        
        try:
            # Extract signature from header (e.g., "sha256=...")
            if "=" in signature:
                algorithm, hex_signature = signature.split("=", 1)
            else:
                algorithm = "sha256"
                hex_signature = signature
            
            # Calculate expected signature
            if algorithm == "sha256":
                expected_signature = hmac.new(
                    secret.encode(),
                    payload,
                    hashlib.sha256
                ).hexdigest()
            else:
                logger.warning(f"Unsupported signature algorithm: {algorithm}")
                return False
            
            # Compare signatures
            return hmac.compare_digest(hex_signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Webhook signature verification error: {e}")
            return False


class JWTAuth:
    """JWT token authentication for advanced scenarios"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def create_token(self, user_id: str, permissions: list = None, expires_hours: int = 24) -> str:
        """Create JWT token"""
        payload = {
            "user_id": user_id,
            "permissions": permissions or [],
            "exp": datetime.utcnow() + timedelta(hours=expires_hours),
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None


# Security instances
security_middleware = SecurityMiddleware
api_key_auth = APIKeyAuth()
webhook_auth = WebhookAuth()
jwt_auth = JWTAuth(getattr(Config, 'SECRET_KEY', 'default-secret-key'))

# FastAPI dependencies
security_scheme = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    """FastAPI dependency for API key verification"""
    api_key = credentials.credentials
    key_info = await api_key_auth.verify_api_key(api_key)
    
    if not key_info:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return key_info

async def verify_admin_access(key_info: dict = Depends(verify_api_key)):
    """FastAPI dependency for admin access verification"""
    if "admin" not in key_info.get("permissions", []):
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    return key_info

async def verify_webhook_request(request: Request):
    """FastAPI dependency for webhook signature verification"""
    if not hasattr(Config, 'WEBHOOK_SECRET') or not Config.WEBHOOK_SECRET:
        # If no webhook secret configured, skip verification
        logger.warning("Webhook secret not configured, skipping signature verification")
        return True
    
    signature = request.headers.get("X-Signature-256") or request.headers.get("X-Hub-Signature-256")
    if not signature:
        raise HTTPException(
            status_code=401,
            detail="Missing webhook signature"
        )
    
    body = await request.body()
    if not webhook_auth.verify_webhook_signature(body, signature, Config.WEBHOOK_SECRET):
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook signature"
        )
    
    return True


class InputSanitizer:
    """Input sanitization utilities"""
    
    @staticmethod
    def sanitize_phone_number(phone: str) -> str:
        """Sanitize phone number input"""
        if not phone:
            return ""
        
        # Remove all non-digit characters except +
        sanitized = "".join(c for c in phone if c.isdigit() or c == "+")
        
        # Ensure it starts with + for international format
        if not sanitized.startswith("+"):
            sanitized = "+" + sanitized
        
        return sanitized
    
    @staticmethod
    def sanitize_message_content(content: str) -> str:
        """Sanitize message content"""
        if not content:
            return ""
        
        # Remove potential XSS characters
        dangerous_chars = ["<", ">", "&", '"', "'"]
        sanitized = content
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")
        
        # Limit length
        max_length = 4096
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None


# Sanitizer instance
input_sanitizer = InputSanitizer()


class SecurityLogger:
    """Security event logging"""
    
    @staticmethod
    def log_auth_attempt(success: bool, identifier: str, ip_address: str):
        """Log authentication attempt"""
        status = "SUCCESS" if success else "FAILED"
        logger.warning(f"AUTH_ATTEMPT {status} - ID: {identifier} - IP: {ip_address}")
    
    @staticmethod
    def log_rate_limit_exceeded(ip_address: str, endpoint: str):
        """Log rate limit exceeded"""
        logger.warning(f"RATE_LIMIT_EXCEEDED - IP: {ip_address} - Endpoint: {endpoint}")
    
    @staticmethod
    def log_suspicious_activity(description: str, ip_address: str, details: dict = None):
        """Log suspicious activity"""
        logger.warning(f"SUSPICIOUS_ACTIVITY - {description} - IP: {ip_address} - Details: {details}")
    
    @staticmethod
    def log_webhook_verification(success: bool, source_ip: str):
        """Log webhook verification attempt"""
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"WEBHOOK_VERIFICATION {status} - IP: {source_ip}")


# Security logger instance
security_logger = SecurityLogger()
