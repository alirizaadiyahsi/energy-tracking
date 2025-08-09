"""
Common exception classes for all microservices
"""

from typing import Any, Dict, Optional


class BaseServiceException(Exception):
    """Base exception for all service-specific exceptions"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "UNKNOWN_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(BaseServiceException):
    """Raised when data validation fails"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            status_code=400
        )


class AuthenticationError(BaseServiceException):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401
        )


class AuthorizationError(BaseServiceException):
    """Raised when authorization fails"""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403
        )


class ResourceNotFoundError(BaseServiceException):
    """Raised when a requested resource is not found"""
    
    def __init__(self, resource: str, identifier: str = ""):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            status_code=404
        )


class ResourceConflictError(BaseServiceException):
    """Raised when a resource conflict occurs"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="RESOURCE_CONFLICT",
            details=details,
            status_code=409
        )


class ExternalServiceError(BaseServiceException):
    """Raised when an external service call fails"""
    
    def __init__(self, service: str, message: str = "External service error"):
        super().__init__(
            message=f"{service}: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=502
        )


class RateLimitExceededError(BaseServiceException):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, limit: int, window: str):
        super().__init__(
            message=f"Rate limit exceeded: {limit} requests per {window}",
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429
        )


# Alias for backward compatibility
ConflictError = ResourceConflictError
RateLimitError = RateLimitExceededError


def setup_exception_handlers(app):
    """Setup exception handlers for FastAPI app"""
    from fastapi import HTTPException
    from fastapi.responses import JSONResponse
    from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
    import logging
    
    logger = logging.getLogger(__name__)
    
    @app.exception_handler(BaseServiceException)
    async def service_exception_handler(request, exc: BaseServiceException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details
                },
                "request_id": getattr(request.state, 'request_id', None)
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "HTTP_ERROR",
                    "message": exc.detail,
                },
                "request_id": getattr(request.state, 'request_id', None)
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Internal server error",
                },
                "request_id": getattr(request.state, 'request_id', None)
            }
        )
