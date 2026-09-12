"""
Task Schedule Routes
Provides endpoints for AI-powered Daily Task generation, retrieval, and completion.
Ensures validation, database persistence, duplicate protection, and transaction safety.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

from pydantic import BaseModel, Field, field_validator

from farmxpert.models.database import get_db
from farmxpert.models.user_models import User
from farmxpert.models.farm_models import Farm, Field as FarmField, Crop, SoilTest, Task, FarmTask
from farmxpert.models.farm_profile_models import FarmProfile
from farmxpert.interfaces.api.routes.auth_routes import get_current_user
from farmxpert.agents.operations.task_scheduler_agent import TaskSchedulerAgent

logger = logging.getLogger("task_routes")

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskStatusUpdate(BaseModel):
    is_completed: bool


class GeneratedTaskValidator(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = ""
    category: str = "other"
    priority: str = "medium"

    @field_validator("title")
    @classmethod
    def clean_title(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Task title cannot be empty")
        return s[:255]

    @field_validator("category")
    @classmethod
    def clean_category(cls, v: str) -> str:
        allowed = {"irrigation", "pest", "fertilizer", "harvest", "maintenance", "other"}
        s = (v or "").lower().strip()
        return s if s in allowed else "other"

    @field_validator("priority")
    @classmethod
    def clean_priority(cls, v: str) -> str:
        allowed = {"high", "medium", "low"}
        s = (v or "").lower().strip()
        return s if s in allowed else "medium"


def _format_task_item(t: FarmTask) -> Dict[str, Any]:
    return {
        "id": t.id,
        "title": t.title,
        "description": t.description or "",
        "category": t.category or "other",
        "priority": t.priority or "medium",
        "is_completed": bool(t.is_completed),
        "scheduled_date": t.scheduled_date.isoformat() if t.scheduled_date else datetime.utcnow().isoformat(),
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


@router.post("/generate")
async def generate_daily_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Generate daily tasks for the user using the TaskSchedulerAgent.
    Gathers real farm data, crops, and telemetry, validates output,
    persists tasks atomically to PostgreSQL/SQLite, and prevents duplicate tasks.
    """
    try:
        logger.info(f"Generating daily tasks for user_id={current_user.id}")

        # 1. Resolve Farm and Profile Information
        crop_name = "Field Crops"
        location_str = "Regional Farm"
        farm_size = ""
        growth_stage = "Vegetative"

        # Check Farm table
        farm = None
        try:
            farm = db.query(Farm).filter(Farm.user_id == current_user.id).first()
            if not farm and hasattr(current_user, "username"):
                farm = db.query(Farm).first()
        except Exception as e:
            logger.warning(f"Error querying Farm: {e}")

        # Check FarmProfile (from onboarding)
        farm_profile = None
        try:
            farm_profile = db.query(FarmProfile).filter(FarmProfile.user_id == current_user.id).first()
        except Exception as e:
            logger.warning(f"Error querying FarmProfile: {e}")

        # Extract Onboarding Data from user model if present
        user_onboarding = getattr(current_user, 'onboarding_data', {})
        if not isinstance(user_onboarding, dict):
            user_onboarding = {}

        # Resolve Crop Name
        if farm and farm.crop_type:
            crop_name = farm.crop_type
        elif farm_profile and farm_profile.specific_crop:
            crop_name = farm_profile.specific_crop
        elif farm_profile and farm_profile.primary_crops and isinstance(farm_profile.primary_crops, list):
            crop_name = farm_profile.primary_crops[0]
        elif user_onboarding.get('specificCrop'):
            crop_name = user_onboarding.get('specificCrop')
        elif user_onboarding.get('mainCropCategory'):
            crop_name = user_onboarding.get('mainCropCategory')

        # Check active crops table
        if farm:
            try:
                active_crop = db.query(Crop).filter(Crop.farm_id == farm.id).order_by(Crop.created_at.desc()).first()
                if active_crop and active_crop.crop_type:
                    crop_name = active_crop.crop_type
            except Exception:
                pass

        # Resolve Location & Farm Size
        if farm and (farm.district or farm.state):
            location_str = f"{farm.district or ''}, {farm.state or ''}".strip(", ")
        elif farm_profile and (farm_profile.district or farm_profile.state or farm_profile.location):
            location_str = farm_profile.location or f"{farm_profile.district or ''}, {farm_profile.state or ''}".strip(", ")
        elif user_onboarding.get('state'):
            location_str = user_onboarding.get('state')

        if farm_profile and farm_profile.farm_size:
            farm_size = f"{farm_profile.farm_size} {farm_profile.farm_size_unit or 'acres'}"
        elif user_onboarding.get('farmSize'):
            farm_size = f"{user_onboarding.get('farmSize')} acres"

        # 2. Retrieve Soil & Sensor Telemetry
        soil_data: Dict[str, Any] = {}
        if farm:
            try:
                latest_soil = (
                    db.query(SoilTest)
                    .filter(SoilTest.farm_id == farm.id)
                    .order_by(SoilTest.test_date.desc())
                    .first()
                )
                if latest_soil:
                    soil_data = {
                        "moisture": float(latest_soil.soil_moisture) if latest_soil.soil_moisture is not None else None,
                        "ph": float(latest_soil.soil_ph) if latest_soil.soil_ph is not None else None,
                        "temperature": float(latest_soil.soil_temperature) if latest_soil.soil_temperature is not None else None,
                        "nitrogen": float(latest_soil.nitrogen) if latest_soil.nitrogen is not None else None,
                        "phosphorus": float(latest_soil.phosphorus) if latest_soil.phosphorus is not None else None,
                        "potassium": float(latest_soil.potassium) if latest_soil.potassium is not None else None,
                    }
            except Exception as e:
                logger.warning(f"Could not retrieve SoilTest for task generation: {e}")

        # Check Blynk SensorReading if soil_data still empty
        if not soil_data and farm:
            try:
                from farmxpert.models.blynk_models import SensorReading
                reading = (
                    db.query(SensorReading)
                    .filter(SensorReading.farm_id == farm.id)
                    .order_by(SensorReading.recorded_at.desc())
                    .first()
                )
                if reading:
                    soil_data = {
                        "moisture": float(reading.soil_moisture) if reading.soil_moisture is not None else None,
                        "ph": float(reading.soil_ph) if reading.soil_ph is not None else None,
                        "nitrogen": float(reading.nitrogen) if reading.nitrogen is not None else None,
                    }
            except Exception:
                pass

        # 3. Call TaskSchedulerAgent
        agent = TaskSchedulerAgent()
        generated_tasks_raw = await agent.generate_daily_tasks(
            crop=crop_name,
            growth_stage=growth_stage,
            soil_data=soil_data,
            location=location_str,
            farm_size=farm_size
        )

        if not generated_tasks_raw or not isinstance(generated_tasks_raw, list):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Task Scheduler Agent failed to generate daily tasks."
            )

        # 4. Duplicate Protection & Idempotent Persistence
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        existing_today_tasks = (
            db.query(FarmTask)
            .filter(
                FarmTask.user_id == current_user.id,
                FarmTask.scheduled_date >= today_start,
                FarmTask.scheduled_date < today_end
            )
            .all()
        )

        existing_titles = {t.title.strip().lower() for t in existing_today_tasks}

        new_saved_tasks = []
        for raw_item in generated_tasks_raw:
            if not isinstance(raw_item, dict):
                continue

            try:
                validated = GeneratedTaskValidator(**raw_item)
            except Exception as val_err:
                logger.warning(f"Skipping malformed generated task: {raw_item} (Error: {val_err})")
                continue

            # Check uniqueness against existing tasks for today
            if validated.title.lower() in existing_titles:
                logger.info(f"Duplicate task detected for today, skipping: '{validated.title}'")
                continue

            # Persist to FarmTask (for the daily checklist)
            new_task = FarmTask(
                user_id=current_user.id,
                title=validated.title,
                description=validated.description,
                category=validated.category,
                priority=validated.priority,
                scheduled_date=datetime.utcnow(),
                is_completed=False,
                created_at=datetime.utcnow()
            )
            db.add(new_task)
            new_saved_tasks.append(new_task)
            existing_titles.add(validated.title.lower())

            # Also sync to core Task table if farm is identified
            if farm:
                try:
                    new_core_task = Task(
                        farm_id=farm.id,
                        task_type=validated.category,
                        title=validated.title,
                        description=validated.description,
                        priority=validated.priority,
                        status="pending",
                        scheduled_date=datetime.utcnow(),
                        created_at=datetime.utcnow()
                    )
                    db.add(new_core_task)
                except Exception as core_err:
                    logger.warning(f"Could not mirror task to core Task model: {core_err}")

        # Atomic commit
        db.commit()

        # If new tasks were added, return all current tasks for today (new + existing)
        all_today_tasks = (
            db.query(FarmTask)
            .filter(FarmTask.user_id == current_user.id)
            .order_by(FarmTask.is_completed.asc(), FarmTask.created_at.desc())
            .limit(10)
            .all()
        )

        return [_format_task_item(t) for t in all_today_tasks]

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Error generating daily tasks: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating daily tasks: {str(e)}"
        )


@router.get("/today")
async def get_today_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get latest daily tasks for the authenticated farmer."""
    try:
        tasks = (
            db.query(FarmTask)
            .filter(FarmTask.user_id == current_user.id)
            .order_by(FarmTask.is_completed.asc(), FarmTask.created_at.desc())
            .limit(15)
            .all()
        )
        return [_format_task_item(t) for t in tasks]

    except Exception as e:
        logger.error(f"Error fetching today tasks: {e}", exc_info=True)
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
    """Toggle the completion status of a task with transaction safety."""
    try:
        task = db.query(FarmTask).filter(FarmTask.id == task_id, FarmTask.user_id == current_user.id).first()

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        task.is_completed = status_update.is_completed
        task.completed_at = datetime.utcnow() if status_update.is_completed else None
        task.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(task)

        return {
            "id": task.id,
            "is_completed": task.is_completed,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Error updating task: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating task: {str(e)}"
        )
