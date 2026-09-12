"""
Task Schedule Routes
Provides endpoints for AI-powered Daily Task generation, retrieval, and completion.
Ensures validation, database persistence, duplicate protection, and transaction safety.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import logging

from pydantic import BaseModel, Field, field_validator

from farmxpert.models.database import get_db
from farmxpert.models.user_models import User
from farmxpert.models.farm_models import Farm, Field as FarmField, Crop, SoilTest, Task, FarmTask
from farmxpert.models.farm_profile_models import FarmProfile
from farmxpert.interfaces.api.routes.auth_routes import get_current_user
from farmxpert.agents.operations.task_scheduler_agent import TaskSchedulerAgent
from farmxpert.services.daily_flow_service import DailyFlowService

logger = logging.getLogger("task_routes")

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskStatusUpdate(BaseModel):
    is_completed: bool


class FlowGenerateRequest(BaseModel):
    farm_id: Optional[int] = None
    crop_id: Optional[int] = None
    planting_date: Optional[str] = None


def _resolve_farm_and_crop(
    db: Session,
    current_user: User,
    farm_id: Optional[int] = None,
    crop_id: Optional[int] = None
) -> Tuple[Farm, Crop]:
    farm = None
    if farm_id:
        farm = db.query(Farm).filter(Farm.id == farm_id, Farm.user_id == current_user.id).first()
    if not farm:
        farm = db.query(Farm).filter(Farm.user_id == current_user.id).first()
    if not farm:
        # Check FarmProfile for user's configured details
        profile = db.query(FarmProfile).filter(FarmProfile.user_id == current_user.id).first()
        farm_name = profile.farm_name if profile and profile.farm_name else f"{current_user.full_name or 'My'} Farm"
        crop_type = (profile.specific_crop or (profile.primary_crops[0] if profile.primary_crops and isinstance(profile.primary_crops, list) and len(profile.primary_crops) > 0 else "Cotton")) if profile else "Cotton"
        state = profile.state if profile and profile.state else "Gujarat"
        district = profile.district if profile and profile.district else "Rajkot"
        village = profile.village if profile and profile.village else ""
        soil_type = profile.soil_type if profile and profile.soil_type else "Black Soil"

        # Ensure AuthUser exists if required by DB relationships
        try:
            from farmxpert.models.user_models import AuthUser
            au = db.query(AuthUser).filter(AuthUser.id == current_user.id).first()
            if not au:
                au = AuthUser(
                    id=current_user.id,
                    farmer_id=f"FRM{current_user.id:04d}",
                    email=current_user.email,
                    username=current_user.username,
                    name=current_user.full_name or current_user.username,
                    phone=current_user.phone,
                    password_hash=current_user.hashed_password,
                    role=getattr(current_user, "role", "farmer"),
                )
                db.add(au)
                db.flush()
        except Exception as au_err:
            logger.warning(f"AuthUser sync note: {au_err}")

        farm = Farm(
            user_id=current_user.id,
            farm_name=farm_name,
            crop_type=crop_type,
            state=state,
            district=district,
            village=village,
            soil_type=soil_type,
            size_acres=5.0
        )
        if profile and profile.latitude is not None and profile.longitude is not None:
            farm.latitude = profile.latitude
            farm.longitude = profile.longitude

        db.add(farm)
        db.commit()
        db.refresh(farm)

    crop = None
    if crop_id:
        crop = db.query(Crop).filter(Crop.id == crop_id, Crop.farm_id == farm.id).first()
    if not crop:
        crop = DailyFlowService.get_or_create_active_crop(db, farm, current_user)

    return farm, crop


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
            detail="Unable to generate daily tasks at this time. Please try again."
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
            detail="Unable to load today's tasks. Please try again."
        )


@router.get("/farms-and-crops")
async def get_farms_and_crops(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Retrieve user's farms and their registered crops for Daily Flow selection."""
    try:
        farms = db.query(Farm).filter(Farm.user_id == current_user.id).all()
        if not farms:
            f, _ = _resolve_farm_and_crop(db, current_user)
            farms = [f] if f else []

        result_farms = []
        for f in farms:
            crops = db.query(Crop).filter(Crop.farm_id == f.id).all()
            if not crops:
                # Initialize active crop if missing
                c = DailyFlowService.get_or_create_active_crop(db, f, current_user)
                crops = [c]

            result_farms.append({
                "id": f.id,
                "name": f.farm_name or f.name or "My Farm",
                "location": f"{f.district or ''}, {f.state or ''}".strip(", ") or (f.location or "Regional Farm"),
                "crops": [
                    {
                        "id": c.id,
                        "crop_type": c.crop_type,
                        "variety": c.variety or "Standard",
                        "planting_date": c.planting_date.isoformat() if c.planting_date else None,
                        "expected_harvest_date": c.expected_harvest_date.isoformat() if c.expected_harvest_date else None,
                        "status": c.status or "growing"
                    }
                    for c in crops
                ]
            })

        active_farm = farms[0] if farms else None
        active_crop_id = None
        if active_farm and result_farms and result_farms[0]["crops"]:
            active_crop_id = result_farms[0]["crops"][0]["id"]

        return {
            "success": True,
            "farms": result_farms,
            "active_farm_id": active_farm.id if active_farm else None,
            "active_crop_id": active_crop_id
        }
    except Exception as e:
        logger.error(f"Error getting farms and crops: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve farm details. Please try again."
        )


