# 🚀 DATABASE SETUP INSTRUCTIONS

## Current Status: PostgreSQL Not Installed

Your system doesn't have PostgreSQL installed. Here are your options:

## Option 1: Install PostgreSQL (Recommended for Production)

### Step 1: Install PostgreSQL
1. Download from: https://www.postgresql.org/download/windows/
2. Run installer with password: `postgres`
3. Keep port 5432 (default)
4. Install pgAdmin 4 (recommended)

### Step 2: Start PostgreSQL Service
1. Open Windows Services (Win+R → `services.msc`)
2. Find `postgresql-x64-15` (version may vary)
3. Right-click → Start
4. Set Startup Type to Automatic

### Step 3: Create .env File
Create a `.env` file in project root with:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/farmxpert_db
GEMINI_API_KEY=your_gemini_api_key_here
OPENWEATHER_API_KEY=your_openweather_api_key_here
SECRET_KEY=your-secret-key-change-in-production
```

### Step 4: Run Setup
```bash
python scripts/setup_postgresql.py
```

## Option 2: Use SQLite (Quick Development)

### Step 1: Create .env File
Create a `.env` file in project root with:
```env
DATABASE_URL=sqlite:///./farmxpert.db
GEMINI_API_KEY=your_gemini_api_key_here
OPENWEATHER_API_KEY=your_openweather_api_key_here
SECRET_KEY=your-secret-key-change-in-production
```

### Step 2: Initialize Database
```bash
python farmxpert/scripts/init_db.py
```

## Option 3: Use Docker (If you have Docker)

```bash
docker run --name farmxpert-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=farmxpert_db \
  -p 5432:5432 \
  -d postgres:15
```

Then create .env file with PostgreSQL URL and run setup.

## 🔧 Manual .env File Creation

Since .env is ignored by git, create it manually:

1. **Right-click** in project root
2. **New** → **Text Document**
3. **Rename** to `.env` (including the dot)
4. **Add content** based on your chosen option above

## 🧪 Test Database Connection

After setup, test with:
```bash
python scripts/test_database_connection.py
```

## 🚀 Start Application

Once database is ready:
```bash
python -m uvicorn farmxpert.app.main:app --reload
```

Visit: http://localhost:8000/health

## 📋 Recommendation

For **development**: Use SQLite (Option 2) - fastest setup
For **production**: Use PostgreSQL (Option 1) - more robust

## 🆘 Need Help?

Check: `POSTGRESQL_SETUP.md` for detailed troubleshooting

---

**Current Issue**: PostgreSQL not found on your system
**Solution**: Choose one of the options above to get your database running
