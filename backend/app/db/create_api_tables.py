# backend/app/db/create_api_tables.py
"""
Script to create API tracking tables without Alembic
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.models.api_tracking import ApiCall, ApiQuotaUsage
from app.models.flight import Route
from app.core.database import Base, engine
from app.utils.logger import logger

def create_api_tracking_tables():
    """Create API tracking tables"""
    
    try:
        # Create all tables (this will create new ones and skip existing)
        Base.metadata.create_all(bind=engine)
        logger.info("API tracking tables created successfully")
        
        # Add last_scanned_at column to routes if it doesn't exist
        with engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE routes ADD COLUMN last_scanned_at TIMESTAMP"))
                conn.commit()
                logger.info("Added last_scanned_at column to routes table")
            except Exception as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    logger.info("last_scanned_at column already exists")
                else:
                    logger.error(f"Error adding column: {e}")
        
        # Verify tables exist
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('api_calls', 'api_quota_usage')
            """))
            tables = [row[0] for row in result]
            
            if 'api_calls' in tables:
                logger.info("✓ api_calls table exists")
            else:
                logger.error("✗ api_calls table not created")
                
            if 'api_quota_usage' in tables:
                logger.info("✓ api_quota_usage table exists")
            else:
                logger.error("✗ api_quota_usage table not created")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating API tracking tables: {e}")
        return False

if __name__ == "__main__":
    success = create_api_tracking_tables()
    if success:
        print("\n✅ API tracking tables created successfully!")
        print("You can now run the system initialization script.")
    else:
        print("\n❌ Failed to create API tracking tables. Check the logs.")