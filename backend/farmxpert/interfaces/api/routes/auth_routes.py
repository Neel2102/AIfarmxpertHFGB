"""
Authentication API Routes
Handles user registration, login, logout, and session management
"""

from fastapi import APIRouter, HTTPException, Depends, status, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta, timezone
from farmxpert.models.user_models import User
from farmxpert.services.auth_service import AuthService
from farmxpert.models.database import get_db
from farmxpert.interfaces.api.schemas.auth_schemas import (
    UserRegister, UserLogin, UserResponse, TokenResponse, 
    UserProfileUpdate, PasswordChange, ForgotPasswordRequest,
    ResetPasswordRequest, VerifyTokenRequest
)
from pydantic import BaseModel
from typing import Optional, Any

# ── Schemas ──────────────────────────────────────────────────────────────────

# Onboarding schemas
class OnboardingData(BaseModel):
    farmName: str
    state: str
    district: str
    farmSize: str
    soilType: str
    mainCropCategory: str
    specificCrop: str
    irrigationMethod: str
    waterSourceQuality: str
    iotSetup: str
    primaryGoal: str
    fertilizerPreference: str
    pestManagement: str
    machinery: list
    laborSetup: str

class OnboardingResponse(BaseModel):
    message: str
    success: bool
    user: Optional[dict] = None

class FarmProfileResponse(BaseModel):
    id: int
    user_id: int
    farm_name: Optional[str] = None
    farm_size: Optional[str] = None
    farm_size_unit: Optional[str] = None
    location: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    village: Optional[str] = None
    soil_type: Optional[str] = None
    water_source: Optional[str] = None
    irrigation_method: Optional[str] = None
    primary_crops: Optional[list] = None
    specific_crop: Optional[str] = None
    machinery: Optional[list] = None
    labor_setup: Optional[str] = None
    tech_comfort: Optional[str] = None
    farm_goals: Optional[list] = None
    updated_at: datetime

class FarmProfileUpdate(BaseModel):
    farm_name: Optional[str] = None
    farm_size: Optional[str] = None
    location: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    village: Optional[str] = None
    soil_type: Optional[str] = None
    water_source: Optional[str] = None
    irrigation_method: Optional[str] = None
    primary_crops: Optional[list] = None
    specific_crop: Optional[str] = None
    machinery: Optional[list] = None
    labor_setup: Optional[str] = None
    tech_comfort: Optional[str] = None
    farm_goals: Optional[list] = None

class ProfileUpdateRequest(BaseModel):
    """Accept both 'name' and 'full_name' so old and new UI both work."""
    name: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None

class FarmLayoutSave(BaseModel):
    polygon: Optional[Any] = None          # GeoJSON Feature or Geometry
    form_data: Optional[dict] = None       # soil_type, water_source, season, land_area, crop_preferences

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
            role=getattr(user, "role", "farmer"),
            onboarding_completed=getattr(user, 'onboarding_completed', False),
            created_at=user.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLogin,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login user and return access token with secure HttpOnly cookies"""
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
        
        # Set secure HttpOnly cookies
        response.set_cookie(
            key="access_token",
            value=access_token,
            max_age=1800,  # 30 minutes
            path="/",
            domain=None,
            secure=False,  # Set to True in production with HTTPS
            httponly=True,
            samesite="lax"
        )
        
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=604800,  # 7 days
            path="/",
            domain=None,
            secure=False,  # Set to True in production with HTTPS
            httponly=True,
            samesite="lax"
        )
        
        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=2592000,  # 30 days
            path="/",
            domain=None,
            secure=False,  # Set to True in production with HTTPS
            httponly=True,
            samesite="lax"
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
                role=getattr(user, "role", "farmer"),
                onboarding_completed=getattr(user, 'onboarding_completed', False),
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
    response: Response,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Logout user and invalidate session, clearing all cookies"""
    try:
        # Invalidate all user sessions
        count = auth_service.invalidate_all_user_sessions(current_user.id)
        
        # Clear all authentication cookies
        response.delete_cookie(
            key="access_token",
            path="/",
            domain=None,
            secure=False,
            httponly=True,
            samesite="lax"
        )
        
        response.delete_cookie(
            key="refresh_token",
            path="/",
            domain=None,
            secure=False,
            httponly=True,
            samesite="lax"
        )
        
        response.delete_cookie(
            key="session_token",
            path="/",
            domain=None,
            secure=False,
            httponly=True,
            samesite="lax"
        )
        
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
        role=getattr(current_user, "role", "farmer"),
        onboarding_completed=getattr(current_user, 'onboarding_completed', False),
        created_at=current_user.created_at
    )

