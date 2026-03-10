
import sys
import os
sys.path.append(os.getcwd())

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from farmxpert.config.settings import settings
from farmxpert.services.auth_service import AuthService
from farmxpert.models.user_models import User
from farmxpert.models.database import Base

def test_onboarding():
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    auth_service = AuthService(db)
    
    # Try to find a user
    user = db.query(User).first()
    if not user:
        print("No user found in DB to test with!")
        return
        
    print(f"Testing with user: {user.username} (ID: {user.id})")
    
    onboarding_data = {
        "farmName": "Test Farm",
        "state": "Maharashtra",
        "district": "Pune",
        "farmSize": "10.5",
        "soilType": "clay",
        "mainCropCategory": "cereals",
        "specificCrop": "Wheat",
        "irrigationMethod": "drip",
        "waterSourceQuality": "fresh",
        "iotSetup": "none",
        "primaryGoal": "yield",
        "fertilizerPreference": "organic",
        "pestManagement": "preventive",
        "machinery": ["tractor"],
        "laborSetup": "family"
    }
    
    try:
        # We manually call the logic to see the exception
        # Instead of calling auth_service.complete_user_onboarding,
        # we do it manually or wrap it
        
        # Mark onboarding as incomplete first for testing
        user.onboarding_completed = False
        db.commit()
        
        print("Calling complete_user_onboarding...")
        success = auth_service.complete_user_onboarding(user.id, onboarding_data)
        
        if success:
            print("SUCCESS! Onboarding completed.")
        else:
            print("FAILED! Onboarding returned False.")
            # Let's try to reproduce it manually to see the exception
            from datetime import datetime
            profile_fields = {
                "farm_name":          onboarding_data.get("farmName"),
                "farm_size":          str(onboarding_data.get("farmSize", "")),
                "farm_size_unit":     "acres",
                "state":              onboarding_data.get("state"),
                "district":           onboarding_data.get("district"),
                "soil_type":          onboarding_data.get("soilType"),
                "water_source":       onboarding_data.get("waterSourceQuality"),
                "irrigation_method":  onboarding_data.get("irrigationMethod"),
                "primary_crops":      [onboarding_data.get("mainCropCategory", "")],
                "specific_crop":      onboarding_data.get("specificCrop"),
                "labor_setup":        onboarding_data.get("laborSetup"),
                "machinery":          onboarding_data.get("machinery", []),
                "pest_management":    onboarding_data.get("pestManagement"),
                "fertilizer_approach": onboarding_data.get("fertilizerPreference"),
                "farm_goals":         [onboarding_data.get("primaryGoal", "")],
                "tech_comfort":       onboarding_data.get("iotSetup"),
                "updated_at":         datetime.utcnow(),
            }
            
            from farmxpert.models.farm_profile_models import FarmProfile
            existing_profile = db.query(FarmProfile).filter(FarmProfile.user_id == user.id).first()
            if existing_profile:
                print("Updating existing profile...")
                for field, value in profile_fields.items():
                    setattr(existing_profile, field, value)
            else:
                print("Creating new profile...")
                new_profile = FarmProfile(user_id=user.id, **profile_fields)
                db.add(new_profile)
            
            user.onboarding_completed = True
            db.commit()
            print("Manual commit success!")
            
    except Exception as e:
        print(f"EXCEPTION CAUGHT: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_onboarding()
