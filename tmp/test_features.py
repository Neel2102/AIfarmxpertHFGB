import pytest
import asyncio
import os
from datetime import datetime

# Adjust Python path to find farmxpert module
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, project_root)

from farmxpert.app.orchestrator.agent import OrchestratorAgent
from farmxpert.agents.supply_chain.market_intelligence_agent import MarketIntelligenceAgent
from farmxpert.agents.operations.task_scheduler_agent import TaskSchedulerAgent
from farmxpert.models.farm_profile_models import FarmProfile
from farmxpert.models.farm_models import SoilTest

def test_build_system_prompt():
    # Setup mock data that matches the SQLAlchemy model properties
    class MockUser:
        def __init__(self):
            self.onboarding_data = {
                "farmSize": "10",
                "state": "Maharashtra",
                "specificCrop": "Sugarcane",
                "soilType": "Black Cotton",
                "irrigationMethod": "Drip"
            }

    class MockSensorReading:
        def __init__(self):
            self.soil_ph = 6.8
            self.soil_moisture = 45.0
            self.nitrogen = 120.5
            self.phosphorus = 40.0
            self.potassium = 200.0

    user = MockUser()
    sensor_reading = MockSensorReading()

    # Call the method
    prompt = OrchestratorAgent._build_system_prompt(user, sensor_reading)

    # Assertions
    assert "Maharashtra" in prompt
    assert "10" in prompt
    assert "Sugarcane" in prompt
    assert "Black Cotton" in prompt
    assert "Drip" in prompt
    assert "pH 6.8" in prompt
    assert "moisture 45" in prompt
    assert "N=120" in prompt

def test_market_price_structure():
    agent = MarketIntelligenceAgent()
    crops = ["cotton", "soybeans"]
    location = "Gujarat"
    
    # Use deterministic date seed as implemented
    prices = agent._get_current_prices(crops, location)
    
    # Check cotton structure
    assert "cotton" in prices
    cotton_data = prices["cotton"]
    
    assert "current_price_per_ton" in cotton_data
    assert "price_trend" in cotton_data
    assert "trend_direction" in cotton_data
    assert "trend_percent" in cotton_data
    assert "advice" in cotton_data
    assert "advice_reason" in cotton_data
    
    # Advice should be SELL or HOLD
    assert cotton_data["advice"] in ["SELL", "HOLD"]
    
    # Trend percent should be a float/int
    assert isinstance(cotton_data["trend_percent"], (float, int))

@pytest.mark.asyncio
async def test_task_generation():
    agent = TaskSchedulerAgent()
    
    # Mock parameters
    crop = "Wheat"
    growth_stage = "Vegetative"
    soil_data = {"moisture": 30, "ph": 7.0}
    location = "Punjab"
    farm_size = "5 acres"
    
    # Since this calls Gemini directly, we need a valid key in the environment
    # If it fails, our method has a fallback, which should return exactly 3 tasks
    tasks = await agent.generate_daily_tasks(crop, growth_stage, soil_data, location, farm_size)
    
    assert isinstance(tasks, list)
    assert len(tasks) == 3
    
    for task in tasks:
        assert isinstance(task, dict)
        assert "title" in task
        assert "description" in task
        assert "category" in task
        assert "priority" in task
        assert task["priority"] in ["high", "medium", "low"]
        assert task["category"] in ["irrigation", "pest", "fertilizer", "harvest", "maintenance", "other"]
        
    # Check that at least one task is high priority as prompted
    priorities = [task["priority"] for task in tasks]
    assert "high" in priorities

if __name__ == "__main__":
    print("Running test_build_system_prompt...")
    test_build_system_prompt()
    print("Running test_market_price_structure...")
    test_market_price_structure()
    print("Running test_task_generation...")
    asyncio.run(test_task_generation())
    print("All tests passed!")
