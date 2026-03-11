import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from farmxpert.agents.agronomy.seed_selection_agent import SeedSelectionAgent

async def test_seed_selection():
    print("🌱 Testing Seed Selection Agent...")
    print("-" * 30)
    
    agent = SeedSelectionAgent()
    
    # Test cases
    queries = [
        "What are the best rice varieties for high yield in Tamil Nadu?",
        "Recommend some disease resistant wheat varieties for Punjab.",
        "I want to grow maize in Gujarat, which seeds are best for low budget?"
    ]
    
    for query in queries:
        print(f"\nUser Query: {query}")
        
        # Simulate input
        inputs = {
            "query": query,
            "context": {
                "farm_location": "Tamil Nadu" if "Tamil Nadu" in query else ("Punjab" if "Punjab" in query else "Gujarat"),
                "preferences": {
                    "goal": "high_yield" if "high yield" in query else "disease_resistant",
                    "budget": "low" if "low budget" in query else "medium"
                },
                "soil_data": {"ph": 6.5, "type": "clay_loam"}
            }
        }
        
        # Run agent
        response = await agent.handle(inputs)
        
        print(f"Agent Response: {response.get('response')}")
        if response.get('recommendations'):
            print(f"Recommendations: {response.get('recommendations')}")
        print("-" * 20)

if __name__ == "__main__":
    asyncio.run(test_seed_selection())
