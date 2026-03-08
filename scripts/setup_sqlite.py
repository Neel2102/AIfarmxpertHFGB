#!/usr/bin/env python3
"""
SQLite Database Setup for FarmXpert (Development Alternative)
Use this if you don't want to install PostgreSQL
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_sqlite():
    """Set up SQLite database for development"""
    print("🚀 Setting up SQLite Database for Development")
    print("=" * 50)
    
    # Create .env file with SQLite configuration
    env_content = """# FarmXpert Environment Configuration (SQLite)

# Database Configuration - SQLite for Development
DATABASE_URL=sqlite:///./farmxpert.db

# Redis Configuration (optional for development)
REDIS_URL=redis://localhost:6379/0

# API Keys (add your actual keys here)
GEMINI_API_KEY=your_gemini_api_key_here
OPENWEATHER_API_KEY=your_openweather_api_key_here

# Application Settings
APP_NAME=FarmXpert AI Platform
APP_ENV=development
SECRET_KEY=your-secret-key-change-in-production

# Static Data Directory
STATIC_DATA_DIR=data/static
"""
    
    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    
    print("📝 Creating .env file with SQLite configuration...")
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully")
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        print("💡 Please create .env file manually with SQLite configuration")
        return False
    
    # Test SQLite connection
    print("🔗 Testing SQLite connection...")
    try:
        from farmxpert.config.settings import settings
        from sqlalchemy import create_engine, text
        
        engine = create_engine(settings.database_url)
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]
            if test_value == 1:
                print("✅ SQLite connection successful")
            else:
                print("❌ SQLite connection failed")
                return False
    
    except Exception as e:
        print(f"❌ SQLite connection failed: {e}")
        return False
    
    # Create database tables
    print("🏗️  Creating database tables...")
    try:
        from farmxpert.models.database import Base
        
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        
        # List created tables
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"✅ Created {len(tables)} tables:")
            for table in tables:
                print(f"   - {table}")
    
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
    
    # Insert sample data
    print("📊 Inserting sample data...")
    try:
        from farmxpert.scripts.init_db import init_database
        init_database()
        print("✅ Sample data inserted successfully")
    
    except Exception as e:
        print(f"⚠️  Sample data insertion failed: {e}")
        print("💡 This is not critical, the database structure is ready")
    
    print("\n" + "=" * 50)
    print("🎉 SQLite setup completed successfully!")
    print("\n✅ What was accomplished:")
    print("  ✅ SQLite database configured")
    print("  ✅ .env file created with SQLite settings")
    print("  ✅ Database connection tested")
    print("  ✅ Database tables created")
    print("  ✅ Sample data inserted (if possible)")
    
    print("\n📝 Notes:")
    print("  • SQLite is great for development and testing")
    print("  • For production, consider PostgreSQL")
    print("  • Database file: farmxpert.db (in project root)")
    print("  • No server required - SQLite is file-based")
    
    print("\n🚀 Your FarmXpert application is now ready with SQLite!")
    
    return True

if __name__ == "__main__":
    success = setup_sqlite()
    if success:
        print("\n🎯 Next Steps:")
        print("1. Start the application: python -m uvicorn farmxpert.app.main:app --reload")
        print("2. Visit: http://localhost:8000/health")
        print("3. Test the API endpoints")
        print("\n💡 To switch to PostgreSQL later:")
        print("1. Install PostgreSQL")
        print("2. Update DATABASE_URL in .env")
        print("3. Run: python scripts/setup_postgresql.py")
    else:
        print("\n❌ SQLite setup failed. Please check the error messages above.")
