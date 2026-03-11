import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add the backend directory to python path for simple testing
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from farmxpert.agents.operations.machinery_equipment_agent import MachineryEquipmentAgent

async def test_machinery_equipment():
    print("Initializing MachineryEquipmentAgent...")
    agent = MachineryEquipmentAgent()
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    test_input = {
        "query": "My John Deere tractor is overheating when plowing, what should I do?",
        "context": {
            "farm_size": 150,
            "available_equipment": ["tractor", "plow", "sprayer"],
            "current_tasks": ["plowing"],
            "usage_stats": {
                "tractor": {"hours_used": 1200, "last_service": "2023-08-01"}
            },
            "telemetry": {
                "tractor_engine_temp": 105,
                "tractor_fluid_pressure": "low"
            },
            "equipment_meta": [{"name": "tractor", "brand": "John Deere"}]
        }
    }
    
    print(f"\nSending input: {json.dumps(test_input, indent=2)}\n")
    try:
        response = await agent.handle(test_input)
        print("\n--- Response Received ---")
        print(json.dumps(response, indent=2))
        print("\nTest passed! MachineryEquipmentAgent successfully processed input using REAL tools.")
    except Exception as e:
        print(f"Error during agent execution: {e}")

if __name__ == "__main__":
    asyncio.run(test_machinery_equipment())
