"""
Enhanced error handling for auth service using shared libraries
"""

import sys
import os

# Add libs to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs'))

from libs.common.exceptions import (
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    ConflictError,
    RateLimitError
)
from libs.common.responses import error_response
from infrastructure.logging import ServiceLogger

logger = ServiceLogger("auth-service")

# Auth-specific exceptions
class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid"""
    def __init__(self, message: str = "Invalid username or password"):
        super().__init__(message)

class AccountLockedError(AuthenticationError):
    """Raised when account is locked due to too many failed attempts"""
    def __init__(self, lockout_time: int):
        super().__init__(f"Account locked. Try again in {lockout_time} minutes")

class TokenExpiredError(AuthenticationError):
    """Raised when JWT token has expired"""
    def __init__(self, message: str = "Token has expired"):
        super().__init__(message)

class InsufficientPermissionsError(AuthorizationError):
    """Raised when user lacks required permissions"""
    def __init__(self, required_permission: str):
        super().__init__(f"Insufficient permissions. Required: {required_permission}")

class UserAlreadyExistsError(ConflictError):
    """Raised when trying to create a user that already exists"""
    def __init__(self, identifier: str):
        super().__init__(f"User already exists: {identifier}")

class RoleNotFoundError(ResourceNotFoundError):
    """Raised when a role is not found"""
    def __init__(self, role_id: str):
        super().__init__("Role", role_id)

class PermissionNotFoundError(ResourceNotFoundError):
    """Raised when a permission is not found"""
    def __init__(self, permission_id: str):
        super().__init__("Permission", permission_id)

# Helper functions for common error responses
def auth_error_response(error: Exception, request_id: str = None):
    """Generate standardized authentication error response"""
    logger.error(f"Authentication error: {str(error)}", extra={"request_id": request_id})
    
    if isinstance(error, InvalidCredentialsError):
        return error_response(
            "INVALID_CREDENTIALS",
            str(error),
            status_code=401,
            request_id=request_id
        )
    elif isinstance(error, AccountLockedError):
        return error_response(
            "ACCOUNT_LOCKED",
            str(error),
            status_code=423,
            request_id=request_id
        )
    elif isinstance(error, TokenExpiredError):
        return error_response(
            "TOKEN_EXPIRED",
            str(error),
            status_code=401,
            request_id=request_id
        )
    else:
        return error_response(
            "AUTHENTICATION_ERROR",
            "Authentication failed",
            status_code=401,
            request_id=request_id
        )

def validation_error_response(error: ValidationError, request_id: str = None):
    """Generate standardized validation error response"""
    logger.warning(f"Validation error: {str(error)}", extra={"request_id": request_id})
    
    return error_response(
        "VALIDATION_ERROR",
        str(error),
        status_code=422,
        details=error.details,
        request_id=request_id
    )

def authorization_error_response(error: AuthorizationError, request_id: str = None):
    """Generate standardized authorization error response"""
    logger.warning(f"Authorization error: {str(error)}", extra={"request_id": request_id})
    
    return error_response(
        "AUTHORIZATION_ERROR",
        str(error),
        status_code=403,
        request_id=request_id
    )
