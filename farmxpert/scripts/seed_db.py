
import sys
import os
from datetime import datetime, timedelta
import random

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from farmxpert.models.database import SessionLocal, engine, Base
from farmxpert.models.farm_models import Farm, Field, SoilTest, Crop, Task, WeatherData, MarketPrice

def seed_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if farm exists
        farm = db.query(Farm).filter(Farm.id == 1).first()
        if farm:
            print("Farm ID 1 already exists. Skipping seed.")
            return

        print("Seeding database...")
        
        # Create Farm
        farm = Farm(
            name="Krishna Farm",
            location="Ahmedabad, Gujarat",
            size_acres=15.0,
            farmer_name="Krishna Patel",
            farmer_phone="+91-9876543210",
            farmer_email="krishna.patel@example.com"
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
                ph_level=random.uniform(6.5, 7.5),
                nitrogen_ppm=random.uniform(20, 50),
                phosphorus_ppm=random.uniform(15, 40),
                potassium_ppm=random.uniform(100, 200),
                organic_matter_percent=random.uniform(0.5, 2.0),
                soil_texture=field.soil_type,
                test_lab="Gujarat State Lab",
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

        print("Database seeded successfully with Krishna Farm data!")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
