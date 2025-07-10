# backend/app/services/admin_service.py
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from app.models.user import User, UserTier
from app.models.flight import Route, Deal, PriceHistory
from app.models.alert import Alert
from app.services.flight_scanner import FlightScanner
from app.services.dynamic_route_manager import DynamicRouteManager
# from app.tasks.flight_tasks import scan_specific_route, scan_tier_routes
from app.utils.logger import logger
import json

# Mock task functions for development
class MockTask:
    def __init__(self, task_id: str):
        self.id = task_id

def scan_specific_route(route_id: int):
    return MockTask(f"mock-scan-{route_id}")

def scan_tier_routes(tier: int):
    return MockTask(f"mock-tier-{tier}")


class AdminService:
    """Service for admin dashboard operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.route_manager = DynamicRouteManager(db)
        self.scanner = FlightScanner(db)
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get comprehensive dashboard statistics"""
        
        # Time periods
        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # User statistics
        total_users = self.db.query(User).count()
        active_users = self.db.query(User).filter(User.is_active == True).count()
        new_users_today = self.db.query(User).filter(User.created_at >= today).count()
        new_users_week = self.db.query(User).filter(User.created_at >= week_ago).count()
        
        # User tier distribution
        tier_distribution = self.db.query(
            User.tier, func.count(User.id).label('count')
        ).group_by(User.tier).all()
        
        # Route statistics
        total_routes = self.db.query(Route).count()
        active_routes = self.db.query(Route).filter(Route.is_active == True).count()
        
        # Deal statistics
        total_deals = self.db.query(Deal).count()
        active_deals = self.db.query(Deal).filter(Deal.is_active == True).count()
        deals_today = self.db.query(Deal).filter(Deal.detected_at >= today).count()
        deals_week = self.db.query(Deal).filter(Deal.detected_at >= week_ago).count()
        
        # Alert statistics
        total_alerts = self.db.query(Alert).count()
        alerts_today = self.db.query(Alert).filter(Alert.created_at >= today).count()
        alerts_week = self.db.query(Alert).filter(Alert.created_at >= week_ago).count()
        
        # Price history count (API usage approximation)
        api_calls_today = self.db.query(PriceHistory).filter(
            PriceHistory.scanned_at >= today
        ).count()
        api_calls_week = self.db.query(PriceHistory).filter(
            PriceHistory.scanned_at >= week_ago
        ).count()
        
        return {
            'users': {
                'total': total_users,
                'active': active_users,
                'new_today': new_users_today,
                'new_week': new_users_week,
                'tier_distribution': {tier.tier.value: tier.count for tier in tier_distribution}
            },
            'routes': {
                'total': total_routes,
                'active': active_routes
            },
            'deals': {
                'total': total_deals,
                'active': active_deals,
                'today': deals_today,
                'week': deals_week
            },
            'alerts': {
                'total': total_alerts,
                'today': alerts_today,
                'week': alerts_week
            },
            'api_usage': {
                'calls_today': api_calls_today,
                'calls_week': api_calls_week,
                'daily_quota': 333,
                'monthly_quota': 10000
            }
        }
    
    def get_route_performance(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get route performance metrics"""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get routes with their deal counts and performance metrics
        route_performance = self.db.query(
            Route.id,
            Route.origin,
            Route.destination,
            Route.tier,
            Route.scan_interval_hours,
            Route.is_active,
            func.count(Deal.id).label('deal_count'),
            func.avg(Deal.discount_percentage).label('avg_discount'),
            func.max(Deal.discount_percentage).label('max_discount'),
            func.count(PriceHistory.id).label('scan_count')
        ).outerjoin(Deal, and_(
            Deal.route_id == Route.id,
            Deal.detected_at >= cutoff_date
        )).outerjoin(PriceHistory, and_(
            PriceHistory.route_id == Route.id,
            PriceHistory.scanned_at >= cutoff_date
        )).group_by(
            Route.id, Route.origin, Route.destination, 
            Route.tier, Route.scan_interval_hours, Route.is_active
        ).order_by(func.count(Deal.id).desc()).all()
        
        performance_data = []
        for route in route_performance:
            performance_data.append({
                'id': route.id,
                'route': f"{route.origin} → {route.destination}",
                'tier': route.tier,
                'scan_interval': route.scan_interval_hours,
                'is_active': route.is_active,
                'deals_found': route.deal_count or 0,
                'avg_discount': float(route.avg_discount) if route.avg_discount else 0,
                'max_discount': float(route.max_discount) if route.max_discount else 0,
                'scans_performed': route.scan_count or 0,
                'efficiency': (route.deal_count or 0) / max(route.scan_count or 1, 1)
            })
        
        return performance_data
    
    def get_seasonal_strategy_visualization(self) -> Dict[str, Any]:
        """Get seasonal strategy visualization data"""
        
        # Get current seasonal distribution
        distribution = self.route_manager.calculate_optimal_scan_distribution()
        
        # Get seasonal calendar
        seasonal_calendar = self.route_manager.get_seasonal_calendar()
        
        # Get active seasonal routes
        current_month = datetime.now().month
        active_seasonal_routes = []
        
        for period, config in self.route_manager.seasonal_periods.items():
            # Handle special case for year-round events
            if config['months'] == 'all' or current_month in config['months']:
                for origin, destination in config['routes']:
                    route = self.db.query(Route).filter(
                        Route.origin == origin,
                        Route.destination == destination,
                        Route.is_active == True
                    ).first()
                    
                    if route:
                        active_seasonal_routes.append({
                            'route': f"{origin} → {destination}",
                            'period': period,
                            'tier': route.tier,
                            'scan_frequency': f"Every {route.scan_interval_hours}h"
                        })
        
        return {
            'distribution': distribution,
            'seasonal_calendar': seasonal_calendar,
            'active_seasonal_routes': active_seasonal_routes,
            'current_month': datetime.now().strftime('%B'),
            'optimization_recommendations': distribution.get('recommendations', [])
        }
    
    def get_user_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get user analytics and growth metrics"""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Daily user registrations (SQLite compatible)
        daily_registrations = self.db.query(
            func.strftime('%Y-%m-%d', User.created_at).label('date'),
            func.count(User.id).label('count')
        ).filter(
            User.created_at >= cutoff_date
        ).group_by(
            func.strftime('%Y-%m-%d', User.created_at)
        ).order_by('date').all()
        
        # User engagement metrics (SQLite compatible)
        active_users_data = self.db.query(
            func.strftime('%Y-%m-%d', User.last_login_at).label('date'),
            func.count(User.id).label('active_count')
        ).filter(
            User.last_login_at >= cutoff_date
        ).group_by(
            func.strftime('%Y-%m-%d', User.last_login_at)
        ).order_by('date').all()
        
        # Alert engagement
        alert_engagement = self.db.query(
            User.tier,
            func.count(Alert.id).label('alert_count'),
            func.count(User.id).label('user_count')
        ).outerjoin(Alert).group_by(User.tier).all()
        
        return {
            'daily_registrations': [
                {'date': reg.date, 'count': reg.count}  # Already in ISO format from strftime
                for reg in daily_registrations
            ],
            'daily_active_users': [
                {'date': active.date, 'count': active.active_count}  # Already in ISO format from strftime
                for active in active_users_data
            ],
            'engagement_by_tier': [
                {
                    'tier': eng.tier.value,
                    'alerts_per_user': eng.alert_count / max(eng.user_count, 1),
                    'total_alerts': eng.alert_count,
                    'total_users': eng.user_count
                }
                for eng in alert_engagement
            ]
        }
    
    def trigger_route_scan(self, route_id: int) -> Dict[str, Any]:
        """Trigger manual scan for a specific route"""
        
        route = self.db.query(Route).filter(Route.id == route_id).first()
        if not route:
            return {'error': 'Route not found'}
        
        # Use direct FlightScanner instead of Celery for now
        try:
            scanner = FlightScanner(self.db)
            import asyncio
            
            # Create new event loop for async execution
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the scan
            deals = loop.run_until_complete(scanner.scan_route(route))
            
            return {
                'route': f"{route.origin} → {route.destination}",
                'deals_found': len(deals),
                'status': 'scan_completed',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error scanning route {route_id}: {e}")
            return {
                'error': f'Scan failed: {str(e)}',
                'route': f"{route.origin} → {route.destination}"
            }
    
    def trigger_tier_scan(self, tier: int) -> Dict[str, Any]:
        """Trigger manual scan for all routes in a tier"""
        
        routes = self.db.query(Route).filter(
            Route.tier == tier,
            Route.is_active == True
        ).all()
        
        if not routes:
            return {'error': f'No active routes found for tier {tier}'}
        
        # Use direct FlightScanner instead of Celery for now
        try:
            scanner = FlightScanner(self.db)
            import asyncio
            
            # Create new event loop for async execution
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the scan for all routes in tier
            result = loop.run_until_complete(scanner.scan_all_routes(tier=tier))
            
            return {
                'tier': tier,
                'routes_count': len(routes),
                'routes_scanned': result.get('routes_scanned', 0),
                'deals_found': result.get('deals_found', 0),
                'status': 'scan_completed',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error scanning tier {tier}: {e}")
            return {
                'error': f'Tier scan failed: {str(e)}',
                'tier': tier,
                'routes_count': len(routes)
            }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics"""
        
        # Check recent scan activity
        recent_scans = self.db.query(PriceHistory).filter(
            PriceHistory.scanned_at >= datetime.now() - timedelta(hours=1)
        ).count()
        
        # Check recent deals
        recent_deals = self.db.query(Deal).filter(
            Deal.detected_at >= datetime.now() - timedelta(hours=1)
        ).count()
        
        # Check recent alerts
        recent_alerts = self.db.query(Alert).filter(
            Alert.created_at >= datetime.now() - timedelta(hours=1)
        ).count()
        
        # Check system status
        system_status = 'healthy'
        if recent_scans == 0:
            system_status = 'warning'
        
        return {
            'status': system_status,
            'recent_scans': recent_scans,
            'recent_deals': recent_deals,
            'recent_alerts': recent_alerts,
            'last_update': datetime.now().isoformat()
        }
    
    def update_route_settings(self, route_id: int, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update route settings"""
        
        route = self.db.query(Route).filter(Route.id == route_id).first()
        if not route:
            return {'error': 'Route not found'}
        
        # Update allowed fields
        if 'tier' in settings:
            route.tier = settings['tier']
        if 'scan_interval_hours' in settings:
            route.scan_interval_hours = settings['scan_interval_hours']
        if 'is_active' in settings:
            route.is_active = settings['is_active']
        
        self.db.commit()
        
        return {
            'route_id': route_id,
            'route': f"{route.origin} → {route.destination}",
            'updated_settings': settings
        }
    
    def get_round_trip_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get round-trip specific metrics and analysis"""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Regional distribution with round-trip data
        regional_stats = self.db.query(
            Route.region,
            func.count(Route.id).label('route_count'),
            func.avg(Route.min_stay_nights).label('avg_min_stay'),
            func.avg(Route.max_stay_nights).label('avg_max_stay'),
            func.count(Deal.id).label('deals_found')
        ).outerjoin(Deal, and_(
            Deal.route_id == Route.id,
            Deal.detected_at >= cutoff_date
        )).group_by(Route.region).all()
        
        regional_distribution = {}
        for stat in regional_stats:
            regional_distribution[stat.region or 'unknown'] = {
                'count': stat.route_count,
                'avg_min_stay': float(stat.avg_min_stay or 0),
                'avg_max_stay': float(stat.avg_max_stay or 0),
                'deals_found': stat.deals_found or 0
            }
        
        # Round-trip compliance analysis
        valid_deals = self.db.query(Deal).filter(
            Deal.is_valid_round_trip == True,
            Deal.detected_at >= cutoff_date
        ).count()
        
        invalid_deals = self.db.query(Deal).filter(
            Deal.is_valid_round_trip == False,
            Deal.detected_at >= cutoff_date
        ).count()
        
        total_deals = valid_deals + invalid_deals
        compliance_rate = (valid_deals / total_deals * 100) if total_deals > 0 else 0
        
        # Stay duration analysis
        stay_durations = self.db.query(Deal.stay_duration_nights).filter(
            Deal.stay_duration_nights.isnot(None),
            Deal.detected_at >= cutoff_date
        ).all()
        
        if stay_durations:
            stay_nights = [s[0] for s in stay_durations if s[0]]
            avg_stay = sum(stay_nights) / len(stay_nights) if stay_nights else 0
            
            # Stay distribution
            short_stays = len([s for s in stay_nights if 3 <= s <= 7])
            medium_stays = len([s for s in stay_nights if 7 < s <= 14])
            long_stays = len([s for s in stay_nights if s > 14])
        else:
            avg_stay = 0
            short_stays = medium_stays = long_stays = 0
        
        # Advance booking analysis
        advance_bookings = self.db.query(Deal.advance_booking_days).filter(
            Deal.advance_booking_days.isnot(None),
            Deal.detected_at >= cutoff_date
        ).all()
        
        if advance_bookings:
            booking_days = [b[0] for b in advance_bookings if b[0]]
            avg_advance = sum(booking_days) / len(booking_days) if booking_days else 0
            
            # Booking distribution
            short_advance = len([b for b in booking_days if 30 <= b < 60])
            medium_advance = len([b for b in booking_days if 60 <= b <= 120])
            long_advance = len([b for b in booking_days if b > 120])
        else:
            avg_advance = 0
            short_advance = medium_advance = long_advance = 0
        
        # Weekday patterns
        weekday_departures = self.db.query(
            Deal.departure_day_of_week,
            func.count(Deal.id).label('count')
        ).filter(
            Deal.departure_day_of_week.isnot(None),
            Deal.detected_at >= cutoff_date
        ).group_by(Deal.departure_day_of_week).all()
        
        weekday_stats = {}
        for wd in weekday_departures:
            weekday_names = {1: 'monday', 2: 'tuesday', 3: 'wednesday', 
                           4: 'thursday', 5: 'friday', 6: 'saturday', 7: 'sunday'}
            day_name = weekday_names.get(wd[0], f'day_{wd[0]}')
            weekday_stats[f'{day_name}_departures'] = wd[1]
        
        # Route type distribution
        route_types = self.db.query(
            Route.route_type,
            func.count(Route.id).label('count')
        ).group_by(Route.route_type).all()
        
        route_type_stats = {rt[0] or 'unknown': rt[1] for rt in route_types}
        
        return {
            'total_routes': self.db.query(Route).count(),
            'round_trip_routes': route_type_stats.get('round_trip', 0),
            'regional_distribution': regional_distribution,
            'round_trip_compliance': {
                'valid_deals': valid_deals,
                'invalid_deals': invalid_deals,
                'total_deals': total_deals,
                'compliance_rate': round(compliance_rate, 2)
            },
            'stay_duration_analysis': {
                'avg_stay_nights': round(avg_stay, 1),
                'stay_distribution': {
                    '3-7 nights (Europe proche)': short_stays,
                    '7-14 nights (Europe populaire)': medium_stays,
                    '15+ nights (Long courrier)': long_stays
                }
            },
            'advance_booking_trends': {
                'avg_advance_days': round(avg_advance, 1),
                'booking_distribution': {
                    '30-60 days': short_advance,
                    '60-120 days': medium_advance,
                    '120+ days': long_advance
                }
            },
            'weekday_patterns': weekday_stats,
            'route_type_distribution': route_type_stats
        }
