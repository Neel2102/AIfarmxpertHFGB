"""
Authentication Service
Handles user authentication, session management, and JWT tokens
"""

import jwt
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from farmxpert.models.database import Base
from farmxpert.models.user_models import User, UserSession
from farmxpert.models.farm_profile_models import FarmProfile
from farmxpert.models.database import get_db
from farmxpert.config.settings import get_settings
from farmxpert.services.email_service import email_service

settings = get_settings()

class AuthService:
    """Service for handling authentication operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.secret_key = settings.secret_key
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
        # Secure cookie configuration
        self.cookie_settings = {
            "max_age": 1800,  # 30 minutes for access token
            "expires": datetime.now(timezone.utc) + timedelta(minutes=30),
            "path": "/",
            "domain": None,
            "secure": False,  # Set to True in production with HTTPS
            "httponly": True,
            "samesite": "lax"
        }
    
    def create_access_token(self, user_id: int, username: str) -> str:
        """Create JWT access token"""
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        payload = {
            "user_id": user_id,
            "username": username,
            "exp": expire,
            "type": "access"
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: int) -> str:
        """Create JWT refresh token"""
        expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)
        payload = {
            "user_id": user_id,
            "exp": expire,
            "type": "refresh"
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        user = self.db.query(User).filter(
            and_(
                (User.username == username) | (User.email == username),
                User.is_active == True
            )
        ).first()
        
        if user and user.check_password(password):
            # Update last login
            user.last_login = datetime.utcnow()
            self.db.commit()
            return user
        
        return None
    
    def create_user_session(self, user: User, ip_address: str = None, user_agent: str = None) -> str:
        """Create a new user session"""
        # Generate session token
        session_token = secrets.token_urlsafe(32)
        
        # Create session record
        session = UserSession(
            user_id=user.id,
            session_token=session_token,
            expires_at=datetime.utcnow() + timedelta(days=30),  # 30 days
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(session)
        self.db.commit()
        
        return session_token
    
    def get_user_by_session(self, session_token: str) -> Optional[User]:
        """Get user by session token"""
        session = self.db.query(UserSession).filter(
            and_(
                UserSession.session_token == session_token,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.now(timezone.utc)
            )
        ).first()
        
        if session:
            # Update last activity
            session.last_activity = datetime.utcnow()
            self.db.commit()
            return session.user
        
        return None
    
    def invalidate_session(self, session_token: str) -> bool:
        """Invalidate a user session"""
        session = self.db.query(UserSession).filter(
            UserSession.session_token == session_token
        ).first()
        
        if session:
            session.is_active = False
            self.db.commit()
            return True
        
        return False
    
    def invalidate_all_user_sessions(self, user_id: int) -> int:
        """Invalidate all sessions for a user"""
        sessions = self.db.query(UserSession).filter(
            and_(UserSession.user_id == user_id, UserSession.is_active == True)
        ).all()
        
        count = 0
        for session in sessions:
            session.is_active = False
            count += 1
        
        self.db.commit()
        return count
    
    def is_token_blacklisted(self, token: str) -> bool:
        """Check if a token is blacklisted (for logout functionality)"""
        # This would require a blacklist table in the database
        # For now, return False as we don't have token blacklisting implemented
        return False
    
    def blacklist_token(self, token: str) -> bool:
        """Blacklist a token (for logout functionality)"""
        # This would require a blacklist table in the database
        # For now, return True as a placeholder
        return True
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        expired_sessions = self.db.query(UserSession).filter(
            UserSession.expires_at < datetime.utcnow()
        ).all()
        
        count = len(expired_sessions)
        for session in expired_sessions:
            self.db.delete(session)
        
        self.db.commit()
        return count
    
    def register_user(self, username: str, email: str, password: str, full_name: str, phone: str = None) -> Optional[User]:
        """Register a new user and auto-create their farm"""
        # Check if user already exists
        existing_user = self.db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            return None
        
        # Create new user
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            phone=phone,
            is_active=True,
            is_verified=False
        )
        user.set_password(password)
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        # Auto-create a default farm for the farmer
        # TODO: Fix farm creation after ensuring proper database schema
        # try:
        #     from farmxpert.models.farm_models import Farm
        #     farm = Farm(
        #         name=f"{full_name}'s Farm",
        #         location="Not set",
        #         size_acres=0,
        #         farmer_name=full_name,
        #         farmer_phone=phone,
        #         farmer_email=email,
        #     )
        #     self.db.add(farm)
        #     self.db.commit()
        # except Exception as e:
        #     print(f"Auto-farm creation note: {e}")
        
        return user
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()
    
    def update_user_profile(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user profile"""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        # Support both 'name' and 'full_name' from frontend
        if 'name' in kwargs and kwargs['name']:
            user.full_name = kwargs['name']
        
        # Update allowed fields
        allowed_fields = ['full_name', 'email', 'phone']
        for field, value in kwargs.items():
            if field in allowed_fields and hasattr(user, field):
                setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Change user password"""
        user = self.get_user_by_id(user_id)
        if not user or not user.check_password(old_password):
            return False
        
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()
        self.db.commit()
        
        # Invalidate all existing sessions for security
        self.invalidate_all_user_sessions(user_id)
        
        return True
    
    def request_password_reset(self, email: str) -> bool:
        """Request password reset for user"""
        try:
            # Find user by email
            user = self.db.query(User).filter(
                and_(User.email == email, User.is_active == True)
            ).first()
            
            if not user:
                # Don't reveal if email exists or not for security
                return True
            
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            
            # Create or update reset token record
            existing_token = self.db.query(PasswordResetToken).filter(
                PasswordResetToken.user_id == user.id
            ).first()
            
            if existing_token:
                # Update existing token
                existing_token.token = reset_token
                existing_token.expires_at = datetime.utcnow() + timedelta(hours=1)
                existing_token.used = False
            else:
                # Create new token
                reset_token_record = PasswordResetToken(
                    user_id=user.id,
                    token=reset_token,
                    expires_at=datetime.utcnow() + timedelta(hours=1)
                )
                self.db.add(reset_token_record)
            
            self.db.commit()
            
            # Send reset email
            email_sent = email_service.send_password_reset_email(
                to_email=user.email,
                reset_token=reset_token,
                user_name=user.full_name
            )
            
            return email_sent
            
        except Exception as e:
            print(f"Error requesting password reset: {e}")
            return False
    
    def reset_password_with_token(self, token: str, new_password: str) -> bool:
        """Reset password using reset token"""
        try:
            # Find valid reset token
            reset_token_record = self.db.query(PasswordResetToken).filter(
                and_(
                    PasswordResetToken.token == token,
                    PasswordResetToken.expires_at > datetime.utcnow(),
                    PasswordResetToken.used == False
                )
            ).first()
            
            if not reset_token_record:
                return False
            
            # Get user
            user = self.db.query(User).filter(User.id == reset_token_record.user_id).first()
            if not user:
                return False
            
            # Update password
            user.set_password(new_password)
            user.updated_at = datetime.utcnow()
            
            # Mark token as used
            reset_token_record.used = True
            reset_token_record.used_at = datetime.utcnow()
            
            # Invalidate all user sessions for security
            self.invalidate_all_user_sessions(user.id)
            
            self.db.commit()
            
            return True
            
        except Exception as e:
            print(f"Error resetting password: {e}")
            return False
    
    def verify_reset_token(self, token: str) -> bool:
        """Verify if reset token is valid"""
        try:
            reset_token_record = self.db.query(PasswordResetToken).filter(
                and_(
                    PasswordResetToken.token == token,
                    PasswordResetToken.expires_at > datetime.utcnow(),
                    PasswordResetToken.used == False
                )
            ).first()
            
            return reset_token_record is not None
            
        except Exception as e:
            print(f"Error verifying reset token: {e}")
            return False
    
    def complete_user_onboarding(self, user_id: int, onboarding_data: dict) -> bool:
        """Complete user onboarding and save farm profile with exact camelCase key mapping."""
        try:
            # Get user
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False

            # Build canonicalized fields from the exact keys the React form sends
            profile_fields = {
                "farm_name":          onboarding_data.get("farmName"),
                "farm_size":          str(onboarding_data.get("farmSize", "")),
                "farm_size_unit":     "acres",
                "state":              onboarding_data.get("state"),
                "district":           onboarding_data.get("district"),
                # Soil
                "soil_type":          onboarding_data.get("soilType"),
                # Water
                "water_source":       onboarding_data.get("waterSourceQuality"),   # FIX
                "irrigation_method":  onboarding_data.get("irrigationMethod"),
                # Crop
                "primary_crops":      [onboarding_data.get("mainCropCategory", "")],  # FIX
                "specific_crop":      onboarding_data.get("specificCrop"),
                # Labour & machinery
                "labor_setup":        onboarding_data.get("laborSetup"),
                "machinery":          onboarding_data.get("machinery", []),
                # Practices
                "pest_management":    onboarding_data.get("pestManagement"),
                "fertilizer_approach": onboarding_data.get("fertilizerPreference"),  # FIX
                # Goals & tech
                "farm_goals":         [onboarding_data.get("primaryGoal", "")],  # FIX
                "tech_comfort":       onboarding_data.get("iotSetup"),            # FIX
                "updated_at":         datetime.utcnow(),
            }

            # Check if farm profile already exists
            existing_profile = self.db.query(FarmProfile).filter(
                FarmProfile.user_id == user_id
            ).first()

            if existing_profile:
                for field, value in profile_fields.items():
                    if value is not None and hasattr(existing_profile, field):
                        setattr(existing_profile, field, value)
            else:
                new_profile = FarmProfile(
                    user_id=user_id,
                    created_at=datetime.utcnow(),
                    **{k: v for k, v in profile_fields.items()}
                )
                self.db.add(new_profile)

            # Mark user as having completed onboarding
            user.onboarding_completed = True
            user.updated_at = datetime.utcnow()

            self.db.commit()
            print(f"Onboarding completed for user {user_id}")
            return True

        except Exception as e:
            print(f"Error completing onboarding: {e}")
            self.db.rollback()
            return False

    def get_farm_profile(self, user_id: int) -> Optional[FarmProfile]:
        """Get farm profile by user ID"""
        return self.db.query(FarmProfile).filter(FarmProfile.user_id == user_id).first()

    def update_farm_profile(self, user_id: int, profile_data: dict) -> Optional[FarmProfile]:
        """Update farm profile data"""
        try:
            profile = self.get_farm_profile(user_id)
            if not profile:
                profile = FarmProfile(user_id=user_id, created_at=datetime.utcnow())
                self.db.add(profile)
            
            # Update fields
            for field, value in profile_data.items():
                if hasattr(profile, field):
                    setattr(profile, field, value)
            
            profile.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(profile)
            return profile
        except Exception as e:
            print(f"Error updating farm profile: {e}")
            self.db.rollback()
            return None
