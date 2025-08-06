"""
User service - handles user CRUD operations and user management
"""
import logging
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from models.user import User
from core.cache import cache

logger = logging.getLogger(__name__)

class UserService:
    """User management service class"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Get user by ID error: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            result = await self.db.execute(
                select(User).where(User.email == email.lower())
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Get user by email error: {e}")
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            result = await self.db.execute(
                select(User).where(User.username == username)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Get user by username error: {e}")
            return None
    
    async def create_user(
        self,
        email: str,
        password_hash: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
        is_active: bool = True,
        is_verified: bool = False,
        is_superuser: bool = False
    ) -> User:
        """Create a new user"""
        try:
            user = User(
                email=email.lower(),
                username=username,
                password_hash=password_hash,
                first_name=first_name,
                last_name=last_name,
                is_active=is_active,
                is_verified=is_verified,
                is_superuser=is_superuser
            )
            
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            
            logger.info(f"User created: {user.email}")
            return user
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Create user error: {e}")
            raise
    
    async def update_user(
        self,
        user_id: str,
        **kwargs
    ) -> Optional[User]:
        """Update user information"""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return None
            
            # Update allowed fields
            allowed_fields = [
                'email', 'username', 'first_name', 'last_name', 
                'phone_number', 'is_active', 'is_verified', 'is_superuser'
            ]
            
            for field, value in kwargs.items():
                if field in allowed_fields and hasattr(user, field):
                    setattr(user, field, value)
            
            await self.db.commit()
            await self.db.refresh(user)
            
            logger.info(f"User updated: {user.email}")
            return user
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Update user error: {e}")
            return None
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user (soft delete by setting is_active to False)"""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return False
            
            user.is_active = False
            await self.db.commit()
            
            logger.info(f"User deleted: {user.email}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Delete user error: {e}")
            return False
    
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """List users with pagination"""
        try:
            query = select(User)
            
            if is_active is not None:
                query = query.where(User.is_active == is_active)
            
            query = query.offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"List users error: {e}")
            return []
    
    async def count_users(self, is_active: Optional[bool] = None) -> int:
        """Count users"""
        try:
            query = select(User)
            
            if is_active is not None:
                query = query.where(User.is_active == is_active)
            
            result = await self.db.execute(query)
            return len(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Count users error: {e}")
            return 0
    
    async def activate_user(self, user_id: str) -> bool:
        """Activate user account"""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return False
            
            user.is_active = True
            await self.db.commit()
            
            logger.info(f"User activated: {user.email}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Activate user error: {e}")
            return False
    
    async def deactivate_user(self, user_id: str) -> bool:
        """Deactivate user account"""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return False
            
            user.is_active = False
            await self.db.commit()
            
            logger.info(f"User deactivated: {user.email}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Deactivate user error: {e}")
            return False
    
    async def verify_user_email(self, user_id: str) -> bool:
        """Verify user email"""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return False
            
            user.is_verified = True
            user.email_verification_token = None
            user.email_verification_expires = None
            await self.db.commit()
            
            logger.info(f"User email verified: {user.email}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Verify user email error: {e}")
            return False
