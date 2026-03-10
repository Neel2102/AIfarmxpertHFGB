
from sqlalchemy import create_engine, inspect
from farmxpert.config.settings import settings

def check_db():
    print(f"Connecting to: {settings.database_url}")
    try:
        engine = create_engine(settings.database_url)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Tables found: {tables}")
        
        if 'farm_profiles' in tables:
            print("\nColumns in 'farm_profiles':")
            columns = inspector.get_columns('farm_profiles')
            for col in columns:
                print(f"  - {col['name']} ({col['type']})")
        else:
            print("\nWARNING: 'farm_profiles' table NOT found!")
            
        if 'users' in tables:
            print("\nColumns in 'users':")
            columns = inspector.get_columns('users')
            for col in columns:
                print(f"  - {col['name']} ({col['type']})")
        else:
            print("\nWARNING: 'users' table NOT found!")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
