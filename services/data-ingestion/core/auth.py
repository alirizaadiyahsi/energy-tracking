"""
Authentication and authorization utilities for the data-ingestion service.
"""

import logging
import httpx
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.config import settings

logger = logging.getLogger(__name__)

# Security scheme for JWT Bearer tokens
security = HTTPBearer()

class AuthError(Exception):
    """Custom exception for authentication errors"""
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class User:
    """User model for authenticated requests"""
    def __init__(self, user_id: str, email: str, roles: List[str], organization_id: Optional[str] = None):
        self.id = user_id
        self.email = email
        self.roles = roles
        self.organization_id = organization_id
        
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role"""
        return role in self.roles
        
    def has_any_role(self, roles: List[str]) -> bool:
        """Check if user has any of the specified roles"""
        return any(role in self.roles for role in roles)


class AuthService:
    """Service for authentication and authorization operations"""
    
    def __init__(self):
        self.auth_service_url = settings.AUTH_SERVICE_URL
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token with auth service"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = await self.client.post(
                f"{self.auth_service_url}/auth/validate",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise AuthError("Invalid or expired token")
            else:
                logger.error(f"Auth service error: {response.status_code} - {response.text}")
                raise AuthError("Authentication service error", 503)
                
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to auth service: {e}")
            raise AuthError("Authentication service unavailable", 503)
    
    async def check_permission(self, user_id: str, permission: str, resource_id: Optional[str] = None) -> bool:
        """Check if user has specific permission"""
        try:
            payload = {
                "user_id": user_id,
                "permission": permission,
                "resource_id": resource_id
            }
            
            response = await self.client.post(
                f"{self.auth_service_url}/auth/check-permission",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("has_permission", False)
            else:
                logger.error(f"Permission check failed: {response.status_code}")
                return False
                
        except httpx.RequestError as e:
            logger.error(f"Failed to check permissions: {e}")
            return False
    
    async def get_user_info(self, token: str) -> User:
        """Get user information from validated token"""
        try:
            user_data = await self.validate_token(token)
            
            return User(
                user_id=user_data.get("user_id"),
                email=user_data.get("email"),
                roles=user_data.get("roles", []),
                organization_id=user_data.get("organization_id")
            )
        except AuthError:
            raise
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            raise AuthError("Failed to retrieve user information")

# Global auth service instance
auth_service = AuthService()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """FastAPI dependency to get current authenticated user"""
    try:
        token = credentials.credentials
        user = await auth_service.get_user_info(token)
        
        if not user.id:
            raise AuthError("Invalid user data")
            
        return user
        
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[User]:
    """FastAPI dependency to get current user (optional)"""
    if not credentials:
        return None
        
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def require_permission(permission: str, resource_id_param: Optional[str] = None):
    """Decorator to require specific permission for endpoint access"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs (injected by FastAPI)
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Get resource ID from path parameters if specified
            resource_id = None
            if resource_id_param and resource_id_param in kwargs:
                resource_id = kwargs[resource_id_param]
            
            # Check permission
            has_permission = await auth_service.check_permission(
                current_user.id, 
                permission, 
                resource_id
            )
            
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: {permission}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_roles(roles: List[str]):
    """Decorator to require specific roles for endpoint access"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not current_user.has_any_role(roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient roles. Required one of: {', '.join(roles)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
