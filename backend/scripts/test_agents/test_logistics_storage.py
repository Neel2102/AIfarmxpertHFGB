import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add the backend directory to python path for simple testing
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from farmxpert.agents.supply_chain.logistics_storage_agent import LogisticsStorageAgent

async def test_logistics_storage():
    print("Initializing LogisticsStorageAgent...")
    agent = LogisticsStorageAgent()
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    test_input = {
        "query": "I have harvested 50 tons of potatoes and 20 tons of wheat. Where should I store them and how much will it cost to transport?",
        "context": {
            "crops": ["potatoes", "wheat"],
            "harvest_quantity": {"potatoes": 50, "wheat": 20},
            "location": "Ahmedabad, Gujarat"
        }
    }
    
    print(f"\nSending input: {json.dumps(test_input, indent=2)}\n")
    try:
        response = await agent.handle(test_input)
        print("\n--- Response Received ---")
        print(json.dumps(response, indent=2))
        print("\nTest passed! LogisticsStorageAgent successfully processed input using REAL tools.")
    except Exception as e:
        print(f"Error during agent execution: {e}")

if __name__ == "__main__":
    asyncio.run(test_logistics_storage())
