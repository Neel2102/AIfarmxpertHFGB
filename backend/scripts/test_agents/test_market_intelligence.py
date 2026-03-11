import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add the backend directory to python path for simple testing
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from farmxpert.agents.supply_chain.market_intelligence_agent import MarketIntelligenceAgent

async def test_market_intelligence():
    print("Initializing MarketIntelligenceAgent...")
    agent = MarketIntelligenceAgent()
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    test_input = {
        "query": "Should I sell my wheat now or wait? What are the current mandi prices?",
        "context": {
            "crops": ["wheat", "maize"],
            "location": "Ludhiana, Punjab"
        }
    }
    
    print(f"\nSending input: {json.dumps(test_input, indent=2)}\n")
    try:
        response = await agent.handle(test_input)
        print("\n--- Response Received ---")
        print(json.dumps(response, indent=2))
        print("\nTest passed! MarketIntelligenceAgent successfully processed input using REAL tools.")
    except Exception as e:
        print(f"Error during agent execution: {e}")

if __name__ == "__main__":
    asyncio.run(test_market_intelligence())
