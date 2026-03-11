import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add the backend directory to python path for simple testing
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from farmxpert.agents.agronomy.pest_disease_diagnostic_agent import PestDiseaseDiagnosticAgent

async def test_pest_disease_agent():
    print("Initializing PestDiseaseDiagnosticAgent...")
    agent = PestDiseaseDiagnosticAgent()
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    test_input = {
        "query": "My wheat crop has yellowing leaves and brown spots.",
        "crop": "wheat",
        "location": "Punjab",
        "symptoms": ["yellowing leaves", "brown spots"],
        "environmental_data": {
            "temperature": 28,
            "humidity": 85,
            "recent_rainfall": True
        },
        "voice_data": {
            "transcript": "Hi, I have noticed some problems with my wheat. The leaves are turning yellow with some brown circular patches on them."
        }
    }
    
    print(f"\nSending input: {json.dumps(test_input, indent=2)}\n")
    try:
        response = await agent.handle(test_input)
        print("\n--- Response Received ---")
        print(json.dumps(response, indent=2))
        print("\nTest passed! PestDiseaseDiagnosticAgent successfully processed input using REAL tools.")
    except Exception as e:
        print(f"Error during agent execution: {e}")

if __name__ == "__main__":
    asyncio.run(test_pest_disease_agent())
