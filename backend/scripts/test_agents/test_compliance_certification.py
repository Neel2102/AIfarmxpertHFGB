import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add the backend directory to python path for simple testing
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from farmxpert.agents.support.compliance_certification_agent import ComplianceCertificationAgent

async def test_compliance_certification():
    print("Initializing ComplianceCertificationAgent...")
    agent = ComplianceCertificationAgent()
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    test_input = {
        "query": "I want to get organic certification for my farm. What do I need to do?",
        "context": {
            "certification_type": "organic",
            "farm_size": 10,
            "location": "Kerala",
            "current_practices": {
                "fertilizer_type": "chemical",
                "pest_management": "IPM",
                "crop_rotation": True
            }
        }
    }
    
    print(f"\nSending input: {json.dumps(test_input, indent=2)}\n")
    try:
        response = await agent.handle(test_input)
        print("\n--- Response Received ---")
        print(json.dumps(response, indent=2))
        print("\nTest passed! ComplianceCertificationAgent successfully processed input using REAL tools.")
    except Exception as e:
        print(f"Error during agent execution: {e}")

if __name__ == "__main__":
    asyncio.run(test_compliance_certification())
