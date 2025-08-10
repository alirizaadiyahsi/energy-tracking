"""
Authentication service - handles user authentication, session management, and security
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

from core.cache import cache
from core.config import settings
from core.security import security
from models.session import Session
from models.user import User
from services.user_service import UserService
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service class"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)

    async def register_user(
        self,
        email: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
    ) -> User:
        """Register a new user"""
        try:
            # Hash password
            hashed_password = security.hash_password(password)

            # Create user
            user = User(
                email=email.lower(),
                username=username,
                hashed_password=hashed_password,
                full_name=f"{first_name or ''} {last_name or ''}".strip() or None,
                is_active=True,
                email_verified=False,  # Require email verification
            )

            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

            # Generate email verification token
            verification_token = security.create_email_verification_token(user.email)
            user.email_verification_token = verification_token
            user.email_verification_expires = datetime.now(timezone.utc) + timedelta(
                hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS
            )

            await self.db.commit()

            logger.info(f"User registered: {user.email}")
            return user

        except Exception as e:
            await self.db.rollback()
            logger.error(f"User registration failed: {e}")
            raise

    async def authenticate_user(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        remember_me: bool = False,
    ) -> Optional[Tuple[User, Session, Dict[str, Any]]]:
        """Authenticate user and create session"""
        try:
            # Get user by email
            user = await self.user_service.get_user_by_email(email.lower())
            if not user:
                logger.warning(f"Authentication failed: User not found {email}")
                return None

            # Check if user is active
            if not user.is_active:
                logger.warning(f"Authentication failed: Inactive user {email}")
                return None

            # Check if user is locked (using locked_until field)
            if user.locked_until and user.locked_until > datetime.now():
                logger.warning(f"Authentication failed: Locked user {email}")
                return None

            # Verify password
            if not security.verify_password(password, user.hashed_password):
                # Increment failed login attempts
                user.failed_login_attempts += 1

                # Lock user if too many failed attempts
                if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                    user.locked_until = datetime.now() + timedelta(
                        minutes=settings.LOCKOUT_DURATION_MINUTES
                    )
                    logger.warning(f"User locked due to failed attempts: {email}")

                await self.db.commit()
                logger.warning(f"Authentication failed: Invalid password {email}")
                return None

            # Reset failed login attempts on successful login
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login = datetime.now()  # Use timezone-naive datetime

            # Create session
            session = await self._create_session(
                user=user, ip_address=ip_address, user_agent=user_agent, remember_me=remember_me
            )

            # Generate tokens
            tokens = await self._generate_tokens(user, session, remember_me)

            await self.db.commit()

            logger.info(f"User authenticated: {email}")
            return user, session, tokens

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Authentication error: {e}")
            return None

    async def refresh_tokens(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh access token using refresh token"""
        try:
            # Verify refresh token
            payload = security.verify_token(refresh_token)
            if not payload or payload.get("type") != "refresh":
                return None

            # Get session
            session_id = payload.get("session_id")
            if not session_id:
                return None

            session = await self._get_session_by_id(session_id)
            if not session or not session.is_valid:
                return None

            # Get user
            user = await self.user_service.get_user_by_id(session.user_id)
            if not user or not user.is_active:
                return None

            # Generate new tokens using the session's remember_me preference
            tokens = await self._generate_tokens(user, session, session.remember_me)

            # Update session
            session.last_activity = datetime.now(timezone.utc)
            session.access_token = tokens["access_token"]
            if tokens.get("refresh_token"):
                session.refresh_token = tokens["refresh_token"]

            await self.db.commit()

            logger.info(f"Tokens refreshed for user: {user.email}")
            return tokens

        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return None

    async def get_current_user(self, token: str) -> Optional[User]:
        """Get current user from token"""
        try:
            # Verify token
            payload = security.verify_token(token)
            if not payload or payload.get("type") != "access":
                return None

            # Get user
            user_id = payload.get("user_id")
            if not user_id:
                return None

            user = await self.user_service.get_user_by_id(user_id)
            if not user or not user.is_active:
                return None

            # Verify session is still valid
            session_id = payload.get("session_id")
            if session_id:
                session = await self._get_session_by_id(session_id)
                if (
                    not session
                    or session.revoked
                    or session.expires_at < datetime.now()
                ):
                    return None

                # Update last activity (assuming this field exists or we skip it)
                # session.last_activity = datetime.now()
                # await self.db.commit()

            return user

        except Exception as e:
            logger.error(f"Get current user error: {e}")
            return None

    async def verify_email(self, token: str) -> bool:
        """Verify user email using token"""
        try:
            # Verify token
            payload = security.verify_token(token)
            if not payload or payload.get("type") != "email_verification":
                return False

            email = payload.get("email")
            if not email:
                return False

            # Get user
            user = await self.user_service.get_user_by_email(email)
            if not user:
                return False

            # Update user verification status
            user.is_verified = True
            user.email_verification_token = None
            user.email_verification_expires = None

            await self.db.commit()

            logger.info(f"Email verified for user: {email}")
            return True

        except Exception as e:
            logger.error(f"Email verification error: {e}")
            return False

    async def request_password_reset(self, email: str) -> bool:
        """Request password reset"""
        try:
            user = await self.user_service.get_user_by_email(email.lower())
            if not user or not user.is_active:
                # Return True to prevent email enumeration
                return True

            # Generate password reset token
            reset_token = security.create_password_reset_token(user.email)
            user.password_reset_token = reset_token
            user.password_reset_expires = datetime.now(timezone.utc) + timedelta(
                hours=settings.PASSWORD_RESET_EXPIRE_HOURS
            )

            await self.db.commit()

            # TODO: Send email with reset token
            logger.info(f"Password reset requested for user: {email}")
            return True

        except Exception as e:
            logger.error(f"Password reset request error: {e}")
            return True  # Return True to prevent email enumeration

    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using token"""
        try:
            # Verify token
            payload = security.verify_token(token)
            if not payload or payload.get("type") != "password_reset":
                return False

            email = payload.get("email")
            if not email:
                return False

            # Get user
            user = await self.user_service.get_user_by_email(email)
            if not user:
                return False

            # Hash new password
            password_hash = security.hash_password(new_password)

            # Update user password
            user.password_hash = password_hash
            user.password_reset_token = None
            user.password_reset_expires = None
            user.password_changed_at = datetime.now(timezone.utc)
            user.failed_login_attempts = 0
            user.locked_until = None

            # Revoke all existing sessions
            await self._revoke_user_sessions(user.id)

            await self.db.commit()

            logger.info(f"Password reset for user: {email}")
            return True

        except Exception as e:
            logger.error(f"Password reset error: {e}")
            return False

    async def revoke_session(self, session_id: str) -> bool:
        """Revoke a specific session"""
        try:
            session = await self._get_session_by_id(session_id)
            if not session:
                return False

            session.revoke()
            await self.db.commit()

            # Remove from cache
            await cache.delete(f"session:{session_id}")

            logger.info(f"Session revoked: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Session revocation error: {e}")
            return False

    async def _create_session(
        self,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        remember_me: bool = False,
    ) -> Session:
        """Create a new user session"""
        from datetime import timedelta

        # Generate session token
        session_token = security.generate_session_id()

        # Calculate expiration based on remember_me setting
        if remember_me:
            # Long-lived session for "remember me"
            expires_at = datetime.now() + timedelta(days=settings.SESSION_REMEMBER_ME_EXPIRE_DAYS)
        else:
            # Standard session - 24 hours (from settings)
            expires_at = datetime.now() + timedelta(hours=settings.SESSION_EXPIRE_HOURS)

        session = Session(
            user_id=user.id,
            token=session_token,
            device=(
                user_agent[:100] if user_agent else None
            ),  # Truncate to fit field size
            location=ip_address,
            remember_me=remember_me,
            expires_at=expires_at,
        )

        self.db.add(session)
        await self.db.flush()  # Get the ID

        return session

    async def _generate_tokens(self, user: User, session: Session, remember_me: bool = False) -> Dict[str, Any]:
        """Generate JWT tokens for user session"""
        token_data = {
            "user_id": str(user.id),
            "email": user.email,
            "session_id": str(
                session.id
            ),  # Use session.id instead of session.session_id
        }

        # Create tokens with different expiration times based on remember_me
        if remember_me:
            # Longer access token for remember me
            access_token = security.create_access_token(
                token_data, 
                expires_delta=timedelta(days=settings.JWT_REMEMBER_ME_ACCESS_TOKEN_EXPIRE_DAYS)
            )
            # Longer refresh token  
            refresh_token = security.create_refresh_token(
                token_data, 
                expires_delta=timedelta(days=settings.JWT_REMEMBER_ME_REFRESH_TOKEN_EXPIRE_DAYS)
            )
            expires_in = settings.JWT_REMEMBER_ME_ACCESS_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # days to seconds
        else:
            # Standard tokens
            access_token = security.create_access_token(token_data)
            refresh_token = security.create_refresh_token(token_data)
            expires_in = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": expires_in,
        }

    async def _get_session_by_id(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        try:
            # Try cache first
            cached_session = await cache.get(f"session:{session_id}")
            if cached_session:
                # TODO: Deserialize cached session
                pass

            # Get from database
            result = await self.db.execute(
                select(Session).where(Session.id == session_id)
            )
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Get session error: {e}")
            return None

    async def _revoke_user_sessions(self, user_id: str):
        """Revoke all sessions for a user"""
        try:
            await self.db.execute(
                update(Session)
                .where(Session.user_id == user_id)
                .where(Session.is_active == True)
                .values(
                    is_active=False,
                    is_revoked=True,
                    revoked_at=datetime.now(timezone.utc),
                )
            )

            # TODO: Clear cached sessions

        except Exception as e:
            logger.error(f"Revoke user sessions error: {e}")
