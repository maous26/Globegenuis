#!/usr/bin/env python3
"""
System initialization script to set up the enhanced GlobeGenius system
Run this after database migration to configure the system properly
"""

import sys
import os

# Add the backend directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

# Now we can import from app
from sqlalchemy.orm import Session
from app.core.database import get_db, engine, Base
from app.models.flight import Route
from app.models.admin_settings import AdminSettings
from app.models.user import User
from app.services.enhanced_route_manager import EnhancedRouteManager
from app.services.route_expansion_service import RouteExpansionService
from app.utils.logger import logger
from datetime import datetime

def initialize_database():
    """Ensure all tables exist"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")

def setup_admin_settings(db: Session):
    """Configure admin settings"""
    settings = db.query(AdminSettings).first()
    if not settings:
        settings = AdminSettings(
            monitoring_email=os.getenv("ADMIN_MONITORING_EMAIL", "admin@globegenius.app"),
            alert_notifications=True,
            daily_reports=True,
            api_quota_alerts=True,
            deal_alerts=True
        )
        db.add(settings)
        db.commit()
        logger.info("Admin settings configured")
    else:
        logger.info("Admin settings already exist")
    
    return settings

def create_initial_routes(db: Session):
    """Create initial set of routes if none exist"""
    route_count = db.query(Route).count()
    
    if route_count == 0:
        logger.info("No routes found. Creating initial route set...")
        
        expansion_service = RouteExpansionService(db)
        
        # Create a balanced set of 60 routes within quota limits
        result = expansion_service.expand_network_smart(
            target_routes=60,
            focus_area="balanced"
        )
        
        logger.info(f"Created {result['total_added']} initial routes")
        logger.info(f"Distribution: {result['updated_stats']['tier_distribution']}")
    else:
        logger.info(f"Found {route_count} existing routes")

def validate_and_optimize_routes(db: Session):
    """Validate existing routes and optimize distribution"""
    route_manager = EnhancedRouteManager(db)
    
    # Validate routes against business rules
    logger.info("Validating routes against business rules...")
    validation_result = route_manager.validate_and_clean_routes()
    logger.info(f"Validation complete: {validation_result['invalid_routes_found']} invalid routes found")
    
    if validation_result['routes_deactivated'] > 0:
        logger.warning(f"Deactivated {validation_result['routes_deactivated']} invalid routes")
    
    # Optimize route distribution for API quota
    logger.info("Optimizing route distribution for 10,000 monthly API calls...")
    optimization_result = route_manager.auto_optimize_routes(target_api_calls=10000)
    logger.info(f"Optimization complete: {optimization_result['routes_updated']} routes updated")
    
    # Add seasonal priority routes
    logger.info("Adding seasonal priority routes...")
    seasonal_routes = route_manager.get_seasonal_priority_routes()
    logger.info(f"Identified {len(seasonal_routes)} seasonal priority routes")
    
    return optimization_result

def setup_initial_data(db: Session):
    """Setup any additional initial data"""
    # Ensure at least one admin user exists
    admin_user = db.query(User).filter(User.is_admin == True).first()
    if not admin_user:
        logger.warning("No admin user found. Please create one through the application.")
    else:
        logger.info(f"Admin user found: {admin_user.email}")
    
    # Initialize API quota tracking for today
    from app.models.api_tracking import ApiQuotaUsage
    today_quota = db.query(ApiQuotaUsage).filter(
        ApiQuotaUsage.date == datetime.now().date()
    ).first()
    
    if not today_quota:
        today_quota = ApiQuotaUsage(
            date=datetime.now().date(),
            calls_made=0,
            successful_calls=0,
            failed_calls=0
        )
        db.add(today_quota)
        db.commit()
        logger.info("Initialized today's API quota tracking")

def display_system_status(db: Session):
    """Display current system status"""
    from app.models.flight import Route
    from app.models.api_tracking import ApiQuotaUsage
    
    # Get route statistics directly
    total_routes = db.query(Route).filter(Route.is_active == True).count()
    tier_1_routes = db.query(Route).filter(Route.tier == 1, Route.is_active == True).count()
    tier_2_routes = db.query(Route).filter(Route.tier == 2, Route.is_active == True).count()
    tier_3_routes = db.query(Route).filter(Route.tier == 3, Route.is_active == True).count()
    
    # Calculate API usage
    tier_1_daily_calls = tier_1_routes * 12  # Every 2 hours
    tier_2_daily_calls = tier_2_routes * 6   # Every 4 hours
    tier_3_daily_calls = tier_3_routes * 4   # Every 6 hours
    total_daily_calls = tier_1_daily_calls + tier_2_daily_calls + tier_3_daily_calls
    total_monthly_calls = total_daily_calls * 30
    utilization = (total_monthly_calls / 10000) * 100
    
    print("\n" + "="*60)
    print("GLOBEGENIUS SYSTEM INITIALIZATION COMPLETE")
    print("="*60)
    print(f"\nROUTE CONFIGURATION:")
    print(f"  Total Routes: {total_routes}")
    print(f"  - Tier 1 (2h scan): {tier_1_routes} routes")
    print(f"  - Tier 2 (4h scan): {tier_2_routes} routes")
    print(f"  - Tier 3 (6h scan): {tier_3_routes} routes")
    
    print(f"\nAPI QUOTA USAGE:")
    print(f"  Monthly Quota: 10,000 calls")
    print(f"  Estimated Daily: {total_daily_calls} calls")
    print(f"  Estimated Monthly: {total_monthly_calls} calls")
    print(f"  Utilization: {utilization:.1f}%")
    
    print(f"\nMONITORING:")
    admin_settings = db.query(AdminSettings).first()
    if admin_settings:
        print(f"  Email: {admin_settings.monitoring_email}")
        print(f"  Alerts Enabled: {admin_settings.alert_notifications}")
        print(f"  Daily Reports: {admin_settings.daily_reports}")
    
    # Get today's API usage if available
    today_usage = db.query(ApiQuotaUsage).filter(
        ApiQuotaUsage.date == datetime.now().date()
    ).first()
    if today_usage:
        print(f"\nTODAY'S USAGE:")
        print(f"  API Calls Made: {today_usage.calls_made}")
        print(f"  Successful: {today_usage.successful_calls}")
        print(f"  Failed: {today_usage.failed_calls}")
    
    print(f"\nNEXT STEPS:")
    print("  1. Start the application: uvicorn app.main:app --reload")
    print("  2. Access admin dashboard: http://localhost:3001/admin")
    print("  3. Verify monitoring email in Admin Settings")
    print("  4. The scheduler will start automatically")
    print("\n" + "="*60 + "\n")

def main():
    """Main initialization function"""
    logger.info("Starting GlobeGenius system initialization...")
    
    try:
        # Initialize database
        initialize_database()
        
        # Get database session
        db = next(get_db())
        
        # Setup admin settings
        setup_admin_settings(db)
        
        # Create initial routes if needed
        create_initial_routes(db)
        
        # Validate and optimize routes
        validate_and_optimize_routes(db)
        
        # Setup initial data
        setup_initial_data(db)
        
        # Display system status
        display_system_status(db)
        
        db.close()
        
        logger.info("System initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during initialization: {e}")
        raise

if __name__ == "__main__":
    main()