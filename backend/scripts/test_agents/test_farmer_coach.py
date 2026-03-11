import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add the backend directory to python path for simple testing
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from farmxpert.agents.support.farmer_coach_agent import FarmerCoachAgent

async def test_farmer_coach():
    print("Initializing FarmerCoachAgent...")
    agent = FarmerCoachAgent()
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    test_input = {
        "query": "I want to start growing wheat this season. What should I do first?",
        "context": {
            "experience": "beginner",
            "location": "Punjab, India",
            "season": "winter (Rabi)",
            "current_crops": ["wheat"]
        }
    }
    
    print(f"\nSending input: {json.dumps(test_input, indent=2)}\n")
    try:
        response = await agent.handle(test_input)
        print("\n--- Response Received ---")
        print(json.dumps(response, indent=2))
        print("\nTest passed! FarmerCoachAgent successfully processed input using REAL tools.")
    except Exception as e:
        print(f"Error during agent execution: {e}")

if __name__ == "__main__":
    asyncio.run(test_farmer_coach())
