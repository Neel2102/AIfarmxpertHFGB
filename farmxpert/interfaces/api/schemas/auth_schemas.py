"""
Authentication Schemas
Pydantic models for authentication requests and responses
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime

class UserRegister(BaseModel):
    """User registration request"""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: str = Field(..., description="Email address")
    password: str = Field(..., min_length=6, max_length=100, description="Password")
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    
    @validator('username')
    def username_must_be_alphanumeric(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must contain only letters, numbers, underscores, and hyphens')
        return v.lower()
    
    @validator('password')
    def password_must_be_strong(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class UserLogin(BaseModel):
    """User login request"""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")

class UserResponse(BaseModel):
    """User response model"""
    id: int
    username: str
    email: str
    full_name: str
    phone: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    session_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class UserProfileUpdate(BaseModel):
    """User profile update request"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)

class PasswordChange(BaseModel):
    """Password change request"""
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=6, max_length=100, description="New password")
    
    @validator('new_password')
    def password_must_be_strong(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class SessionInfo(BaseModel):
    """Session information"""
    session_id: str
    created_at: datetime
    last_activity: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool

class ForgotPasswordRequest(BaseModel):
    """Forgot password request"""
    email: str = Field(..., description="Email address")
    
    @validator('email')
    def email_must_be_valid(cls, v):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()

class ResetPasswordRequest(BaseModel):
    """Reset password request"""
    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., min_length=6, max_length=100, description="New password")
    
    @validator('new_password')
    def password_must_be_strong(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class VerifyTokenRequest(BaseModel):
    """Verify reset token request"""
    token: str = Field(..., description="Reset token")
