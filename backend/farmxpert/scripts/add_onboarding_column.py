"""
Migration script to add onboarding_completed column to users table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from farmxpert.models.database import DATABASE_URL
from farmxpert.config.settings import get_settings

def add_onboarding_column():
    """Add onboarding_completed column to users table"""
    settings = get_settings()
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            # Check if column already exists
            result = connection.execute(text("""
                SELECT COUNT(*) as count 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name = 'onboarding_completed'
            """))
            
            column_exists = result.fetchone()[0] > 0
            
            if not column_exists:
                # Add the column
                connection.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN onboarding_completed BOOLEAN DEFAULT FALSE
                """))
                connection.commit()
                print("✅ Successfully added onboarding_completed column to users table")
            else:
                print("ℹ️ onboarding_completed column already exists in users table")
                
    except Exception as e:
        print(f"❌ Error adding onboarding_completed column: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔄 Adding onboarding_completed column to users table...")
    success = add_onboarding_column()
    
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        sys.exit(1)
