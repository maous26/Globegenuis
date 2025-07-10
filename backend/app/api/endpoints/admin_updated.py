# backend/app/api/endpoints/admin_updated.py
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from app.api import deps
from app.core.database import get_db
from app.services.admin_service import AdminService
from app.services.route_expansion_service import RouteExpansionService
from app.services.api_monitoring_service import ApiMonitoringService
from app.services.enhanced_route_manager import EnhancedRouteManager
from app.models.user import User
from app.utils.logger import logger

router = APIRouter()

@router.get("/api/kpis")
def get_api_kpis(
    timeframe: str = Query("24h", description="Timeframe: 24h, 7d, 30d"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Dict[str, Any]:
    """Get real-time API KPIs and usage statistics"""
    try:
        monitoring_service = ApiMonitoringService(db)
        return monitoring_service.get_real_time_kpis(timeframe)
    except Exception as e:
        logger.error(f"Error getting API KPIs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve API KPIs")

@router.post("/routes/optimize")
def optimize_routes(
    target_api_calls: int = Body(10000, description="Target monthly API calls"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Dict[str, Any]:
    """Optimize routes based on performance and API quota"""
    try:
        route_manager = EnhancedRouteManager(db)
        result = route_manager.auto_optimize_routes(target_api_calls)
        
        # Send optimization report
        from app.services.route_scheduler import scheduler
        import asyncio
        asyncio.create_task(scheduler._send_optimization_report(result))
        
        return result
    except Exception as e:
        logger.error(f"Error optimizing routes: {e}")
        raise HTTPException(status_code=500, detail="Failed to optimize routes")

@router.get("/routes/validate")
def validate_routes(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Dict[str, Any]:
    """Validate all routes against business rules"""
    try:
        route_manager = EnhancedRouteManager(db)
        return route_manager.validate_and_clean_routes()
    except Exception as e:
        logger.error(f"Error validating routes: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate routes")

@router.get("/routes/seasonal-priority")
def get_seasonal_priority_routes(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> List[Dict[str, Any]]:
    """Get priority routes based on current season"""
    try:
        route_manager = EnhancedRouteManager(db)
        return route_manager.get_seasonal_priority_routes()
    except Exception as e:
        logger.error(f"Error getting seasonal routes: {e}")
        raise HTTPException(status_code=500, detail="Failed to get seasonal routes")

@router.get("/quota/alerts")
def get_quota_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> List[Dict[str, Any]]:
    """Get current quota usage alerts"""
    try:
        monitoring_service = ApiMonitoringService(db)
        return monitoring_service.check_quota_alerts()
    except Exception as e:
        logger.error(f"Error checking quota alerts: {e}")
        return []

@router.post("/quota/send-alert")
async def send_quota_alert_test(
    alert_type: str = Body("warning", description="Alert type: warning or critical"),
    message: str = Body("Test quota alert message"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Dict[str, Any]:
    """Send a test quota alert"""
    try:
        monitoring_service = ApiMonitoringService(db)
        await monitoring_service.send_quota_alert(alert_type, message)
        return {"success": True, "message": "Test alert sent"}
    except Exception as e:
        logger.error(f"Error sending test alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to send test alert")

@router.get("/scheduler/status")
def get_scheduler_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Dict[str, Any]:
    """Get scheduler status and statistics"""
    from app.services.route_scheduler import scheduler
    
    return {
        "running": scheduler.running,
        "daily_scan_count": scheduler.daily_scan_count,
        "last_optimization": scheduler.last_optimization.isoformat() if scheduler.last_optimization else None,
        "scan_tasks": len(scheduler.scan_tasks)
    }

@router.post("/scheduler/start")
async def start_scheduler(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Dict[str, Any]:
    """Start the route scheduler"""
    from app.services.route_scheduler import scheduler
    
    if scheduler.running:
        return {"success": False, "message": "Scheduler already running"}
    
    import asyncio
    asyncio.create_task(scheduler.start())
    return {"success": True, "message": "Scheduler started"}

@router.post("/scheduler/stop")
def stop_scheduler(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Dict[str, Any]:
    """Stop the route scheduler"""
    from app.services.route_scheduler import scheduler
    
    scheduler.stop()
    return {"success": True, "message": "Scheduler stopped"}

@router.get("/routes/quota-config")
def get_quota_configuration(
    monthly_quota: int = Query(10000, description="Monthly API quota"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Dict[str, Any]:
    """Get optimal route configuration for given quota"""
    try:
        route_manager = EnhancedRouteManager(db)
        return route_manager.get_optimal_routes_for_quota(monthly_quota)
    except Exception as e:
        logger.error(f"Error getting quota config: {e}")
        raise HTTPException(status_code=500, detail="Failed to get quota configuration")