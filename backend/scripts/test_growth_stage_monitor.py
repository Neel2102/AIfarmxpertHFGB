import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from farmxpert.agents.agronomy.growth_stage_monitor_agent import GrowthStageMonitorAgent

async def test_growth_stage_monitor():
    print("🌱 Testing Growth Stage Monitor Agent...")
    print("-" * 30)
    
    agent = GrowthStageMonitorAgent()
    
    queries = [
        "What growth stage is my wheat crop in?",
        "Monitor my rice crop development in Punjab.",
        "Is my maize crop developing normally? Planted 35 days ago."
    ]
    
    for query in queries:
        print(f"\nUser Query: {query}")
        
        inputs = {
            "query": query,
            "context": {
                "farm_location": "Punjab",
                "crop": "wheat" if "wheat" in query else ("rice" if "rice" in query else "maize"),
                "planting_date": "2024-01-01",
                "environmental_data": {
                    "temperature": 25,
                    "rainfall": 50,
                    "humidity": 65
                }
            }
        }
        
        response = await agent.handle(inputs)
        print(f"Agent Response: {response.get('response') or response.get('current_stage')}")
        print("-" * 20)

if __name__ == "__main__":
    asyncio.run(test_growth_stage_monitor())
