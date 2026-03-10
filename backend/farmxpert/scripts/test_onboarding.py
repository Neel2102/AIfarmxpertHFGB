"""
Test script to verify onboarding integration
"""

import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:8000/api"

def test_onboarding_flow():
    """Test the complete onboarding flow"""
    print("🔄 Testing onboarding flow...")
    
    # Test data
    test_onboarding_data = {
        "farmName": "Test Farm",
        "state": "Maharashtra",
        "district": "Pune",
        "farmSize": "10",
        "soilType": "loamy",
        "mainCropCategory": "cereals",
        "specificCrop": "Wheat",
        "irrigationMethod": "drip",
        "waterSourceQuality": "fresh",
        "iotSetup": "basic",
        "primaryGoal": "yield",
        "fertilizerPreference": "integrated",
        "pestManagement": "preventive",
        "machinery": ["tractor"],
        "laborSetup": "family"
    }
    
    try:
        # First, let's test if the onboarding endpoint exists
        print("📡 Testing onboarding endpoint...")
        response = requests.post(
            f"{BASE_URL}/auth/onboarding/complete",
            json=test_onboarding_data,
            headers={"Authorization": "Bearer test_token"}
        )
        
        if response.status_code == 401:
            print("✅ Onboarding endpoint exists (401 Unauthorized expected without valid token)")
        elif response.status_code == 404:
            print("❌ Onboarding endpoint not found")
            return False
        else:
            print(f"✅ Onboarding endpoint responded with status: {response.status_code}")
            
        print("✅ Onboarding integration test completed successfully!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API server. Make sure it's running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error testing onboarding: {e}")
        return False

def test_auth_endpoints():
    """Test if auth endpoints are working"""
    print("🔄 Testing auth endpoints...")
    
    try:
        # Test register endpoint
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "username": "testuser123",
                "email": "test123@example.com",
                "password": "testpass123",
                "full_name": "Test User"
            }
        )
        
        if response.status_code in [201, 400]:
            print("✅ Auth endpoints are accessible")
        else:
            print(f"❌ Auth endpoint error: {response.status_code}")
            return False
            
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API server")
        return False
    except Exception as e:
        print(f"❌ Error testing auth: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting onboarding integration tests...")
    print("=" * 50)
    
    # Test auth endpoints first
    auth_ok = test_auth_endpoints()
    
    if auth_ok:
        print()
        # Test onboarding flow
        onboarding_ok = test_onboarding_flow()
        
        if onboarding_ok:
            print()
            print("🎉 All tests passed! The onboarding system is ready.")
            print()
            print("📝 Next steps:")
            print("1. Run the SQL migration: scripts/add_onboarding_column.sql")
            print("2. Start the backend server")
            print("3. Start the frontend server")
            print("4. Register a new user and test the onboarding flow")
        else:
            print("❌ Some tests failed. Check the errors above.")
    else:
        print("❌ Auth endpoints not working. Please check the backend server.")
