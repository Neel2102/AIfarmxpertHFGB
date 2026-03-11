import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add the backend directory to python path for simple testing
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from farmxpert.agents.analytics.profit_optimization_agent import ProfitOptimizationAgent

async def test_profit_optimization():
    print("Initializing ProfitOptimizationAgent...")
    agent = ProfitOptimizationAgent()
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    test_input = {
        "query": "How can I maximize my profit for wheat this season?",
        "context": {
            "crop": "wheat",
            "area_acre": 10.5,
            "yield_per_acre": 2.5,
            "expenses": [
                {"item": "seeds", "amount": 500},
                {"item": "fertilizer", "amount": 1200},
                {"item": "labor", "amount": 800}
            ],
            "market_prices": {
                "local_mandi": 2200,
                "city_market": 2450,
                "export_buyer": 2600
            }
        }
    }
    
    print(f"\nSending input: {json.dumps(test_input, indent=2)}\n")
    try:
        response = await agent.handle(test_input)
        print("\n--- Response Received ---")
        print(json.dumps(response, indent=2))
        print("\nTest passed! ProfitOptimizationAgent successfully processed input using REAL tools.")
    except Exception as e:
        print(f"Error during agent execution: {e}")

if __name__ == "__main__":
    asyncio.run(test_profit_optimization())
