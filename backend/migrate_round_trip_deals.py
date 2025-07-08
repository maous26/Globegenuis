#!/usr/bin/env python3
"""
Migration script to update GlobeGenius database for round-trip deal system
Enhances existing intelligent route system with round-trip constraints
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.database import get_db
from app.services.dynamic_route_manager import DynamicRouteManager
from app.utils.logger import logger


def migrate_database():
    """
    Migrate the database to support round-trip deal validation
    """
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Add new columns to routes table
            logger.info("Adding new columns to routes table...")
            
            route_migrations = [
                "ALTER TABLE routes ADD COLUMN route_type VARCHAR(20) DEFAULT 'round_trip'",
                "ALTER TABLE routes ADD COLUMN region VARCHAR(50)",
                "ALTER TABLE routes ADD COLUMN min_stay_nights INTEGER DEFAULT 3",
                "ALTER TABLE routes ADD COLUMN max_stay_nights INTEGER DEFAULT 30",
                "ALTER TABLE routes ADD COLUMN min_advance_booking_days INTEGER DEFAULT 30",
                "ALTER TABLE routes ADD COLUMN max_advance_booking_days INTEGER DEFAULT 270",
                "ALTER TABLE routes ADD COLUMN allow_mon_wed BOOLEAN DEFAULT 1",
                "ALTER TABLE routes ADD COLUMN allow_tue_fri BOOLEAN DEFAULT 1",
                "ALTER TABLE routes ADD COLUMN allow_wed_sun BOOLEAN DEFAULT 1"
            ]
            
            for migration in route_migrations:
                try:
                    conn.execute(text(migration))
                    logger.info(f"✅ Executed: {migration}")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        logger.info(f"⚠️  Column already exists: {migration}")
                    else:
                        logger.error(f"❌ Error executing {migration}: {e}")
                        raise
            
            # Add new columns to deals table
            logger.info("Adding new columns to deals table...")
            
            deal_migrations = [
                "ALTER TABLE deals ADD COLUMN stay_duration_nights INTEGER",
                "ALTER TABLE deals ADD COLUMN departure_day_of_week INTEGER",
                "ALTER TABLE deals ADD COLUMN return_day_of_week INTEGER", 
                "ALTER TABLE deals ADD COLUMN advance_booking_days INTEGER",
                "ALTER TABLE deals ADD COLUMN meets_stay_requirements BOOLEAN DEFAULT 0",
                "ALTER TABLE deals ADD COLUMN meets_timing_requirements BOOLEAN DEFAULT 0",
                "ALTER TABLE deals ADD COLUMN meets_advance_booking BOOLEAN DEFAULT 0",
                "ALTER TABLE deals ADD COLUMN is_valid_round_trip BOOLEAN DEFAULT 0"
            ]
            
            for migration in deal_migrations:
                try:
                    conn.execute(text(migration))
                    logger.info(f"✅ Executed: {migration}")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        logger.info(f"⚠️  Column already exists: {migration}")
                    else:
                        logger.error(f"❌ Error executing {migration}: {e}")
                        raise
            
            # Create new indexes
            logger.info("Creating new indexes...")
            
            index_migrations = [
                "CREATE INDEX IF NOT EXISTS idx_route_region ON routes(region)",
                "CREATE INDEX IF NOT EXISTS idx_route_type ON routes(route_type)",
                "CREATE INDEX IF NOT EXISTS idx_deals_valid_round_trip ON deals(is_valid_round_trip)",
                "CREATE INDEX IF NOT EXISTS idx_deals_stay_duration ON deals(stay_duration_nights)",
                "CREATE INDEX IF NOT EXISTS idx_deals_advance_booking ON deals(advance_booking_days)"
            ]
            
            for index_sql in index_migrations:
                try:
                    conn.execute(text(index_sql))
                    logger.info(f"✅ Created index: {index_sql}")
                except Exception as e:
                    logger.warning(f"⚠️  Index creation warning: {e}")
            
            conn.commit()
            logger.info("✅ Database schema migration completed successfully!")
            
    except Exception as e:
        logger.error(f"❌ Database migration failed: {e}")
        raise


def enhance_intelligent_routes():
    """
    Enhance existing intelligent route system with round-trip capabilities
    """
    logger.info("Enhancing intelligent route system for round-trip deals...")
    
    db = next(get_db())
    try:
        route_manager = DynamicRouteManager(db)
        
        # Use the existing intelligent system and enhance it
        updated_count = route_manager.enhance_for_round_trip_deals()
        
        logger.info(f"✅ Enhanced {updated_count} intelligent routes for round-trip deals!")
        
        # Display current route statistics
        conn = db.connection()
        result = conn.execute(text("SELECT region, COUNT(*) as count FROM routes GROUP BY region"))
        route_stats = result.fetchall()
        
        logger.info("📊 Route distribution by region:")
        for region, count in route_stats:
            logger.info(f"   • {region}: {count} routes")
            
    except Exception as e:
        logger.error(f"❌ Route enhancement failed: {e}")
        raise
    finally:
        db.close()


def validate_migration():
    """
    Validate that the migration was successful
    """
    logger.info("Validating migration...")
    
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Check routes table structure
            result = conn.execute(text("PRAGMA table_info(routes)"))
            routes_columns = [row[1] for row in result.fetchall()]
            
            required_route_columns = [
                'route_type', 'region', 'min_stay_nights', 'max_stay_nights',
                'min_advance_booking_days', 'max_advance_booking_days',
                'allow_mon_wed', 'allow_tue_fri', 'allow_wed_sun'
            ]
            
            missing_route_columns = [col for col in required_route_columns if col not in routes_columns]
            if missing_route_columns:
                logger.error(f"❌ Missing columns in routes table: {missing_route_columns}")
                return False
            
            # Check deals table structure
            result = conn.execute(text("PRAGMA table_info(deals)"))
            deals_columns = [row[1] for row in result.fetchall()]
            
            required_deal_columns = [
                'stay_duration_nights', 'departure_day_of_week', 'return_day_of_week',
                'advance_booking_days', 'meets_stay_requirements', 'meets_timing_requirements',
                'meets_advance_booking', 'is_valid_round_trip'
            ]
            
            missing_deal_columns = [col for col in required_deal_columns if col not in deals_columns]
            if missing_deal_columns:
                logger.error(f"❌ Missing columns in deals table: {missing_deal_columns}")
                return False
            
            # Check route count and types
            result = conn.execute(text("SELECT COUNT(*) FROM routes WHERE route_type = 'round_trip'"))
            route_count = result.fetchone()[0]
            
            result = conn.execute(text("SELECT region, COUNT(*) FROM routes GROUP BY region"))
            region_stats = result.fetchall()
            
            logger.info(f"✅ Migration validation successful!")
            logger.info(f"   - Routes table: All required columns present")
            logger.info(f"   - Deals table: All required columns present")  
            logger.info(f"   - Round-trip routes configured: {route_count}")
            logger.info(f"   - Regional distribution:")
            for region, count in region_stats:
                logger.info(f"     • {region}: {count} routes")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Migration validation failed: {e}")
        return False


if __name__ == "__main__":
    logger.info("🚀 Starting GlobeGenius round-trip enhancement (preserving intelligent routes)...")
    
    try:
        # Step 1: Migrate database schema
        migrate_database()
        
        # Step 2: Enhance existing intelligent route system  
        enhance_intelligent_routes()
        
        # Step 3: Validate migration
        if validate_migration():
            logger.info("🎉 Round-trip enhancement completed successfully!")
            print("\n✅ SUCCESS: GlobeGenius intelligent routes enhanced for round-trip deals!")
            print("📊 Features preserved & enhanced:")
            print("   • ✅ Intelligent dynamic route management")
            print("   • ✅ Seasonal route optimization")
            print("   • ✅ 10k monthly API quota management")
            print("   • ✅ Performance-based route prioritization")
            print("   • ➕ Round-trip deal validation")
            print("   • ➕ Regional stay duration requirements")
            print("   • ➕ 1-9 month advance booking window")
            print("   • ➕ Weekday pattern validation for short stays")
        else:
            logger.error("❌ Migration validation failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        print(f"\n💥 MIGRATION FAILED: {e}")
        sys.exit(1)
