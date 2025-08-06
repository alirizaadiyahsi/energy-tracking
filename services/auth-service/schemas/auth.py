"""
Authentication schemas for request/response validation
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime

class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr
    password: str
    remember_me: Optional[bool] = False

class LoginResponse(BaseModel):
    """Login response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    email: str
    session_id: str

class RegisterRequest(BaseModel):
    """User registration request schema"""
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class RegisterResponse(BaseModel):
    """User registration response schema"""
    message: str
    user_id: str
    email: str

class TokenRefreshRequest(BaseModel):
    """Token refresh request schema"""
    refresh_token: str

class TokenRefreshResponse(BaseModel):
    """Token refresh response schema"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int

class PasswordResetRequest(BaseModel):
    """Password reset request schema"""
    email: EmailStr

class ChangePasswordRequest(BaseModel):
    """Change password request schema"""
    token: Optional[str] = None  # For reset
    old_password: Optional[str] = None  # For authenticated change
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class EmailVerificationRequest(BaseModel):
    """Email verification request schema"""
    token: str

class UserProfile(BaseModel):
    """User profile schema"""
    id: str
    email: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_verified: bool
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class SessionInfo(BaseModel):
    """Session information schema"""
    session_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_info: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True
