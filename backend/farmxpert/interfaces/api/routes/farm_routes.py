from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from farmxpert.models.database import get_db
from farmxpert.repositories.farm_repository import FarmRepository
from farmxpert.interfaces.api.schemas.farm_schemas import (
    FarmCreate, FarmResponse, TaskCreate, TaskResponse, 
    CropCreate, CropResponse, SoilTestCreate, SoilTestResponse
)

router = APIRouter(prefix="/api/farms", tags=["farms"])

@router.get("/{farm_id}/summary")
async def get_farm_summary(farm_id: int, db: Session = Depends(get_db)):
    """Get farm summary with key metrics"""
    try:
        farm_repo = FarmRepository(db)
        summary = farm_repo.get_farm_summary(farm_id)
        
        if not summary:
            raise HTTPException(status_code=404, detail="Farm not found")
        
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{farm_id}")
async def get_farm(farm_id: int, db: Session = Depends(get_db)):
    """Get farm details"""
    try:
        farm_repo = FarmRepository(db)
        farm = farm_repo.get_farm(farm_id)
        
        if not farm:
            raise HTTPException(status_code=404, detail="Farm not found")
        
        return {
            "id": farm.id,
            "name": farm.name,
            "location": farm.location,
            "size_acres": farm.size_acres,
            "farmer_name": farm.farmer_name,
            "farmer_phone": farm.farmer_phone,
            "farmer_email": farm.farmer_email,
            "created_at": farm.created_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_farm(farm_data: FarmCreate, db: Session = Depends(get_db)):
    """Create a new farm"""
    try:
        farm_repo = FarmRepository(db)
        farm = farm_repo.create_farm(farm_data.dict())
        
        return {
            "id": farm.id,
            "name": farm.name,
            "location": farm.location,
            "size_acres": farm.size_acres,
            "farmer_name": farm.farmer_name,
            "message": "Farm created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{farm_id}/tasks")
async def get_farm_tasks(
    farm_id: int, 
    status: str = None, 
    db: Session = Depends(get_db)
):
    """Get farm tasks"""
    try:
        farm_repo = FarmRepository(db)
        tasks = farm_repo.get_farm_tasks(farm_id, status=status)
        
        return [
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "task_type": task.task_type,
                "scheduled_date": task.scheduled_date,
                "completed_date": task.completed_date,
                "priority": task.priority,
                "status": task.status,
                "assigned_to": task.assigned_to,
                "cost": task.cost
            }
            for task in tasks
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{farm_id}/tasks")
async def create_task(
    farm_id: int, 
    task_data: TaskCreate, 
    db: Session = Depends(get_db)
):
    """Create a new task"""
    try:
        farm_repo = FarmRepository(db)
        task_data_dict = task_data.dict()
        task_data_dict['farm_id'] = farm_id
        
        task = farm_repo.create_task(task_data_dict)
        
        return {
            "id": task.id,
            "title": task.title,
            "scheduled_date": task.scheduled_date,
            "status": task.status,
            "message": "Task created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/tasks/{task_id}/complete")
async def complete_task(task_id: int, db: Session = Depends(get_db)):
    """Mark task as completed"""
    try:
        farm_repo = FarmRepository(db)
        task = farm_repo.update_task_status(task_id, "completed")
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {"message": "Task completed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{farm_id}/crops")
async def get_farm_crops(
    farm_id: int, 
    status: str = None, 
    db: Session = Depends(get_db)
):
    """Get farm crops"""
    try:
        farm_repo = FarmRepository(db)
        crops = farm_repo.get_farm_crops(farm_id, status=status)
        
        return [
            {
                "id": crop.id,
                "crop_type": crop.crop_type,
                "variety": crop.variety,
                "planting_date": crop.planting_date,
                "expected_harvest_date": crop.expected_harvest_date,
                "area_acres": crop.area_acres,
                "status": crop.status,
                "seed_quantity": crop.seed_quantity,
                "seed_cost": crop.seed_cost
            }
            for crop in crops
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{farm_id}/crops")
async def create_crop(
    farm_id: int, 
    crop_data: CropCreate, 
    db: Session = Depends(get_db)
):
    """Create a new crop"""
    try:
        farm_repo = FarmRepository(db)
        crop_data_dict = crop_data.dict()
        crop_data_dict['farm_id'] = farm_id
        
        crop = farm_repo.create_crop(crop_data_dict)
        
        return {
            "id": crop.id,
            "crop_type": crop.crop_type,
            "area_acres": crop.area_acres,
            "status": crop.status,
            "message": "Crop created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{farm_id}/soil-tests")
async def get_soil_tests(farm_id: int, db: Session = Depends(get_db)):
    """Get soil test history"""
    try:
        farm_repo = FarmRepository(db)
        soil_tests = farm_repo.get_soil_test_history(farm_id)
        
        return [
            {
                "id": test.id,
                "test_date": test.test_date,
                "ph_level": test.ph_level,
                "nitrogen_ppm": test.nitrogen_ppm,
                "phosphorus_ppm": test.phosphorus_ppm,
                "potassium_ppm": test.potassium_ppm,
                "organic_matter_percent": test.organic_matter_percent,
                "soil_texture": test.soil_texture,
                "test_lab": test.test_lab,
                "notes": test.notes
            }
            for test in soil_tests
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{farm_id}/soil-tests")
async def create_soil_test(
    farm_id: int, 
    soil_test_data: SoilTestCreate, 
    db: Session = Depends(get_db)
):
    """Create a new soil test"""
    try:
        farm_repo = FarmRepository(db)
        soil_test_data_dict = soil_test_data.dict()
        soil_test_data_dict['farm_id'] = farm_id
        
        soil_test = farm_repo.create_soil_test(soil_test_data_dict)
        
        return {
            "id": soil_test.id,
            "test_date": soil_test.test_date,
            "ph_level": soil_test.ph_level,
            "message": "Soil test created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
