#!/usr/bin/env python3
"""
Update ApiCall table for FlightLabs integration
Adds api_provider field and renames timestamp to called_at
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal, engine
from app.models.api_tracking import ApiCall
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_api_call_table():
    """Update ApiCall table structure"""
    db = SessionLocal()
    
    try:
        # Check if api_provider column exists
        result = db.execute(text("PRAGMA table_info(api_calls)"))
        columns = [row[1] for row in result.fetchall()]
        
        logger.info(f"Current api_calls columns: {columns}")
        
        # Add api_provider column if it doesn't exist
        if 'api_provider' not in columns:
            logger.info("Adding api_provider column...")
            db.execute(text("ALTER TABLE api_calls ADD COLUMN api_provider VARCHAR(50) DEFAULT 'aviationstack'"))
            db.commit()
            logger.info("✅ api_provider column added")
        
        # Add called_at column if it doesn't exist (rename from timestamp)
        if 'called_at' not in columns and 'timestamp' in columns:
            logger.info("Renaming timestamp to called_at...")
            # SQLite doesn't support column renaming directly, so we copy the data
            db.execute(text("ALTER TABLE api_calls ADD COLUMN called_at DATETIME"))
            db.execute(text("UPDATE api_calls SET called_at = timestamp"))
            db.commit()
            logger.info("✅ called_at column added and data copied")
        elif 'called_at' not in columns:
            logger.info("Adding called_at column...")
            db.execute(text("ALTER TABLE api_calls ADD COLUMN called_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
            db.commit()
            logger.info("✅ called_at column added")
        
        # Add success column if it doesn't exist
        if 'success' not in columns:
            logger.info("Adding success column...")
            db.execute(text("ALTER TABLE api_calls ADD COLUMN success BOOLEAN DEFAULT 1"))
            db.commit()
            logger.info("✅ success column added")
        
        # Add response_data column if it doesn't exist
        if 'response_data' not in columns:
            logger.info("Adding response_data column...")
            db.execute(text("ALTER TABLE api_calls ADD COLUMN response_data TEXT"))
            db.commit()
            logger.info("✅ response_data column added")
        
        # Update existing records to have proper api_provider
        db.execute(text("UPDATE api_calls SET api_provider = 'aviationstack' WHERE api_provider IS NULL"))
        db.commit()
        
        logger.info("✅ ApiCall table updated successfully")
        
    except Exception as e:
        logger.error(f"❌ Error updating ApiCall table: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    update_api_call_table()
    print("Database migration completed!")
