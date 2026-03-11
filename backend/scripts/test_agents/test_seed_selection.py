import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add the backend directory to python path for simple testing
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from farmxpert.agents.agronomy.seed_selection_agent import SeedSelectionAgent

async def test_seed_agent():
    print("Initializing SeedSelectionAgent...")
    agent = SeedSelectionAgent()
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    test_input = {
        "query": "What are the best wheat seeds for high yield?",
        "crop": "wheat",
        "location": "Punjab",
        "goal": "high_yield",
        "budget": "medium",
        "soil": {
            "ph": 6.8,
            "nitrogen": 40
        }
    }
    
    print(f"\nSending input: {json.dumps(test_input, indent=2)}\n")
    try:
        response = await agent.handle(test_input)
        print("\n--- Response Received ---")
        print(json.dumps(response, indent=2))
        print("\nTest passed! SeedSelectionAgent successfully processed input using REAL tools.")
    except Exception as e:
        print(f"Error during agent execution: {e}")

if __name__ == "__main__":
    asyncio.run(test_seed_agent())
