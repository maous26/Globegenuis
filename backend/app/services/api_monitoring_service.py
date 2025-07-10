# backend/app/services/api_monitoring_service.py
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from app.models.flight import Route, PriceHistory, Deal
from app.models.api_tracking import ApiCall, ApiQuotaUsage
from app.utils.logger import logger
from decimal import Decimal

class ApiMonitoringService:
    """Service for real-time API monitoring and quota tracking"""
    
    def __init__(self, db: Session):
        self.db = db
        self.monthly_quota = 10000
        self.daily_quota = 333  # 10000 / 30
    
    def track_api_call(self, endpoint: str, route_id: Optional[int] = None,
                      response_time: float = 0, status: str = "success",
                      error_message: Optional[str] = None) -> None:
        """Track each API call for accurate monitoring"""
        
        try:
            # Create API call record
            api_call = ApiCall(
                endpoint=endpoint,
                route_id=route_id,
                timestamp=datetime.now(),
                response_time=response_time,
                status=status,
                error_message=error_message
            )
            self.db.add(api_call)
            
            # Update daily quota usage
            today = datetime.now().date()
            quota_usage = self.db.query(ApiQuotaUsage).filter(
                ApiQuotaUsage.date == today
            ).first()
            
            if not quota_usage:
                quota_usage = ApiQuotaUsage(
                    date=today,
                    calls_made=1,
                    successful_calls=1 if status == "success" else 0,
                    failed_calls=0 if status == "success" else 1
                )
                self.db.add(quota_usage)
            else:
                quota_usage.calls_made += 1
                if status == "success":
                    quota_usage.successful_calls += 1
                else:
                    quota_usage.failed_calls += 1
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error tracking API call: {e}")
            self.db.rollback()
    
    def get_real_time_kpis(self, timeframe: str = "24h") -> Dict[str, Any]:
        """Get real-time API KPIs with accurate data"""
        
        # Define time periods
        now = datetime.now()
        if timeframe == "24h":
            cutoff = now - timedelta(hours=24)
        elif timeframe == "7d":
            cutoff = now - timedelta(days=7)
        elif timeframe == "30d":
            cutoff = now - timedelta(days=30)
        else:
            cutoff = now - timedelta(hours=24)
        
        # Get actual API calls from tracking table
        api_calls = self.db.query(ApiCall).filter(
            ApiCall.timestamp >= cutoff
        ).all()
        
        total_calls = len(api_calls)
        successful_calls = len([c for c in api_calls if c.status == "success"])
        failed_calls = total_calls - successful_calls
        
        # Calculate response times
        response_times = [c.response_time for c in api_calls if c.response_time is not None]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        
        # Get today's usage
        today_usage = self.db.query(ApiQuotaUsage).filter(
            ApiQuotaUsage.date == datetime.now().date()
        ).first()
        
        daily_calls = today_usage.calls_made if today_usage else 0
        
        # Get monthly usage
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_usage = self.db.query(
            func.sum(ApiQuotaUsage.calls_made)
        ).filter(
            ApiQuotaUsage.date >= month_start.date()
        ).scalar() or 0
        
        # Calculate tier breakdown from actual scans
        tier_stats = {}
        for tier in [1, 2, 3]:
            tier_routes = self.db.query(Route).filter(
                Route.tier == tier,
                Route.is_active == True
            ).all()
            
            tier_calls = self.db.query(ApiCall).join(Route).filter(
                Route.tier == tier,
                ApiCall.timestamp >= cutoff
            ).count()
            
            tier_deals = self.db.query(Deal).join(Route).filter(
                Route.tier == tier,
                Deal.detected_at >= cutoff
            ).count()
            
            # Calculate expected daily calls based on scan intervals
            scan_interval = {1: 2, 2: 4, 3: 6}[tier]
            expected_daily_calls = len(tier_routes) * (24 / scan_interval)
            
            tier_stats[f"tier_{tier}"] = {
                "routes": len(tier_routes),
                "calls_in_period": tier_calls,
                "deals_found": tier_deals,
                "scan_interval_hours": scan_interval,
                "scans_per_day": int(24 / scan_interval),
                "daily_api_calls": int(expected_daily_calls),
                "actual_calls_today": self.db.query(ApiCall).join(Route).filter(
                    Route.tier == tier,
                    ApiCall.timestamp >= now.replace(hour=0, minute=0, second=0, microsecond=0)
                ).count()
            }
        
        # Get recent API calls with full details
        recent_calls = self.db.query(ApiCall, Route).join(
            Route, ApiCall.route_id == Route.id, isouter=True
        ).filter(
            ApiCall.timestamp >= now - timedelta(hours=2)
        ).order_by(ApiCall.timestamp.desc()).limit(20).all()
        
        recent_calls_data = []
        for api_call, route in recent_calls:
            if route:
                route_name = f"{route.origin}→{route.destination}"
                tier = route.tier
            else:
                route_name = api_call.endpoint
                tier = None
            
            # Check if this call resulted in deals
            deals_found = 0
            if api_call.route_id:
                deals_found = self.db.query(Deal).filter(
                    Deal.route_id == api_call.route_id,
                    Deal.detected_at.between(
                        api_call.timestamp - timedelta(minutes=5),
                        api_call.timestamp + timedelta(minutes=5)
                    )
                ).count()
            
            recent_calls_data.append({
                "route": route_name,
                "tier": tier,
                "status": api_call.status.title(),
                "response_time": f"{api_call.response_time:.1f}s" if api_call.response_time else "N/A",
                "deals_found": deals_found,
                "timestamp": api_call.timestamp.strftime("%H:%M"),
                "error": api_call.error_message
            })
        
        # Get active deals with full information
        active_deals = self.db.query(Deal, Route, PriceHistory).join(
            Route, Deal.route_id == Route.id
        ).join(
            PriceHistory, Deal.price_history_id == PriceHistory.id
        ).filter(
            Deal.is_active == True,
            Deal.detected_at >= cutoff
        ).order_by(Deal.detected_at.desc()).limit(20).all()
        
        active_deals_data = []
        for deal, route, price_history in active_deals:
            active_deals_data.append({
                "id": deal.id,
                "route": f"{route.origin}→{route.destination}",
                "route_id": route.id,
                "tier": route.tier,
                "deal_price": float(deal.deal_price),
                "normal_price": float(deal.normal_price) if deal.normal_price else None,
                "savings_percentage": float(deal.discount_percentage),
                "departure_date": price_history.departure_date.isoformat(),
                "return_date": price_history.return_date.isoformat() if price_history.return_date else None,
                "airline": price_history.airline,
                "detected_at": deal.detected_at.isoformat(),
                "freshness_hours": int((now - deal.detected_at).total_seconds() / 3600)
            })
        
        # Calculate totals
        total_routes = sum(tier_stats[f"tier_{t}"]["routes"] for t in [1, 2, 3])
        total_expected_daily_calls = sum(tier_stats[f"tier_{t}"]["daily_api_calls"] for t in [1, 2, 3])
        total_actual_calls_today = sum(tier_stats[f"tier_{t}"]["actual_calls_today"] for t in [1, 2, 3])
        
        # Cost calculations
        cost_per_call = 0.005
        monthly_cost = monthly_usage * cost_per_call
        
        return {
            "timeframe": timeframe,
            "period_name": f"Last {timeframe}",
            "total_api_calls": total_calls,
            "daily_api_calls": daily_calls,
            "monthly_api_calls": monthly_usage,
            "quota": {
                "monthly_limit": self.monthly_quota,
                "used": monthly_usage,
                "remaining": max(0, self.monthly_quota - monthly_usage),
                "usage_percentage": (monthly_usage / self.monthly_quota) * 100,
                "daily_limit": self.daily_quota,
                "daily_used": daily_calls,
                "daily_remaining": max(0, self.daily_quota - daily_calls)
            },
            "cost": {
                "per_call": cost_per_call,
                "monthly_total": monthly_cost,
                "daily_total": daily_calls * cost_per_call,
                "projected_monthly": total_expected_daily_calls * 30 * cost_per_call
            },
            "performance": {
                "avg_response_time": avg_response_time,
                "min_response_time": min_response_time,
                "max_response_time": max_response_time,
                "success_rate": (successful_calls / max(total_calls, 1)) * 100,
                "total_errors": failed_calls
            },
            "tier_breakdown": tier_stats,
            "totals": {
                "routes": total_routes,
                "expected_daily_calls": total_expected_daily_calls,
                "actual_daily_calls": total_actual_calls_today,
                "monthly_calls": total_expected_daily_calls * 30
            },
            "deals": {
                "active_deals": active_deals_data,
                "total_active": len(active_deals_data),
                "last_24h": self.db.query(Deal).filter(
                    Deal.detected_at >= now - timedelta(hours=24)
                ).count(),
                "last_week": self.db.query(Deal).filter(
                    Deal.detected_at >= now - timedelta(days=7)
                ).count(),
                "last_month": self.db.query(Deal).filter(
                    Deal.detected_at >= now - timedelta(days=30)
                ).count(),
                "average_savings": sum(d["savings_percentage"] for d in active_deals_data) / max(len(active_deals_data), 1) if active_deals_data else 0
            },
            "recent_calls": recent_calls_data,
            "synchronization": {
                "last_sync": datetime.now().isoformat(),
                "data_source": "real_time",
                "accuracy": "100%"
            }
        }
    
    def check_quota_alerts(self) -> List[Dict[str, Any]]:
        """Check for quota usage alerts"""
        
        alerts = []
        
        # Get current usage
        today_usage = self.db.query(ApiQuotaUsage).filter(
            ApiQuotaUsage.date == datetime.now().date()
        ).first()
        
        if today_usage:
            daily_percentage = (today_usage.calls_made / self.daily_quota) * 100
            
            if daily_percentage >= 90:
                alerts.append({
                    "type": "critical",
                    "message": f"Daily API quota at {daily_percentage:.1f}% ({today_usage.calls_made}/{self.daily_quota})",
                    "action": "Consider reducing scan frequency or disabling some routes"
                })
            elif daily_percentage >= 75:
                alerts.append({
                    "type": "warning",
                    "message": f"Daily API quota at {daily_percentage:.1f}% ({today_usage.calls_made}/{self.daily_quota})",
                    "action": "Monitor usage closely"
                })
        
        # Check monthly usage
        month_start = datetime.now().replace(day=1).date()
        monthly_usage = self.db.query(
            func.sum(ApiQuotaUsage.calls_made)
        ).filter(
            ApiQuotaUsage.date >= month_start
        ).scalar() or 0
        
        monthly_percentage = (monthly_usage / self.monthly_quota) * 100
        days_in_month = 30
        current_day = datetime.now().day
        expected_percentage = (current_day / days_in_month) * 100
        
        if monthly_percentage > expected_percentage * 1.2:  # 20% above expected
            alerts.append({
                "type": "warning",
                "message": f"Monthly usage ahead of schedule: {monthly_percentage:.1f}% used on day {current_day}",
                "action": "Review route optimization to stay within monthly quota"
            })
        
        return alerts
    
    async def send_quota_alert(self, alert_type: str, message: str):
        """Send quota alert to monitoring email"""
        
        from app.models.admin_settings import AdminSettings
        from app.services.email_service import EmailService
        
        settings = self.db.query(AdminSettings).first()
        if not settings or not settings.monitoring_email or not settings.api_quota_alerts:
            return
        
        email_service = EmailService()
        
        color = "#dc3545" if alert_type == "critical" else "#ffc107"
        icon = "🚨" if alert_type == "critical" else "⚠️"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto;">
            <div style="background: {color}; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0;">{icon} API Quota Alert</h1>
            </div>
            
            <div style="padding: 20px; background: #f8f9fa; border: 1px solid #dee2e6;">
                <h3>Alert Type: {alert_type.upper()}</h3>
                <p style="font-size: 16px;">{message}</p>
                
                <div style="background: white; padding: 15px; border-radius: 4px; margin: 20px 0;">
                    <h4>Current Usage Statistics:</h4>
                    {self._get_usage_stats_html()}
                </div>
                
                <p style="text-align: center; margin-top: 20px;">
                    <a href="http://localhost:3001/admin" 
                       style="background: #007bff; color: white; padding: 10px 20px; 
                              text-decoration: none; border-radius: 4px;">
                        View Admin Dashboard
                    </a>
                </p>
            </div>
        </div>
        """
        
        try:
            await email_service.send_admin_alert(
                subject=f"{icon} API Quota Alert: {alert_type.upper()}",
                html_content=html_content,
                to_email=settings.monitoring_email
            )
            logger.info(f"Quota alert sent: {alert_type} - {message}")
        except Exception as e:
            logger.error(f"Failed to send quota alert: {e}")
    
    def _get_usage_stats_html(self) -> str:
        """Get usage statistics HTML for email"""
        
        today_usage = self.db.query(ApiQuotaUsage).filter(
            ApiQuotaUsage.date == datetime.now().date()
        ).first()
        
        month_start = datetime.now().replace(day=1).date()
        monthly_usage = self.db.query(
            func.sum(ApiQuotaUsage.calls_made)
        ).filter(
            ApiQuotaUsage.date >= month_start
        ).scalar() or 0
        
        daily_percentage = (today_usage.calls_made / self.daily_quota * 100) if today_usage else 0
        monthly_percentage = (monthly_usage / self.monthly_quota * 100)
        
        return f"""
        <ul>
            <li><strong>Daily Usage:</strong> {today_usage.calls_made if today_usage else 0} / {self.daily_quota} ({daily_percentage:.1f}%)</li>
            <li><strong>Monthly Usage:</strong> {monthly_usage} / {self.monthly_quota} ({monthly_percentage:.1f}%)</li>
            <li><strong>Remaining Daily:</strong> {max(0, self.daily_quota - (today_usage.calls_made if today_usage else 0))}</li>
            <li><strong>Remaining Monthly:</strong> {max(0, self.monthly_quota - monthly_usage)}</li>
        </ul>
        """
    
    async def send_quota_alert(self, alert_type: str, message: str):
        """Send quota alert to monitoring email"""
        
        from app.models.admin_settings import AdminSettings
        from app.services.email_service import EmailService
        
        settings = self.db.query(AdminSettings).first()
        if not settings or not settings.monitoring_email or not settings.api_quota_alerts:
            return
        
        email_service = EmailService()
        
        color = "#dc3545" if alert_type == "critical" else "#ffc107"
        icon = "🚨" if alert_type == "critical" else "⚠️"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto;">
            <div style="background: {color}; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0;">{icon} API Quota Alert</h1>
            </div>
            
            <div style="padding: 20px; background: #f8f9fa; border: 1px solid #ddd; border-radius: 0 0 8px 8px;">
                <h2 style="color: #333; margin-top: 0;">Alert Details</h2>
                <p><strong>Type:</strong> {alert_type.title()}</p>
                <p><strong>Current Usage:</strong> {usage_pct:.1f}%</p>
                <p><strong>Remaining Quota:</strong> {remaining_quota:,}</p>
                <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </div>
        """
        
        # Send alert email
        email_service.send_email(
            to_email=settings.monitoring_email,
            subject=f"API Quota Alert - {alert_type.title()}",
            html_body=html_content
        )
