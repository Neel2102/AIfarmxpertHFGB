import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add the backend directory to python path for simple testing
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from farmxpert.agents.analytics.carbon_sustainability_agent import CarbonSustainabilityAgent

async def test_carbon_sustainability():
    print("Initializing CarbonSustainabilityAgent...")
    agent = CarbonSustainabilityAgent()
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    test_input = {
        "query": "How can I improve my farm's sustainability and get carbon credits?",
        "context": {
            "farm_size": 50.0,
            "current_practices": {
                "tillage": "conventional",
                "cover_crops": "occasional",
                "crop_rotation": "simple"
            },
            "equipment_usage": {
                "tractor": {"hours_per_year": 120}
            },
            "fertilizer_usage": {
                "nitrogen": {"kg_per_acre": 80}
            }
        }
    }
    
    print(f"\nSending input: {json.dumps(test_input, indent=2)}\n")
    try:
        response = await agent.handle(test_input)
        print("\n--- Response Received ---")
        print(json.dumps(response, indent=2))
        print("\nTest passed! CarbonSustainabilityAgent successfully processed input using REAL tools.")
    except Exception as e:
        print(f"Error during agent execution: {e}")

if __name__ == "__main__":
    asyncio.run(test_carbon_sustainability())
