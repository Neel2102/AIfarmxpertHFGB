# PostgreSQL Setup Guide for FarmXpert

## 🚀 Quick Setup Instructions

### Option 1: Install PostgreSQL (Recommended)

#### Step 1: Download and Install PostgreSQL
1. **Download PostgreSQL**: https://www.postgresql.org/download/windows/
2. **Run the installer** with these settings:
   - Password: Choose a memorable password (e.g., `postgres`)
   - Port: 5432 (default)
   - Install pgAdmin 4 (recommended for database management)
   - Install Stack Builder (optional)

#### Step 2: Start PostgreSQL Service
1. Open **Windows Services** (press Win+R, type `services.msc`)
2. Find **postgresql-x64-15** (version may vary)
3. Right-click → **Start** if not running
4. Set **Startup Type** to **Automatic**

#### Step 3: Run Setup Script
```bash
python scripts/setup_postgresql.py
```

### Option 2: Use Docker (Alternative)

If you prefer Docker instead of installing PostgreSQL:

```bash
# Create a docker-compose.yml file
docker run --name farmxpert-postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=farmxpert_db \
  -p 5432:5432 \
  -d postgres:15

# Then run the setup script
python scripts/setup_postgresql.py
```

### Option 3: Use SQLite (Development Only)

For quick development without PostgreSQL:

1. **Update your .env file**:
```env
DATABASE_URL=sqlite:///./farmxpert.db
```

2. **Run database initialization**:
```bash
python farmxpert/scripts/init_db.py
```

## 🔧 Manual Setup Steps

### If the automatic script fails, follow these steps:

#### Step 1: Verify PostgreSQL Installation
Open Command Prompt and run:
```cmd
psql --version
```

#### Step 2: Create Database Manually
```cmd
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE farmxpert_db;

# Exit
\q
```

#### Step 3: Create .env File
Create a `.env` file in the project root with:
```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/farmxpert_db
```

#### Step 4: Initialize Database
```bash
python farmxpert/scripts/init_db.py
```

## 🐛 Troubleshooting

### Issue: "PostgreSQL not found"
**Solution**: Install PostgreSQL from the official website

### Issue: "Connection refused"
**Solution**: Start PostgreSQL service from Windows Services

### Issue: "Password authentication failed"
**Solution**: Update the password in your .env file to match your PostgreSQL password

### Issue: "Database already exists"
**Solution**: This is fine, the script will continue

### Issue: "Permission denied"
**Solution**: Run Command Prompt as Administrator

## 🎯 Verification Steps

After setup, verify everything is working:

1. **Test Database Connection**:
```bash
python scripts/test_database_connection.py
```

2. **Check if Tables Exist**:
```bash
python scripts/verify_database_tables.py
```

3. **Start the Application**:
```bash
python -m uvicorn farmxpert.app.main:app --reload
```

4. **Visit Health Check**:
Open http://localhost:8000/health in your browser

## 📋 Prerequisites Checklist

- [ ] PostgreSQL installed (version 12 or higher)
- [ ] PostgreSQL service running
- [ ] Database `farmxpert_db` created
- [ ] .env file configured with correct DATABASE_URL
- [ ] Database tables created
- [ ] Sample data inserted

## 🆘 Need Help?

If you encounter any issues:

1. Check PostgreSQL service is running
2. Verify your password in .env file
3. Ensure port 5432 is not blocked by firewall
4. Try connecting with pgAdmin or psql directly

## 🚀 Next Steps

Once PostgreSQL is set up:

1. Your FarmXpert application will have full database functionality
2. User authentication and sessions will work
3. Farm data will be persisted
4. Chat history will be saved
5. All features requiring database will be functional
