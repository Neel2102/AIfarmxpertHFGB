
from sqlalchemy import create_engine, text
from farmxpert.config.settings import settings

def migrate_db():
    print(f"Connecting to: {settings.database_url}")
    engine = create_engine(settings.database_url)
    
    # List of columns to add with their types
    new_columns = [
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("farm_polygon", "JSON"),
        ("farm_layout_data", "JSON"),
        ("primary_crops", "JSON"),
        ("machinery", "JSON"),
        ("sustainability_focus", "JSON"),
        ("farm_goals", "JSON"),
        ("village", "VARCHAR(100)"),
        ("latitude", "DOUBLE PRECISION"),
        ("longitude", "DOUBLE PRECISION"),
        ("soil_ph", "VARCHAR(20)"),
        ("soil_organic_matter", "VARCHAR(50)"),
        ("soil_texture", "VARCHAR(100)"),
        ("soil_drainage", "VARCHAR(100)"),
        ("water_availability", "VARCHAR(100)"),
        ("crop_rotation", "VARCHAR(100)"),
        ("cropping_season", "VARCHAR(100)"),
        ("farming_experience", "VARCHAR(100)"),
        ("challenges", "VARCHAR(500)"),
        ("additional_info", "TEXT"),
    ]
    
    for col_name, col_type in new_columns:
        with engine.connect() as conn:
            try:
                conn.execute(text(f"ALTER TABLE farm_profiles ADD COLUMN {col_name} {col_type}"))
                conn.commit()
                print(f"  - Added {col_name}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"  - {col_name} already exists, skipping.")
                else:
                    print(f"  - Error adding {col_name}: {e}")
    
    print("Migration complete!")

if __name__ == "__main__":
    migrate_db()
