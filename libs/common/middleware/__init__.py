"""
Common middleware for all microservices
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..exceptions import RateLimitExceededError


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request
        start_time = time.time()
        
        # Add request ID to headers
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Add headers to response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


class CORSMiddleware(BaseHTTPMiddleware):
    """Enhanced CORS middleware with configurable origins"""
    
    def __init__(self, app, allowed_origins: list = None, allow_credentials: bool = True):
        super().__init__(app)
        self.allowed_origins = allowed_origins or ["*"]
        self.allow_credentials = allow_credentials
    
    async def dispatch(self, request: Request, call_next: Callable):
        origin = request.headers.get("origin")
        
        response = await call_next(request)
        
        # Set CORS headers
        if "*" in self.allowed_origins or origin in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin or "*"
        
        if self.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Request-ID"
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


# Helper functions for middleware setup
def add_cors_middleware(app, allowed_origins: list = None):
    """Add CORS middleware to FastAPI app"""
    from fastapi.middleware.cors import CORSMiddleware
    
    if allowed_origins is None:
        allowed_origins = ["*"]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def add_logging_middleware(app):
    """Add request logging middleware to FastAPI app"""
    app.add_middleware(RequestLoggingMiddleware)


def add_security_headers_middleware(app):
    """Add security headers middleware to FastAPI app"""
    app.add_middleware(SecurityHeadersMiddleware)
