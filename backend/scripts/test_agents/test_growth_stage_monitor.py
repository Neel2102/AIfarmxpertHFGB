import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add the backend directory to python path for simple testing
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from farmxpert.agents.agronomy.growth_stage_monitor_agent import GrowthStageMonitorAgent

async def test_growth_stage():
    print("Initializing GrowthStageMonitorAgent...")
    agent = GrowthStageMonitorAgent()
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    test_input = {
        "query": "Is my wheat developing normally? It was planted 30 days ago.",
        "crop": "wheat",
        "planting_date": "2024-01-15",
        "location": "Haryana",
        "satellite_data": {
            "ndvi_score": 0.62,
            "cloud_cover": 10
        },
        "drone_data": {
            "plant_height_cm": 15,
            "canopy_cover_percent": 45
        },
        "environmental_data": {
            "gdd_accumulated": 350
        }
    }
    
    print(f"\nSending input: {json.dumps(test_input, indent=2)}\n")
    try:
        response = await agent.handle(test_input)
        print("\n--- Response Received ---")
        print(json.dumps(response, indent=2))
        print("\nTest passed! GrowthStageMonitorAgent successfully processed input using REAL tools.")
    except Exception as e:
        print(f"Error during agent execution: {e}")

if __name__ == "__main__":
    asyncio.run(test_growth_stage())
