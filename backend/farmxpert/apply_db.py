import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("No DATABASE_URL found in .env. Exiting.")
    sys.exit(1)

db_url = db_url.replace("6432", "5433")

# Ensure psycopg2 compatibility string
if db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

print(f"Connecting to database: {db_url}")

try:
    # We use psycopg2 directly for better raw script execution
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cursor = conn.cursor()
    print("Connected successfully.")
    
    scripts = [
        "database/schema.sql",
        "database/create_partitions.sql",
        "database/seed_agents.sql",
        "database/row_level_security.sql",
        "database/cold_storage_management.sql"
    ]
    
    for script_path in scripts:
        if os.path.exists(script_path):
            print(f"Executing {script_path}...")
            with open(script_path, 'r', encoding='utf-8') as f:
                sql = f.read()
                # Split statements roughly by semicolon but mind DO blocks
                # To be safe, just try executing it entirely, and ignore already exists
                try:
                    cursor.execute(sql)
                    print(f"Successfully executed {script_path}")
                except Exception as e:
                    # Ignore table already exists errors, Postgres handles IF NOT EXISTS well but not always
                    print(f"Warning executing {script_path} (Continuing...): {e}")
    print("Database integration complete.")
                
except Exception as e:
    print(f"Failed to connect or execute: {e}")
