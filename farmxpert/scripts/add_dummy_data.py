"""
Script to add dummy data for testing
Creates users from different Indian regions with farm data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
from farmxpert.models.user_models import User, Farm, Crop, SoilTest, Task, Yield
from farmxpert.config.database import get_db, engine
from farmxpert.models.user_models import Base

# Create tables
Base.metadata.create_all(bind=engine)

# Indian states and their characteristics
INDIAN_REGIONS = [
    {
        "state": "ahmedabad",
        "district": "Ludhiana",
        "village": "Kila Raipur",
        "latitude": 30.9010,
        "longitude": 75.8573,
        "soil_type": "Alluvial",
        "irrigation_type": "canal",
        "crops": ["Wheat", "Rice", "Maize", "Sugarcane", "Cotton"]
    },
    {
        "state": "Haryana",
        "district": "Karnal",
        "village": "Nilokheri",
        "latitude": 29.6857,
        "longitude": 76.9905,
        "soil_type": "Alluvial",
        "irrigation_type": "tubewell",
        "crops": ["Wheat", "Rice", "Mustard", "Sugarcane", "Bajra"]
    },
    {
        "state": "Uttar Pradesh",
        "district": "Meerut",
        "village": "Sardhana",
        "latitude": 28.9845,
        "longitude": 77.7064,
        "soil_type": "Alluvial",
        "irrigation_type": "canal",
        "crops": ["Wheat", "Rice", "Sugarcane", "Potato", "Onion"]
    },
    {
        "state": "Maharashtra",
        "district": "Nashik",
        "village": "Igatpuri",
        "latitude": 19.6956,
        "longitude": 73.5603,
        "soil_type": "Black Cotton",
        "irrigation_type": "drip",
        "crops": ["Grapes", "Onion", "Tomato", "Sugarcane", "Cotton"]
    },
    {
        "state": "Karnataka",
        "district": "Mysore",
        "village": "Nanjangud",
        "latitude": 12.1200,
        "longitude": 76.6800,
        "soil_type": "Red Sandy",
        "irrigation_type": "sprinkler",
        "crops": ["Ragi", "Jowar", "Maize", "Sugarcane", "Turmeric"]
    },
    {
        "state": "Tamil Nadu",
        "district": "Coimbatore",
        "village": "Pollachi",
        "latitude": 10.6576,
        "longitude": 77.0075,
        "soil_type": "Red Loam",
        "irrigation_type": "drip",
        "crops": ["Cotton", "Sugarcane", "Turmeric", "Coconut", "Banana"]
    },
    {
        "state": "Gujarat",
        "district": "Anand",
        "village": "Charotar",
        "latitude": 22.5645,
        "longitude": 72.9289,
        "soil_type": "Alluvial",
        "irrigation_type": "canal",
        "crops": ["Cotton", "Groundnut", "Wheat", "Maize", "Sugarcane"]
    },
    {
        "state": "Rajasthan",
        "district": "Kota",
        "village": "Bundi",
        "latitude": 25.4418,
        "longitude": 75.6404,
        "soil_type": "Desert",
        "irrigation_type": "tubewell",
        "crops": ["Bajra", "Wheat", "Mustard", "Guar", "Cotton"]
    }
]

# Sample user data
USERS_DATA = [
    {
        "username": "rajesh_kumar",
        "email": "rajesh.kumar@example.com",
        "password": "password123",
        "full_name": "Rajesh Kumar",
        "phone": "+91-9876543210"
    },
    {
        "username": "priya_sharma",
        "email": "priya.sharma@example.com",
        "password": "password123",
        "full_name": "Priya Sharma",
        "phone": "+91-9876543211"
    },
    {
        "username": "amit_patel",
        "email": "amit.patel@example.com",
        "password": "password123",
        "full_name": "Amit Patel",
        "phone": "+91-9876543212"
    },
    {
        "username": "sunita_reddy",
        "email": "sunita.reddy@example.com",
        "password": "password123",
        "full_name": "Sunita Reddy",
        "phone": "+91-9876543213"
    },
    {
        "username": "vikram_singh",
        "email": "vikram.singh@example.com",
        "password": "password123",
        "full_name": "Vikram Singh",
        "phone": "+91-9876543214"
    },
    {
        "username": "meera_iyer",
        "email": "meera.iyer@example.com",
        "password": "password123",
        "full_name": "Meera Iyer",
        "phone": "+91-9876543215"
    },
    {
        "username": "dinesh_joshi",
        "email": "dinesh.joshi@example.com",
        "password": "password123",
        "full_name": "Dinesh Joshi",
        "phone": "+91-9876543216"
    },
    {
        "username": "kavita_mehta",
        "email": "kavita.mehta@example.com",
        "password": "password123",
        "full_name": "Kavita Mehta",
        "phone": "+91-9876543217"
    }
]

def create_dummy_users_and_farms(db: Session):
    """Create dummy users and farms"""
    print("Creating dummy users and farms...")
    
    for i, user_data in enumerate(USERS_DATA):
        # Create user
        user = User(
            username=user_data["username"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            phone=user_data["phone"],
            is_active=True,
            is_verified=True
        )
        user.set_password(user_data["password"])
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Get region data
        region = INDIAN_REGIONS[i % len(INDIAN_REGIONS)]
        
        # Create farm
        farm = Farm(
            name=f"{user.full_name}'s Farm",
            location=f"{region['village']}, {region['district']}, {region['state']}",
            size_acres=random.uniform(5.0, 25.0),  # 5-25 acres
            farmer_name=user.full_name,
            farmer_phone=user.phone,
            farmer_email=user.email
        )
        db.add(farm)
        db.commit()
        db.refresh(farm)
        
        # Create soil test
        soil_test = SoilTest(
            farm_id=farm.id,
            test_date=datetime.now() - timedelta(days=random.randint(30, 90)),
            ph_level=random.uniform(6.0, 8.5),
            nitrogen_ppm=random.uniform(20, 80),
            phosphorus_ppm=random.uniform(10, 50),
            potassium_ppm=random.uniform(100, 300),
            organic_matter_percent=random.uniform(0.5, 3.0),
            soil_texture=region["soil_type"],
            test_lab="Regional Soil Testing Laboratory"
        )
        db.add(soil_test)
        
        # Create crops
        crop_names = region["crops"]
        for j, crop_name in enumerate(crop_names[:3]):  # Create 3 crops per farm
            planting_date = datetime.now() - timedelta(days=random.randint(30, 120))
            expected_harvest = planting_date + timedelta(days=random.randint(90, 180))
            
            crop = Crop(
                farm_id=farm.id,
                crop_type=crop_name,
                variety=f"{crop_name} Variety {j+1}",
                planting_date=planting_date,
                expected_harvest_date=expected_harvest,
                area_acres=random.uniform(1.0, 5.0),
                status=random.choice(["planted", "growing", "harvested"])
            )
            db.add(crop)
            db.commit()
            db.refresh(crop)
            
            # Create tasks for the crop
            task_types = ["planting", "fertilizing", "irrigation", "pest_control", "harvesting"]
            for k, task_type in enumerate(task_types):
                task_date = planting_date + timedelta(days=k * 30)
                if task_date <= datetime.now():
                    task = Task(
                        farm_id=farm.id,
                        crop_id=crop.id,
                        task_type=task_type,
                        title=f"{task_type.title()} for {crop_name}",
                        description=f"Perform {task_type} for {crop_name} in field {j+1}",
                        scheduled_date=task_date,
                        completed_date=task_date + timedelta(days=random.randint(1, 3)) if random.random() > 0.3 else None,
                        priority=random.choice(["low", "medium", "high"]),
                        status=random.choice(["completed", "pending", "in_progress"]),
                        cost=random.uniform(500, 5000)
                    )
                    db.add(task)
            
            # Create yield if crop is harvested
            if crop.status == "harvested" and random.random() > 0.5:
                yield_data = Yield(
                    crop_id=crop.id,
                    harvest_date=expected_harvest + timedelta(days=random.randint(-10, 10)),
                    quantity_tons=random.uniform(2.0, 15.0),
                    quality_grade=random.choice(["A", "B", "C"]),
                    moisture_percent=random.uniform(8, 15),
                    price_per_ton=random.uniform(15000, 35000),
                    total_value=random.uniform(30000, 500000)
                )
                db.add(yield_data)
        
        print(f"Created user: {user.full_name} from {region['state']}")
    
    db.commit()
    print("Dummy data creation completed!")

def main():
    """Main function to create dummy data"""
    db = next(get_db())
    try:
        create_dummy_users_and_farms(db)
    except Exception as e:
        print(f"Error creating dummy data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
