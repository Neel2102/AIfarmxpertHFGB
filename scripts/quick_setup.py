#!/usr/bin/env python3
"""
Quick Database Setup - Creates .env file and initializes database
"""

import os
import sys

def create_env_file():
    """Create .env file in the correct location"""
    
    # Get project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_file = os.path.join(project_root, '.env')
    
    print(f"📁 Project root: {project_root}")
    print(f"📝 Creating .env file at: {env_file}")
    
    # SQLite configuration (quickest setup)
    env_content = """DATABASE_URL=sqlite:///./farmxpert.db
GEMINI_API_KEY=your_gemini_api_key_here
OPENWEATHER_API_KEY=your_openweather_api_key_here
SECRET_KEY=your-secret-key-change-in-production
APP_NAME=FarmXpert AI Platform
APP_ENV=development
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully!")
        print("📝 Using SQLite for quick development setup")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        print("\n📋 Manual .env file creation:")
        print("1. Create a file named '.env' in project root")
        print("2. Add this content:")
        print(env_content)
        return False

def test_sqlite_setup():
    """Test if SQLite setup works"""
    print("\n🧪 Testing SQLite setup...")
    
    try:
        # Add project root to path
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, project_root)
        
        # Test import
        from farmxpert.config.settings import settings
        print(f"📊 Database URL: {settings.database_url}")
        
        # Test SQLite connection
        if settings.database_url.startswith('sqlite'):
            from sqlalchemy import create_engine, text
            
            engine = create_engine(settings.database_url)
            
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1 as test"))
                test_value = result.fetchone()[0]
                
                if test_value == 1:
                    print("✅ SQLite connection successful!")
                    return True
                else:
                    print("❌ SQLite connection test failed")
                    return False
        else:
            print("⚠️  Not using SQLite - check your .env file")
            return False
            
    except Exception as e:
        print(f"❌ SQLite setup test failed: {e}")
        return False

def initialize_database():
    """Initialize database with tables"""
    print("\n🏗️  Initializing database tables...")
    
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, project_root)
        
        from farmxpert.models.database import Base
        from sqlalchemy import create_engine
        from farmxpert.config.settings import settings
        
        engine = create_engine(settings.database_url)
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database tables created successfully!")
        
        # List tables
        with engine.connect() as connection:
            if settings.database_url.startswith('sqlite'):
                result = connection.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """))
            else:
                result = connection.execute(text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """))
            
            tables = [row[0] for row in result.fetchall()]
            print(f"📊 Created {len(tables)} tables:")
            for table in tables:
                print(f"   - {table}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Quick Database Setup for FarmXpert")
    print("=" * 50)
    
    # Step 1: Create .env file
    if not create_env_file():
        print("\n❌ Failed to create .env file")
        return False
    
    # Step 2: Test SQLite setup
    if not test_sqlite_setup():
        print("\n❌ SQLite setup test failed")
        print("💡 Please restart your terminal and try again")
        return False
    
    # Step 3: Initialize database
    if not initialize_database():
        print("\n❌ Database initialization failed")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Database setup completed successfully!")
    print("\n✅ What was accomplished:")
    print("  ✅ .env file created with SQLite configuration")
    print("  ✅ Database connection tested")
    print("  ✅ Database tables created")
    print("  ✅ System ready for FarmXpert")
    
    print("\n🚀 Next Steps:")
    print("1. Start the application:")
    print("   python -m uvicorn farmxpert.app.main:app --reload")
    print("2. Open browser:")
    print("   http://localhost:8000/health")
    print("3. Test API endpoints:")
    print("   python scripts/comprehensive_api_test.py")
    
    print("\n📝 Notes:")
    print("• Using SQLite for quick development")
    print("• Database file: farmxpert.db (in project root)")
    print("• To switch to PostgreSQL later, see DATABASE_SETUP.md")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Setup failed. Please check the errors above.")
        input("Press Enter to exit...")
    else:
        print("\n✅ Ready to go! Start your application now.")
        input("Press Enter to exit...")
