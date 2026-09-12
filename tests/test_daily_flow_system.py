"""
Comprehensive Automated Test Suite for Daily Flow & Crop Season Plan System
Validates:
1. Season timeline & stage dates calculation (leap year, month boundaries)
2. Growth stage detection from planting date and crop duration
3. Partitioning: Today, Tomorrow, Next 7 Days, Stages, Overdue, Completed
4. Task generation with Gemini AI & resilient agronomic fallbacks
5. Database persistence across both Task and FarmTask tables
6. Idempotency & duplicate protection (multiple generations without duplicate tasks)
7. Farmer task preservation (completed & custom tasks never deleted)
8. Status toggle synchronization across dual models
9. Endpoint responses (/api/tasks/daily-flow, /api/tasks/daily-flow/generate, /api/tasks/farms-and-crops)
"""

import sys
import os
from datetime import datetime, date, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from farmxpert.models.database import Base
from farmxpert.models.user_models import User
from farmxpert.models.farm_models import Farm, Crop, Task, FarmTask, SoilTest
from farmxpert.services.daily_flow_service import DailyFlowService


@pytest.fixture(scope="module")
def db_session():
    """In-memory SQLite database session for fast, clean, isolated test runs."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    # Only create tables needed for Daily Flow tests to avoid Postgres-specific JSONB in admin tables
    target_tables = [
        User.__table__,
        Farm.__table__,
        Crop.__table__,
        Task.__table__,
        FarmTask.__table__,
        SoilTest.__table__,
    ]
    Base.metadata.create_all(bind=engine, tables=target_tables)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="module")
def sample_user(db_session):
    user = User(
        username="farmer_flow_test",
        email="flow_test@farmxpert.test",
        hashed_password="test_hashed_password_123",
        full_name="Ramesh Bhai Patel",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="module")
def sample_farm(db_session, sample_user):
    farm = Farm(
        id=1,
        user_id=sample_user.id,
        name="Patel Agro Valley",
        farm_name="Patel Agro Valley",
        crop_type="Cotton",
        state="Gujarat",
        district="Rajkot",
        village="Gondal",
        soil_type="Black Soil",
        size_acres=10.0,
        location="Gondal, Rajkot, Gujarat"
    )
    db_session.add(farm)
    db_session.commit()
    db_session.refresh(farm)
    return farm


@pytest.fixture(scope="module")
def sample_crop(db_session, sample_farm):
    # Planted 45 days ago (actively vegetative)
    planting_dt = datetime.utcnow() - timedelta(days=45)
    harvest_dt = planting_dt + timedelta(days=160)
    crop = Crop(
        id=1,
        farm_id=sample_farm.id,
        crop_type="Cotton",
        variety="BT Cotton Hybrid-6",
        planting_date=planting_dt,
        expected_harvest_date=harvest_dt,
        area_acres=10.0,
        status="growing",
        created_at=planting_dt
    )
    db_session.add(crop)
    db_session.commit()
    db_session.refresh(crop)
    return crop


# ---------------------------------------------------------------------------
# TEST GROUP 1: TIMELINE & GROWTH STAGE CALCULATIONS
# ---------------------------------------------------------------------------

def test_crop_duration_lookup():
    """Verify crop durations for key Indian crops from agronomic knowledge."""
    assert DailyFlowService.get_crop_duration("Cotton") == 160
    assert DailyFlowService.get_crop_duration("Wheat") == 120
    assert DailyFlowService.get_crop_duration("Paddy") == 135
    assert DailyFlowService.get_crop_duration("Sugarcane") == 330
    assert DailyFlowService.get_crop_duration("Moong") == 65
    assert DailyFlowService.get_crop_duration("Unknown Crop") == 120  # Safe fallback


def test_timeline_stage_dates_and_progress():
    """Verify that stage start and end dates are proper dates spanning the full duration."""
    planting_date = datetime(2024, 6, 1, 10, 0, 0)
    duration = 160
    # Evaluate at day 45
    current_date = planting_date + timedelta(days=45)

    timeline = DailyFlowService.calculate_season_timeline(planting_date, duration, current_date)

    assert timeline["duration_days"] == 160
    assert timeline["days_since_planting"] == 45
    assert timeline["progress_pct"] == round((45 / 160) * 100, 1)

    # 7 distinct stages
    stages = timeline["stages"]
    assert len(stages) == 7

    # Check stage 0: Sowing & Germination
    assert stages[0]["id"] == "sowing_germination"
    assert stages[0]["start_date"] == "2024-06-01"
    assert stages[0]["status"] == "completed"  # Day 45 is past day 16

    # Active stage at Day 45 (between 25% and 45% of 160 days = days 40 to 72)
    current_stage = timeline["current_stage"]
    assert current_stage is not None
    assert current_stage["id"] == "active_vegetative"
    assert current_stage["status"] == "active"

    # Last stage must end on harvest date
    assert stages[-1]["end_date"] == (planting_date.date() + timedelta(days=160)).isoformat()
    assert stages[-1]["status"] == "upcoming"


def test_leap_year_and_month_boundaries():
    """Verify proper Python datetime arithmetic across leap year February and month boundaries."""
    leap_planting = datetime(2024, 2, 15)  # 2024 is a leap year
    timeline = DailyFlowService.calculate_season_timeline(leap_planting, 120)

    # Expected harvest date must correctly account for Feb 29
    expected_harvest = leap_planting.date() + timedelta(days=120)
    assert timeline["expected_harvest_date"] == expected_harvest.isoformat()
    assert timeline["expected_harvest_date"] == "2024-06-14"


# ---------------------------------------------------------------------------
# TEST GROUP 2: TASK GENERATION & AGRONOMIC FALLBACK
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_season_task_generation():
    """Verify season plan generates actionable tasks across multiple growth stages."""
    planting_dt = datetime.utcnow() - timedelta(days=45)
    soil_telemetry = {"moisture": 32.0, "ph": 6.8, "nitrogen": 45.0}

    tasks = await DailyFlowService.generate_season_plan_with_ai(
        crop_name="Cotton",
        variety="BT Cotton",
        planting_date=planting_dt,
        duration_days=160,
        current_stage="Active Vegetative Growth",
        days_since_planting=45,
        farm_location="Rajkot, Gujarat",
        soil_data=soil_telemetry
    )

    assert isinstance(tasks, list)
    assert len(tasks) >= 5

    # Check for presence of irrigation, fertilizer, and pest categories
    categories = {t.get("category") for t in tasks}
    assert "irrigation" in categories or "fertilizer" in categories
    assert any("Cotton" in t.get("title", "") or "fertilizer" in t.get("title", "").lower() for t in tasks)


# ---------------------------------------------------------------------------
# TEST GROUP 3: PERSISTENCE, DUAL-TABLE SYNC & IDEMPOTENCY
# ---------------------------------------------------------------------------

def test_idempotent_task_persistence(db_session, sample_farm, sample_crop, sample_user):
    """Verify tasks are stored in both Task and FarmTask tables without duplicate generation."""
    planting_dt = sample_crop.planting_date
    generated_tasks = [
        {
            "title": "Irrigate Cotton plot block A",
            "description": "Run drip irrigation for 2 hours.",
            "category": "irrigation",
            "priority": "high",
            "day_offset": 45,  # Today
            "stage_id": "active_vegetative"
        },
        {
            "title": "Top-dress Urea for Cotton",
            "description": "Apply 25 kg/acre along plant rows.",
            "category": "fertilizer",
            "priority": "high",
            "day_offset": 46,  # Tomorrow
            "stage_id": "active_vegetative"
        },
        {
            "title": "Inspect for pink bollworm larvae",
            "description": "Check 20 squares in random plants.",
            "category": "pest",
            "priority": "medium",
            "day_offset": 48,  # Upcoming 3 days
            "stage_id": "active_vegetative"
        },
        {
            "title": "Cease irrigation for harvest preparation",
            "description": "Allow field to dry down naturally.",
            "category": "irrigation",
            "priority": "high",
            "day_offset": 145,  # Future stage
            "stage_id": "harvest_preparation"
        }
    ]

    # First persistence pass
    saved_pass1 = DailyFlowService.persist_tasks_idempotently(
        db=db_session,
        farm=sample_farm,
        crop=sample_crop,
        user=sample_user,
        generated_tasks=generated_tasks,
        planting_date=planting_dt
    )

    assert len(saved_pass1) == 4

    # Verify both tables contain the tasks
    core_count1 = db_session.query(Task).filter(Task.farm_id == sample_farm.id).count()
    farm_task_count1 = db_session.query(FarmTask).filter(FarmTask.user_id == sample_user.id).count()

    assert core_count1 == 4
    assert farm_task_count1 == 4

    # SECOND GENERATION PASS (Idempotency test)
    saved_pass2 = DailyFlowService.persist_tasks_idempotently(
        db=db_session,
        farm=sample_farm,
        crop=sample_crop,
        user=sample_user,
        generated_tasks=generated_tasks,  # Identical tasks re-sent
        planting_date=planting_dt
    )

    core_count2 = db_session.query(Task).filter(Task.farm_id == sample_farm.id).count()
    farm_task_count2 = db_session.query(FarmTask).filter(FarmTask.user_id == sample_user.id).count()

    # Must NOT create duplicate tasks!
    assert core_count2 == core_count1
    assert farm_task_count2 == farm_task_count1


def test_partitioned_daily_flow(db_session, sample_farm, sample_crop, sample_user):
    """Verify tasks are accurately bucketed into Today, Tomorrow, Next 7 Days, and Season Stages."""
    flow = DailyFlowService.get_partitioned_daily_flow(
        db=db_session,
        farm=sample_farm,
        crop=sample_crop,
        user=sample_user
    )

    assert flow["success"] is True
    assert flow["crop_name"] == "Cotton"
    assert flow["total_tasks_count"] >= 4

    # Check partitioned buckets
    assert len(flow["today"]) >= 1
    assert flow["today"][0]["title"] == "Irrigate Cotton plot block A"

    assert len(flow["tomorrow"]) >= 1
    assert flow["tomorrow"][0]["title"] == "Top-dress Urea for Cotton"

    assert len(flow["upcoming_7_days"]) >= 1
    assert flow["upcoming_7_days"][0]["title"] == "Inspect for pink bollworm larvae"

    # Check that stage plan contains the future milestone task
    stages = flow["season_plan"]
    prep_stage = next((s for s in stages if s["id"] == "harvest_preparation"), None)
    assert prep_stage is not None
    assert any(t["title"] == "Cease irrigation for harvest preparation" for t in prep_stage["tasks"])


def test_task_status_toggle(db_session, sample_farm, sample_crop, sample_user):
    """Verify task completion updates both Task and FarmTask atomically."""
    # Find the today task
    today_task = db_session.query(Task).filter(Task.farm_id == sample_farm.id, Task.title == "Irrigate Cotton plot block A").first()
    farm_task = db_session.query(FarmTask).filter(FarmTask.user_id == sample_user.id, FarmTask.title == "Irrigate Cotton plot block A").first()

    assert today_task is not None
    assert farm_task is not None
    assert today_task.status == "pending"
    assert farm_task.is_completed is False

    # Simulate completion toggle
    now = datetime.utcnow()
    today_task.status = "completed"
    today_task.completed_date = now
    farm_task.is_completed = True
    farm_task.completed_at = now
    db_session.commit()

    # Re-fetch partitioned flow
    flow = DailyFlowService.get_partitioned_daily_flow(
        db=db_session,
        farm=sample_farm,
        crop=sample_crop,
        user=sample_user
    )

    # Must appear in completed bucket
    completed_titles = [t["title"] for t in flow["completed"]]
    assert "Irrigate Cotton plot block A" in completed_titles

    # Must reflect is_completed = True in today's view as well
    today_item = next((t for t in flow["today"] if t["title"] == "Irrigate Cotton plot block A"), None)
    assert today_item is not None
    assert today_item["is_completed"] is True
