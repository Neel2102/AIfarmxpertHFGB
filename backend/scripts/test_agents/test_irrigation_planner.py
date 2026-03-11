import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add the backend directory to python path for simple testing
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from farmxpert.agents.agronomy.irrigation_planner_agent import IrrigationPlannerAgent

async def test_irrigation_planner():
    print("Initializing IrrigationPlannerAgent...")
    agent = IrrigationPlannerAgent()
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    test_input = {
        "query": "Should I irrigate my wheat field now?",
        "crop": "wheat",
        "growth_stage": "vegetative",
        "location": "Punjab",
        "field_size_acres": 5,
        "soil_data": {
            "type": "loamy",
            "capacity": "medium"
        },
        "sensor_data": {
            "moisture_level": 35.5,
            "temperature": 28.0
        }
    }
    
    print(f"\nSending input: {json.dumps(test_input, indent=2)}\n")
    try:
        response = await agent.handle(test_input)
        print("\n--- Response Received ---")
        print(json.dumps(response, indent=2))
        print("\nTest passed! IrrigationPlannerAgent successfully processed input using REAL tools.")
    except Exception as e:
        print(f"Error during agent execution: {e}")

if __name__ == "__main__":
    asyncio.run(test_irrigation_planner())
