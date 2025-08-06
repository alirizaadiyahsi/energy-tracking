"""
Users API endpoints
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import security
from schemas.auth import UserProfile
from services.auth_service import AuthService
from services.user_service import UserService

logger = logging.getLogger(__name__)
security_scheme = HTTPBearer()

router = APIRouter()

async def get_current_user_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db)
):
    """Dependency to get current authenticated user"""
    auth_service = AuthService(db)
    user = await auth_service.get_current_user(credentials.credentials)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    return user

@router.get("/profile", response_model=UserProfile)
async def get_user_profile(
    current_user = Depends(get_current_user_dependency)
):
    """Get current user profile"""
    return UserProfile.from_orm(current_user)

@router.put("/profile", response_model=UserProfile)
async def update_user_profile(
    profile_data: dict,
    current_user = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile"""
    try:
        user_service = UserService(db)
        
        # Filter allowed update fields
        allowed_fields = ['first_name', 'last_name', 'username', 'phone_number']
        update_data = {k: v for k, v in profile_data.items() if k in allowed_fields}
        
        updated_user = await user_service.update_user(str(current_user.id), **update_data)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Profile update failed"
            )
        
        return UserProfile.from_orm(updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )

@router.get("/", response_model=List[UserProfile])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None),
    current_user = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """List users (admin only)"""
    try:
        # Check if user is superuser
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        user_service = UserService(db)
        users = await user_service.list_users(skip=skip, limit=limit, is_active=is_active)
        
        return [UserProfile.from_orm(user) for user in users]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List users error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )

@router.get("/{user_id}", response_model=UserProfile)
async def get_user(
    user_id: str,
    current_user = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID (admin only or own profile)"""
    try:
        # Check permissions
        if str(current_user.id) != user_id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        user_service = UserService(db)
        user = await user_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserProfile.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user"
        )

@router.put("/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Activate user (admin only)"""
    try:
        # Check if user is superuser
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        user_service = UserService(db)
        success = await user_service.activate_user(user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {"message": "User activated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Activate user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate user"
        )

@router.put("/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate user (admin only)"""
    try:
        # Check if user is superuser
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Prevent self-deactivation
        if str(current_user.id) == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own account"
            )
        
        user_service = UserService(db)
        success = await user_service.deactivate_user(user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {"message": "User deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deactivate user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )
