"""
Authentication API endpoints with shared libraries integration
"""

import sys
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

# Add libs to Python path
libs_path = os.path.join(os.path.dirname(__file__), '..', 'libs')
if not os.path.exists(libs_path):
    # Try alternative path for Docker environment
    libs_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs')
sys.path.append(libs_path)

from core.cache import cache
from core.database import get_db
from core.security import security
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from schemas.auth import (
    ChangePasswordRequest,
    EmailVerificationRequest,
    LoginRequest,
    LoginResponse,
    PasswordResetRequest,
    RegisterRequest,
    RegisterResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
)
from services.auth_service import AuthService
from services.user_service import UserService
from sqlalchemy.ext.asyncio import AsyncSession

# Import shared libraries
from libs.common.responses import success_response, error_response
from libs.common.validation import CommonValidators, validate_and_sanitize
from libs.monitoring.metrics import MetricsCollector
from infrastructure.logging import ServiceLogger
from api.errors import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    auth_error_response,
    validation_error_response
)

logger = ServiceLogger("auth-service")
metrics = MetricsCollector("auth-service")
security_scheme = HTTPBearer()

router = APIRouter()


@router.post("/register", response_model=RegisterResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user with enhanced security validation"""
    request_id = getattr(request, 'request_id', None)
    
    with metrics.time_operation("user_registration"):
        try:
            # Validate and sanitize input
            validator = CommonValidators.user_registration()
            request_dict = request.dict()
            is_valid, sanitized_data, validation_errors = validate_and_sanitize(request_dict, validator)
            
            if not is_valid:
                metrics.increment_counter("registration_validation_errors")
                logger.warning("Registration validation failed", extra={
                    "errors": validation_errors,
                    "request_id": request_id
                })
                return error_response(
                    "VALIDATION_ERROR",
                    "Registration validation failed",
                    status_code=422,
                    details=validation_errors,
                    request_id=request_id
                )
            
            logger.log_api_call("POST", "/auth/register", 200, 0, extra={"email": sanitized_data["email"]})
            
            auth_service = AuthService(db)
            user_service = UserService(db)

            # Check if user already exists
            existing_user = await user_service.get_user_by_email(sanitized_data["email"])
            if existing_user:
                metrics.increment_counter("registration_conflicts")
                raise UserAlreadyExistsError(sanitized_data["email"])

            # Create user with sanitized data
            user = await auth_service.register_user(
                email=sanitized_data["email"],
                password=sanitized_data["password"],
                first_name=sanitized_data["first_name"],
                last_name=sanitized_data["last_name"],
            )

            metrics.increment_counter("successful_registrations")
            logger.info("User registered successfully", extra={
                "user_id": str(user.id),
                "email": user.email,
                "request_id": request_id
            })

            return success_response(
                data=RegisterResponse(
                    message="Registration successful", 
                    user_id=str(user.id), 
                    email=user.email
                ),
                message="User registered successfully"
            )

        except UserAlreadyExistsError as e:
            return auth_error_response(e, request_id)
        except Exception as e:
            metrics.increment_counter("registration_errors")
            logger.error(f"Registration error: {e}", extra={"request_id": request_id})
            return error_response(
                "REGISTRATION_ERROR",
                "Registration failed",
                status_code=500,
                request_id=request_id
            )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest, http_request: Request, db: AsyncSession = Depends(get_db)
):
    """Authenticate user with enhanced security monitoring"""
    request_id = getattr(request, 'request_id', None)
    
    with metrics.time_operation("user_login"):
        try:
            # Validate and sanitize input
            validator = CommonValidators.user_login()
            request_dict = request.dict()
            is_valid, sanitized_data, validation_errors = validate_and_sanitize(request_dict, validator)
            
            if not is_valid:
                metrics.increment_counter("login_validation_errors")
                logger.warning("Login validation failed", extra={
                    "errors": validation_errors,
                    "request_id": request_id
                })
                return error_response(
                    "VALIDATION_ERROR",
                    "Login validation failed",
                    status_code=422,
                    details=validation_errors,
                    request_id=request_id
                )
            
            logger.log_api_call("POST", "/auth/login", 200, 0, extra={"email": sanitized_data["email"]})
            
            auth_service = AuthService(db)

            # Get client info
            ip_address = http_request.client.host
            user_agent = http_request.headers.get("user-agent", "")

            # Authenticate user with sanitized data
            result = await auth_service.authenticate_user(
                email=sanitized_data["email"],
                password=sanitized_data["password"],
                ip_address=ip_address,
                user_agent=user_agent,
            )

            if not result:
                metrics.increment_counter("failed_logins")
                
                # Log security event for failed login
                logger.warning("Failed login attempt", extra={
                    "email": sanitized_data["email"],
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "request_id": request_id
                })
                
                raise InvalidCredentialsError()

            user, session, tokens = result

            metrics.increment_counter("successful_logins")
            logger.info("User logged in successfully", extra={
                "user_id": str(user.id),
                "email": user.email,
                "ip_address": ip_address,
                "session_id": str(session.id),
                "request_id": request_id
            })

            return LoginResponse(
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                token_type="bearer",
                expires_in=tokens["expires_in"],
                user_id=str(user.id),
                email=user.email,
                session_id=str(session.id)
            )

        except InvalidCredentialsError as e:
            return auth_error_response(e, request_id)
        except Exception as e:
            metrics.increment_counter("login_errors")
            logger.error(f"Login error: {e}", extra={"request_id": request_id})
            return error_response(
                "LOGIN_ERROR",
                "Login failed",
                status_code=500,
                request_id=request_id
            )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    request: TokenRefreshRequest, 
    db: AsyncSession = Depends(get_db),
    http_request: Request = None
):
    """Refresh access token using refresh token"""
    request_id = str(uuid.uuid4())
    
    try:
        # Input validation for refresh token
        validation_result = CommonValidators.validate_and_sanitize({
            "refresh_token": request.refresh_token
        })
        
        if not validation_result.is_valid:
            logger.warning("Token refresh validation failed", extra={
                "errors": validation_result.errors,
                "request_id": request_id
            })
            return error_response(
                "VALIDATION_ERROR",
                "Token refresh validation failed",
                status_code=422,
                details=validation_result.errors,
                request_id=request_id
            )
        
        auth_service = AuthService(db)

        # Get client info for audit logging
        ip_address = http_request.client.host if http_request else "unknown"
        user_agent = http_request.headers.get("user-agent", "") if http_request else ""

        # Verify refresh token and get new tokens
        result = await auth_service.refresh_tokens(validation_result.cleaned_data["refresh_token"])

        if not result:
            logger.warning("Token refresh failed - invalid token", extra={
                "ip_address": ip_address,
                "user_agent": user_agent,
                "request_id": request_id
            })
            return error_response(
                "INVALID_REFRESH_TOKEN",
                "Invalid refresh token",
                status_code=401,
                request_id=request_id
            )

        tokens = result

        logger.info("Token refreshed successfully", extra={
            "ip_address": ip_address,
            "user_agent": user_agent,
            "request_id": request_id
        })

        return TokenRefreshResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token"),
            token_type="bearer",
            expires_in=tokens["expires_in"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}", extra={"request_id": request_id})
        return error_response(
            "TOKEN_REFRESH_ERROR",
            "Token refresh failed",
            status_code=500,
            request_id=request_id
        )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
    http_request: Request = None
):
    """Logout user and revoke session"""
    request_id = str(uuid.uuid4())
    
    try:
        # Input validation for credentials
        validation_result = CommonValidators.validate_and_sanitize({
            "token": credentials.credentials if credentials else None
        })
        
        if not validation_result.is_valid:
            logger.warning("Logout validation failed", extra={
                "errors": validation_result.errors,
                "request_id": request_id
            })
            return error_response(
                "VALIDATION_ERROR",
                "Logout validation failed",
                status_code=422,
                details=validation_result.errors,
                request_id=request_id
            )
        
        auth_service = AuthService(db)

        # Verify token and get user
        payload = security.verify_token(validation_result.cleaned_data["token"])
        if not payload:
            return error_response(
                "INVALID_TOKEN",
                "Invalid token",
                status_code=401,
                request_id=request_id
            )

        # Get client info for audit logging
        ip_address = http_request.client.host if http_request else "unknown"
        user_agent = http_request.headers.get("user-agent", "") if http_request else ""

        # Revoke session
        await auth_service.revoke_session(payload.get("session_id"))

        # Log successful logout
        logger.info("User logged out successfully", extra={
            "user_id": payload.get("sub"),
            "session_id": payload.get("session_id"),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "request_id": request_id
        })

        return success_response(
            data={"status": "logged_out"},
            message="Logged out successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {e}", extra={"request_id": request_id})
        return error_response(
            "LOGOUT_ERROR",
            "Logout failed",
            status_code=500,
            request_id=request_id
        )


@router.post("/verify-email")
async def verify_email(
    request: EmailVerificationRequest, db: AsyncSession = Depends(get_db)
):
    """Verify user email address"""
    try:
        auth_service = AuthService(db)

        success = await auth_service.verify_email(request.token)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token",
            )

        return {"message": "Email verified successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed",
        )


@router.post("/password-reset-request")
async def password_reset_request(
    request: PasswordResetRequest, db: AsyncSession = Depends(get_db)
):
    """Request password reset"""
    try:
        auth_service = AuthService(db)

        success = await auth_service.request_password_reset(request.email)

        # Always return success to prevent email enumeration
        return {"message": "If the email exists, a password reset link has been sent"}

    except Exception as e:
        logger.error(f"Password reset request error: {e}")
        # Still return success message
        return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/password-reset")
async def password_reset(
    request: ChangePasswordRequest, db: AsyncSession = Depends(get_db)
):
    """Reset password using token"""
    try:
        auth_service = AuthService(db)

        success = await auth_service.reset_password(
            token=request.token, new_password=request.new_password
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        return {"message": "Password reset successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed",
        )


@router.get("/me")
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Get current user information"""
    try:
        auth_service = AuthService(db)

        # Verify token and get user
        user = await auth_service.get_current_user(credentials.credentials)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        return {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "phone": user.phone,
            "department": user.department,
            "position": user.position,
            "status": user.status,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "email_verified": user.email_verified,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information",
        )
