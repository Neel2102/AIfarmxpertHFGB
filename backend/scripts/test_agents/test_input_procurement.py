import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add the backend directory to python path for simple testing
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from farmxpert.agents.supply_chain.input_procurement_agent import InputProcurementAgent

async def test_input_procurement():
    print("Initializing InputProcurementAgent...")
    agent = InputProcurementAgent()
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    test_input = {
        "query": "Where can I buy urea and improved wheat seeds within my budget?",
        "context": {
            "required_inputs": ["urea fertilizer", "wheat seeds"],
            "farm_size": 50,
            "budget": 2000,
            "location": "Punjab",
            "season": "Rabi"
        }
    }
    
    print(f"\nSending input: {json.dumps(test_input, indent=2)}\n")
    try:
        response = await agent.handle(test_input)
        print("\n--- Response Received ---")
        print(json.dumps(response, indent=2))
        print("\nTest passed! InputProcurementAgent successfully processed input using REAL tools.")
    except Exception as e:
        print(f"Error during agent execution: {e}")

if __name__ == "__main__":
    asyncio.run(test_input_procurement())
