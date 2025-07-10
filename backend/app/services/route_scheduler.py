# backend/app/services/route_scheduler.py
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.flight import Route
from app.models.admin_settings import AdminSettings
from app.services.enhanced_flight_scanner import EnhancedFlightScanner
from app.services.api_monitoring_service import ApiMonitoringService
from app.services.enhanced_route_manager import EnhancedRouteManager
from app.services.email_service import EmailService
from app.core.database import get_db
from app.utils.logger import logger
import schedule
import time

class RouteScheduler:
    """Automated route scanning scheduler with monitoring"""
    
    def __init__(self):
        self.running = False
        self.scan_tasks = {}
        self.daily_scan_count = 0
        self.last_optimization = None
        
    async def start(self):
        """Start the scheduler"""
        self.running = True
        logger.info("Route scheduler started")
        
        # Schedule daily tasks
        schedule.every().day.at("00:00").do(self._reset_daily_counters)
        schedule.every().day.at("06:00").do(self._morning_optimization)
        schedule.every().day.at("18:00").do(self._evening_report)
        schedule.every().hour.do(self._check_quota_status)
        
        # Start the main loop
        await self._main_loop()
    
    async def _main_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                # Get database session
                db = next(get_db())
                
                # Check and run scheduled jobs
                schedule.run_pending()
                
                # Scan routes based on their intervals
                await self._scan_due_routes(db)
                
                # Sleep for a short interval
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in scheduler main loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
            finally:
                db.close()
    
    async def _scan_due_routes(self, db: Session):
        """Scan routes that are due for scanning"""
        
        try:
            # Check if we're within quota limits
            monitoring = ApiMonitoringService(db)
            quota_alerts = monitoring.check_quota_alerts()
            
            # If critical quota alert, pause scanning
            if any(alert["type"] == "critical" for alert in quota_alerts):
                logger.warning("Critical quota limit reached, pausing scans")
                return
            
            # Get routes due for scanning
            now = datetime.now()
            due_routes = []
            
            for tier in [1, 2, 3]:
                interval_hours = {1: 2, 2: 4, 3: 6}[tier]
                
                routes = db.query(Route).filter(
                    and_(
                        Route.is_active == True,
                        Route.tier == tier,
                        Route.last_scanned_at < now - timedelta(hours=interval_hours)
                    )
                ).limit(5).all()  # Limit concurrent scans
                
                due_routes.extend(routes)
            
            if not due_routes:
                return
            
            # Scan routes
            scanner = EnhancedFlightScanner(db)
            
            for route in due_routes:
                try:
                    # Track API call
                    start_time = datetime.now()
                    
                    # Scan route
                    deals = await scanner.scan_route(route)
                    
                    # Track completion
                    response_time = (datetime.now() - start_time).total_seconds()
                    monitoring.track_api_call(
                        endpoint=f"scan_route_{route.id}",
                        route_id=route.id,
                        response_time=response_time,
                        status="success"
                    )
                    
                    # Update route last scan time
                    route.last_scanned_at = datetime.now()
                    db.commit()
                    
                    self.daily_scan_count += 1
                    
                    logger.info(f"Scanned route {route.origin}->{route.destination}: {len(deals)} deals found")
                    
                except Exception as e:
                    logger.error(f"Error scanning route {route.id}: {e}")
                    monitoring.track_api_call(
                        endpoint=f"scan_route_{route.id}",
                        route_id=route.id,
                        response_time=0,
                        status="error",
                        error_message=str(e)
                    )
                
                # Small delay between scans
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"Error in _scan_due_routes: {e}")
    
    def _reset_daily_counters(self):
        """Reset daily counters"""
        self.daily_scan_count = 0
        logger.info("Daily counters reset")
    
    def _morning_optimization(self):
        """Run morning route optimization"""
        try:
            db = next(get_db())
            
            # Run route optimization
            route_manager = EnhancedRouteManager(db)
            result = route_manager.auto_optimize_routes(target_api_calls=10000)
            
            self.last_optimization = datetime.now()
            
            logger.info(f"Morning optimization complete: {result['routes_updated']} routes updated")
            
            # Send optimization report if enabled
            asyncio.create_task(self._send_optimization_report(result))
            
        except Exception as e:
            logger.error(f"Error in morning optimization: {e}")
        finally:
            db.close()
    
    async def _evening_report(self):
        """Send evening summary report"""
        try:
            db = next(get_db())
            
            # Get admin settings
            settings = db.query(AdminSettings).first()
            if not settings or not settings.monitoring_email or not settings.daily_reports:
                return
            
            # Get daily statistics
            monitoring = ApiMonitoringService(db)
            kpis = monitoring.get_real_time_kpis("24h")
            
            # Prepare report
            html_content = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto;">
                <div style="background: #17a2b8; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                    <h1 style="margin: 0;">📊 Daily Operations Report</h1>
                </div>
                
                <div style="padding: 20px; background: #f8f9fa; border: 1px solid #dee2e6;">
                    <h3>Date: {datetime.now().strftime('%Y-%m-%d')}</h3>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0;">
                        <div style="background: white; padding: 15px; border-radius: 4px;">
                            <div style="font-size: 24px; font-weight: bold; color: #28a745;">
                                {kpis['daily_api_calls']}
                            </div>
                            <div style="color: #6c757d;">API Calls Today</div>
                        </div>
                        
                        <div style="background: white; padding: 15px; border-radius: 4px;">
                            <div style="font-size: 24px; font-weight: bold; color: #ffc107;">
                                {kpis['deals']['last_24h']}
                            </div>
                            <div style="color: #6c757d;">Deals Found</div>
                        </div>
                        
                        <div style="background: white; padding: 15px; border-radius: 4px;">
                            <div style="font-size: 24px; font-weight: bold; color: #17a2b8;">
                                {kpis['performance']['success_rate']:.1f}%
                            </div>
                            <div style="color: #6c757d;">Success Rate</div>
                        </div>
                        
                        <div style="background: white; padding: 15px; border-radius: 4px;">
                            <div style="font-size: 24px; font-weight: bold; color: #6c757d;">
                                ${kpis['cost']['daily_total']:.2f}
                            </div>
                            <div style="color: #6c757d;">Daily Cost</div>
                        </div>
                    </div>
                    
                    <h4>Tier Performance:</h4>
                    <ul>
                        <li>Tier 1: {kpis['tier_breakdown']['tier_1']['actual_calls_today']} calls, {kpis['tier_breakdown']['tier_1']['deals_found']} deals</li>
                        <li>Tier 2: {kpis['tier_breakdown']['tier_2']['actual_calls_today']} calls, {kpis['tier_breakdown']['tier_2']['deals_found']} deals</li>
                        <li>Tier 3: {kpis['tier_breakdown']['tier_3']['actual_calls_today']} calls, {kpis['tier_breakdown']['tier_3']['deals_found']} deals</li>
                    </ul>
                    
                    <h4>Top Deals Found:</h4>
                    {self._format_top_deals(kpis['deals']['active_deals'][:5])}
                    
                    <p style="text-align: center; margin-top: 30px;">
                        <a href="http://localhost:3001/admin" 
                           style="background: #007bff; color: white; padding: 10px 20px; 
                                  text-decoration: none; border-radius: 4px;">
                            View Full Dashboard
                        </a>
                    </p>
                </div>
                
                <div style="text-align: center; color: #6c757d; font-size: 12px; margin-top: 20px;">
                    <p>GlobeGenius Daily Report</p>
                    <p>Next optimization scheduled for tomorrow at 06:00</p>
                </div>
            </div>
            """
            
            # Send report
            email_service = EmailService()
            await email_service.send_admin_alert(
                subject=f"📊 Daily Report: {kpis['deals']['last_24h']} deals found",
                html_content=html_content,
                to_email=settings.monitoring_email
            )
            
            logger.info("Evening report sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending evening report: {e}")
        finally:
            db.close()
    
    def _format_top_deals(self, deals: List[Dict]) -> str:
        """Format top deals for email"""
        if not deals:
            return "<p>No deals found today</p>"
        
        html = "<ul>"
        for deal in deals:
            html += f"""
            <li>
                <strong>{deal['route']}</strong>: 
                €{deal['deal_price']} 
                (save {deal['savings_percentage']:.0f}%)
                - Departure: {deal['departure_date'][:10]}
            </li>
            """
        html += "</ul>"
        
        return html
    
    async def _check_quota_status(self):
        """Check quota status and send alerts if needed"""
        try:
            db = next(get_db())
            monitoring = ApiMonitoringService(db)
            
            alerts = monitoring.check_quota_alerts()
            
            for alert in alerts:
                await monitoring.send_quota_alert(alert["type"], alert["message"])
                
        except Exception as e:
            logger.error(f"Error checking quota status: {e}")
        finally:
            db.close()
    
    async def _send_optimization_report(self, result: Dict):
        """Send optimization report"""
        try:
            db = next(get_db())
            settings = db.query(AdminSettings).first()
            
            if not settings or not settings.monitoring_email:
                return
            
            if result['routes_updated'] == 0:
                return  # No changes to report
            
            html_content = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto;">
                <div style="background: #28a745; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                    <h1 style="margin: 0;">🔧 Route Optimization Complete</h1>
                </div>
                
                <div style="padding: 20px; background: #f8f9fa; border: 1px solid #dee2e6;">
                    <p><strong>Routes Updated:</strong> {result['routes_updated']}</p>
                    
                    <h4>New Distribution:</h4>
                    <ul>
                        <li>Tier 1: {result['new_distribution'].get(1, 0)} routes</li>
                        <li>Tier 2: {result['new_distribution'].get(2, 0)} routes</li>
                        <li>Tier 3: {result['new_distribution'].get(3, 0)} routes</li>
                    </ul>
                    
                    <h4>Top Updated Routes:</h4>
                    <ul>
                        {self._format_route_updates(result['updates'][:5])}
                    </ul>
                    
                    <p style="background: #e7f3ff; padding: 10px; border-radius: 4px;">
                        Routes have been reorganized based on recent performance to maximize deal discovery 
                        while staying within API quota limits.
                    </p>
                </div>
            </div>
            """
            
            email_service = EmailService()
            await email_service.send_admin_alert(
                subject="🔧 Route Optimization Complete",
                html_content=html_content,
                to_email=settings.monitoring_email
            )
            
        except Exception as e:
            logger.error(f"Error sending optimization report: {e}")
        finally:
            db.close()
    
    def _format_route_updates(self, updates: List[Dict]) -> str:
        """Format route updates for email"""
        html = ""
        for update in updates:
            html += f"""<li>{update['route']}: Tier {update['old_tier']} → Tier {update['new_tier']} (score: {update['score']:.1f})</li>"""
        return html
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        logger.info("Route scheduler stopped")

# Singleton instance
scheduler = RouteScheduler()