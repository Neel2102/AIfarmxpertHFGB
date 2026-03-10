#!/usr/bin/env python3
"""
Create user authentication tables
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from farmxpert.models.user_models import User, UserSession, PasswordResetToken

def create_user_tables():
    """Create user authentication tables"""
    print("Creating user authentication tables...")
    
    try:
        print("✅ Skipped: tables are managed by Alembic migrations.")
        
    except Exception as e:
        print(f"❌ Error creating user tables: {e}")
        return False
    
    return True

if __name__ == "__main__":
    create_user_tables()
