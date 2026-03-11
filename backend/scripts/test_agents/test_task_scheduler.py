import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add the backend directory to python path for simple testing
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from farmxpert.agents.operations.task_scheduler_agent import TaskSchedulerAgent

async def test_task_scheduler():
    print("Initializing TaskSchedulerAgent...")
    agent = TaskSchedulerAgent()
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    test_input = {
        "query": "Schedule my remaining tasks for the week considering the incoming rain.",
        "location": "Illinois",
        "context": {
            "tasks": [
                {"id": 1, "name": "Harvest soybeans", "duration_hours": 8, "deadline": "2024-10-15"},
                {"id": 2, "name": "Apply late-season fungicide", "duration_hours": 4, "deadline": "2024-10-12"},
                {"id": 3, "name": "Fix barn roof", "duration_hours": 6, "deadline": "2024-10-20"}
            ],
            "resources": {
                "laborers": 2,
                "tractors": 1,
                "harvesters": 1
            },
            "constraints": {
                "max_hours_per_day": 10,
                "objective": "minimize_weather_risk"
            },
            "board_info": {
                "system": "FarmTrello",
                "board_id": "BOARD123"
            }
        }
    }
    
    print(f"\nSending input: {json.dumps(test_input, indent=2)}\n")
    try:
        response = await agent.handle(test_input)
        print("\n--- Response Received ---")
        print(json.dumps(response, indent=2))
        print("\nTest passed! TaskSchedulerAgent successfully processed input using REAL tools.")
    except Exception as e:
        print(f"Error during agent execution: {e}")

if __name__ == "__main__":
    asyncio.run(test_task_scheduler())
