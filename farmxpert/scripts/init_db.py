#!/usr/bin/env python3
"""
Database initialization script for FarmXpert
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from farmxpert.models.database import Base
from farmxpert.models.farm_models import *
from farmxpert.repositories.farm_repository import FarmRepository
from sqlalchemy.orm import sessionmaker
from farmxpert.config.settings import settings
from datetime import datetime, timedelta

def init_database():
    """Initialize database with tables and sample data"""
    print("Initializing FarmXpert database...")
    
    # Create engine
    engine = create_engine(settings.database_url)
    
    # Create all tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Create sample farm
        print("Creating sample farm...")
        farm_data = {
            "name": "Green Valley Farm",
            "location": "ahmedabad, India",
            "size_acres": 25.0,
            "farmer_name": "Rajinder Singh",
            "farmer_phone": "+91-98765-43210",
            "farmer_email": "rajinder@greenvalleyfarm.com"
        }
        
        farm_repo = FarmRepository(db)
        farm = farm_repo.create_farm(farm_data)
        print(f"Created farm: {farm.name}")
        
        # Create sample crop
        crop_data = {
            "farm_id": farm.id,
            "crop_type": "Wheat",
            "variety": "HD-2967",
            "planting_date": datetime.now() - timedelta(days=30),
            "expected_harvest_date": datetime.now() + timedelta(days=90),
            "area_acres": 10.0,
            "seed_quantity": 100.0,
            "seed_cost": 3000.0,
            "status": "growing"
        }
        
        crop = farm_repo.create_crop(crop_data)
        print(f"Created crop: {crop.crop_type}")
        
        # Create sample task
        task_data = {
            "farm_id": farm.id,
            "crop_id": crop.id,
            "task_type": "irrigation",
            "title": "Irrigate Wheat Field",
            "description": "Apply irrigation to wheat crop",
            "scheduled_date": datetime.now() + timedelta(days=2),
            "priority": "high",
            "status": "pending",
            "assigned_to": "Farm Worker 1",
            "cost": 500.0
        }
        
        task = farm_repo.create_task(task_data)
        print(f"Created task: {task.title}")
        
        print("\n✅ Database initialization completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during database initialization: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
