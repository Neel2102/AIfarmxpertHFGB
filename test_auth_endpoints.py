#!/usr/bin/env python3
"""
Test script for authentication endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_login_endpoint():
    """Test the login endpoint"""
    print("Testing login endpoint...")
    
    login_data = {
        "username": "testuser",
        "password": "password123",
        "ip_address": "127.0.0.1",
        "user_agent": "test-script"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=login_data,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Data: {json.dumps(data, indent=2)}")
            
            # Check for cookies
            cookies = response.cookies
            print(f"Cookies: {dict(cookies)}")
            
            if 'access_token' in cookies:
                print("✅ Access token cookie set successfully!")
            else:
                print("❌ Access token cookie not found")
                
        else:
            print(f"Error Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

def test_logout_endpoint():
    """Test the logout endpoint"""
    print("\nTesting logout endpoint...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/logout",
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Logout endpoint working!")
        else:
            print("❌ Logout endpoint failed")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

def test_health_endpoint():
    """Test if the server is running"""
    print("Testing server health...")
    
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        print(f"Server Status: {response.status_code}")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Server not accessible: {e}")
        return False

if __name__ == "__main__":
    print("🔐 Authentication Flow Test Script")
    print("=" * 50)
    
    # Test server health first
    if test_health_endpoint():
        # Test login
        test_login_endpoint()
        
        # Test logout
        test_logout_endpoint()
    else:
        print("❌ Server is not running. Please start the backend server first.")
    
    print("\n" + "=" * 50)
    print("Test completed!")
