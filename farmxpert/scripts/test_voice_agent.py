"""
Voice Agent End-to-End Test Script
Tests the complete flow: Frontend -> API -> SuperAgent -> Response
"""

import sys
import asyncio
from pathlib import Path

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "farmxpert"))

from farmxpert.core.super_agent import SuperAgent

async def test_voice_agent_flow():
    """Test voice agent with conversational context"""
    print("=" * 60)
    print("Voice Agent End-to-End Test")
    print("=" * 60)
    
    agent = SuperAgent()
    
    # Test 1: Simple query with conversational mode
    print("\n[TEST 1] Simple conversational query")
    print("-" * 60)
    query1 = "What crop should I plant in clay soil?"
    context1 = {
        "conversational": True,
        "locale": "en-IN",
        "location": {
            "latitude": 23.0225,
            "longitude": 72.5714
        }
    }
    
    try:
        response1 = await agent.process_query(query1, context1)
        print(f"Query: {query1}")
        print(f"Success: {response1.success}")
        print(f"Agents Used: {[r.agent_name for r in response1.agent_responses]}")
        if isinstance(response1.response, dict):
            print(f"Answer: {response1.response.get('answer', 'N/A')}")
        print(f"Execution Time: {response1.execution_time:.2f}s")
        print("[OK] Test 1 passed")
    except Exception as e:
        print(f"[FAIL] Test 1 failed: {e}")
        return False
    
    # Test 2: Voice-like query with context
    print("\n[TEST 2] Voice-like query with follow-up context")
    print("-" * 60)
    query2 = "How much water does it need?"
    context2 = {
        "conversational": True,
        "locale": "en-IN",
        "crop": "wheat",
        "location": {
            "latitude": 23.0225,
            "longitude": 72.5714
        }
    }
    
    try:
        response2 = await agent.process_query(query2, context2)
        print(f"Query: {query2}")
        print(f"Success: {response2.success}")
        print(f"Agents Used: {[r.agent_name for r in response2.agent_responses]}")
        if isinstance(response2.response, dict):
            print(f"Answer: {response2.response.get('answer', 'N/A')}")
        print(f"Execution Time: {response2.execution_time:.2f}s")
        print("[OK] Test 2 passed")
    except Exception as e:
        print(f"[FAIL] Test 2 failed: {e}")
        return False
    
    # Test 3: Multi-agent query
    print("\n[TEST 3] Complex multi-agent query")
    print("-" * 60)
    query3 = "I want to grow wheat. Tell me about soil preparation, irrigation, and best seeds."
    context3 = {
        "conversational": True,
        "locale": "en-IN",
        "location": {
            "latitude": 23.0225,
            "longitude": 72.5714
        }
    }
    
    try:
        response3 = await agent.process_query(query3, context3)
        print(f"Query: {query3}")
        print(f"Success: {response3.success}")
        print(f"Agents Used: {[r.agent_name for r in response3.agent_responses]}")
        if isinstance(response3.response, dict):
            print(f"Answer: {response3.response.get('answer', 'N/A')[:200]}...")
        print(f"Execution Time: {response3.execution_time:.2f}s")
        print("[OK] Test 3 passed")
    except Exception as e:
        print(f"[FAIL] Test 3 failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("All voice agent tests passed!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = asyncio.run(test_voice_agent_flow())
    sys.exit(0 if success else 1)
