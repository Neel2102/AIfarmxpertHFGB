import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add the backend directory to python path for simple testing
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from farmxpert.agents.agronomy.crop_selector_agent import CropSelectorAgent

async def test_crop_agent():
    print("Initializing CropSelectorAgent...")
    agent = CropSelectorAgent()
    
    # Enable debug logging if the agent uses it
    import logging
    logging.basicConfig(level=logging.INFO)
    
    test_input = {
        "query": "What crops are good for clay soil in summer?",
        "location": "Maharashtra",
        "season": "Summer",
        "soil": {
            "ph": 7.0,
            "nitrogen": 15
        }
    }
    
    print(f"\nSending input: {json.dumps(test_input, indent=2)}\n")
    try:
        response = await agent.handle(test_input)
        print("\n--- Response Received ---")
        print(json.dumps(response, indent=2))
        print("\nTest passed! Agent successfully processed input using REAL tools.")
    except Exception as e:
        print(f"Error during agent execution: {e}")

if __name__ == "__main__":
    asyncio.run(test_crop_agent())
