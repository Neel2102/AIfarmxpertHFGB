#!/usr/bin/env python3
"""
Simple test user creation using direct database operations
"""

import sqlite3
import hashlib
import os
import secrets

def hash_password(password: str) -> str:
    """Hash password using PBKDF2"""
    salt = os.urandom(32).hex()
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"{salt}:{pwd_hash.hex()}"

def create_test_user_sqlite():
    """Create test user directly in SQLite database"""
    db_path = "backend/farmxpert/database.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute("SELECT id FROM auth_users WHERE username = ?", ("testuser",))
        existing = cursor.fetchone()
        
        if existing:
            print("✅ Test user already exists!")
            cursor.execute("SELECT username, email, is_active FROM auth_users WHERE username = ?", ("testuser",))
            user_data = cursor.fetchone()
            print(f"   Username: {user_data[0]}")
            print(f"   Email: {user_data[1]}")
            print(f"   Active: {user_data[2]}")
            conn.close()
            return True
        
        # Create new user
        password = "password123"
        hashed_password = hash_password(password)
        
        cursor.execute("""
            INSERT INTO auth_users (username, email, password_hash, full_name, is_active, is_verified, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, ("testuser", "test@example.com", hashed_password, "Test User", True, False))
        
        conn.commit()
        
        # Verify creation
        cursor.execute("SELECT id, username FROM auth_users WHERE username = ?", ("testuser",))
        user_data = cursor.fetchone()
        
        if user_data:
            print("✅ Test user created successfully!")
            print(f"   ID: {user_data[0]}")
            print(f"   Username: {user_data[1]}")
            print(f"   Email: test@example.com")
            print(f"   Password: {password}")
            conn.close()
            return True
        else:
            print("❌ Failed to create test user")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("👤 Creating Test User (Direct Database)")
    print("=" * 50)
    
    success = create_test_user_sqlite()
    
    print("=" * 50)
    if success:
        print("✅ Test user ready for authentication testing!")
        print("   Username: testuser")
        print("   Password: password123")
    else:
        print("❌ Failed to create test user")
