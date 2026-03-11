import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from farmxpert.agents.agronomy.crop_selector_agent import CropSelectorAgent
from farmxpert.config.settings import settings

async def test_crop_selector():
    print("🌾 Testing Crop Selector Agent...")
    print("-" * 30)
    
    agent = CropSelectorAgent()
    
    # Test cases
    queries = [
        "What crops should I plant in Punjab during Rabi season with loamy soil?",
        "I have clay soil in Gujarat, recommend some crops for Kharif.",
        "What is the market price for Wheat in Haryana?"
    ]
    
    for query in queries:
        print(f"\nUser Query: {query}")
        
        # Simulate input
        inputs = {
            "query": query,
            "context": {
                "farm_location": "Punjab" if "Punjab" in query else ("Gujarat" if "Gujarat" in query else "Haryana"),
                "state": "Punjab" if "Punjab" in query else ("Gujarat" if "Gujarat" in query else "Haryana"),
                "district": "Ludhiana",
                "season": "Rabi" if "Rabi" in query else "Kharif",
                "soil": {"ph": 6.8, "type": "loamy" if "loamy" in query else "clay"}
            },
            "session_id": "test_session_123"
        }
        
        # Run agent
        response = await agent.handle(inputs)
        
        print(f"Agent Response: {response.get('response')}")
        if response.get('recommendations'):
            print(f"Recommendations: {response.get('recommendations')}")
        if response.get('metadata', {}).get('tools_used'):
             print(f"Tools Used: {response.get('metadata', {}).get('tools_used')}")
        print("-" * 20)

if __name__ == "__main__":
    asyncio.run(test_crop_selector())