@router.get("/daily-flow")
async def get_daily_flow(
    farm_id: Optional[int] = None,
    crop_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get full partitioned Daily Flow for the active crop season:
    returns today, tomorrow, upcoming 7 days, stage-by-stage season flow, overdue, and completed tasks.
    """
    try:
        farm, crop = _resolve_farm_and_crop(db, current_user, farm_id, crop_id)
        return DailyFlowService.get_partitioned_daily_flow(db, farm, crop, current_user)
    except Exception as e:
        logger.error(f"Error fetching daily flow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve your daily flow schedule. Please try again or generate a new season flow."
        )


@router.post("/daily-flow/generate")
async def generate_daily_flow(
    req: Optional[FlowGenerateRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generate or regenerate the season-long farming plan and upcoming daily tasks.
    Synthesizes AI and agronomic rules based on real farm, soil, and crop telemetry.
    Persists idempotently without uncontrolled duplicates.
    """
    try:
        farm_id = req.farm_id if req else None
        crop_id = req.crop_id if req else None
        farm, crop = _resolve_farm_and_crop(db, current_user, farm_id, crop_id)

        if req and req.planting_date:
            try:
                crop.planting_date = datetime.fromisoformat(req.planting_date.replace("Z", "+00:00"))
                db.commit()
            except Exception as e:
                logger.warning(f"Could not parse custom planting date: {e}")

        # Gather real soil telemetry
        soil_data: Dict[str, Any] = {}
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
                "nitrogen": float(latest_soil.nitrogen) if latest_soil.nitrogen is not None else None,
                "phosphorus": float(latest_soil.phosphorus) if latest_soil.phosphorus is not None else None,
                "potassium": float(latest_soil.potassium) if latest_soil.potassium is not None else None,
            }

        duration = DailyFlowService.get_crop_duration(crop.crop_type, crop.variety)
        planting_dt = crop.planting_date or datetime.utcnow()
        timeline = DailyFlowService.calculate_season_timeline(planting_dt, duration)
        current_stage_name = timeline["current_stage"]["name"] if timeline.get("current_stage") else "Active Vegetative"

        location_str = f"{farm.district or ''}, {farm.state or ''}".strip(", ") or (farm.location or "Gujarat, India")

        # Generate seasonal tasks with AI + agronomic backup
        generated_tasks = await DailyFlowService.generate_season_plan_with_ai(
            crop_name=crop.crop_type,
            variety=crop.variety or "Standard",
            planting_date=planting_dt,
            duration_days=duration,
            current_stage=current_stage_name,
            days_since_planting=timeline["days_since_planting"],
            farm_location=location_str,
            soil_data=soil_data
        )

        # Persist idempotently
        DailyFlowService.persist_tasks_idempotently(
            db=db,
            farm=farm,
            crop=crop,
            user=current_user,
            generated_tasks=generated_tasks,
            planting_date=planting_dt
        )

        return DailyFlowService.get_partitioned_daily_flow(db, farm, crop, current_user)

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Error generating daily flow: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate season flow right now. Please verify your farm details and try again."
        )


@router.patch("/{task_id}/complete")
async def complete_task(
    task_id: int,
    status_update: TaskStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Toggle the completion status of a task across both Task and FarmTask tables atomically."""
    try:
        now_dt = datetime.utcnow()
        farm_task = db.query(FarmTask).filter(FarmTask.id == task_id, FarmTask.user_id == current_user.id).first()
        core_task = None

        if farm_task:
            farm_task.is_completed = status_update.is_completed
            farm_task.completed_at = now_dt if status_update.is_completed else None
            farm_task.updated_at = now_dt
            # Sync to core Task table by title
            core_task = db.query(Task).filter(Task.title == farm_task.title).first()
        else:
            core_task = db.query(Task).filter(Task.id == task_id).first()
            if core_task:
                farm_task = db.query(FarmTask).filter(FarmTask.title == core_task.title, FarmTask.user_id == current_user.id).first()

        if not farm_task and not core_task:
            raise HTTPException(status_code=404, detail="Task not found")

        if core_task:
            core_task.status = "completed" if status_update.is_completed else "pending"
            core_task.completed_date = now_dt if status_update.is_completed else None
            core_task.updated_at = now_dt

        if farm_task:
            farm_task.is_completed = status_update.is_completed
            farm_task.completed_at = now_dt if status_update.is_completed else None
            farm_task.updated_at = now_dt

        db.commit()

        target_id = farm_task.id if farm_task else core_task.id
        return {
            "id": target_id,
            "is_completed": status_update.is_completed,
            "status": "completed" if status_update.is_completed else "pending",
            "completed_at": now_dt.isoformat() if status_update.is_completed else None
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

