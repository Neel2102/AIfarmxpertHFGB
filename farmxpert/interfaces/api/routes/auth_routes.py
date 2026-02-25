"""
Authentication API Routes
Handles user registration, login, logout, and session management
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from farmxpert.models.user_models import User
from farmxpert.services.auth_service import AuthService
from farmxpert.models.database import get_db
from farmxpert.interfaces.api.schemas.auth_schemas import (
    UserRegister, UserLogin, UserResponse, TokenResponse, 
    UserProfileUpdate, PasswordChange, ForgotPasswordRequest,
    ResetPasswordRequest, VerifyTokenRequest
)

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Dependency to get auth service"""
    return AuthService(db)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    
    # Try JWT token first
    payload = auth_service.verify_token(token)
    if payload and payload.get("type") == "access":
        user = auth_service.get_user_by_id(payload["user_id"])
        if user and user.is_active:
            return user
    
    # Try session token
    user = auth_service.get_user_by_session(token)
    if user and user.is_active:
        return user
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegister,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user"""
    try:
        user = auth_service.register_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            phone=user_data.phone
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already exists"
            )
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login user and return access token"""
    try:
        user = auth_service.authenticate_user(
            username=login_data.username,
            password=login_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Create tokens
        access_token = auth_service.create_access_token(user.id, user.username)
        refresh_token = auth_service.create_refresh_token(user.id)
        
        # Create session
        session_token = auth_service.create_user_session(
            user=user,
            ip_address=login_data.ip_address,
            user_agent=login_data.user_agent
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            session_token=session_token,
            token_type="bearer",
            expires_in=auth_service.access_token_expire_minutes * 60,
            user=UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                phone=user.phone,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/logout")
async def logout_user(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Logout user and invalidate session"""
    try:
        # Invalidate all user sessions
        count = auth_service.invalidate_all_user_sessions(current_user.id)
        
        return {
            "message": "Successfully logged out",
            "sessions_invalidated": count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at
    )

@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Update user profile"""
    try:
        user = auth_service.update_user_profile(
            user_id=current_user.id,
            **profile_data.dict(exclude_unset=True)
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile update failed: {str(e)}"
        )

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Change user password"""
    try:
        success = auth_service.change_password(
            user_id=current_user.id,
            old_password=password_data.old_password,
            new_password=password_data.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid old password"
            )
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password change failed: {str(e)}"
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Refresh access token using refresh token"""
    try:
        payload = auth_service.verify_token(refresh_token)
        
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user = auth_service.get_user_by_id(payload["user_id"])
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        access_token = auth_service.create_access_token(user.id, user.username)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,  # Keep the same refresh token
            token_type="bearer",
            expires_in=auth_service.access_token_expire_minutes * 60,
            user=UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                phone=user.phone,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )

@router.get("/sessions")
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get user's active sessions"""
    try:
        # This would require additional methods in AuthService
        # For now, return a simple response
        return {
            "message": "Active sessions retrieved",
            "user_id": current_user.id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sessions: {str(e)}"
        )

@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Request password reset"""
    try:
        success = auth_service.request_password_reset(request.email)
        
        # Always return success for security (don't reveal if email exists)
        return {
            "message": "If an account with that email exists, a password reset link has been sent.",
            "success": True
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process password reset request: {str(e)}"
        )

@router.post("/verify-reset-token")
async def verify_reset_token(
    request: VerifyTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Verify if reset token is valid"""
    try:
        is_valid = auth_service.verify_reset_token(request.token)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        return {
            "message": "Token is valid",
            "valid": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify token: {str(e)}"
        )

@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Reset password using token"""
    try:
        success = auth_service.reset_password_with_token(
            request.token, 
            request.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        return {
            "message": "Password reset successfully",
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset password: {str(e)}"
        )
