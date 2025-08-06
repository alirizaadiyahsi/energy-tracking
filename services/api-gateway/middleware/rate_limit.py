"""
Rate limiting middleware
"""
import time
import logging
from typing import Dict
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using in-memory storage"""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients: Dict[str, Dict] = {}
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Clean up old entries
        self._cleanup_expired(current_time)
        
        # Check rate limit
        if not self._is_allowed(client_ip, current_time):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded"
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        client_data = self.clients.get(client_ip, {})
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.calls - len(client_data.get("requests", []))))
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.period))
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _cleanup_expired(self, current_time: float):
        """Remove expired entries"""
        expired_clients = []
        
        for client_ip, data in self.clients.items():
            # Filter out expired requests
            data["requests"] = [req_time for req_time in data.get("requests", []) 
                              if current_time - req_time < self.period]
            
            # Remove clients with no recent requests
            if not data["requests"]:
                expired_clients.append(client_ip)
        
        for client_ip in expired_clients:
            del self.clients[client_ip]
    
    def _is_allowed(self, client_ip: str, current_time: float) -> bool:
        """Check if client is allowed to make request"""
        if client_ip not in self.clients:
            self.clients[client_ip] = {"requests": []}
        
        client_data = self.clients[client_ip]
        
        # Filter recent requests
        client_data["requests"] = [req_time for req_time in client_data["requests"] 
                                  if current_time - req_time < self.period]
        
        # Check if under limit
        if len(client_data["requests"]) < self.calls:
            client_data["requests"].append(current_time)
            return True
        
        return False
