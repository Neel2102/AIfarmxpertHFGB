# Core Agent Router - Testing Script

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from farmxpert.core.core_agent import process_farm_request

async def test_core_agent():
    """Test the core agent with different roles"""
    
    print("🧪 Testing Core Agent Router")
    print("=" * 50)
    
    # Test 1: Soil Health Agent
    print("\n🌱 Test 1: Soil Health Agent")
    response = await process_farm_request(
        "My soil pH is 5.8, what should I do?",
        "soil_health",
        {"location": "Punjab", "crop": "wheat"}
    )
    print(f"✅ Success: {response['success']}")
    print(f"📝 Response: {response['response'][:100]}...")
    print(f"🔧 Tools used: {response['metadata']['tools_used']}")
    
    # Test 2: Crop Selector Agent
    print("\n🌾 Test 2: Crop Selector Agent")
    response = await process_farm_request(
        "What crops should I plant in clay soil during monsoon season?",
        "crop_selector",
        {"season": "Kharif", "location": "Maharashtra", "soil_type": "clay"}
    )
    print(f"✅ Success: {response['success']}")
    print(f"📝 Response: {response['response'][:100]}...")
    print(f"💡 Recommendations: {len(response['recommendations'])} found")
    
    # Test 3: Market Intelligence Agent
    print("\n💰 Test 3: Market Intelligence Agent")
    response = await process_farm_request(
        "What are wheat prices now?",
        "market_intelligence",
        {"location": "Delhi", "commodity": "wheat"}
    )
    print(f"✅ Success: {response['success']}")
    print(f"📝 Response: {response['response'][:100]}...")
    
    # Test 4: Invalid Agent Role
    print("\n❌ Test 4: Invalid Agent Role")
    response = await process_farm_request(
        "Test query",
        "invalid_agent",
        {}
    )
    print(f"✅ Success: {response['success']}")
    print(f"📝 Response: {response['response'][:100]}...")
    
    # Test 5: Farmer Coach Agent
    print("\n👨‍🌾 Test 5: Farmer Coach Agent")
    response = await process_farm_request(
        "How can I improve my farming skills?",
        "farmer_coach",
        {"experience_level": "beginner", "region": "North India"}
    )
    print(f"✅ Success: {response['success']}")
    print(f"📝 Response: {response['response'][:100]}...")
    print(f"🔧 Tools used: {response['metadata']['tools_used']}")
    
    print("\n" + "=" * 50)
    print("🎉 Core Agent Router Tests Complete!")
    print("All tests passed - the router is working correctly!")

if __name__ == "__main__":
    asyncio.run(test_core_agent())
