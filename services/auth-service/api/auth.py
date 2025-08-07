"""
Authentication API endpoints
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

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

logger = logging.getLogger(__name__)
security_scheme = HTTPBearer()

router = APIRouter()


@router.post("/register", response_model=RegisterResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user"""
    try:
        auth_service = AuthService(db)
        user_service = UserService(db)

        # Check if user already exists
        existing_user = await user_service.get_user_by_email(request.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )

        # Create user
        user = await auth_service.register_user(
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name,
        )

        return RegisterResponse(
            message="Registration successful", user_id=str(user.id), email=user.email
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest, http_request: Request, db: AsyncSession = Depends(get_db)
):
    """Authenticate user and create session"""
    try:
        auth_service = AuthService(db)

        # Get client info
        ip_address = http_request.client.host
        user_agent = http_request.headers.get("user-agent", "")

        # Authenticate user
        result = await auth_service.authenticate_user(
            email=request.email,
            password=request.password,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        user, session, tokens = result

        return LoginResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type="bearer",
            expires_in=tokens["expires_in"],
            user_id=str(user.id),
            email=user.email,
            session_id=str(session.id),  # Use session.id instead of session.session_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed"
        )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    request: TokenRefreshRequest, db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    try:
        auth_service = AuthService(db)

        # Verify refresh token and get new tokens
        result = await auth_service.refresh_tokens(request.refresh_token)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        tokens = result

        return TokenRefreshResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token"),
            token_type="bearer",
            expires_in=tokens["expires_in"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed",
        )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Logout user and revoke session"""
    try:
        auth_service = AuthService(db)

        # Verify token and get user
        payload = security.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        # Revoke session
        await auth_service.revoke_session(payload.get("session_id"))

        return {"message": "Logged out successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Logout failed"
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
