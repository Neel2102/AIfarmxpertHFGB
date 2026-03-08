#!/usr/bin/env python3
"""
Test the login API directly
"""
import requests
import json

def test_login_api():
    url = "http://localhost:8000/api/auth/login"
    data = {
        "username": "testuser",
        "password": "password123"
    }
    
    try:
        print(f"🔐 Testing login API: {url}")
        print(f"📤 Data: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, json=data, timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ SUCCESS!")
            print(f"📄 Response: {json.dumps(response.json(), indent=2)}")
        else:
            print("❌ ERROR!")
            print(f"📄 Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error - Backend not running")
    except requests.exceptions.Timeout:
        print("❌ Timeout Error")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

if __name__ == "__main__":
    test_login_api()
