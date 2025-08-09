"""
Advanced security middleware for microservices
Includes rate limiting, request validation, security headers, and audit logging
"""

import time
import json
import hashlib
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
import redis.asyncio as redis
from libs.common.cache import CacheManager
from infrastructure.logging import ServiceLogger

logger = ServiceLogger("security-middleware")

class SecurityConfig:
    """Security configuration settings"""
    
    # Rate limiting settings
    RATE_LIMIT_REQUESTS_PER_MINUTE = 100
    RATE_LIMIT_REQUESTS_PER_HOUR = 1000
    RATE_LIMIT_BURST_SIZE = 10
    
    # Security headers
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
    }
    
    # Request validation
    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_HEADER_SIZE = 8192  # 8KB
    BLOCKED_USER_AGENTS = ["curl", "wget", "python-requests"]
    
    # Audit logging
    AUDIT_SENSITIVE_ENDPOINTS = ["/auth/login", "/auth/register", "/users", "/admin"]
    AUDIT_LOG_REQUESTS = True
    AUDIT_LOG_RESPONSES = False

class RateLimiter:
    """Redis-based rate limiter with sliding window"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.logger = ServiceLogger("rate-limiter")
    
    async def is_allowed(self, 
                        identifier: str, 
                        limit_per_minute: int = 60,
                        limit_per_hour: int = 1000) -> tuple[bool, Dict]:
        """
        Check if request is allowed based on rate limits
        Returns (is_allowed, info_dict)
        """
        now = datetime.utcnow()
        minute_key = f"rate_limit:minute:{identifier}:{now.strftime('%Y%m%d%H%M')}"
        hour_key = f"rate_limit:hour:{identifier}:{now.strftime('%Y%m%d%H')}"
        
        try:
            # Get current counts
            minute_count = await self.cache.get(minute_key) or 0
            hour_count = await self.cache.get(hour_key) or 0
            
            minute_count = int(minute_count)
            hour_count = int(hour_count)
            
            # Check limits
            if minute_count >= limit_per_minute:
                self.logger.warning(f"Rate limit exceeded (minute): {identifier}", extra={
                    "identifier": identifier,
                    "minute_count": minute_count,
                    "limit": limit_per_minute
                })
                return False, {
                    "limit_type": "minute",
                    "current": minute_count,
                    "limit": limit_per_minute,
                    "reset_time": (now + timedelta(minutes=1)).isoformat()
                }
            
            if hour_count >= limit_per_hour:
                self.logger.warning(f"Rate limit exceeded (hour): {identifier}", extra={
                    "identifier": identifier,
                    "hour_count": hour_count,
                    "limit": limit_per_hour
                })
                return False, {
                    "limit_type": "hour",
                    "current": hour_count,
                    "limit": limit_per_hour,
                    "reset_time": (now + timedelta(hours=1)).isoformat()
                }
            
            # Increment counters
            await self.cache.set(minute_key, minute_count + 1, expire=60)
            await self.cache.set(hour_key, hour_count + 1, expire=3600)
            
            return True, {
                "minute_remaining": limit_per_minute - minute_count - 1,
                "hour_remaining": limit_per_hour - hour_count - 1
            }
            
        except Exception as e:
            self.logger.error(f"Rate limiting error: {e}")
            # Allow request if rate limiter fails
            return True, {"error": "rate_limiter_unavailable"}

class SecurityValidator:
    """Request security validation"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.logger = ServiceLogger("security-validator")
    
    async def validate_request(self, request: Request) -> Optional[HTTPException]:
        """Validate request security"""
        
        # Allow health checks to bypass security (for Docker health checks)
        if request.url.path in ["/health", "/health/"]:
            return None
        
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.config.MAX_REQUEST_SIZE:
            self.logger.warning(f"Request too large: {content_length} bytes", extra={
                "ip": request.client.host,
                "path": request.url.path
            })
            return HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Request entity too large"
            )
        
        # Check header size
        headers_size = sum(len(k) + len(v) for k, v in request.headers.items())
        if headers_size > self.config.MAX_HEADER_SIZE:
            self.logger.warning(f"Headers too large: {headers_size} bytes", extra={
                "ip": request.client.host,
                "path": request.url.path
            })
            return HTTPException(
                status_code=status.HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE,
                detail="Request headers too large"
            )
        
        # Check user agent
        user_agent = request.headers.get("user-agent", "").lower()
        for blocked_agent in self.config.BLOCKED_USER_AGENTS:
            if blocked_agent in user_agent:
                self.logger.warning(f"Blocked user agent: {user_agent}", extra={
                    "ip": request.client.host,
                    "path": request.url.path,
                    "user_agent": user_agent
                })
                return HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User agent not allowed"
                )
        
        # Check for common attack patterns
        suspicious_patterns = [
            "script>", "<iframe", "javascript:", "vbscript:",
            "union select", "drop table", "insert into",
            "../", "..\\", "/etc/passwd", "\\x"
        ]
        
        # Check URL path
        path_lower = request.url.path.lower()
        for pattern in suspicious_patterns:
            if pattern in path_lower:
                self.logger.warning(f"Suspicious path pattern: {pattern}", extra={
                    "ip": request.client.host,
                    "path": request.url.path,
                    "pattern": pattern
                })
                return HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Malicious request detected"
                )
        
        # Check query parameters
        for param_value in request.query_params.values():
            param_lower = param_value.lower()
            for pattern in suspicious_patterns:
                if pattern in param_lower:
                    self.logger.warning(f"Suspicious query parameter: {pattern}", extra={
                        "ip": request.client.host,
                        "path": request.url.path,
                        "pattern": pattern
                    })
                    return HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Malicious request detected"
                    )
        
        return None

