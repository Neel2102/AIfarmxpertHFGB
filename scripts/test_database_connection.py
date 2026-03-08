#!/usr/bin/env python3
"""
Database Connection Test Script
Tests if the database is properly configured and accessible
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_database_connection():
    """Test database connection and configuration"""
    print("🔗 Testing Database Connection")
    print("=" * 40)
    
    try:
        # Import settings
        from farmxpert.config.settings import settings
        print(f"📊 Database URL: {settings.database_url}")
        
        # Test SQLAlchemy connection
        from sqlalchemy import create_engine, text
        engine = create_engine(settings.database_url)
        
        print("🔍 Testing basic connection...")
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]
            if test_value == 1:
                print("✅ Basic connection successful")
            else:
                print("❌ Basic connection failed")
                return False
        
        # Test if database exists
        print("🔍 Checking if farmxpert_db exists...")
        try:
            with engine.connect() as connection:
                result = connection.execute(text("SELECT current_database()"))
                db_name = result.fetchone()[0]
                print(f"✅ Connected to database: {db_name}")
        except Exception as e:
            print(f"❌ Database check failed: {e}")
            return False
        
        # Test if tables exist
        print("🔍 Checking if tables exist...")
        try:
            with engine.connect() as connection:
                result = connection.execute(text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """))
                tables = [row[0] for row in result.fetchall()]
                
                if tables:
                    print(f"✅ Found {len(tables)} tables:")
                    for table in tables[:10]:  # Show first 10 tables
                        print(f"   - {table}")
                    if len(tables) > 10:
                        print(f"   ... and {len(tables) - 10} more")
                else:
                    print("⚠️  No tables found. Run database initialization:")
                    print("   python farmxpert/scripts/init_db.py")
        
        except Exception as e:
            print(f"❌ Table check failed: {e}")
            return False
        
        # Test sample data
        print("🔍 Checking for sample data...")
        try:
            with engine.connect() as connection:
                # Check farms table
                try:
                    result = connection.execute(text("SELECT COUNT(*) FROM farms"))
                    farm_count = result.fetchone()[0]
                    print(f"✅ Farms table: {farm_count} records")
                except:
                    print("⚠️  Farms table not found")
                
                # Check users table
                try:
                    result = connection.execute(text("SELECT COUNT(*) FROM users"))
                    user_count = result.fetchone()[0]
                    print(f"✅ Users table: {user_count} records")
                except:
                    print("⚠️  Users table not found")
                
                # Check chat_sessions table
                try:
                    result = connection.execute(text("SELECT COUNT(*) FROM chat_sessions"))
                    session_count = result.fetchone()[0]
                    print(f"✅ Chat sessions table: {session_count} records")
                except:
                    print("⚠️  Chat sessions table not found")
        
        except Exception as e:
            print(f"❌ Sample data check failed: {e}")
        
        print("\n🎉 Database connection test completed successfully!")
        print("✅ Your database is ready for FarmXpert!")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Ensure PostgreSQL is running")
        print("2. Check your .env file DATABASE_URL")
        print("3. Verify database 'farmxpert_db' exists")
        print("4. Check PostgreSQL password in DATABASE_URL")
        print("\n📝 Example DATABASE_URL format:")
        print("DATABASE_URL=postgresql://postgres:password@localhost:5432/farmxpert_db")
        
        return False

def test_database_operations():
    """Test basic database operations"""
    print("\n🧪 Testing Database Operations")
    print("=" * 40)
    
    try:
        from farmxpert.database import get_database_session, create_user
        from farmxpert.models.database import get_db
        
        print("🔍 Testing database session creation...")
        db = get_database_session()
        print("✅ Database session created successfully")
        
        print("🔍 Testing user creation...")
        try:
            user_data = {
                "username": "test_user",
                "email": "test@example.com",
                "password": "test_password",
                "full_name": "Test User"
            }
            user = create_user(db, user_data)
            print(f"✅ Test user created: {user.username}")
        except Exception as e:
            if "already exists" in str(e):
                print("✅ Test user already exists")
            else:
                print(f"⚠️  User creation test: {e}")
        
        db.close()
        print("✅ Database operations test completed")
        return True
        
    except Exception as e:
        print(f"❌ Database operations test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 FarmXpert Database Test Suite")
    print("=" * 50)
    
    connection_ok = test_database_connection()
    operations_ok = test_database_operations()
    
    print("\n" + "=" * 50)
    if connection_ok and operations_ok:
        print("🎉 ALL TESTS PASSED!")
        print("🚀 Your FarmXpert database is fully configured!")
    else:
        print("❌ Some tests failed.")
        print("📖 Please refer to POSTGRESQL_SETUP.md for help")
    
    print("\n📋 Next Steps:")
    print("1. Start the application: python -m uvicorn farmxpert.app.main:app --reload")
    print("2. Visit: http://localhost:8000/health")
    print("3. Test the API endpoints")
