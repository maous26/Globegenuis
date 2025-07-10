from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create engine with SQLite-specific configuration for better concurrency
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite-specific configuration
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=1,  # SQLite only supports single connection
        max_overflow=0,  # No overflow for SQLite
        pool_timeout=20,  # Longer timeout for locked database
        pool_recycle=3600,  # Recycle connections every hour
        connect_args={
            "check_same_thread": False,  # Allow multiple threads
            "timeout": 20  # 20 second timeout for database locks
        }
    )
else:
    # PostgreSQL/other database configuration
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()