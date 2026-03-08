#!/usr/bin/env python3
"""
Setup .env file for Docker PostgreSQL Database
"""

import os

def create_docker_env():
    """Create .env file configured for Docker PostgreSQL"""
    
    # Get project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_file = os.path.join(project_root, '.env')
    
    print("🐕 Setting up .env for Docker PostgreSQL")
    print("=" * 50)
    print(f"📁 Project root: {project_root}")
    print(f"📝 Creating .env file at: {env_file}")
    
    # Docker PostgreSQL configuration
    env_content = """# FarmXpert Environment Configuration - Docker PostgreSQL

# Database Configuration - Docker PostgreSQL on port 5433
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/farmxpert

# Redis Configuration (if you have Redis running)
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
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully!")
        print("📝 Configured for Docker PostgreSQL:")
        print("   • Host: localhost")
        print("   • Port: 5433")
        print("   • Database: farmxpert")
        print("   • Username: postgres")
        print("   • Password: postgres")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        print("\n📋 Manual .env file creation:")
        print("1. Create a file named '.env' in project root")
        print("2. Add this content:")
        print(env_content)
        return False

def test_docker_connection():
    """Test connection to Docker PostgreSQL"""
    print("\n🧪 Testing Docker PostgreSQL connection...")
    
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from farmxpert.config.settings import settings
        from sqlalchemy import create_engine, text
        
        print(f"📊 Database URL: {settings.database_url}")
        
        engine = create_engine(settings.database_url)
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL!")
            print(f"📊 Version: {version.split(',')[0]}")
            
            # Check if farmxpert database exists
            result = connection.execute(text("SELECT current_database()"))
            db_name = result.fetchone()[0]
            print(f"📊 Current database: {db_name}")
            
            return True
    
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def check_database_tables():
    """Check what tables exist in the database"""
    print("\n📊 Checking database tables...")
    
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from farmxpert.config.settings import settings
        from sqlalchemy import create_engine, text
        
        engine = create_engine(settings.database_url)
        
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                print(f"✅ Found {len(tables)} tables:")
                for table in tables:
                    print(f"   - {table}")
            else:
                print("⚠️  No tables found. Need to initialize database.")
                return False
    
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return False

def main():
    """Main setup function"""
    print("🐕 Docker PostgreSQL Setup for FarmXpert")
    print("=" * 50)
    
    # Step 1: Create .env file
    if not create_docker_env():
        print("\n❌ Failed to create .env file")
        return False
    
    # Step 2: Test connection
    if not test_docker_connection():
        print("\n❌ Docker PostgreSQL connection failed")
        print("💡 Make sure Docker containers are running:")
        print("   docker ps")
        return False
    
    # Step 3: Check tables
    check_database_tables()
    
    print("\n" + "=" * 50)
    print("🎉 Docker PostgreSQL setup completed!")
    print("\n✅ What was accomplished:")
    print("  ✅ .env file configured for Docker PostgreSQL")
    print("  ✅ Database connection tested")
    print("  ✅ Database tables checked")
    
    print("\n🚀 Next Steps:")
    print("1. Start the application:")
    print("   python -m uvicorn farmxpert.app.main:app --reload")
    print("2. Open browser:")
    print("   http://localhost:8000/health")
    print("3. Test API endpoints:")
    print("   python scripts/comprehensive_api_test.py")
    
    print("\n📝 Docker Status:")
    print("• farmxpert_db: PostgreSQL on port 5433")
    print("• farmxpert_pgbouncer: Connection pooler on port 5432")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Setup failed. Check Docker containers:")
        print("docker ps")
        input("Press Enter to exit...")
    else:
        print("\n✅ Ready to go! Your Docker database is configured!")
        input("Press Enter to exit...")
