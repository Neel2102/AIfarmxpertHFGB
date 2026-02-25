import asyncio
import os
import sys

# Add project root to path (assuming running from AIfarmxpert root)
sys.path.append(os.getcwd())

from farmxpert.core.super_agent import SuperAgent

async def test_routing():
    agent = SuperAgent()
    
    print("\n--- TEST 1: General Conversation ---")
    query1 = "Hi, how are you?"
    print(f"Query: {query1}")
    response1 = await agent.process_query(query1, session_id="test_session")
    print(f"Response: {response1.natural_language}")
    print(f"Agents Used: {len(response1.agent_responses)}")
    
    if len(response1.agent_responses) == 0:
        print("PASS: No agents triggered for general query.")
    else:
        print(f"FAIL: Agents triggered: {[r.agent_name for r in response1.agent_responses]}")

    print("\n--- TEST 2: Advisory Query ---")
    query2 = "What yield can I expect for Wheat on 5 acres?"
    print(f"Query: {query2}")
    response2 = await agent.process_query(query2, context={"farm_size": "5 acres", "soil_type": "loam"}, session_id="test_session")
    print(f"Response: {response2.natural_language[:100]}...")
    print(f"Agents Used: {len(response2.agent_responses)}")
    
    if len(response2.agent_responses) > 0:
        print("PASS: Agents triggered for advisory query.")
    else:
        print("FAIL: No agents triggered for advisory query.")

if __name__ == "__main__":
    asyncio.run(test_routing())
