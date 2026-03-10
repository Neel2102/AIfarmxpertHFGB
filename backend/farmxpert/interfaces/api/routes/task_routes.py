"""
Task Schedule Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any, List

from farmxpert.models.database import get_db
from farmxpert.models.user_models import User
from farmxpert.models.farm_models import FarmTask, SoilTest
from farmxpert.models.farm_profile_models import FarmProfile
from farmxpert.interfaces.api.routes.auth_routes import get_current_user
from farmxpert.agents.operations.task_scheduler_agent import TaskSchedulerAgent
from farmxpert.app.shared.utils import logger
from pydantic import BaseModel

router = APIRouter(prefix="/tasks", tags=["tasks"])

class TaskStatusUpdate(BaseModel):
    is_completed: bool

@router.post("/generate")
async def generate_daily_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Generate 3 daily tasks for the user using the TaskSchedulerAgent."""
    try:
        # Determine crop and state
        crop_name = "Unknown Crop"
        state = "Unknown Location"
        farm_size = ""
        
        # User is already current_user. We just need to check onboarding_data.
        profile = getattr(current_user, 'onboarding_data', {})
        if not isinstance(profile, dict):
            profile = {}

        if profile:
            if profile.get('specificCrop'):
                crop_name = profile.get('specificCrop')
            elif profile.get('mainCropCategory'):
                crop_name = profile.get('mainCropCategory')
            
            if profile.get('state'):
                state = profile.get('state')
                
            if profile.get('farmSize'):
                farm_size = f"{profile.get('farmSize')} acres"
                
        # To get SensorReading we need to know the farm
        soil_test = None
        from farmxpert.models.farm_models import Farm
        from farmxpert.models.blynk_models import SensorReading
        
        farm = db.query(Farm).filter(Farm.farmer_name == current_user.username).first()
        if farm:
            soil_test = (
                db.query(SensorReading)
                .filter(SensorReading.farm_id == farm.id)
                .order_by(SensorReading.recorded_at.desc())
                .first()
            )
                
        soil_data = {}
        if soil_test:
            soil_data = {
                "moisture": float(soil_test.soil_moisture) if soil_test.soil_moisture else None,
                "ph": float(soil_test.soil_ph) if soil_test.soil_ph else None,
                "n": float(soil_test.nitrogen) if soil_test.nitrogen else None,
                "p": float(soil_test.phosphorus) if soil_test.phosphorus else None,
                "k": float(soil_test.potassium) if soil_test.potassium else None
            }
            
        # Call TaskSchedulerAgent helper method specifically meant for quick Daily Tasks
        agent = TaskSchedulerAgent()
        generated_tasks = await agent.generate_daily_tasks(
            crop=crop_name,
            growth_stage="Vegetative", # simplified for demo
            soil_data=soil_data,
            location=state,
            farm_size=farm_size
        )
        
        if not generated_tasks or len(generated_tasks) == 0:
            raise HTTPException(status_code=500, detail="Agent failed to generate tasks")
            
        # Save to database
        tasks_to_return = []
        for task_dict in generated_tasks:
            new_task = FarmTask(
                user_id=current_user.id,
                title=task_dict.get("title", "Farm Task"),
                description=task_dict.get("description", ""),
                category=task_dict.get("category", "other"),
                priority=task_dict.get("priority", "medium"),
                scheduled_date=datetime.utcnow()
            )
            db.add(new_task)
            db.commit()
            db.refresh(new_task)
            
            tasks_to_return.append({
                "id": new_task.id,
                "title": new_task.title,
                "description": new_task.description,
                "category": new_task.category,
                "priority": new_task.priority,
                "is_completed": new_task.is_completed,
                "scheduled_date": new_task.scheduled_date.isoformat()
            })
            
        return tasks_to_return
        
    except Exception as e:
        logger.error(f"Error generating tasks: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating tasks: {str(e)}"
        )

@router.get("/today")
async def get_today_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get all tasks scheduled for today or earlier that are not completed."""
    try:
        tasks = (
            db.query(FarmTask)
            .filter(FarmTask.user_id == current_user.id)
            .order_by(FarmTask.created_at.desc())
            .limit(10) # Get latest 10 tasks to act as "today's tasks"
            .all()
        )
        
        return [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "category": t.category,
                "priority": t.priority,
                "is_completed": t.is_completed,
                "scheduled_date": t.scheduled_date.isoformat()
            }
            for t in tasks
        ]
        
    except Exception as e:
        logger.error(f"Error fetching today tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching tasks: {str(e)}"
        )

@router.patch("/{task_id}/complete")
async def complete_task(
    task_id: int,
    status_update: TaskStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Toggle the completion status of a task."""
    try:
        task = db.query(FarmTask).filter(FarmTask.id == task_id, FarmTask.user_id == current_user.id).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
            
        task.is_completed = status_update.is_completed
        task.completed_at = datetime.utcnow() if status_update.is_completed else None
        
        db.commit()
        
        return {
            "id": task.id,
            "is_completed": task.is_completed,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating task: {str(e)}"
        )
