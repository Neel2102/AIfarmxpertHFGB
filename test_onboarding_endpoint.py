#!/usr/bin/env python3
"""
Test script to check onboarding completion endpoint
"""

import requests
import json

def test_onboarding_complete():
    """Test onboarding completion endpoint"""
    url = "http://localhost:8000/api/auth/onboarding/complete"
    
    # Test data - you'll need a valid access token
    headers = {
        "Authorization": "Bearer YOUR_ACCESS_TOKEN_HERE",
        "Content-Type": "application/json"
    }
    
    data = {
        "farm_size": "5 acres",
        "location": "California",
        "crops": ["wheat", "corn"],
        "experience": "intermediate"
    }
    
    try:
        print("🔄 Testing onboarding completion endpoint...")
        print(f"URL: {url}")
        print(f"Data: {json.dumps(data, indent=2)}")
        print()
        
        response = requests.post(url, json=data, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print()
        
        try:
            result = response.json()
            print("Response:")
            print(json.dumps(result, indent=2))
        except:
            print(f"Raw response: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend server at localhost:8000")
        print("Make sure the backend is running!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("⚠️  This test requires a valid access token")
    print("⚠️  Replace 'YOUR_ACCESS_TOKEN_HERE' with a real token")
    print()
    test_onboarding_complete()