class AuditLogger:
    """Security audit logging"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.logger = ServiceLogger("audit-logger")
    
    async def log_request(self, request: Request, user_id: Optional[str] = None):
        """Log security-relevant requests"""
        
        if not self.config.AUDIT_LOG_REQUESTS:
            return
        
        # Check if endpoint should be audited
        path = request.url.path
        should_audit = any(sensitive in path for sensitive in self.config.AUDIT_SENSITIVE_ENDPOINTS)
        
        if should_audit:
            audit_data = {
                "event_type": "api_request",
                "timestamp": datetime.utcnow().isoformat(),
                "ip_address": request.client.host,
                "user_agent": request.headers.get("user-agent"),
                "method": request.method,
                "path": path,
                "query_params": dict(request.query_params),
                "user_id": user_id,
                "headers": {
                    "authorization": "***" if "authorization" in request.headers else None,
                    "content-type": request.headers.get("content-type"),
                    "origin": request.headers.get("origin"),
                    "referer": request.headers.get("referer")
                }
            }
            
            self.logger.info("Security audit log", extra=audit_data)
    
    async def log_response(self, request: Request, response: Response, 
                          processing_time: float, user_id: Optional[str] = None):
        """Log security-relevant responses"""
        
        if not self.config.AUDIT_LOG_RESPONSES:
            return
        
        # Log failed authentication attempts
        if (request.url.path in ["/auth/login", "/auth/register"] and 
            response.status_code >= 400):
            
            audit_data = {
                "event_type": "auth_failure",
                "timestamp": datetime.utcnow().isoformat(),
                "ip_address": request.client.host,
                "user_agent": request.headers.get("user-agent"),
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "processing_time": processing_time,
                "user_id": user_id
            }
            
            self.logger.warning("Authentication failure", extra=audit_data)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware"""
    
    def __init__(self, app, cache_manager: CacheManager, config: Optional[SecurityConfig] = None):
        super().__init__(app)
        self.config = config or SecurityConfig()
        self.rate_limiter = RateLimiter(cache_manager)
        self.validator = SecurityValidator(self.config)
        self.audit_logger = AuditLogger(self.config)
        self.logger = ServiceLogger("security-middleware")
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        
        try:
            # Get client identifier (IP + User-Agent hash)
            client_ip = request.client.host
            user_agent = request.headers.get("user-agent", "")
            identifier = f"{client_ip}:{hashlib.md5(user_agent.encode()).hexdigest()[:8]}"
            
            # Rate limiting
            is_allowed, rate_info = await self.rate_limiter.is_allowed(
                identifier,
                self.config.RATE_LIMIT_REQUESTS_PER_MINUTE,
                self.config.RATE_LIMIT_REQUESTS_PER_HOUR
            )
            
            if not is_allowed:
                return Response(
                    content=json.dumps({
                        "error": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests",
                        "details": rate_info
                    }),
                    status_code=429,
                    headers={"Content-Type": "application/json"}
                )
            
            # Request validation
            validation_error = await self.validator.validate_request(request)
            if validation_error:
                return Response(
                    content=json.dumps({
                        "error": "INVALID_REQUEST",
                        "message": validation_error.detail
                    }),
                    status_code=validation_error.status_code,
                    headers={"Content-Type": "application/json"}
                )
            
            # Audit logging (before request processing)
            await self.audit_logger.log_request(request)
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            for header, value in self.config.SECURITY_HEADERS.items():
                response.headers[header] = value
            
            # Add rate limit headers
            if "minute_remaining" in rate_info:
                response.headers["X-RateLimit-Remaining-Minute"] = str(rate_info["minute_remaining"])
                response.headers["X-RateLimit-Remaining-Hour"] = str(rate_info["hour_remaining"])
            
            # Audit logging (after request processing)
            processing_time = time.time() - start_time
            await self.audit_logger.log_response(request, response, processing_time)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Security middleware error: {e}", extra={
                "ip": request.client.host,
                "path": request.url.path,
                "error": str(e)
            })
            
            # Return generic error response
            return Response(
                content=json.dumps({
                    "error": "INTERNAL_SERVER_ERROR",
                    "message": "An error occurred processing your request"
                }),
                status_code=500,
                headers={"Content-Type": "application/json"}
            )

# Helper functions for easy integration
def add_security_middleware(app, cache_manager: CacheManager, config: Optional[SecurityConfig] = None):
    """Add security middleware to FastAPI app"""
    app.add_middleware(SecurityMiddleware, cache_manager=cache_manager, config=config)

def create_security_config(
    rate_limit_per_minute: int = 100,
    rate_limit_per_hour: int = 1000,
    max_request_size: int = 10 * 1024 * 1024,
    audit_endpoints: List[str] = None
) -> SecurityConfig:
    """Create custom security configuration"""
    config = SecurityConfig()
    config.RATE_LIMIT_REQUESTS_PER_MINUTE = rate_limit_per_minute
    config.RATE_LIMIT_REQUESTS_PER_HOUR = rate_limit_per_hour
    config.MAX_REQUEST_SIZE = max_request_size
    
    if audit_endpoints:
        config.AUDIT_SENSITIVE_ENDPOINTS = audit_endpoints
    
    return config
