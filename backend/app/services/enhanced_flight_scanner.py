# backend/app/services/enhanced_flight_scanner.py
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.flight import Route, PriceHistory, Deal
from app.models.alert import Alert
from app.models.admin_settings import AdminSettings
from app.models.api_tracking import ApiCall, ApiQuotaUsage
from app.services.enhanced_route_manager import EnhancedRouteManager
from app.services.email_service import EmailService
from app.utils.logger import logger
import aiohttp
import asyncio
import json
import os
from decimal import Decimal

class EnhancedFlightScanner:
    """Enhanced flight scanner with business rules enforcement and monitoring"""
    
    def __init__(self, db: Session):
        self.db = db
        self.api_key = os.getenv("FLIGHT_API_KEY")
        self.api_base_url = "https://api.example.com/flights"  # Replace with actual API
        self.route_manager = EnhancedRouteManager(db)
        self.email_service = EmailService()
        self.scan_results = {
            "total_scans": 0,
            "successful_scans": 0,
            "failed_scans": 0,
            "deals_found": 0,
            "invalid_deals_filtered": 0
        }
    
    async def scan_route(self, route: Route) -> List[Deal]:
        """Scan a single route for deals with business rules validation"""
        
        deals = []
        start_time = datetime.now()
        
        try:
            # Generate search dates based on business rules
            search_dates = self._generate_search_dates(route)
            
            async with aiohttp.ClientSession() as session:
                for date_pair in search_dates:
                    departure_date, return_date = date_pair
                    
                    # Validate dates against business rules
                    is_valid, reason = self.route_manager.validate_deal_parameters(
                        route.origin, 
                        route.destination,
                        departure_date,
                        return_date
                    )
                    
                    if not is_valid:
                        logger.info(f"Skipping invalid date combination: {reason}")
                        self.scan_results["invalid_deals_filtered"] += 1
                        continue
                    
                    # Perform API call
                    try:
                        prices = await self._fetch_prices(
                            session,
                            route.origin,
                            route.destination,
                            departure_date,
                            return_date
                        )
                        
                        if prices:
                            # Process and validate deals
                            route_deals = await self._process_prices(
                                route,
                                prices,
                                departure_date,
                                return_date
                            )
                            deals.extend(route_deals)
                        
                    except Exception as e:
                        logger.error(f"Error fetching prices for {route.origin}->{route.destination}: {e}")
                        self.scan_results["failed_scans"] += 1
            
            # Record scan in price history
            response_time = (datetime.now() - start_time).total_seconds()
            self._record_scan(route, len(deals), response_time, "success")
            
            self.scan_results["successful_scans"] += 1
            self.scan_results["deals_found"] += len(deals)
            
            # Send monitoring alert if deals found
            if deals and self._should_send_monitoring_alert():
                await self._send_monitoring_alert(route, deals)
            
        except Exception as e:
            logger.error(f"Error scanning route {route.id}: {e}")
            self._record_scan(route, 0, 0, "error")
            self.scan_results["failed_scans"] += 1
        
        finally:
            self.scan_results["total_scans"] += 1
        
        return deals
    
    def _generate_search_dates(self, route: Route) -> List[tuple]:
        """Generate search dates based on business rules"""
        
        search_dates = []
        today = datetime.now().date()
        
        # Determine destination category
        dest_category = None
        for category, data in self.route_manager.destination_categories.items():
            if route.destination in data["airports"]:
                dest_category = category
                break
        
        if not dest_category:
            logger.warning(f"Unknown destination category for {route.destination}")
            return []
        
        category_rules = self.route_manager.destination_categories[dest_category]
        min_advance, max_advance = category_rules["advance_booking"]
        min_stay = category_rules["min_stay"]
        max_stay = category_rules["max_stay"]
        
        # Generate departure dates (respecting advance booking rules)
        departure_dates = []
        for days_ahead in range(min_advance, min(max_advance, 270), 7):  # Weekly intervals
            departure_dates.append(today + timedelta(days=days_ahead))
        
        # For each departure date, generate valid return dates
        for dep_date in departure_dates[:10]:  # Limit to 10 departure dates
            # For domestic French routes with short stays
            if dest_category == "domestic_french" and min_stay <= 5:
                dep_weekday = dep_date.strftime("%A").lower()
                
                # Check if short stay is allowed from this day
                if dep_weekday in category_rules.get("short_stay_days", []):
                    # Generate short stay options (3-5 days)
                    for stay_length in range(3, 6):
                        ret_date = dep_date + timedelta(days=stay_length)
                        search_dates.append((dep_date, ret_date))
                else:
                    # Standard stays only
                    for stay_length in range(min_stay, min(max_stay + 1, 15), 7):
                        ret_date = dep_date + timedelta(days=stay_length)
                        search_dates.append((dep_date, ret_date))
            else:
                # Standard stay durations for other categories
                stay_options = []
                if dest_category in ["european", "north_american", "middle_eastern"]:
                    stay_options = [7, 10, 14]  # Week, 10 days, 2 weeks
                elif dest_category in ["asian", "oceanian", "african"]:
                    stay_options = [14, 21, 28]  # 2, 3, 4 weeks
                
                for stay_length in stay_options:
                    if min_stay <= stay_length <= max_stay:
                        ret_date = dep_date + timedelta(days=stay_length)
                        search_dates.append((dep_date, ret_date))
        
        return search_dates[:20]  # Limit total searches per route
    
    async def _fetch_prices(self, session: aiohttp.ClientSession, 
                          origin: str, destination: str,
                          departure_date: datetime, return_date: datetime) -> List[Dict]:
        """Fetch prices from flight API"""
        
        # This is a placeholder - implement actual API call
        # For now, return mock data
        mock_price = 200 + (hash(f"{origin}{destination}{departure_date}") % 800)
        
        return [{
            "price": mock_price,
            "currency": "EUR",
            "airline": "Mock Airlines",
            "flight_number": "MK123",
            "booking_class": "Economy",
            "departure_time": departure_date.isoformat(),
            "return_time": return_date.isoformat()
        }]
    
    async def _process_prices(self, route: Route, prices: List[Dict],
                            departure_date: datetime, return_date: datetime) -> List[Deal]:
        """Process prices and create deals if they meet criteria"""
        
        deals = []
        
        for price_data in prices:
            # Calculate if this is a deal
            historical_avg = await self._get_historical_average(route, departure_date, return_date)
            
            if not historical_avg:
                historical_avg = price_data["price"] * 1.2  # Assume 20% higher as baseline
            
            current_price = Decimal(str(price_data["price"]))
            discount_percentage = ((historical_avg - current_price) / historical_avg) * 100
            
            # Only create deal if discount is significant (>15%)
            if discount_percentage > 15:
                # Create price history record
                price_history = PriceHistory(
                    route_id=route.id,
                    price=current_price,
                    currency=price_data.get("currency", "EUR"),
                    departure_date=departure_date,
                    return_date=return_date,
                    airline=price_data.get("airline"),
                    flight_number=price_data.get("flight_number"),
                    booking_class=price_data.get("booking_class", "Economy"),
                    scanned_at=datetime.now(),
                    response_time=0.5,  # Mock response time
                    status="success"
                )
                self.db.add(price_history)
                self.db.flush()
                
                # Create deal
                deal = Deal(
                    route_id=route.id,
                    price_history_id=price_history.id,
                    deal_price=current_price,
                    normal_price=historical_avg,
                    discount_percentage=discount_percentage,
                    detected_at=datetime.now(),
                    expires_at=departure_date - timedelta(days=7),  # Expires 1 week before departure
                    is_active=True,
                    confidence_score=0.8,
                    anomaly_score=discount_percentage / 100
                )
                
                self.db.add(deal)
                deals.append(deal)
        
        if deals:
            self.db.commit()
        
        return deals
    
    async def _get_historical_average(self, route: Route, 
                                    departure_date: datetime, 
                                    return_date: datetime) -> Optional[Decimal]:
        """Get historical average price for similar dates"""
        
        # Look for similar trips in the past 90 days
        similar_prices = self.db.query(PriceHistory.price).filter(
            PriceHistory.route_id == route.id,
            PriceHistory.departure_date.between(
                departure_date - timedelta(days=45),
                departure_date + timedelta(days=45)
            ),
            PriceHistory.scanned_at >= datetime.now() - timedelta(days=90)
        ).all()
        
        if similar_prices:
            avg_price = sum(p.price for p in similar_prices) / len(similar_prices)
            return avg_price
        
        return None
    
    def _record_scan(self, route: Route, deals_found: int, 
                    response_time: float, status: str):
        """Record scan in database for monitoring"""
        
        # Update route last scan time
        route.last_scanned_at = datetime.now()
        
        # You might want to create a scan log table for detailed tracking
        logger.info(f"Scan completed for {route.origin}->{route.destination}: "
                   f"{deals_found} deals found, {response_time:.2f}s, status: {status}")
    
    def _should_send_monitoring_alert(self) -> bool:
        """Check if monitoring alerts are enabled"""
        
        settings = self.db.query(AdminSettings).first()
        return settings and settings.alert_notifications and settings.monitoring_email
    
    async def _send_monitoring_alert(self, route: Route, deals: List[Deal]):
        """Send monitoring alert for new deals"""
        
        settings = self.db.query(AdminSettings).first()
        if not settings or not settings.monitoring_email:
            return
        
        # Prepare email content
        deals_html = ""
        for deal in deals[:5]:  # Show top 5 deals
            deals_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                    {route.origin} → {route.destination}
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                    €{deal.deal_price}
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                    -{deal.discount_percentage:.0f}%
                </td>
            </tr>
            """
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto;">
            <div style="background: #28a745; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0;">🎯 New Flight Deals Detected!</h1>
            </div>
            
            <div style="padding: 20px; background: #f8f9fa; border: 1px solid #dee2e6;">
                <p>Scanner has found {len(deals)} new deals on route {route.origin} → {route.destination}</p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <thead>
                        <tr style="background: #e9ecef;">
                            <th style="padding: 10px; text-align: left;">Route</th>
                            <th style="padding: 10px; text-align: left;">Price</th>
                            <th style="padding: 10px; text-align: left;">Discount</th>
                        </tr>
                    </thead>
                    <tbody>
                        {deals_html}
                    </tbody>
                </table>
                
                <p style="text-align: center; margin-top: 20px;">
                    <a href="http://localhost:3001/admin" 
                       style="background: #007bff; color: white; padding: 10px 20px; 
                              text-decoration: none; border-radius: 4px;">
                        View All Deals in Admin
                    </a>
                </p>
            </div>
            
            <div style="text-align: center; color: #6c757d; font-size: 12px; margin-top: 20px;">
                <p>GlobeGenius Monitoring System</p>
                <p>Scan Results Summary: {self.scan_results['successful_scans']} successful, 
                   {self.scan_results['failed_scans']} failed, 
                   {self.scan_results['deals_found']} total deals found</p>
            </div>
        </div>
        """
        
        try:
            await self.email_service.send_admin_alert(
                subject=f"🎯 {len(deals)} New Deals: {route.origin}→{route.destination}",
                html_content=html_content,
                to_email=settings.monitoring_email
            )
            logger.info(f"Monitoring alert sent to {settings.monitoring_email}")
        except Exception as e:
            logger.error(f"Failed to send monitoring alert: {e}")
    
    async def scan_all_routes(self, tier: Optional[int] = None) -> Dict[str, Any]:
        """Scan all routes or specific tier with monitoring"""
        
        # Reset scan results
        self.scan_results = {
            "total_scans": 0,
            "successful_scans": 0,
            "failed_scans": 0,
            "deals_found": 0,
            "invalid_deals_filtered": 0
        }
        
        query = self.db.query(Route).filter(Route.is_active == True)
        if tier:
            query = query.filter(Route.tier == tier)
        
        routes = query.all()
        all_deals = []
        
        logger.info(f"Starting scan for {len(routes)} routes (tier: {tier or 'all'})")
        
        # Process routes in batches to avoid overwhelming the API
        batch_size = 5
        for i in range(0, len(routes), batch_size):
            batch = routes[i:i + batch_size]
            
            # Create tasks for concurrent scanning
            tasks = [self.scan_route(route) for route in batch]
            batch_results = await asyncio.gather(*tasks)
            
            for deals in batch_results:
                all_deals.extend(deals)
            
            # Small delay between batches
            await asyncio.sleep(1)
        
        # Send summary monitoring email
        await self._send_scan_summary()
        
        return {
            "routes_scanned": len(routes),
            "deals_found": len(all_deals),
            "scan_results": self.scan_results,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _send_scan_summary(self):
        """Send scan summary to monitoring email"""
        
        settings = self.db.query(AdminSettings).first()
        if not settings or not settings.monitoring_email or not settings.daily_reports:
            return
        
        # Only send if there were significant results
        if self.scan_results["total_scans"] == 0:
            return
        
        success_rate = (self.scan_results["successful_scans"] / self.scan_results["total_scans"]) * 100
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto;">
            <div style="background: #17a2b8; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0;">📊 Flight Scanner Summary Report</h1>
            </div>
            
            <div style="padding: 20px; background: #f8f9fa; border: 1px solid #dee2e6;">
                <h3>Scan Statistics</h3>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0;">
                    <div style="background: white; padding: 15px; border-radius: 4px;">
                        <div style="font-size: 24px; font-weight: bold; color: #28a745;">
                            {self.scan_results['successful_scans']}
                        </div>
                        <div style="color: #6c757d;">Successful Scans</div>
                    </div>
                    
                    <div style="background: white; padding: 15px; border-radius: 4px;">
                        <div style="font-size: 24px; font-weight: bold; color: #dc3545;">
                            {self.scan_results['failed_scans']}
                        </div>
                        <div style="color: #6c757d;">Failed Scans</div>
                    </div>
                    
                    <div style="background: white; padding: 15px; border-radius: 4px;">
                        <div style="font-size: 24px; font-weight: bold; color: #ffc107;">
                            {self.scan_results['deals_found']}
                        </div>
                        <div style="color: #6c757d;">Deals Found</div>
                    </div>
                    
                    <div style="background: white; padding: 15px; border-radius: 4px;">
                        <div style="font-size: 24px; font-weight: bold; color: #17a2b8;">
                            {success_rate:.1f}%
                        </div>
                        <div style="color: #6c757d;">Success Rate</div>
                    </div>
                </div>
                
                <p style="margin-top: 20px;">
                    <strong>Invalid Deals Filtered:</strong> {self.scan_results['invalid_deals_filtered']}<br>
                    <small style="color: #6c757d;">
                        (Deals that didn't meet business rules for advance booking or stay duration)
                    </small>
                </p>
                
                <p style="text-align: center; margin-top: 30px;">
                    <a href="http://localhost:3001/admin" 
                       style="background: #007bff; color: white; padding: 10px 20px; 
                              text-decoration: none; border-radius: 4px;">
                        View Detailed Report
                    </a>
                </p>
            </div>
            
            <div style="text-align: center; color: #6c757d; font-size: 12px; margin-top: 20px;">
                <p>GlobeGenius Flight Scanner</p>
                <p>Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </div>
        """
        
        try:
            await self.email_service.send_admin_alert(
                subject=f"📊 Scanner Report: {self.scan_results['deals_found']} deals found",
                html_content=html_content,
                to_email=settings.monitoring_email
            )
            logger.info("Scan summary sent to monitoring email")
        except Exception as e:
            logger.error(f"Failed to send scan summary: {e}")