#!/usr/bin/env python3
"""
PostgreSQL Database Setup Script for FarmXpert
This script will guide you through setting up PostgreSQL and creating the database.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_postgresql_installed():
    """Check if PostgreSQL is installed and accessible"""
    print("🔍 Checking PostgreSQL installation...")
    
    try:
        # Try to run psql command
        result = subprocess.run(['psql', '--version'], capture_output=True, text=True)
        print(f"✅ PostgreSQL found: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("❌ PostgreSQL not found. Please install PostgreSQL first.")
        print("\n📥 Installation Instructions:")
        print("1. Download PostgreSQL from: https://www.postgresql.org/download/windows/")
        print("2. Run the installer and remember your password")
        print("3. Make sure to install pgAdmin 4 (optional but helpful)")
        print("4. Restart your computer after installation")
        return False

def check_postgresql_running():
    """Check if PostgreSQL service is running"""
    print("\n🔍 Checking if PostgreSQL service is running...")
    
    try:
        # Try to connect to PostgreSQL
        result = subprocess.run(['psql', '-U', 'postgres', '-c', 'SELECT 1;'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ PostgreSQL service is running")
            return True
        else:
            print("❌ PostgreSQL service is not accessible")
            return False
    except Exception as e:
        print(f"❌ Error checking PostgreSQL: {e}")
        return False

def create_database():
    """Create the farmxpert_db database"""
    print("\n🏗️  Creating farmxpert_db database...")
    
    try:
        # Create database
        result = subprocess.run(['psql', '-U', 'postgres', '-c', 'CREATE DATABASE farmxpert_db;'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Database 'farmxpert_db' created successfully")
            return True
        elif "already exists" in result.stderr:
            print("✅ Database 'farmxpert_db' already exists")
            return True
        else:
            print(f"❌ Error creating database: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

def create_env_file():
    """Create .env file with database configuration"""
    print("\n📝 Creating .env file...")
    
    env_content = """# FarmXpert Environment Configuration

# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/farmxpert_db

# Redis Configuration
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
    
    env_file = Path('.env')
    
    # Check if .env already exists
    if env_file.exists():
        print("⚠️  .env file already exists. Skipping creation.")
        return True
    
    try:
        # Create .env file
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully")
        print("📝 Please edit .env file and add your actual API keys")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        print("💡 Please create .env file manually with the following content:")
        print(env_content)
        return False

def test_database_connection():
    """Test database connection using the settings"""
    print("\n🔗 Testing database connection...")
    
    try:
        # Add project root to path
        sys.path.append(str(Path(__file__).parent.parent))
        
        from farmxpert.config.settings import settings
        from sqlalchemy import create_engine
        
        # Test connection
        engine = create_engine(settings.database_url)
        connection = engine.connect()
        connection.close()
        
        print("✅ Database connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("💡 Please check your PostgreSQL password and update .env file")
        return False

def run_database_init():
    """Run the database initialization script"""
    print("\n🚀 Running database initialization...")
    
    try:
        init_script = Path(__file__).parent / 'init_db.py'
        if not init_script.exists():
            print(f"❌ Database init script not found: {init_script}")
            return False
        
        result = subprocess.run([sys.executable, str(init_script)], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database initialization completed successfully")
            print(result.stdout)
            return True
        else:
            print(f"❌ Database initialization failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running database initialization: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 FarmXpert PostgreSQL Setup")
    print("=" * 50)
    
    # Step 1: Check PostgreSQL installation
    if not check_postgresql_installed():
        print("\n❌ Please install PostgreSQL first and run this script again.")
        return False
    
    # Step 2: Check if PostgreSQL is running
    if not check_postgresql_running():
        print("\n❌ Please start PostgreSQL service and run this script again.")
        print("💡 You can start PostgreSQL from Windows Services or run: net start postgresql-x64-15")
        return False
    
    # Step 3: Create database
    if not create_database():
        print("\n❌ Failed to create database. Please check PostgreSQL permissions.")
        return False
    
    # Step 4: Create .env file
    if not create_env_file():
        print("\n⚠️  .env file creation failed, but you can create it manually.")
    
    # Step 5: Test database connection
    if not test_database_connection():
        print("\n❌ Database connection test failed.")
        print("💡 Please update your PostgreSQL password in .env file:")
        print("   DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/farmxpert_db")
        return False
    
    # Step 6: Run database initialization
    if not run_database_init():
        print("\n❌ Database initialization failed.")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 PostgreSQL setup completed successfully!")
    print("\n✅ What was accomplished:")
    print("  ✅ PostgreSQL service verified")
    print("  ✅ Database 'farmxpert_db' created")
    print("  ✅ .env file configured")
    print("  ✅ Database connection tested")
    print("  ✅ Database tables created")
    print("  ✅ Sample data inserted")
    
    print("\n🚀 Your FarmXpert application is now ready to use the database!")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Setup failed. Please resolve the issues above and try again.")
        sys.exit(1)
