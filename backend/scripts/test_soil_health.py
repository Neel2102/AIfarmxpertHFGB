import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from farmxpert.agents.agronomy.soil_health_agent import SoilHealthAgent

async def test_soil_health():
    print("🔬 Testing Soil Health Agent...")
    print("-" * 30)
    
    agent = SoilHealthAgent()
    
    # Test cases
    queries = [
        "My soil pH is 5.5, what should I do?",
        "What amendments do I need for sugarcane in Maharashtra?",
        "Analyze my soil NPK: Nitrogen 35, Phosphorus 15, Potassium 20."
    ]
    
    for query in queries:
        print(f"\nUser Query: {query}")
        
        # Simulate input
        inputs = {
            "query": query,
            "context": {
                "farm_location": "Maharashtra",
                "soil_data": {
                    "ph": 5.5 if "5.5" in query else 7.0,
                    "npk": {
                        "nitrogen": 35 if "Nitrogen 35" in query else 45,
                        "phosphorus": 15 if "Phosphorus 15" in query else 25,
                        "potassium": 20 if "Potassium 20" in query else 30
                    }
                }
            }
        }
        
        # Run agent
        response = await agent.handle(inputs)
        
        print(f"Agent Response: {response.get('response')}")
        print("-" * 20)

if __name__ == "__main__":
    asyncio.run(test_soil_health())
