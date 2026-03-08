"""
Simple test script to check the API endpoints without complex dependencies
"""

import requests
import json

def test_endpoints():
    """Test the basic API endpoints"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing API Endpoints")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n🏥 Test 1: Health Check")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check passed")
            print(f"📊 Status: {data.get('status')}")
            print(f"🤖 Core Agent: {data.get('core_agent')}")
            print(f"📈 Available Agents: {data.get('available_agents')}")
        else:
            print(f"❌ Health check failed: {response.text}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test 2: Root endpoint
    print("\n🏠 Test 2: Root Endpoint")
    try:
        response = requests.get(f"{base_url}/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ Root endpoint working")
            print(f"📊 Architecture: {data.get('architecture')}")
            print(f"🔗 Endpoints: {list(data.get('endpoints', {}).keys())}")
        else:
            print(f"❌ Root endpoint failed: {response.text}")
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
    
    # Test 3: Super Agent Chat (this should work)
    print("\n💬 Test 3: Super Agent Chat")
    try:
        response = requests.post(
            f"{base_url}/api/super-agent/chat",
            json={
                "message": "Hello, can you help me with farming?",
                "context": {"location": "Test"}
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ Super agent chat working")
            print(f"💬 Response: {data.get('response', '')[:100]}...")
        else:
            print(f"❌ Super agent chat failed: {response.text}")
    except Exception as e:
        print(f"❌ Super agent chat error: {e}")
    
    # Test 4: Direct agent call
    print("\n🤖 Test 4: Direct Agent Call")
    try:
        response = requests.post(
            f"{base_url}/api/agents/soil_health",
            json={
                "query": "My soil pH is 6.5, is this good?",
                "context": {"location": "Punjab"}
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ Direct agent call working")
            print(f"💬 Response: {data.get('response', '')[:100]}...")
        else:
            print(f"❌ Direct agent call failed: {response.text}")
    except Exception as e:
        print(f"❌ Direct agent call error: {e}")

if __name__ == "__main__":
    test_endpoints()
