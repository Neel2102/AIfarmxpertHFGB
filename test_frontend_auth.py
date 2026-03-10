#!/usr/bin/env python3
"""
Test frontend authentication by simulating browser behavior
"""

import requests
import json
from urllib.parse import urljoin

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3001"

class FrontendAuthTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.cookies.clear()
    
    def test_frontend_login(self):
        """Test login through the frontend API"""
        print("🔐 Testing Frontend Login Flow")
        print("=" * 50)
        
        # Test login endpoint
        login_data = {
            "username": "testuser",
            "password": "password123",
            "ip_address": "127.0.0.1",
            "user_agent": "frontend-test"
        }
        
        try:
            response = self.session.post(
                f"{BASE_URL}/api/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"Login Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Login successful!")
                print(f"User: {data.get('user', {}).get('username', 'Unknown')}")
                print(f"Token Type: {data.get('token_type', 'Unknown')}")
                
                # Check cookies
                cookies = dict(self.session.cookies)
                print(f"Cookies received: {list(cookies.keys())}")
                
                return True
            else:
                print(f"❌ Login failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def test_protected_route(self):
        """Test access to protected routes"""
        print("\n🛡️ Testing Protected Route Access")
        print("=" * 50)
        
        try:
            # Test /api/auth/me endpoint
            response = self.session.get(
                f"{BASE_URL}/api/auth/me",
                timeout=10
            )
            
            print(f"Protected Route Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Protected route access successful!")
                print(f"Authenticated User: {data.get('username', 'Unknown')}")
                return True
            else:
                print(f"❌ Protected route access denied: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Protected route error: {e}")
            return False
    
    def test_logout(self):
        """Test logout functionality"""
        print("\n🚪 Testing Logout Flow")
        print("=" * 50)
        
        try:
            response = self.session.post(
                f"{BASE_URL}/api/auth/logout",
                timeout=10
            )
            
            print(f"Logout Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Logout successful!")
                print(f"Message: {data.get('message', 'Unknown')}")
                
                # Check if cookies were cleared
                remaining_cookies = dict(self.session.cookies)
                if not remaining_cookies:
                    print("✅ All cookies cleared successfully!")
                else:
                    print(f"⚠️ Some cookies remain: {list(remaining_cookies.keys())}")
                
                return True
            else:
                print(f"❌ Logout failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Logout error: {e}")
            return False
    
    def test_post_logout_access(self):
        """Test that protected routes are inaccessible after logout"""
        print("\n🔒 Testing Post-Logout Protection")
        print("=" * 50)
        
        try:
            response = self.session.get(
                f"{BASE_URL}/api/auth/me",
                timeout=10
            )
            
            print(f"Post-Logout Access Status: {response.status_code}")
            
            if response.status_code == 401 or response.status_code == 403:
                print("✅ Post-logout protection working!")
                print("Protected routes correctly deny access after logout")
                return True
            else:
                print(f"❌ Post-logout protection failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Post-logout test error: {e}")
            return False
    
    def run_full_test(self):
        """Run complete authentication flow test"""
        print("🧪 Frontend Authentication Flow Test")
        print("=" * 60)
        
        # Test login
        login_success = self.test_frontend_login()
        
        if login_success:
            # Test protected route access
            protected_success = self.test_protected_route()
            
            # Test logout
            logout_success = self.test_logout()
            
            # Test post-logout protection
            post_logout_success = self.test_post_logout_access()
            
            # Summary
            print("\n📊 Test Summary")
            print("=" * 50)
            print(f"Login: {'✅ PASS' if login_success else '❌ FAIL'}")
            print(f"Protected Route: {'✅ PASS' if protected_success else '❌ FAIL'}")
            print(f"Logout: {'✅ PASS' if logout_success else '❌ FAIL'}")
            print(f"Post-Logout Protection: {'✅ PASS' if post_logout_success else '❌ FAIL'}")
            
            all_passed = all([login_success, protected_success, logout_success, post_logout_success])
            print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
            
            return all_passed
        else:
            print("\n❌ Cannot continue tests - login failed")
            return False

def main():
    tester = FrontendAuthTester()
    success = tester.run_full_test()
    
    if success:
        print("\n🎉 Frontend authentication flow is working correctly!")
        print("You can now test the full application in the browser.")
    else:
        print("\n⚠️ Some authentication features need attention.")
        print("Please check the backend logs and database connection.")

if __name__ == "__main__":
    main()
