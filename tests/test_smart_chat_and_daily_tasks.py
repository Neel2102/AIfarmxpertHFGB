"""
Comprehensive End-to-End Tests for:
1. Smart Chat / AI Orchestrator with specialized agents
2. Daily Task Generation, Validation, Duplicate Protection, and Persistence
"""

import asyncio
import os
import sys
from datetime import datetime

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from farmxpert.models.database import engine, get_db, Base
from farmxpert.models.user_models import User
from farmxpert.models.farm_models import Farm, Crop, SoilTest, Task, FarmTask
from farmxpert.models.farm_profile_models import FarmProfile
from farmxpert.services.orchestrator.intent_router import intent_router, IntentType
from farmxpert.services.orchestrator.farmxpert_orchestrator import farmxpert_orchestrator
from farmxpert.interfaces.api.routes.task_routes import (
    generate_daily_tasks, get_today_tasks, complete_task, TaskStatusUpdate
)
from sqlalchemy.orm import Session


def setup_test_data(db: Session) -> User:
    """Create or retrieve a test user with farm and soil test data."""
    test_user = db.query(User).filter(User.email == "testfarmer@farmxpert.com").first()
    if not test_user:
        test_user = User(
            email="testfarmer@farmxpert.com",
            full_name="Rajesh Patel",
            username="rajesh_farmer",
            is_active=True,
            onboarding_completed=True
        )
        test_user.set_password("SecurePassword123")
        db.add(test_user)
        db.commit()
        db.refresh(test_user)

    # Ensure FarmProfile exists for test user
    farm_profile = db.query(FarmProfile).filter(FarmProfile.user_id == test_user.id).first()
    if not farm_profile:
        farm_profile = FarmProfile(
            user_id=test_user.id,
            farm_name="Patel Organic Farm",
            farm_size="5",
            farm_size_unit="acres",
            location="Gondal, Rajkot, Gujarat",
            state="Gujarat",
            district="Rajkot",
            village="Gondal",
            specific_crop="Cotton",
            primary_crops=["Cotton", "Groundnut"],
            soil_type="Black Soil"
        )
        db.add(farm_profile)
        db.commit()

    # Ensure farm exists for test user
    farm = db.query(Farm).filter(Farm.user_id == test_user.id).first()
    if not farm:
        farm = Farm(
            user_id=test_user.id,
            farm_name="Patel Organic Farm",
            crop_type="Cotton",
            state="Gujarat",
            district="Rajkot",
            village="Gondal",
            soil_type="Black Soil",
            latitude=21.9619,
            longitude=70.7923
        )
        db.add(farm)
        db.commit()
        db.refresh(farm)

    # Ensure soil test exists
    soil = db.query(SoilTest).filter(SoilTest.farm_id == farm.id).first()
    if not soil:
        soil = SoilTest(
            farm_id=farm.id,
            soil_moisture=26.5,  # Low moisture to test irrigation reasoning
            soil_ph=7.2,
            nitrogen=130.0,
            phosphorus=22.0,
            potassium=180.0,
            soil_ec=1.1,
            air_temperature=32.0,
            air_humidity=55.0,
            test_date=datetime.utcnow()
        )
        db.add(soil)
        db.commit()

    return test_user


