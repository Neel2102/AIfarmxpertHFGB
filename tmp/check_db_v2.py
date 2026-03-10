
from sqlalchemy import create_engine, inspect, text
from farmxpert.config.settings import settings

def check_db():
    print(f"Connecting to: {settings.database_url}")
    try:
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            # Try a raw SQL query to see columns
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'farm_profiles'"))
            cols = [row[0] for row in result]
            print(f"Postgres information_schema columns for 'farm_profiles': {cols}")
            
            # Check if any data exists
            result = conn.execute(text("SELECT COUNT(*) FROM farm_profiles"))
            count = result.scalar()
            print(f"Total rows in 'farm_profiles': {count}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
