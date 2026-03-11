import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add the backend directory to python path for simple testing
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from farmxpert.agents.agronomy.fertilizer_advisor_agent import FertilizerAdvisorAgent

async def test_fertilizer_advisor():
    print("Initializing FertilizerAdvisorAgent...")
    agent = FertilizerAdvisorAgent()
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    test_input = {
        "query": "What fertilizer should I apply for my wheat crop currently in the vegetative stage? Rain is expected soon.",
        "crop": "wheat",
        "growth_stage": "vegetative",
        "location": "Punjab",
        "soil_data": {
            "ph": 6.8,
            "nitrogen": 20,
            "phosphorus": 15,
            "potassium": 40
        },
        "area_acres": 2.5
    }
    
    print(f"\nSending input: {json.dumps(test_input, indent=2)}\n")
    try:
        response = await agent.handle(test_input)
        print("\n--- Response Received ---")
        print(json.dumps(response, indent=2))
        print("\nTest passed! FertilizerAdvisorAgent successfully processed input using REAL tools.")
    except Exception as e:
        print(f"Error during agent execution: {e}")

if __name__ == "__main__":
    asyncio.run(test_fertilizer_advisor())
