"""
Daily Flow and Seasonal Farming Plan Service.
Calculates season timeline, growth stages, real calendar dates,
and coordinates AI-powered and agronomic task scheduling.
"""

from __future__ import annotations
import re
import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from farmxpert.models.farm_models import Farm, Crop, Task, FarmTask, SoilTest
from farmxpert.models.farm_profile_models import FarmProfile
from farmxpert.models.user_models import User
from farmxpert.services.gemini_service import gemini_service

logger = logging.getLogger("daily_flow_service")

# Standard Crop Durations (days) from agronomic databases
DEFAULT_CROP_DURATIONS: Dict[str, int] = {
    "cotton": 160,
    "wheat": 120,
    "paddy": 135,
    "rice": 135,
    "maize": 110,
    "corn": 110,
    "soybean": 100,
    "groundnut": 115,
    "peanut": 115,
    "sugarcane": 330,
    "mustard": 115,
    "chickpea": 110,
    "gram": 110,
    "green gram": 65,
    "moong": 65,
    "black gram": 70,
    "urad": 70,
    "pigeon pea": 165,
    "tur": 165,
    "tomato": 130,
    "potato": 100,
    "onion": 135,
    "pearl millet": 85,
    "bajra": 85,
    "sorghum": 100,
    "jowar": 100,
    "chilli": 150,
}

# Standard Stage Proportions
STAGE_DEFINITIONS = [
    {
        "id": "sowing_germination",
        "name": "Sowing & Germination",
        "start_pct": 0.0,
        "end_pct": 0.10,
        "description": "Seedbed preparation, seed treatment, sowing, and seedling emergence."
    },
    {
        "id": "seedling_establishment",
        "name": "Seedling & Early Growth",
        "start_pct": 0.10,
        "end_pct": 0.25,
        "description": "Thinning, initial weed scouting, first irrigation, and root establishment."
    },
    {
        "id": "active_vegetative",
        "name": "Active Vegetative Growth",
        "start_pct": 0.25,
        "end_pct": 0.45,
        "description": "Canopy development, stem branching, primary nutrient top-dressing (Urea/NPK)."
    },
    {
        "id": "flowering_budding",
        "name": "Flowering & Budding",
        "start_pct": 0.45,
        "end_pct": 0.65,
        "description": "Critical reproductive phase, flower retention, micronutrient sprays, and pest vigilance."
    },
    {
        "id": "fruit_grain_development",
        "name": "Fruit / Boll / Grain Development",
        "start_pct": 0.65,
        "end_pct": 0.85,
        "description": "Pod/boll filling, grain weight increase, potassium fertilization, disease prevention."
    },
    {
        "id": "harvest_preparation",
        "name": "Maturity & Harvest Preparation",
        "start_pct": 0.85,
        "end_pct": 0.95,
        "description": "Moisture dry-down, pre-harvest irrigation cut-off, machinery and storage preparation."
    },
    {
        "id": "harvest_post_harvest",
        "name": "Harvest & Post-Harvest",
        "start_pct": 0.95,
        "end_pct": 1.0,
        "description": "Field harvest, threshing, grading, APMC mandi price comparison, and safe storage."
    }
]


