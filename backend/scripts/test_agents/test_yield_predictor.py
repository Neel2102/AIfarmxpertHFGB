import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add the backend directory to python path for simple testing
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from farmxpert.agents.analytics.yield_predictor_agent import YieldPredictorAgent

async def test_yield_predictor():
    print("Initializing YieldPredictorAgent...")
    agent = YieldPredictorAgent()
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    test_input = {
        "query": "What is my expected wheat yield this season?",
        "context": {
            "crop": "wheat",
            "area": 10.0,
            "soil_data": {
                "ph": 6.8,
                "npk": {"nitrogen": 120, "phosphorus": 40, "potassium": 80},
                "organic_matter": 2.5
            },
            "weather_data": {
                "average_temperature": 22,
                "total_rainfall": 85,
                "drought_days": 2
            }
        }
    }
    
    print(f"\nSending input: {json.dumps(test_input, indent=2)}\n")
    try:
        response = await agent.handle(test_input)
        print("\n--- Response Received ---")
        print(json.dumps(response, indent=2))
        print("\nTest passed! YieldPredictorAgent successfully processed input.")
    except Exception as e:
        print(f"Error during agent execution: {e}")

if __name__ == "__main__":
    asyncio.run(test_yield_predictor())
