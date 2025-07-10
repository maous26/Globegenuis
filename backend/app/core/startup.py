# backend/app/core/startup.py
import asyncio
from app.core.database import get_db
from app.models.admin_settings import AdminSettings
from app.utils.logger import logger

async def initialize_system():
    """Initialize system on startup"""
    try:
        db = next(get_db())
        
        # Ensure admin settings exist
        settings = db.query(AdminSettings).first()
        if not settings:
            settings = AdminSettings(
                monitoring_email="admin@globegenius.app",
                alert_notifications=True,
                daily_reports=True,
                api_quota_alerts=True,
                deal_alerts=True
            )
            db.add(settings)
            db.commit()
            logger.info("Created default admin settings")
        
        logger.info("System initialization complete")
        
        db.close()
        
    except Exception as e:
        logger.error(f"Error during system initialization: {e}")

async def shutdown_system():
    """Cleanup on shutdown"""
    try:
        logger.info("System shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")