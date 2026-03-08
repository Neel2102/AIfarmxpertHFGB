#!/usr/bin/env python3
"""
Test authentication service directly
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'farmxpert'))

from farmxpert.services.auth_service import AuthService
from farmxpert.models.database import get_db

def test_auth_service():
    db = next(get_db())
    try:
        auth_service = AuthService(db)
        
        # Test authentication
        print("🔐 Testing user authentication...")
        user = auth_service.authenticate_user("testuser", "password123")
        
        if user:
            print(f"✅ User authenticated: {user.username}")
            
            # Test token creation
            print("🔑 Testing token creation...")
            try:
                access_token = auth_service.create_access_token(user.id, user.username)
                print(f"✅ Access token created: {access_token[:20]}...")
                
                refresh_token = auth_service.create_refresh_token(user.id)
                print(f"✅ Refresh token created: {refresh_token[:20]}...")
                
                # Test session creation
                print("📝 Testing session creation...")
                session_token = auth_service.create_user_session(user=user)
                print(f"✅ Session created: {session_token[:20]}...")
                
                print("🎉 All authentication steps working!")
                return True
                
            except Exception as e:
                print(f"❌ Token/Session creation failed: {e}")
                return False
        else:
            print("❌ User authentication failed")
            return False
            
    except Exception as e:
        print(f"❌ Auth service error: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    test_auth_service()
