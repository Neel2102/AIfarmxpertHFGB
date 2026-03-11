import sys
import os
from datetime import datetime, timedelta
import random

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from farmxpert.models.database import SessionLocal, engine, Base
from farmxpert.models.farm_models import Farm, Field, SoilTest, Crop, Task, WeatherData, MarketPrice
from farmxpert.models.user_models import User, AuthUser

def seed_db():
    print("Creating missing database tables using SQLAlchemy...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        print("Seeding users...")
        # 1. Add Users to both User and AuthUser tables
        user1_data = {
            "username": "farmer_john",
            "email": "john@farmxpert.com",
            "full_name": "John Doe",
            "role": "farmer",
            "is_active": True,
            "is_verified": True
        }
        user2_data = {
            "username": "admin_jane",
            "email": "jane@farmxpert.com",
            "full_name": "Jane Smith",
            "role": "admin",
            "is_active": True,
            "is_verified": True
        }

        user1 = db.query(User).filter(User.username == user1_data["username"]).first()
        if not user1:
            user1 = User(**user1_data)
            user1.set_password("password123")
            db.add(user1)
            
        user2 = db.query(User).filter(User.username == user2_data["username"]).first()
        if not user2:
            user2 = User(**user2_data)
            user2.set_password("password123")
            db.add(user2)
            
        db.commit()
        db.refresh(user1)
        db.refresh(user2)

        # Add corresponding AuthUsers
        auth_user1 = db.query(AuthUser).filter(AuthUser.username == user1.username).first()
        if not auth_user1:
            auth_user1 = AuthUser(
                farmer_id="FARMER-001",
                email=user1.email,
                username=user1.username,
                name=user1.full_name,
                password_hash=user1.hashed_password,
                role=user1.role
            )
            db.add(auth_user1)
            
        auth_user2 = db.query(AuthUser).filter(AuthUser.username == user2.username).first()
        if not auth_user2:
            auth_user2 = AuthUser(
                farmer_id="ADMIN-001",
                email=user2.email,
                username=user2.username,
                name=user2.full_name,
                password_hash=user2.hashed_password,
                role=user2.role
            )
            db.add(auth_user2)
            
        db.commit()
        db.refresh(auth_user1)

        # 2. Add Farm (Requires auth_user)
        farm = db.query(Farm).filter(Farm.farm_name == "Krishna Farm").first()
        if farm:
            print("Farm Krishna Farm already exists. Seed complete for users.")
            return

        print("Seeding farm data...")
        farm = Farm(
            user_id=auth_user1.id,  # from AuthUser
            farm_name="Krishna Farm",
            state="Gujarat",
            district="Ahmedabad",
            village="Sanand",
            soil_type="Loamy",
            latitude=22.9868,
            longitude=72.4334
        )
        db.add(farm)
        db.commit()
        db.refresh(farm)
        
        # Create Fields
        fields = [
            Field(farm_id=farm.id, name="North Field", size_acres=5.0, soil_type="Loamy", irrigation_type="Drip"),
            Field(farm_id=farm.id, name="South Field", size_acres=4.0, soil_type="Clay Loam", irrigation_type="Canal"),
            Field(farm_id=farm.id, name="East Field", size_acres=6.0, soil_type="Sandy Loam", irrigation_type="Sprinkler")
        ]
        db.add_all(fields)
        db.commit()
        
        # Soil Tests
        for field in fields:
            test = SoilTest(
                farm_id=farm.id,
                field_id=field.id,
                test_date=datetime.now() - timedelta(days=random.randint(30, 180)),
                soil_ph=random.uniform(6.5, 7.5),
                nitrogen=random.uniform(20, 50),
                phosphorus=random.uniform(15, 40),
                potassium=random.uniform(100, 200),
                source="lab",
                notes="Standard annual test"
            )
            db.add(test)
        db.commit()
        
        # Crops
        crops_data = [
            {"type": "Cotton", "variety": "Bt Cotton", "area": 5.0, "status": "growing"},
            {"type": "Wheat", "variety": "Lok-1", "area": 4.0, "status": "planted"},
            {"type": "Groundnut", "variety": "GG-20", "area": 3.0, "status": "harvested"},
            {"type": "Cumin", "variety": "GC-4", "area": 3.0, "status": "growing"}
        ]
        
        db_crops = []
        for i, c in enumerate(crops_data):
            crop = Crop(
                farm_id=farm.id,
                field_id=fields[i % len(fields)].id,
                crop_type=c["type"],
                variety=c["variety"],
                area_acres=c["area"],
                planting_date=datetime.now() - timedelta(days=random.randint(10, 60)),
                expected_harvest_date=datetime.now() + timedelta(days=random.randint(60, 120)),
                status=c["status"]
            )
            db.add(crop)
            db_crops.append(crop)
        db.commit()
        
        # Tasks
        tasks_data = [
            {"title": "Irrigation for Cotton", "type": "irrigation", "status": "pending", "priority": "high"},
            {"title": "Fertilizer Application", "type": "fertilizing", "status": "in_progress", "priority": "medium"},
            {"title": "Pest Scouting", "type": "monitoring", "status": "completed", "priority": "medium"},
            {"title": "Soil Sampling", "type": "testing", "status": "pending", "priority": "low"},
            {"title": "Harvest Planning", "type": "planning", "status": "pending", "priority": "high"}
        ]
        
        for t in tasks_data:
            task = Task(
                farm_id=farm.id,
                crop_id=db_crops[0].id if db_crops else None,
                title=t["title"],
                task_type=t["type"],
                status=t["status"],
                priority=t["priority"],
                scheduled_date=datetime.now() + timedelta(days=random.randint(1, 14)),
                description=f"Routine {t['title']} activity"
            )
            db.add(task)
        db.commit()

        # Market Prices (Mock but active)
        market_crops = ["Cotton", "Wheat", "Groundnut", "Rice", "Cumin"]
        for mc in market_crops:
            price = MarketPrice(
                crop_type=mc,
                market_location="APMC Ahmedabad",
                price_per_ton=random.uniform(5000, 15000),
                date=datetime.now(),
                source="AgMarket",
                quality_grade="A"
            )
            db.add(price)
        db.commit()

        print("Database seeded successfully with Users and Farm data!")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