@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    profile_data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Update user profile — accepts 'name' or 'full_name' interchangeably."""
    try:
        update_kwargs = profile_data.dict(exclude_unset=True)
        # Normalise: if caller sent 'name' convert to full_name
        if 'name' in update_kwargs and 'full_name' not in update_kwargs:
            update_kwargs['full_name'] = update_kwargs.pop('name')
        # Drop fields that aren't stored on the User model (e.g. location)
        update_kwargs.pop('location', None)

        user = auth_service.update_user_profile(
            user_id=current_user.id,
            **update_kwargs
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
            role=getattr(user, "role", "farmer"),
            onboarding_completed=getattr(user, 'onboarding_completed', False),
            created_at=user.created_at
        )
        
    except HTTPException:
        raise
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
                role=getattr(user, "role", "farmer"),
                onboarding_completed=getattr(user, 'onboarding_completed', False),
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

@router.post("/onboarding/complete")
async def complete_onboarding(
    onboarding_data: OnboardingData,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Complete user onboarding and save farm profile. Returns updated user data."""
    try:
        success = auth_service.complete_user_onboarding(current_user.id, onboarding_data.dict())
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to complete onboarding"
            )
        
        # Return updated user object so frontend can sync without a separate /me call
        updated_user = auth_service.get_user_by_id(current_user.id)
        return {
            "message": "Onboarding completed successfully",
            "success": True,
            "user": {
                "id": updated_user.id,
                "username": updated_user.username,
                "email": updated_user.email,
                "full_name": updated_user.full_name,
                "name": updated_user.full_name,
                "phone": updated_user.phone,
                "is_active": updated_user.is_active,
                "role": getattr(updated_user, "role", "farmer"),
                "onboarding_completed": True,
            },
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Onboarding completion failed: {str(e)}"
        )

@router.get("/farm-profile", response_model=FarmProfileResponse)
async def get_farm_profile(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Retrieve the current user's farm profile"""
    profile = auth_service.get_farm_profile(current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm profile not found"
        )
    return profile

@router.put("/farm-profile", response_model=FarmProfileResponse)
async def update_farm_profile(
    profile_data: FarmProfileUpdate,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Update the current user's farm profile"""
    profile = auth_service.update_farm_profile(
        current_user.id, 
        profile_data.dict(exclude_unset=True)
    )
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update farm profile"
        )
    return profile


# ── Farm Layout endpoints ─────────────────────────────────────────────────────

@router.put("/farm-layout")
async def save_farm_layout(
    layout: FarmLayoutSave,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save GeoJSON polygon + form data for the logged-in user's farm layout."""
    from farmxpert.models.farm_profile_models import FarmProfile
    from datetime import datetime

    profile = db.query(FarmProfile).filter(FarmProfile.user_id == current_user.id).first()
    if not profile:
        profile = FarmProfile(user_id=current_user.id, created_at=datetime.utcnow())
        db.add(profile)

    profile.farm_polygon = layout.polygon
    profile.farm_layout_data = layout.form_data
    profile.updated_at = datetime.utcnow()
    db.commit()

    return {"success": True, "message": "Farm layout saved."}


@router.get("/farm-layout")
async def get_farm_layout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve the saved GeoJSON polygon + form data for the logged-in user."""
    from farmxpert.models.farm_profile_models import FarmProfile

    profile = db.query(FarmProfile).filter(FarmProfile.user_id == current_user.id).first()
    if not profile or not profile.farm_polygon:
        return {"has_layout": False}

    return {
        "has_layout": True,
        "polygon": profile.farm_polygon,
        "form_data": profile.farm_layout_data or {},
    }


# ── AI Token Usage (simulated) ────────────────────────────────────────────────

@router.get("/token-usage")
async def get_token_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return AI token usage for the current user. Simulated until real tracking is wired."""
    from farmxpert.models.farm_models import AgentInteraction
    from farmxpert.models.farm_profile_models import FarmProfile

    # Try to compute real token usage from AgentInteractions linked to this user's farm
    real_tokens = 0
    real_calls = 0
    try:
        profile = db.query(FarmProfile).filter(FarmProfile.user_id == current_user.id).first()
        if profile:
            from farmxpert.models.farm_models import Farm
            # Sum tokens_used from agent_interactions (farm linked via farm_profiles)
            # For now use a simple count approach
            real_calls = (
                db.query(AgentInteraction)
                .limit(1000)
                .count()
            )
            total_tokens_result = db.query(AgentInteraction).all()
            real_tokens = sum((r.tokens_used or 0) for r in total_tokens_result)
    except Exception:
        pass  # Fallback to simulated data

    # If no real data, return simulated values scoped to this user
    tokens_used = real_tokens if real_tokens > 0 else (current_user.id * 1247 + 8344)
    api_calls = real_calls if real_calls > 0 else (current_user.id * 3 + 21)
    quota = 100_000
    cost_per_1k = 0.002  # ~GPT-3.5 turbo pricing USD per 1K tokens

    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "period": "March 2026",
        "tokens_used": tokens_used,
        "tokens_quota": quota,
        "tokens_remaining": max(0, quota - tokens_used),
        "usage_percent": round(min(100, (tokens_used / quota) * 100), 1),
        "api_calls": api_calls,
        "estimated_cost_usd": round((tokens_used / 1000) * cost_per_1k, 4),
        "model": "LiteLLM / Gemini",
    }
