"""
Response formatting utilities for consistent API responses
"""

from typing import Any, Dict, Optional, List, Union
from datetime import datetime
from fastapi import status
from fastapi.responses import JSONResponse
import uuid


class APIResponse:
    """Standardized API response formatter"""
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
        status_code: int = status.HTTP_200_OK,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create success response"""
        return {
            "success": True,
            "data": data,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id or str(uuid.uuid4())
        }
    
    @staticmethod
    def error(
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create error response"""
        return {
            "success": False,
            "error": {
                "code": error_code,
                "message": message,
                "details": details or {}
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id or str(uuid.uuid4())
        }
    
    @staticmethod
    def paginated(
        data: List[Any],
        page: int,
        limit: int,
        total: int,
        message: str = "Success",
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create paginated response"""
        total_pages = (total + limit - 1) // limit
        
        return {
            "success": True,
            "data": data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            },
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id or str(uuid.uuid4())
        }
    
    @staticmethod
    def created(
        data: Any,
        message: str = "Resource created successfully",
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create 201 Created response"""
        return APIResponse.success(
            data=data,
            message=message,
            status_code=status.HTTP_201_CREATED,
            request_id=request_id
        )
    
    @staticmethod
    def no_content(
        message: str = "Operation completed successfully",
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create 204 No Content response"""
        return {
            "success": True,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id or str(uuid.uuid4())
        }


def create_json_response(
    content: Dict[str, Any],
    status_code: int = status.HTTP_200_OK,
    headers: Optional[Dict[str, str]] = None
) -> JSONResponse:
    """Create FastAPI JSONResponse with proper headers"""
    response_headers = {
        "Content-Type": "application/json",
        "X-Content-Type-Options": "nosniff"
    }
    
    if headers:
        response_headers.update(headers)
    
    return JSONResponse(
        content=content,
        status_code=status_code,
        headers=response_headers
    )


class ErrorResponse:
    """Predefined error responses"""
    
    @staticmethod
    def validation_error(message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validation error response"""
        return APIResponse.error(
            error_code="VALIDATION_ERROR",
            message=message,
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    @staticmethod
    def unauthorized(message: str = "Authentication required") -> Dict[str, Any]:
        """Unauthorized error response"""
        return APIResponse.error(
            error_code="UNAUTHORIZED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    @staticmethod
    def forbidden(message: str = "Insufficient permissions") -> Dict[str, Any]:
        """Forbidden error response"""
        return APIResponse.error(
            error_code="FORBIDDEN",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    @staticmethod
    def not_found(resource: str, identifier: str = "") -> Dict[str, Any]:
        """Not found error response"""
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        
        return APIResponse.error(
            error_code="NOT_FOUND",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    @staticmethod
    def conflict(message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Conflict error response"""
        return APIResponse.error(
            error_code="CONFLICT",
            message=message,
            details=details,
            status_code=status.HTTP_409_CONFLICT
        )
    
    @staticmethod
    def rate_limit_exceeded(limit: int, window: str) -> Dict[str, Any]:
        """Rate limit exceeded error response"""
        return APIResponse.error(
            error_code="RATE_LIMIT_EXCEEDED",
            message=f"Rate limit exceeded: {limit} requests per {window}",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )
    
    @staticmethod
    def internal_server_error(message: str = "Internal server error") -> Dict[str, Any]:
        """Internal server error response"""
        return APIResponse.error(
            error_code="INTERNAL_SERVER_ERROR",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    @staticmethod
    def service_unavailable(message: str = "Service temporarily unavailable") -> Dict[str, Any]:
        """Service unavailable error response"""
        return APIResponse.error(
            error_code="SERVICE_UNAVAILABLE",
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class ResponseHelper:
    """Helper class for creating common responses"""
    
    @staticmethod
    def health_response(status: str, checks: Dict[str, Any], service_name: str) -> Dict[str, Any]:
        """Create health check response"""
        return {
            "service": service_name,
            "status": status,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "checks": checks
        }
    
    @staticmethod
    def metrics_response(metrics: Dict[str, Any], service_name: str) -> Dict[str, Any]:
        """Create metrics response"""
        return {
            "service": service_name,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    @staticmethod
    def version_response(version: str, service_name: str, build_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create version response"""
        response = {
            "service": service_name,
            "version": version,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if build_info:
            response["build"] = build_info
        
        return response


# Convenience functions for backward compatibility
def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = status.HTTP_200_OK,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create success response - convenience function"""
    return APIResponse.success(data, message, status_code, request_id)


def error_response(
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create error response - convenience function"""
    return APIResponse.error(error_code, message, details, status_code, request_id)
