"""
Common authentication utilities
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext


class TokenManager:
    """JWT token management utilities"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.PyJWTError:
            return None
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)


class PermissionChecker:
    """Utility for checking permissions"""
    
    @staticmethod
    def has_permission(user_permissions: list, required_permission: str) -> bool:
        """Check if user has required permission"""
        return required_permission in user_permissions
    
    @staticmethod
    def has_role(user_roles: list, required_role: str) -> bool:
        """Check if user has required role"""
        return required_role in user_roles
    
    @staticmethod
    def has_any_permission(user_permissions: list, required_permissions: list) -> bool:
        """Check if user has any of the required permissions"""
        return any(perm in user_permissions for perm in required_permissions)
    
    @staticmethod
    def has_all_permissions(user_permissions: list, required_permissions: list) -> bool:
        """Check if user has all required permissions"""
        return all(perm in user_permissions for perm in required_permissions)
