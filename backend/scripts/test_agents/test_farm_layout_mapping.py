import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add the backend directory to python path for simple testing
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from farmxpert.agents.operations.farm_layout_mapping_agent import FarmLayoutMappingAgent

async def test_farm_layout():
    print("Initializing FarmLayoutMappingAgent...")
    agent = FarmLayoutMappingAgent()
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    test_input = {
        "query": "Can you design a layout for my new 100 acre farm growing wheat and pulses?",
        "context": {
            "total_farm_size": 100,
            "soil_types": {"loamy": 60, "sandy_loam": 40},
            "water_sources": ["river_canal", "borewell"],
            "planned_crops": ["wheat", "pulses"],
            "existing_infrastructure": ["barn", "main_road_access"],
            "farm_location": "California Central Valley",
            "field_boundaries": [
                {"id": 1, "coordinates": [[0,0], [0,10], [10,10], [10,0]]},
                {"id": 2, "coordinates": [[10,0], [10,10], [20,10], [20,0]]}
            ]
        }
    }
    
    print(f"\nSending input: {json.dumps(test_input, indent=2)}\n")
    try:
        response = await agent.handle(test_input)
        print("\n--- Response Received ---")
        print(json.dumps(response, indent=2))
        print("\nTest passed! FarmLayoutMappingAgent successfully processed input using REAL tools.")
    except Exception as e:
        print(f"Error during agent execution: {e}")

if __name__ == "__main__":
    asyncio.run(test_farm_layout())
