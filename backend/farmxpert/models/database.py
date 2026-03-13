from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from farmxpert.config.settings import settings

# Helper to get engine arguments based on DB URL
def get_engine_args():
    db_url = settings.database_url
    connect_args = {}
    
    # Enable SSL for cloud databases (like Railway/Supabase/Neon)
    if "sslmode" in db_url:
        # If already in URL, SQLAlchemy handles it but we can reinforce it
        pass
    elif any(host in db_url.lower() for host in ["railway", "supabase", "neon", "render", "aws", "elephantsql"]):
        # Common cloud providers often require SSL
        connect_args["sslmode"] = "require"
        
    return {
        "url": db_url,
        "echo": settings.app_env == "development",
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "connect_args": connect_args
    }

# Create database engine with connection arguments
engine = create_engine(**get_engine_args())

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
