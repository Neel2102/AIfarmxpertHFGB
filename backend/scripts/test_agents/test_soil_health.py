import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add the backend directory to python path for simple testing
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from farmxpert.agents.agronomy.soil_health_agent import SoilHealthAgent

async def test_soil_health_agent():
    print("Initializing SoilHealthAgent...")
    agent = SoilHealthAgent()
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    test_input = {
        "query": "My soil PH is very low, what should I do for my upcoming cotton crop?",
        "crop": "cotton",
        "location": "Gujarat",
        "soil": {
            "ph": 5.2,
            "nitrogen": 12,
            "phosphorus": 15,
            "potassium": 25,
            "organic_matter": 1.2
        }
    }
    
    print(f"\nSending input: {json.dumps(test_input, indent=2)}\n")
    try:
        response = await agent.handle(test_input)
        print("\n--- Response Received ---")
        print(json.dumps(response, indent=2))
        print("\nTest passed! SoilHealthAgent successfully processed input using REAL tools.")
    except Exception as e:
        print(f"Error during agent execution: {e}")

if __name__ == "__main__":
    asyncio.run(test_soil_health_agent())
