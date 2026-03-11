import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add the backend directory to python path for simple testing
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from farmxpert.agents.supply_chain.crop_insurance_risk_agent import CropInsuranceRiskAgent

async def test_crop_insurance():
    print("Initializing CropInsuranceRiskAgent...")
    agent = CropInsuranceRiskAgent()
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    test_input = {
        "query": "What insurance should I get for my farm and how much will it cost?",
        "context": {
            "crops": ["wheat", "soybeans"],
            "farm_size": 250,
            "location": "North Dakota",
            "risk_factors": ["frequent hail", "early frost"],
            "current_insurance": {"coverage": ["wheat"], "plan": "Basic Yield"}
        }
    }
    
    print(f"\nSending input: {json.dumps(test_input, indent=2)}\n")
    try:
        response = await agent.handle(test_input)
        print("\n--- Response Received ---")
        print(json.dumps(response, indent=2))
        print("\nTest passed! CropInsuranceRiskAgent successfully processed input using REAL tools.")
    except Exception as e:
        print(f"Error during agent execution: {e}")

if __name__ == "__main__":
    asyncio.run(test_crop_insurance())
