#!/usr/bin/env python3
"""
Script to create a test user with proper password hash
"""
import hashlib
import os

def hash_password(password: str) -> str:
    """Hash password using the same method as the application"""
    salt = os.urandom(32).hex()
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"{salt}:{pwd_hash.hex()}"

# Create user with password "password123"
password = "password123"
hashed_password = hash_password(password)

print(f"Username: testuser")
print(f"Password: {password}")
print(f"Hashed password: {hashed_password}")
print()
print("SQL to update user:")
print(f"UPDATE auth_users SET password_hash = '{hashed_password}' WHERE username = 'testuser';")
