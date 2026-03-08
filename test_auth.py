#!/usr/bin/env python3
"""
Test script to verify user authentication
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'farmxpert'))

from farmxpert.models.database import get_db
from farmxpert.models.user_models import User

def test_user_auth():
    db = next(get_db())
    try:
        # Find user
        user = db.query(User).filter(User.username == 'testuser').first()
        if not user:
            print("❌ User not found")
            return False
            
        print(f"✅ User found: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Active: {user.is_active}")
        
        # Test password
        password_valid = user.check_password('password123')
        print(f"   Password valid: {password_valid}")
        
        if password_valid:
            print("✅ Authentication should work!")
        else:
            print("❌ Password verification failed")
            
        return password_valid
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    test_user_auth()
