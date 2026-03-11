import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from farmxpert.agents.agronomy.fertilizer_advisor_agent import FertilizerAdvisorAgent

async def test_fertilizer_advisor():
    print("🌿 Testing Fertilizer Advisor Agent...")
    print("-" * 30)
    
    agent = FertilizerAdvisorAgent()
    
    # Test cases
    queries = [
        "What fertilizer should I use for wheat during vegetative stage?",
        "Create a fertilizer schedule for rice in Punjab for 2 acres.",
        "How do I adjust my fertilizer schedule for upcoming rain next week?"
    ]
    
    for query in queries:
        print(f"\nUser Query: {query}")
        
        # Simulate input
        inputs = {
            "query": query,
            "context": {
                "farm_location": "Punjab",
                "crop": "rice" if "rice" in query else "wheat",
                "growth_stage": "vegetative",
                "area_acres": 2.0 if "2 acres" in query else 1.0,
                "soil_data": {
                    "ph": 6.5,
                    "npk": {"nitrogen": 45, "phosphorus": 25, "potassium": 30}
                }
            }
        }
        
        # Run agent
        response = await agent.handle(inputs)
        
        print(f"Agent Response: {response.get('response')}")
        print("-" * 20)

if __name__ == "__main__":
    asyncio.run(test_fertilizer_advisor())
