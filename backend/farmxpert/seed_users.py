
import os
import sys
import hashlib
import secrets
from datetime import datetime

# Add the current directory to sys.path to allow imports
sys.path.append(os.getcwd())

from farmxpert.models.database import SessionLocal
from farmxpert.models.user_models import User

def hash_password(password: str) -> str:
    """Hash password using the same method as User.set_password"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"{salt}:{pwd_hash.hex()}"

def seed_users():
    db = SessionLocal()
    try:
        # Check if users already exist
        admin_exists = db.query(User).filter(User.username == "admin").first()
        farmer_exists = db.query(User).filter(User.username == "farmer").first()

        if not admin_exists:
            admin = User(
                username="admin",
                email="admin@farmxpert.ai",
                full_name="System Administrator",
                hashed_password=hash_password("admin123"),
                role="admin",
                is_active=True,
                is_verified=True,
                onboarding_completed=True
            )
            db.add(admin)
            print("Creating admin user...")

        if not farmer_exists:
            farmer = User(
                username="farmer",
                email="farmer@farmxpert.ai",
                full_name="Modern Farmer",
                hashed_password=hash_password("farmer123"),
                role="farmer",
                is_active=True,
                is_verified=True,
                onboarding_completed=True
            )
            db.add(farmer)
            print("Creating farmer user...")

        db.commit()
        print("✅ Users seeded successfully!")
        print("Admin: admin / admin123")
        print("Farmer: farmer / farmer123")
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding users: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_users()
