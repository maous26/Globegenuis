# backend/app/api/endpoints/admin.py
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from app.api import deps
from app.core.database import get_db
from app.services.admin_service import AdminService
from app.services.route_expansion_service import RouteExpansionService
from app.models.user import User
from app.utils.logger import logger

router = APIRouter()


@router.get("/dashboard/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Dict[str, Any]:
    """Get comprehensive dashboard statistics"""
    admin_service = AdminService(db)
    return admin_service.get_dashboard_stats()


@router.get("/routes/performance")
def get_route_performance(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> List[Dict[str, Any]]:
    """Get route performance metrics"""
    admin_service = AdminService(db)
    return admin_service.get_route_performance(days)


@router.get("/seasonal/visualization")
def get_seasonal_visualization(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Dict[str, Any]:
    """Get seasonal strategy visualization data"""
    admin_service = AdminService(db)
    return admin_service.get_seasonal_strategy_visualization()


@router.get("/users/analytics")
def get_user_analytics(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Dict[str, Any]:
    """Get user analytics and growth metrics"""
    admin_service = AdminService(db)
    return admin_service.get_user_analytics(days)


@router.post("/routes/{route_id}/scan")
def trigger_route_scan(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Dict[str, Any]:
    """Trigger manual scan for a specific route"""
    admin_service = AdminService(db)
    result = admin_service.trigger_route_scan(route_id)
    
    if 'error' in result:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return result


@router.post("/routes/tier/{tier}/scan")
def trigger_tier_scan(
    tier: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Dict[str, Any]:
    """Trigger manual scan for all routes in a tier"""
    if tier not in [1, 2, 3]:
        raise HTTPException(status_code=400, detail="Invalid tier. Must be 1, 2, or 3")
    
    admin_service = AdminService(db)
    result = admin_service.trigger_tier_scan(tier)
    
    if 'error' in result:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return result


@router.get("/system/health")
def get_system_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Dict[str, Any]:
    """Get system health metrics"""
    admin_service = AdminService(db)
    return admin_service.get_system_health()


@router.put("/routes/{route_id}/settings")
def update_route_settings(
    route_id: int,
    settings: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Dict[str, Any]:
    """Update route settings"""
    admin_service = AdminService(db)
    result = admin_service.update_route_settings(route_id, settings)
    
    if 'error' in result:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return result


@router.get("/monitoring/scanner")
def get_scanner_monitoring(
    hours: int = Query(24, description="Number of hours to monitor"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Dict[str, Any]:
    """Get scanner monitoring data"""
    admin_service = AdminService(db)
    
    # Get scanner activity for the specified hours
    from datetime import datetime, timedelta
    from app.models.flight import PriceHistory, Deal
    from sqlalchemy import func, and_
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    # Scanner activity by hour
    hourly_scans = db.query(
        func.date_trunc('hour', PriceHistory.scanned_at).label('hour'),
        func.count(PriceHistory.id).label('scan_count')
    ).filter(
        PriceHistory.scanned_at >= cutoff_time
    ).group_by(
        func.date_trunc('hour', PriceHistory.scanned_at)
    ).order_by('hour').all()
    
    # Deals detected by hour
    hourly_deals = db.query(
        func.date_trunc('hour', Deal.detected_at).label('hour'),
        func.count(Deal.id).label('deal_count')
    ).filter(
        Deal.detected_at >= cutoff_time
    ).group_by(
        func.date_trunc('hour', Deal.detected_at)
    ).order_by('hour').all()
    
    # API quota usage
    total_scans_today = db.query(PriceHistory).filter(
        PriceHistory.scanned_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    ).count()
    
    return {
        'hourly_scans': [
            {
                'hour': scan.hour.isoformat(),
                'scan_count': scan.scan_count
            }
            for scan in hourly_scans
        ],
        'hourly_deals': [
            {
                'hour': deal.hour.isoformat(),
                'deal_count': deal.deal_count
            }
            for deal in hourly_deals
        ],
        'api_quota': {
            'used_today': total_scans_today,
            'daily_limit': 333,
            'remaining': max(0, 333 - total_scans_today),
            'usage_percentage': (total_scans_today / 333) * 100
        },
        'period': f"Last {hours} hours"
    }


@router.get("/users/list")
def get_users_list(
    skip: int = Query(0, description="Number of users to skip"),
    limit: int = Query(50, description="Maximum number of users to return"),
    search: Optional[str] = Query(None, description="Search by email or name"),
    tier: Optional[str] = Query(None, description="Filter by tier"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Dict[str, Any]:
    """Get paginated users list with search and filters"""
    from app.models.user import User, UserTier
    from sqlalchemy import or_
    
    # Build query
    query = db.query(User)
    
    # Apply search filter
    if search:
        query = query.filter(
            or_(
                User.email.ilike(f"%{search}%"),
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%")
            )
        )
    
    # Apply tier filter
    if tier:
        try:
            tier_enum = UserTier(tier)
            query = query.filter(User.tier == tier_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid tier value")
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    users = query.offset(skip).limit(limit).all()
    
    # Format response
    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'tier': user.tier.value,
            'is_active': user.is_active,
            'is_verified': user.is_verified,
            'is_admin': user.is_admin,
            'auth_provider': user.auth_provider,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'last_login_at': user.last_login_at.isoformat() if user.last_login_at else None,
            'profile_picture': user.profile_picture
        })
    
    return {
        'users': users_data,
        'total': total,
        'skip': skip,
        'limit': limit,
        'has_more': total > skip + limit
    }


@router.get("/routes/expansion/stats")
def get_route_expansion_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Dict[str, Any]:
    """Get current route statistics and expansion opportunities"""
    expansion_service = RouteExpansionService(db)
    return expansion_service.get_current_route_stats()


@router.get("/routes/expansion/suggestions")
def get_route_suggestions(
    count: int = Query(20, description="Number of route suggestions"),
    target_tier: int = Query(3, ge=1, le=3, description="Target tier for suggestions"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> List[Dict[str, Any]]:
    """Get intelligent route suggestions for network expansion"""
    expansion_service = RouteExpansionService(db)
    return expansion_service.suggest_new_routes(count, target_tier)


@router.post("/routes/expansion/add-routes")
def add_routes_manually(
    route_configs: List[Dict[str, Any]] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Dict[str, Any]:
    """Manually add multiple routes from a list of configurations"""
    expansion_service = RouteExpansionService(db)
    return expansion_service.add_routes_automatically(route_configs)


@router.post("/routes/expansion/smart-expand")
def smart_network_expansion(
    target_routes: int = Body(..., description="Target total number of routes"),
    focus_area: str = Body("balanced", description="Focus area: balanced, domestic, international, vacation"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Dict[str, Any]:
    """Automatically expand network to target number of routes with smart selection"""
    
    # Validate focus area
    valid_focus_areas = ["balanced", "domestic", "international", "vacation"]
    if focus_area not in valid_focus_areas:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid focus_area. Must be one of: {', '.join(valid_focus_areas)}"
        )
    
    # Validate target routes
    if target_routes < 1 or target_routes > 500:
        raise HTTPException(
            status_code=400,
            detail="Target routes must be between 1 and 500"
        )
    
    expansion_service = RouteExpansionService(db)
    return expansion_service.expand_network_smart(target_routes, focus_area)


@router.get("/routes/expansion/preview")
def preview_expansion(
    target_routes: int = Query(..., description="Target total number of routes"),
    focus_area: str = Query("balanced", description="Focus area: balanced, domestic, international, vacation"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Dict[str, Any]:
    """Preview what routes would be added without actually adding them"""
    
    # Validate focus area
    valid_focus_areas = ["balanced", "domestic", "international", "vacation"]
    if focus_area not in valid_focus_areas:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid focus_area. Must be one of: {', '.join(valid_focus_areas)}"
        )
    
    expansion_service = RouteExpansionService(db)
    current_stats = expansion_service.get_current_route_stats()
    current_total = current_stats["total_routes"]
    
    if current_total >= target_routes:
        return {
            "message": f"Already have {current_total} routes (target: {target_routes})",
            "preview_routes": [],
            "current_stats": current_stats
        }
    
    routes_to_add = target_routes - current_total
    
    # Determine tier distribution based on focus area
    if focus_area == "domestic":
        tier_distribution = {"tier_3": 0.6, "tier_2": 0.3, "tier_1": 0.1}
    elif focus_area == "international":
        tier_distribution = {"tier_2": 0.5, "tier_1": 0.3, "tier_3": 0.2}
    elif focus_area == "vacation":
        tier_distribution = {"tier_3": 0.5, "tier_2": 0.4, "tier_1": 0.1}
    else:  # balanced
        tier_distribution = {"tier_3": 0.5, "tier_2": 0.3, "tier_1": 0.2}
    
    # Generate preview for each tier
    preview_routes = []
    tier_breakdown = {}
    
    for tier_name, percentage in tier_distribution.items():
        tier_num = int(tier_name.split("_")[1])
        tier_routes_count = int(routes_to_add * percentage)
        tier_breakdown[f"tier_{tier_num}"] = tier_routes_count
        
        if tier_routes_count > 0:
            suggestions = expansion_service.suggest_new_routes(tier_routes_count, tier_num)
            preview_routes.extend(suggestions)
    
    return {
        "expansion_strategy": focus_area,
        "target_routes": target_routes,
        "current_total": current_total,
        "routes_to_add": routes_to_add,
        "tier_breakdown": tier_breakdown,
        "preview_routes": preview_routes,
        "current_stats": current_stats
    }


@router.get("/api/kpis")
def get_api_kpis(
    timeframe: str = Query("24h", description="Timeframe: 24h, 7d, 30d"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Dict[str, Any]:
    """Get real-time API KPIs and usage statistics"""
    from datetime import datetime, timedelta
    from app.models.flight import PriceHistory, Deal, Route
    from app.models.alert import Alert
    from sqlalchemy import func, and_
    
    # Define time periods
    now = datetime.now()
    if timeframe == "24h":
        cutoff = now - timedelta(hours=24)
        period_name = "Last 24 hours"
    elif timeframe == "7d":
        cutoff = now - timedelta(days=7)
        period_name = "Last 7 days"
    elif timeframe == "30d":
        cutoff = now - timedelta(days=30)
        period_name = "Last 30 days"
    else:
        cutoff = now - timedelta(hours=24)
        period_name = "Last 24 hours"
    
    # API Usage Statistics
    total_api_calls = db.query(PriceHistory).filter(
        PriceHistory.scanned_at >= cutoff
    ).count()
    
    # Daily API calls for quota calculation
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    daily_api_calls = db.query(PriceHistory).filter(
        PriceHistory.scanned_at >= today
    ).count()
    
    # Monthly API calls
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_api_calls = db.query(PriceHistory).filter(
        PriceHistory.scanned_at >= month_start
    ).count()
    
    # Route and tier breakdown
    tier_stats = {}
    for tier in [1, 2, 3]:
        routes_count = db.query(Route).filter(
            Route.tier == tier,
            Route.is_active == True
        ).count()
        
        # Calculate scans for this tier in the timeframe
        tier_scans = db.query(PriceHistory).join(Route).filter(
            Route.tier == tier,
            PriceHistory.scanned_at >= cutoff
        ).count()
        
        # Calculate deals found for this tier
        tier_deals = db.query(Deal).join(Route).filter(
            Route.tier == tier,
            Deal.detected_at >= cutoff
        ).count()
        
        # Calculate average scan interval for this tier
        scan_interval = 2 if tier == 1 else (4 if tier == 2 else 6)
        scans_per_day = routes_count * (24 / scan_interval) if routes_count > 0 else 0
        
        tier_stats[f"tier_{tier}"] = {
            "routes": routes_count,
            "scans_in_period": tier_scans,
            "deals_found": tier_deals,
            "scan_interval_hours": scan_interval,
            "scans_per_day": int(scans_per_day),
            "daily_api_calls": int(scans_per_day)
        }
    
    # Performance metrics
    performance_stats = db.query(
        func.avg(PriceHistory.response_time).label('avg_response_time'),
        func.min(PriceHistory.response_time).label('min_response_time'),
        func.max(PriceHistory.response_time).label('max_response_time'),
        func.count(PriceHistory.id).label('total_scans')
    ).filter(
        PriceHistory.scanned_at >= cutoff,
        PriceHistory.response_time.isnot(None)
    ).first()
    
    # Error statistics
    total_scans_with_status = db.query(PriceHistory).filter(
        PriceHistory.scanned_at >= cutoff,
        PriceHistory.status.isnot(None)
    ).count()
    
    successful_scans = db.query(PriceHistory).filter(
        PriceHistory.scanned_at >= cutoff,
        PriceHistory.status == 'success'
    ).count()
    
    error_scans = total_scans_with_status - successful_scans
    success_rate = (successful_scans / max(total_scans_with_status, 1)) * 100
    
    # Recent API calls for log
    recent_calls = db.query(PriceHistory).join(Route).filter(
        PriceHistory.scanned_at >= now - timedelta(hours=2)
    ).order_by(PriceHistory.scanned_at.desc()).limit(10).all()
    
    recent_calls_data = []
    for call in recent_calls:
        route_name = f"{call.route.origin}→{call.route.destination}"
        status = call.status or "unknown"
        response_time = f"{call.response_time:.1f}s" if call.response_time else "N/A"
        
        # Count deals found for this specific scan
        deals_in_scan = db.query(Deal).filter(
            Deal.route_id == call.route_id,
            Deal.detected_at.between(
                call.scanned_at - timedelta(minutes=5),
                call.scanned_at + timedelta(minutes=5)
            )
        ).count()
        
        recent_calls_data.append({
            "route": route_name,
            "tier": call.route.tier,
            "status": status.title(),
            "response_time": response_time,
            "deals_found": deals_in_scan,
            "timestamp": call.scanned_at.strftime("%H:%M")
        })
    
    # Calculate totals
    total_routes = sum(tier_stats[f"tier_{tier}"]["routes"] for tier in [1, 2, 3])
    total_daily_calls = sum(tier_stats[f"tier_{tier}"]["daily_api_calls"] for tier in [1, 2, 3])
    
    # Quota calculations (assuming 10,000 monthly limit)
    monthly_quota = 10000
    quota_usage_percentage = (monthly_api_calls / monthly_quota) * 100
    remaining_quota = max(0, monthly_quota - monthly_api_calls)
    
    # Cost calculations (assuming $0.005 per call)
    cost_per_call = 0.005
    monthly_cost = monthly_api_calls * cost_per_call
    
    return {
        "timeframe": timeframe,
        "period_name": period_name,
        "total_api_calls": total_api_calls,
        "daily_api_calls": daily_api_calls,
        "monthly_api_calls": monthly_api_calls,
        "quota": {
            "monthly_limit": monthly_quota,
            "used": monthly_api_calls,
            "remaining": remaining_quota,
            "usage_percentage": quota_usage_percentage,
            "daily_limit": 333,  # 10000/30
            "daily_used": daily_api_calls
        },
        "cost": {
            "per_call": cost_per_call,
            "monthly_total": monthly_cost,
            "projected_monthly": total_daily_calls * 30 * cost_per_call
        },
        "performance": {
            "avg_response_time": float(performance_stats.avg_response_time or 0),
            "min_response_time": float(performance_stats.min_response_time or 0),
            "max_response_time": float(performance_stats.max_response_time or 0),
            "success_rate": success_rate,
            "total_errors": error_scans
        },
        "tier_breakdown": tier_stats,
        "totals": {
            "routes": total_routes,
            "daily_calls": total_daily_calls,
            "monthly_calls": total_daily_calls * 30
        },
        "recent_calls": recent_calls_data
    }