class GeneratedTaskItem(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = ""
    category: str = "other"
    priority: str = "medium"
    day_offset: Optional[int] = 0
    stage_id: Optional[str] = None

    @field_validator("title")
    @classmethod
    def clean_title(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Title cannot be empty")
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


class DailyFlowService:
    """Core service for managing the season-long crop flow and daily task operations."""

    @staticmethod
    def get_or_create_active_crop(db: Session, farm: Farm, current_user: User) -> Crop:
        """
        Resolve the active crop for the farm, or create one based on farm/profile data or sensible defaults.
        Ensures all non-null DB constraints (area_acres) are fulfilled.
        """
        crop = db.query(Crop).filter(Crop.farm_id == farm.id, Crop.status == "growing").first()
        if not crop:
            crop = db.query(Crop).filter(Crop.farm_id == farm.id).first()

        if not crop:
            crop_name = getattr(farm, "crop_type", None)
            if not crop_name:
                profile = db.query(FarmProfile).filter(FarmProfile.user_id == current_user.id).first()
                if profile:
                    crop_name = profile.specific_crop or (
                        profile.primary_crops[0] if profile.primary_crops and isinstance(profile.primary_crops, list) and len(profile.primary_crops) > 0 else None
                    )
            if not crop_name:
                crop_name = "Cotton"

            duration = DailyFlowService.get_crop_duration(crop_name)
            # Default to 25 days into the season so active vegetative tasks exist
            planting_date = datetime.utcnow() - timedelta(days=25)
            expected_harvest = planting_date + timedelta(days=duration)

            crop = Crop(
                farm_id=farm.id,
                crop_type=crop_name,
                variety="Standard",
                planting_date=planting_date,
                expected_harvest_date=expected_harvest,
                area_acres=float(getattr(farm, "size_acres", None) or 5.0),
                status="growing"
            )
            db.add(crop)
            db.commit()
            db.refresh(crop)

        return crop

    @staticmethod
    def get_crop_duration(crop_name: str, variety: Optional[str] = None) -> int:
        """Derive standard crop duration in days."""
        clean = (crop_name or "").lower().strip()
        for k, v in DEFAULT_CROP_DURATIONS.items():
            if k in clean or clean in k:
                return v
        return 120  # Sensible default duration for general field crops

    @staticmethod
    def calculate_season_timeline(
        planting_date: datetime,
        duration_days: int,
        current_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Calculate actual calendar dates for each growth stage across the season.
        Handles leap years and month boundaries using proper Python datetime arithmetic.
        """
        if current_date is None:
            current_date = datetime.utcnow()

        today_d = current_date.date()
        planting_d = planting_date.date()
        harvest_d = planting_d + timedelta(days=duration_days)

        days_since_planting = (today_d - planting_d).days
        total_days = max(1, duration_days)
        progress_pct = max(0.0, min(100.0, round((days_since_planting / total_days) * 100, 1)))

        stages_output = []
        current_stage_info = None

        for idx, stage in enumerate(STAGE_DEFINITIONS):
            start_day = int(stage["start_pct"] * duration_days)
            end_day = duration_days if idx == len(STAGE_DEFINITIONS) - 1 else int(stage["end_pct"] * duration_days)
            
            stage_start_date = planting_d + timedelta(days=start_day)
            stage_end_date = planting_d + timedelta(days=end_day)

            if today_d > stage_end_date:
                status = "completed"
            elif stage_start_date <= today_d <= stage_end_date:
                status = "active"
            else:
                status = "upcoming"

            stage_duration = max(1, (stage_end_date - stage_start_date).days)
            if status == "completed":
                stage_prog = 100
            elif status == "upcoming":
                stage_prog = 0
            else:
                elapsed = (today_d - stage_start_date).days
                stage_prog = max(0, min(100, round((elapsed / stage_duration) * 100)))

            stage_data = {
                "id": stage["id"],
                "name": stage["name"],
                "description": stage["description"],
                "start_day": start_day,
                "end_day": end_day,
                "day_range": f"Days {start_day}–{end_day}",
                "start_date": stage_start_date.isoformat(),
                "end_date": stage_end_date.isoformat(),
                "status": status,
                "progress_pct": stage_prog,
                "tasks": []
            }
            stages_output.append(stage_data)

            if status == "active":
                current_stage_info = stage_data

        if not current_stage_info:
            if days_since_planting < 0:
                current_stage_info = {
                    "id": "pre_planting",
                    "name": "Pre-Planting Preparation",
                    "description": "Preparing field and procuring inputs prior to sowing.",
                    "status": "active"
                }
            else:
                current_stage_info = stages_output[-1]

        return {
            "planting_date": planting_d.isoformat(),
            "expected_harvest_date": harvest_d.isoformat(),
            "duration_days": duration_days,
            "days_since_planting": days_since_planting,
            "progress_pct": progress_pct,
            "current_stage": current_stage_info,
            "stages": stages_output
        }

    @staticmethod
    def get_or_create_active_crop(db: Session, farm: Farm, user: User) -> Crop:
        """
        Retrieves or initializes a Crop entity for the farm with valid planting dates.
        Ensures foreign keys are strictly database-governed and never hallucinated.
        """
        crop = db.query(Crop).filter(Crop.farm_id == farm.id).order_by(Crop.created_at.desc()).first()
        if crop and crop.planting_date:
            return crop

        # Fallback to Onboarding or Farm data
        crop_type = farm.crop_type or "Cotton"
        farm_profile = db.query(FarmProfile).filter(FarmProfile.user_id == user.id).first()
        if farm_profile and farm_profile.specific_crop:
            crop_type = farm_profile.specific_crop

        duration = DailyFlowService.get_crop_duration(crop_type)
        now = datetime.utcnow()
        planting_dt = now - timedelta(days=35)
        harvest_dt = planting_dt + timedelta(days=duration)

        if crop:
            crop.crop_type = crop.crop_type or crop_type
            if not crop.planting_date:
                crop.planting_date = planting_dt
                crop.expected_harvest_date = harvest_dt
            db.commit()
            db.refresh(crop)
            return crop

        new_crop = Crop(
            farm_id=farm.id,
            crop_type=crop_type,
            variety="Standard High-Yield",
            planting_date=planting_dt,
            expected_harvest_date=harvest_dt,
            area_acres=farm.size_acres or 5.0,
            status="growing",
            created_at=now
        )
        db.add(new_crop)
        db.commit()
        db.refresh(new_crop)
        logger.info(f"Created active crop id={new_crop.id} for farm_id={farm.id}")
        return new_crop

    @staticmethod
    async def generate_season_plan_with_ai(
        crop_name: str,
        variety: str,
        planting_date: datetime,
        duration_days: int,
        current_stage: str,
        days_since_planting: int,
        farm_location: str,
        soil_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generates structured milestone tasks across each growth stage using Gemini.
        Returns a list of validated task dictionaries.
        """
        prompt = f"""
You are an expert precision agronomist designing a seasonal crop management plan.
Farm Details:
- Crop: {crop_name} (Variety: {variety})
- Location: {farm_location}
- Total Duration: {duration_days} days
- Planting Date: {planting_date.strftime('%Y-%m-%d')}
- Current Day: Day {days_since_planting} of {duration_days}
- Current Stage: {current_stage}
- Soil Telemetry: {json.dumps(soil_data)}

Generate a comprehensive season flow consisting of:
1. Two to three critical tasks for TODAY and TOMORROW based on current stage and soil readings.
2. Two major milestone tasks for each of the following 7 stages across the cycle:
   - "sowing_germination" (Days 0–{int(0.10*duration_days)})
   - "seedling_establishment" (Days {int(0.10*duration_days)}–{int(0.25*duration_days)})
   - "active_vegetative" (Days {int(0.25*duration_days)}–{int(0.45*duration_days)})
   - "flowering_budding" (Days {int(0.45*duration_days)}–{int(0.65*duration_days)})
   - "fruit_grain_development" (Days {int(0.65*duration_days)}–{int(0.85*duration_days)})
   - "harvest_preparation" (Days {int(0.85*duration_days)}–{int(0.95*duration_days)})
   - "harvest_post_harvest" (Days {int(0.95*duration_days)}–{duration_days})

Return ONLY a valid JSON array of objects with NO markdown formatting or commentary.
Each task object MUST have:
- "title": string (Clear, specific action, e.g. "Apply second dose of Urea and verify soil moisture")
- "description": string (Detailed instruction with agronomic reason)
- "category": string (One of: "irrigation", "pest", "fertilizer", "harvest", "maintenance", "other")
- "priority": string ("high", "medium", or "low")
- "day_offset": integer (The recommended day of crop cycle from 0 to {duration_days})
- "stage_id": string (One of the 7 stage ids above)
"""
        try:
            raw_response = await gemini_service.generate_response(
                prompt,
                {"task": "season_flow_generation", "crop": crop_name}
            )
            json_match = re.search(r'\[\s*\{[\s\S]*\}\s*\]', raw_response or "")
            if json_match:
                tasks_raw = json.loads(json_match.group(0))
            else:
                cleaned = re.sub(r'```json\s*', '', raw_response or '')
                cleaned = re.sub(r'\s*```', '', cleaned).strip()
                tasks_raw = json.loads(cleaned)

            if isinstance(tasks_raw, list) and len(tasks_raw) > 0:
                logger.info(f"Gemini successfully generated {len(tasks_raw)} seasonal tasks.")
                return tasks_raw
        except Exception as e:
            logger.warning(f"AI season flow generation encountered error: {e}. Utilizing agronomic expert rules.")

        # Resilient Agronomic Expert Fallback
        return DailyFlowService._get_agronomic_fallback_tasks(
            crop_name=crop_name,
            duration_days=duration_days,
            days_since_planting=days_since_planting,
            soil_data=soil_data
        )

    @staticmethod
    def _get_agronomic_fallback_tasks(
        crop_name: str,
        duration_days: int,
        days_since_planting: int,
        soil_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Produces realistic agronomic milestone tasks across all 7 stages if LLM is unavailable."""
        crop = crop_name.capitalize()
        moisture = soil_data.get("moisture")

        tasks = []

        # Immediate today / tomorrow actionable tasks based on telemetry
        if moisture is not None and moisture < 35:
            tasks.append({
                "title": f"Urgent irrigation cycle for {crop}",
                "description": f"Soil moisture telemetry is at {moisture}%, indicating root-zone moisture stress. Run scheduled irrigation.",
                "category": "irrigation",
                "priority": "high",
                "day_offset": days_since_planting,
                "stage_id": "active_vegetative"
            })
        else:
            tasks.append({
                "title": f"Foliar scouting for sucking pests in {crop}",
                "description": "Inspect underside of leaves in 20 random plants across the field for early signs of aphids or thrips.",
                "category": "pest",
                "priority": "high",
                "day_offset": days_since_planting,
                "stage_id": "active_vegetative"
            })

        tasks.append({
            "title": f"Check drip lines and soil aeration for {crop}",
            "description": "Inspect lateral drip lines for emitter blockages and confirm root zone moisture infiltration.",
            "category": "maintenance",
            "priority": "medium",
            "day_offset": days_since_planting + 1,
            "stage_id": "active_vegetative"
        })

        # Milestone tasks across stages
        stage_templates = [
            ("sowing_germination", 0, "Basal fertilizer and seedbed preparation", f"Incorporate farmyard manure and basal NPK into soil before sowing {crop}.", "fertilizer", "high"),
            ("sowing_germination", 7, "Emergence & germination inspection", f"Assess percentage of seedling emergence across field plots for {crop}.", "maintenance", "medium"),
            ("seedling_establishment", 18, f"Thinning and weed scouting for {crop}", "Remove excess crowded seedlings to ensure recommended plant population.", "other", "medium"),
            ("seedling_establishment", 28, f"Early vegetative irrigation & hoeing", "Light inter-cultivation to break soil crust and promote aeration.", "irrigation", "high"),
            ("active_vegetative", 40, f"Top-dressing Nitrogen / Urea for {crop}", "Apply split nitrogen dosage along rows to fuel rapid stem and leaf expansion.", "fertilizer", "high"),
            ("active_vegetative", 55, f"Canopy vigor & disease inspection", "Check for leaf spot or bacterial blight before onset of flowering.", "pest", "medium"),
            ("flowering_budding", 70, f"Flowering moisture management", f"Maintain consistent soil moisture to prevent flower and bud abortion in {crop}.", "irrigation", "high"),
            ("flowering_budding", 80, f"Micronutrient foliar spray (Boron/Zinc)", "Spray liquid micronutrient solution during peak flowering to enhance fruit set.", "fertilizer", "medium"),
            ("fruit_grain_development", 100, f"Potassium top-dress and boll/grain monitoring", "Ensure adequate potassium availability for optimal boll/seed weight and density.", "fertilizer", "high"),
            ("fruit_grain_development", 115, f"Late-season pest barrier check", "Scout for bollworms or pod borers and install pheromone lures if threshold exceeded.", "pest", "medium"),
            ("harvest_preparation", int(duration_days * 0.88), f"Cease irrigation 10-14 days before harvest", f"Allow field to dry down naturally to facilitate harvest machinery for {crop}.", "irrigation", "high"),
            ("harvest_preparation", int(duration_days * 0.93), f"Inspect crop maturity & test harvest sample", "Sample grain or bolls to verify moisture percentage meets storage specifications.", "harvest", "medium"),
            ("harvest_post_harvest", int(duration_days * 0.98), f"Primary harvesting operation for {crop}", "Pick or combine harvest during dry morning conditions for maximum quality grade.", "harvest", "high"),
            ("harvest_post_harvest", duration_days, f"Post-harvest sorting, grading & APMC price check", "Grade harvested produce and check nearest APMC mandi rates before sale.", "other", "medium"),
        ]

        for stage_id, offset, title, desc, cat, pri in stage_templates:
            tasks.append({
                "title": title,
                "description": desc,
                "category": cat,
                "priority": pri,
                "day_offset": offset,
                "stage_id": stage_id
            })

        return tasks

    @staticmethod
    def persist_tasks_idempotently(
        db: Session,
        farm: Farm,
        crop: Crop,
        user: User,
        generated_tasks: List[Dict[str, Any]],
        planting_date: datetime
    ) -> List[Task]:
        """
        Saves generated tasks safely into PostgreSQL/SQLite `tasks` and `farm_tasks` tables.
        Implements duplicate protection: checks if a task with the same normalized title
        and scheduled date already exists. Never overwrites or deletes farmer-completed tasks.
        """
        planting_d = planting_date.date()
        today_d = datetime.utcnow().date()

        existing_farm_tasks = db.query(Task).filter(
            Task.farm_id == farm.id,
            Task.crop_id == crop.id
        ).all()

        existing_user_farm_tasks = db.query(FarmTask).filter(
            FarmTask.user_id == user.id
        ).all()

        existing_task_keys = {
            (t.title.strip().lower(), t.scheduled_date.date().isoformat()): t
            for t in existing_farm_tasks if t.scheduled_date
        }
        existing_user_task_keys = {
            (ft.title.strip().lower(), ft.scheduled_date.date().isoformat()): ft
            for ft in existing_user_farm_tasks if ft.scheduled_date
        }

        saved_tasks = []

        for item in generated_tasks:
            try:
                val = GeneratedTaskItem(**item)
            except Exception as e:
                logger.warning(f"Skipping malformed task during persistence: {item} ({e})")
                continue

            offset = val.day_offset if val.day_offset is not None else 0
            if offset == 0:
                task_date = today_d
            else:
                task_date = planting_d + timedelta(days=offset)

            task_dt = datetime(task_date.year, task_date.month, task_date.day, 9, 0, 0)
            key = (val.title.strip().lower(), task_date.isoformat())

            if key in existing_task_keys:
                logger.debug(f"Task already exists in Task table: '{val.title}' on {task_date}")
                saved_tasks.append(existing_task_keys[key])
                continue

            new_task = Task(
                farm_id=farm.id,
                crop_id=crop.id,
                task_type=val.category,
                title=val.title,
                description=val.description,
                priority=val.priority,
                status="pending",
                scheduled_date=task_dt,
                created_at=datetime.utcnow()
            )
            db.add(new_task)
            saved_tasks.append(new_task)
            existing_task_keys[key] = new_task

            if key not in existing_user_task_keys:
                new_farm_task = FarmTask(
                    user_id=user.id,
                    title=val.title,
                    description=val.description,
                    category=val.category,
                    priority=val.priority,
                    scheduled_date=task_dt,
                    is_completed=False,
                    created_at=datetime.utcnow()
                )
                db.add(new_farm_task)
                existing_user_task_keys[key] = new_farm_task

        db.commit()
        logger.info(f"Committed {len(saved_tasks)} seasonal and daily tasks for farm {farm.id}.")
        return saved_tasks

    @staticmethod
    def get_partitioned_daily_flow(
        db: Session,
        farm: Farm,
        crop: Crop,
        user: User
    ) -> Dict[str, Any]:
        """
        Retrieves all tasks for the farm & crop and partitions them into:
        today, tomorrow, upcoming_7_days, season_plan (stages), overdue, and completed.
        """
        today_d = datetime.utcnow().date()
        tomorrow_d = today_d + timedelta(days=1)
        next_7_d = today_d + timedelta(days=7)

        planting_date = crop.planting_date or datetime.utcnow()
        duration = DailyFlowService.get_crop_duration(crop.crop_type, crop.variety)
        timeline = DailyFlowService.calculate_season_timeline(planting_date, duration)

        all_tasks = (
            db.query(Task)
            .filter(Task.farm_id == farm.id, Task.crop_id == crop.id)
            .order_by(Task.scheduled_date.asc())
            .all()
        )

        user_tasks = {
            t.title.strip().lower(): t
            for t in db.query(FarmTask).filter(FarmTask.user_id == user.id).all()
        }

        def format_task(t: Task) -> Dict[str, Any]:
            user_t = user_tasks.get(t.title.strip().lower())
            is_comp = (t.status == "completed") or (user_t and user_t.is_completed)
            return {
                "id": t.id,
                "farm_task_id": user_t.id if user_t else None,
                "title": t.title,
                "description": t.description or "",
                "category": t.task_type or "other",
                "priority": t.priority or "medium",
                "scheduled_date": t.scheduled_date.isoformat() if t.scheduled_date else None,
                "scheduled_date_str": t.scheduled_date.strftime('%b %d, %Y') if t.scheduled_date else "",
                "is_completed": bool(is_comp),
                "status": "completed" if is_comp else t.status or "pending",
            }

        today_tasks = []
        tomorrow_tasks = []
        upcoming_7_tasks = []
        overdue_tasks = []
        completed_tasks = []

        stage_task_buckets: Dict[str, List[Dict[str, Any]]] = {
            stage["id"]: [] for stage in timeline["stages"]
        }

        for task in all_tasks:
            formatted = format_task(task)
            task_date = task.scheduled_date.date() if task.scheduled_date else today_d

            if formatted["is_completed"]:
                completed_tasks.append(formatted)

            if not formatted["is_completed"] and task_date < today_d:
                overdue_tasks.append(formatted)

            if task_date == today_d:
                today_tasks.append(formatted)
            elif task_date == tomorrow_d:
                tomorrow_tasks.append(formatted)
            elif today_d < task_date <= next_7_d:
                upcoming_7_tasks.append(formatted)

            assigned_stage = False
            for stage in timeline["stages"]:
                s_start = datetime.fromisoformat(stage["start_date"]).date()
                s_end = datetime.fromisoformat(stage["end_date"]).date()
                if s_start <= task_date <= s_end:
                    stage_task_buckets[stage["id"]].append(formatted)
                    assigned_stage = True
                    break

            if not assigned_stage and timeline["stages"]:
                timeline["stages"][-1]["tasks"].append(formatted)

        for stage in timeline["stages"]:
            stage["tasks"] = stage_task_buckets.get(stage["id"], [])

        return {
            "success": True,
            "farm_id": farm.id,
            "farm_name": farm.farm_name or farm.name or "My Farm",
            "farm_location": f"{farm.district or ''}, {farm.state or ''}".strip(", "),
            "crop_id": crop.id,
            "crop_name": crop.crop_type,
            "crop_variety": crop.variety or "Standard",
            "season_info": {
                "planting_date": timeline["planting_date"],
                "expected_harvest_date": timeline["expected_harvest_date"],
                "duration_days": timeline["duration_days"],
                "days_since_planting": timeline["days_since_planting"],
                "progress_pct": timeline["progress_pct"],
                "current_stage": timeline["current_stage"],
            },
            "today": today_tasks,
            "tomorrow": tomorrow_tasks,
            "upcoming_7_days": upcoming_7_tasks,
            "upcoming": upcoming_7_tasks,
            "season_plan": timeline["stages"],
            "stages": timeline["stages"],
            "overdue": overdue_tasks,
            "completed": completed_tasks,
            "total_tasks_count": len(all_tasks)
        }
                tomorrow_tasks.append(formatted)
            elif today_d < task_date <= next_7_d:
                upcoming_7_tasks.append(formatted)

            assigned_stage = False
            for stage in timeline["stages"]:
                s_start = datetime.fromisoformat(stage["start_date"]).date()
                s_end = datetime.fromisoformat(stage["end_date"]).date()
                if s_start <= task_date <= s_end:
                    stage_task_buckets[stage["id"]].append(formatted)
                    assigned_stage = True
                    break

            if not assigned_stage and timeline["stages"]:
                timeline["stages"][-1]["tasks"].append(formatted)

        for stage in timeline["stages"]:
            stage["tasks"] = stage_task_buckets.get(stage["id"], [])

        return {
            "success": True,
            "farm_id": farm.id,
            "farm_name": farm.farm_name or farm.name or "My Farm",
            "farm_location": f"{farm.district or ''}, {farm.state or ''}".strip(", "),
            "crop_id": crop.id,
            "crop_name": crop.crop_type,
            "crop_variety": crop.variety or "Standard",
            "season_info": {
                "planting_date": timeline["planting_date"],
                "expected_harvest_date": timeline["expected_harvest_date"],
                "duration_days": timeline["duration_days"],
                "days_since_planting": timeline["days_since_planting"],
                "progress_pct": timeline["progress_pct"],
                "current_stage": timeline["current_stage"],
            },
            "today": today_tasks,
            "tomorrow": tomorrow_tasks,
            "upcoming_7_days": upcoming_7_tasks,
            "upcoming": upcoming_7_tasks,
            "season_plan": timeline["stages"],
            "stages": timeline["stages"],
            "overdue": overdue_tasks,
            "completed": completed_tasks,
            "total_tasks_count": len(all_tasks)
        }
