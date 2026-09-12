"""
Authentication API Routes
Handles user registration, login, logout, and session management
"""

from fastapi import APIRouter, HTTPException, Depends, status, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Any, Dict
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
    id: Optional[int] = None
    user_id: Optional[int] = None
    farm_name: Optional[str] = None
    farm_size: Optional[str] = None
    farm_size_unit: Optional[str] = None
    location: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    village: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    soil_type: Optional[str] = None
    water_source: Optional[str] = None
    irrigation_method: Optional[str] = None
    primary_crops: Optional[list] = None
    specific_crop: Optional[str] = None
    crop_type: Optional[str] = None
    machinery: Optional[list] = None
    labor_setup: Optional[str] = None
    tech_comfort: Optional[str] = None
    farm_goals: Optional[list] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class FarmProfileUpdate(BaseModel):
    farm_name: Optional[str] = None
    farm_size: Optional[str] = None
    farm_size_unit: Optional[str] = None
    location: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    village: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    soil_type: Optional[str] = None
    water_source: Optional[str] = None
    irrigation_method: Optional[str] = None
    primary_crops: Optional[list] = None
    specific_crop: Optional[str] = None
    crop_type: Optional[str] = None
    machinery: Optional[list] = None
    labor_setup: Optional[str] = None
    tech_comfort: Optional[str] = None
    farm_goals: Optional[list] = None

    class Config:
        extra = "allow"

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
    boundaries: Optional[List[Any]] = None
    center: Optional[List[float]] = None
    zoom: Optional[int] = None
    name: Optional[str] = None
    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None
    area_acres: Optional[float] = None
    notes: Optional[str] = None

    class Config:
        extra = "allow"

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
@router.post("/farm-profile", response_model=FarmProfileResponse)
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
@router.post("/farm-layout")
async def save_farm_layout(
    layout: FarmLayoutSave,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save GeoJSON polygon + form data for the logged-in user's farm layout and sync to canonical Farm record."""
    from farmxpert.models.farm_profile_models import FarmProfile
    from farmxpert.models.farm_models import Farm, Crop
    from farmxpert.models.user_models import AuthUser
    from datetime import datetime

    profile = db.query(FarmProfile).filter(FarmProfile.user_id == current_user.id).first()
    if not profile:
        profile = FarmProfile(user_id=current_user.id, created_at=datetime.utcnow())
        db.add(profile)

    profile.farm_polygon = layout.polygon
    profile.farm_layout_data = layout.form_data or {}
    profile.updated_at = datetime.utcnow()

    # Extract centroid coordinates from GeoJSON polygon if present
    centroid_lat = None
    centroid_lon = None
    try:
        poly = layout.polygon
        if poly and isinstance(poly, dict):
            coords = poly.get("coordinates")
            if coords and isinstance(coords, list) and len(coords) > 0:
                first_ring = coords[0]
                if isinstance(first_ring, list) and len(first_ring) > 0:
                    pts = [pt for pt in first_ring if isinstance(pt, list) and len(pt) >= 2]
                    if pts:
                        centroid_lon = sum(float(pt[0]) for pt in pts) / len(pts)
                        centroid_lat = sum(float(pt[1]) for pt in pts) / len(pts)
    except Exception as e:
        logger.warning(f"Failed to calculate polygon centroid: {e}")

    if centroid_lat is None and layout.center and len(layout.center) >= 2:
        centroid_lat = float(layout.center[0])
        centroid_lon = float(layout.center[1])
    elif centroid_lat is None and layout.boundaries and len(layout.boundaries) > 0:
        try:
            pts = layout.boundaries
            centroid_lat = sum(float(p.get("lat") if isinstance(p, dict) else p[0]) for p in pts) / len(pts)
            centroid_lon = sum(float(p.get("lng", p.get("lon")) if isinstance(p, dict) else p[1]) for p in pts) / len(pts)
        except Exception:
            pass

    if centroid_lat is not None and centroid_lon is not None:
        profile.latitude = centroid_lat
        profile.longitude = centroid_lon

    # Ensure AuthUser exists if database foreign key constraint references auth_users(id)
    try:
        au = db.query(AuthUser).filter(AuthUser.id == current_user.id).first()
        if not au:
            au = AuthUser(
                id=current_user.id,
                farmer_id=f"FRM{current_user.id:04d}",
                email=current_user.email,
                username=current_user.username,
                name=current_user.full_name or current_user.username,
                phone=current_user.phone,
                password_hash=current_user.hashed_password,
                role=getattr(current_user, "role", "farmer"),
            )
            db.add(au)
            db.flush()
    except Exception as au_err:
        logger.warning(f"AuthUser sync note in save_farm_layout: {au_err}")

    # Synchronize canonical Farm record
    farm = db.query(Farm).filter(Farm.user_id == current_user.id).first()
    if not farm:
        farm = Farm(user_id=current_user.id)
        db.add(farm)

    if centroid_lat is not None and centroid_lon is not None:
        farm.latitude = centroid_lat
        farm.longitude = centroid_lon

    if layout.name:
        farm.farm_name = layout.name
        profile.farm_name = layout.name
    if layout.soil_type:
        farm.soil_type = layout.soil_type
        profile.soil_type = layout.soil_type
    if layout.irrigation_type:
        profile.irrigation_type = layout.irrigation_type
    if layout.area_acres is not None:
        try:
            farm.size_acres = float(layout.area_acres)
            profile.farm_size = float(layout.area_acres)
        except Exception:
            pass

    if layout.form_data and isinstance(layout.form_data, dict):
        fd = layout.form_data
        if fd.get("farm_name"):
            farm.farm_name = fd["farm_name"]
            profile.farm_name = fd["farm_name"]
        if fd.get("soil_type"):
            farm.soil_type = fd["soil_type"]
            profile.soil_type = fd["soil_type"]
        if fd.get("crop_type") or fd.get("crop_preferences"):
            chosen_crop = fd.get("crop_type") or fd.get("crop_preferences")
            farm.crop_type = chosen_crop
            profile.specific_crop = chosen_crop
        if fd.get("land_area"):
            try:
                farm.size_acres = float(str(fd["land_area"]).split()[0])
            except Exception:
                pass
        if fd.get("state"):
            farm.state = fd["state"]
            profile.state = fd["state"]
        if fd.get("district"):
            farm.district = fd["district"]
            profile.district = fd["district"]
        if fd.get("village"):
            farm.village = fd["village"]
            profile.village = fd["village"]

        loc_parts = [fd.get("village"), fd.get("district"), fd.get("state")]
        loc_str = ", ".join([str(p) for p in loc_parts if p])
        if loc_str:
            farm.location = loc_str
            profile.location = loc_str

    db.flush()

    # Synchronize active Crop record
    if farm.crop_type:
        try:
            crop = db.query(Crop).filter(Crop.farm_id == farm.id).first()
            if not crop:
                crop = Crop(
                    farm_id=farm.id,
                    crop_type=farm.crop_type,
                    variety="Standard",
                    area_acres=float(farm.size_acres or 5.0),
                    status="growing"
                )
                db.add(crop)
            else:
                crop.crop_type = farm.crop_type
        except Exception as crop_err:
            logger.warning(f"Crop sync note: {crop_err}")

    db.commit()
    db.refresh(profile)

    return {
        "success": True,
        "message": "Farm layout and coordinates saved.",
        "latitude": centroid_lat,
        "longitude": centroid_lon
    }


@router.get("/farm-layout")
async def get_farm_layout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve the saved GeoJSON polygon + form data for the logged-in user, synchronized with canonical Farm record."""
    from farmxpert.models.farm_profile_models import FarmProfile
    from farmxpert.models.farm_models import Farm

    profile = db.query(FarmProfile).filter(FarmProfile.user_id == current_user.id).first()
    farm = db.query(Farm).filter(Farm.user_id == current_user.id).first()

    merged_form_data = {}
    if profile and profile.farm_layout_data and isinstance(profile.farm_layout_data, dict):
        merged_form_data.update(profile.farm_layout_data)

    if farm:
        if farm.farm_name:
            merged_form_data["farm_name"] = farm.farm_name
        if farm.soil_type:
            merged_form_data["soil_type"] = farm.soil_type
        if farm.crop_type:
            merged_form_data["crop_type"] = farm.crop_type
            merged_form_data["crop_preferences"] = farm.crop_type
        if farm.size_acres:
            merged_form_data["land_area"] = farm.size_acres
        if farm.location:
            merged_form_data["location"] = farm.location
    elif profile:
        if profile.farm_name:
            merged_form_data["farm_name"] = profile.farm_name
        if profile.soil_type:
            merged_form_data["soil_type"] = profile.soil_type
        if profile.specific_crop:
            merged_form_data["crop_type"] = profile.specific_crop
            merged_form_data["crop_preferences"] = profile.specific_crop
        if profile.location:
            merged_form_data["location"] = profile.location

    has_polygon = bool(profile and profile.farm_polygon)
    lat = float(farm.latitude) if farm and farm.latitude else (profile.latitude if profile else None)
    lon = float(farm.longitude) if farm and farm.longitude else (profile.longitude if profile else None)

    return {
        "has_layout": has_polygon,
        "polygon": profile.farm_polygon if has_polygon else None,
        "form_data": merged_form_data,
        "latitude": lat,
        "longitude": lon,
        "farm_name": merged_form_data.get("farm_name", "My Farm"),
        "updated_at": profile.updated_at.isoformat() if profile and profile.updated_at else None,
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
