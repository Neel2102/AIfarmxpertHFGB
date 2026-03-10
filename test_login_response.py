#!/usr/bin/env python3
"""
Test script to check login response from backend
"""

import requests
import json

def test_register_and_login():
    """Test register and login endpoints"""
    base_url = "http://localhost:8000/api"
    
    # First try to register a new user
    register_data = {
        "username": "onboardingtest",
        "email": "onboardingtest@example.com",
        "password": "testpass123",
        "full_name": "Onboarding Test User"
    }
    
    try:
        print("🔄 Testing registration...")
        reg_response = requests.post(f"{base_url}/auth/register", json=register_data)
        print(f"Register Status: {reg_response.status_code}")
        
        if reg_response.status_code == 201:
            print("✅ Registration successful!")
        elif reg_response.status_code == 400 and "already exists" in reg_response.text:
            print("ℹ️ User already exists, proceeding to login...")
        else:
            print("❌ Registration failed:")
            print(reg_response.text)
            return
        
        # Now try to login
        print("\n🔄 Testing login...")
        login_data = {
            "username": "onboardingtest",
            "password": "testpass123",
            "ip_address": "127.0.0.1",
            "user_agent": "test"
        }
        
        login_response = requests.post(f"{base_url}/auth/login", json=login_data)
        print(f"Login Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            result = login_response.json()
            print("✅ Login successful!")
            print("Response:")
            print(json.dumps(result, indent=2))
            
            if 'user' in result:
                user = result['user']
                print(f"\n🎯 User onboarding_completed: {user.get('onboarding_completed', 'MISSING')}")
                print(f"🎯 Type: {type(user.get('onboarding_completed'))}")
                
                if 'onboarding_completed' not in user:
                    print("❌ ERROR: onboarding_completed field is missing from response!")
                elif user['onboarding_completed'] is False:
                    print("✅ onboarding_completed is False - should redirect to onboarding")
                elif user['onboarding_completed'] is True:
                    print("❌ onboarding_completed is True - will go to dashboard")
            else:
                print("❌ ERROR: No user field in response!")
        else:
            print("❌ Login failed!")
            print(login_response.text)
                
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend server at localhost:8000")
        print("Make sure the backend is running!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_register_and_login()
