from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
from farmxpert.models.database import get_db
from farmxpert.models.farm_models import Farm, Task, Crop, SoilTest, Field

router = APIRouter()

@router.get("/{farm_id}")
async def get_farm(farm_id: int, db: Session = Depends(get_db)):
    try:
        farm = db.query(Farm).filter(Farm.id == farm_id).first()
        if not farm:
            raise HTTPException(status_code=404, detail="Farm not found")
        return farm
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{farm_id}/summary")
async def get_farm_summary(farm_id: int, db: Session = Depends(get_db)):
    try:
        # Calculate summary stats from DB
        total_crops = db.query(Crop).filter(Crop.farm_id == farm_id, Crop.status == "growing").count()
        active_tasks = db.query(Task).filter(Task.farm_id == farm_id, Task.status.in_(["pending", "in_progress"])).count()
        completed_tasks = db.query(Task).filter(Task.farm_id == farm_id, Task.status == "completed").count()
        
        # Determine soil health score based on latest test if available
        soil_score = 85 # Default fallback
        latest_test = db.query(SoilTest).filter(SoilTest.farm_id == farm_id).order_by(SoilTest.test_date.desc()).first()
        if latest_test:
            # Simple heuristic
            score = 0
            if 6.0 <= latest_test.ph_level <= 7.5: score += 40
            else: score += 20
            if latest_test.organic_matter_percent > 1.0: score += 30
            else: score += 10
            if latest_test.nitrogen_ppm > 20: score += 30
            else: score += 10
            soil_score = score

        return {
            "total_crops": total_crops,
            "active_tasks": active_tasks,
            "completed_tasks": completed_tasks,
            "soil_health_score": soil_score,
            "weather_alert": False, # Placeholder until weather integration
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@router.get("/{farm_id}/tasks")
async def get_farm_tasks(farm_id: int, status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Task).filter(Task.farm_id == farm_id)
    if status:
        query = query.filter(Task.status == status)
    return query.all()

@router.get("/{farm_id}/crops")
async def get_farm_crops(farm_id: int, status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Crop).filter(Crop.farm_id == farm_id)
    if status:
        query = query.filter(Crop.status == status)
    return query.all()

@router.get("/{farm_id}/soil-tests")
async def get_soil_tests(farm_id: int, db: Session = Depends(get_db)):
    return db.query(SoilTest).filter(SoilTest.farm_id == farm_id).order_by(SoilTest.test_date.desc()).all()
