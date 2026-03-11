import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add the backend directory to python path for simple testing
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from farmxpert.agents.support.community_engagement_agent import CommunityEngagementAgent

async def test_community_engagement():
    print("Initializing CommunityEngagementAgent...")
    agent = CommunityEngagementAgent()
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    test_input = {
        "query": "I'm looking to join a cooperative. Any suggestions?",
        "context": {
            "location": "Pune, Maharashtra",
            "farm_size": 15,
            "farmer_interests": ["sustainable farming", "bulk purchasing", "market access"]
        }
    }
    
    print(f"\nSending input: {json.dumps(test_input, indent=2)}\n")
    try:
        response = await agent.handle(test_input)
        print("\n--- Response Received ---")
        print(json.dumps(response, indent=2))
        print("\nTest passed! CommunityEngagementAgent successfully processed input using REAL tools.")
    except Exception as e:
        print(f"Error during agent execution: {e}")

if __name__ == "__main__":
    asyncio.run(test_community_engagement())