async def run_tests():
    print("=" * 60)
    print("STARTING FARMXPERT TEST SUITE")
    print("=" * 60)

    # Ensure test-relevant tables exist in local database
    for model in [User, Farm, Crop, SoilTest, Task, FarmTask, FarmProfile]:
        try:
            model.__table__.create(bind=engine, checkfirst=True)
        except Exception:
            pass

    db = next(get_db())
    test_user = setup_test_data(db)
    print(f"Test User configured: id={test_user.id}, email={test_user.email}")

    # -------------------------------------------------------------
    # PART 1: SMART CHAT INTENT ROUTING TESTS
    # -------------------------------------------------------------
    print("\n--- Part 1: Intent Routing Verification ---")
    test_queries = [
        ("What should I do about low soil moisture?", IntentType.IRRIGATION, "irrigation_planner"),
        ("Which crop should I plant this season?", IntentType.CROP_SELECTION, "crop_selector"),
        ("Give me today's farming tasks.", IntentType.TASK_SCHEDULING, "task_scheduler"),
        ("What is the soil health of my farm?", IntentType.SOIL_HEALTH, "soil_health"),
        ("Should I irrigate today?", IntentType.IRRIGATION, "irrigation_planner"),
        ("What fertilizer should I use?", IntentType.FERTILIZER, "fertilizer_advisor"),
        ("Predict my yield.", IntentType.YIELD_PREDICTION, "yield_predictor"),
        ("What crops are suitable for my soil?", IntentType.CROP_SELECTION, "crop_selector"),
        ("What is the current market situation?", IntentType.MARKET_PRICES, "market_intelligence"),
        ("Show me my farm's current conditions.", IntentType.FARM_STATUS, "weather_watcher"),
        ("What tasks do I need to complete today?", IntentType.TASK_SCHEDULING, "task_scheduler"),
    ]

    for q, expected_intent, expected_agent in test_queries:
        routed = intent_router.route_query(q)
        status_flag = "PASS" if (routed.primary_intent == expected_intent and routed.selected_agent == expected_agent) else "FAIL"
        print(f"[{status_flag}] '{q}'")
        print(f"       Intent: {routed.primary_intent.value} (Expected: {expected_intent.value})")
        print(f"       Agent:  {routed.selected_agent} (Expected: {expected_agent})")
        assert routed.primary_intent == expected_intent, f"Intent mismatch for '{q}'"
        assert routed.selected_agent == expected_agent, f"Agent mismatch for '{q}'"

    # -------------------------------------------------------------
    # PART 2: SMART CHAT ORCHESTRATOR EXECUTION TESTS
    # -------------------------------------------------------------
    print("\n--- Part 2: Smart Chat Orchestrator Execution ---")
    
    # Test execution with real context
    chat_cases = [
        "What should I do about low soil moisture?",
        "What fertilizer should I use?",
        "Give me today's farming tasks.",
        "Which crop should I plant this season?",
    ]

    for query in chat_cases:
        print(f"\nTesting Orchestrator with Query: '{query}'")
        res = await farmxpert_orchestrator.process_request(
            message=query,
            user=test_user,
            db=db,
            session_id="test_session_123"
        )
        assert res["success"] is True, f"Orchestrator failed for query: {query}"
        assert len(res["response"]) > 10, f"Response too short: {res['response']}"
        assert res["response"] == res["message"], "response and message fields should match for frontend"
        assert len(res["agent_responses"]) > 0, "agent_responses must contain consulted agent"
        print(f" -> Selected Agent: {res['agent']}")
        print(f" -> Response: {res['response'][:140]}...")
        print(f" -> Sources Consulted: {[a['agent_name'] for a in res['agent_responses']]}")

    # Test Missing Farm Context (Graceful fallback)
    print("\nTesting Orchestrator with User with No Farm:")
    no_farm_user = User(id=99999, email="nofarm@example.com", full_name="No Farm Farmer", is_active=True)
    res_nofarm = await farmxpert_orchestrator.process_request(
        message="What tasks do I need to complete today?",
        user=no_farm_user,
        db=db,
        session_id="test_nofarm"
    )
    print(f" -> No-farm response: {res_nofarm['response']}")
    assert "add or link a farm" in res_nofarm["response"].lower() or "farm" in res_nofarm["response"].lower()

    # -------------------------------------------------------------
    # PART 3: DAILY TASK GENERATION & PERSISTENCE TESTS
    # -------------------------------------------------------------
    print("\n--- Part 3: Daily Task Generation, Validation & Persistence ---")
    
    # 1. Clean existing tasks for clean test
    db.query(FarmTask).filter(FarmTask.user_id == test_user.id).delete()
    db.commit()

    # 2. Generate daily tasks
    print("Calling generate_daily_tasks...")
    tasks_result = await generate_daily_tasks(current_user=test_user, db=db)
    print(f"Generated {len(tasks_result)} tasks:")
    for t in tasks_result:
        print(f" - [{t['priority'].upper()}] {t['title']} ({t['category']})")
        assert t["id"] is not None, "Task must have database ID"
        assert t["title"], "Task must have title"
        assert t["priority"] in ["high", "medium", "low"]
        assert t["category"] in ["irrigation", "pest", "fertilizer", "harvest", "maintenance", "other"]

    assert len(tasks_result) >= 3, "Should generate at least 3 daily tasks"

    # 3. Verify real DB records in FarmTask
    db_tasks = db.query(FarmTask).filter(FarmTask.user_id == test_user.id).all()
    assert len(db_tasks) >= 3, "Tasks must be saved in database"
    print(f"Verified {len(db_tasks)} records persisted in 'farm_tasks' table.")

    # 4. Duplicate Protection: Generate again immediately
    print("\nCalling generate_daily_tasks second time to verify duplicate protection...")
    tasks_result_2 = await generate_daily_tasks(current_user=test_user, db=db)
    db_tasks_after = db.query(FarmTask).filter(FarmTask.user_id == test_user.id).all()
    print(f"Total tasks in DB after second generation: {len(db_tasks_after)}")
    assert len(db_tasks_after) == len(db_tasks), "Duplicate generation must not create duplicate tasks for today"

    # 5. Fetch Today's Tasks
    print("\nCalling get_today_tasks...")
    today_tasks = await get_today_tasks(current_user=test_user, db=db)
    assert len(today_tasks) >= 3, "get_today_tasks should return the generated tasks"
    print(f"Successfully retrieved {len(today_tasks)} tasks from /api/tasks/today.")

    # 6. Complete a task
    task_to_complete = today_tasks[0]
    print(f"\nCompleting task ID {task_to_complete['id']}: '{task_to_complete['title']}'...")
    complete_res = await complete_task(
        task_id=task_to_complete["id"],
        status_update=TaskStatusUpdate(is_completed=True),
        current_user=test_user,
        db=db
    )
    assert complete_res["is_completed"] is True
    assert complete_res["completed_at"] is not None
    print(f"Task status updated: is_completed={complete_res['is_completed']}, completed_at={complete_res['completed_at']}")

    # Verify task completion persisted in database
    verified_task = db.query(FarmTask).filter(FarmTask.id == task_to_complete["id"]).first()
    assert verified_task.is_completed is True
    print("Task completion verified in database record.")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY! 100% VERIFIED.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_tests())
