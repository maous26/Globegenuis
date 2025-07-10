#!/usr/bin/env python3
"""
Console-specific flight scanner with optimized API usage
Designed to work within API rate limits for manual console scanning
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.flight import Route, Deal
from app.services.travelpayouts_api import TravelPayoutsAPI
from app.services.aviation_api import AviationStackAPI
from app.utils.logger import logger


class ConsoleFlightScanner:
    """Optimized scanner for console/manual use with minimal API calls"""
    
    def __init__(self, db: Session):
        self.db = db
        self.travelpayouts_api = TravelPayoutsAPI()
        self.aviation_api = AviationStackAPI()
        self.use_travelpayouts_fallback = True
        
    async def scan_route_lightweight(self, route: Route) -> Dict[str, Any]:
        """Lightweight scan focusing on one strategic date combination"""
        logger.info(f"🔍 Console scanning: {route.origin} → {route.destination}")
        
        try:
            # Strategic single date approach - 45 days ahead, 7-day stay
            departure_date = datetime.now() + timedelta(days=45)
            
            # Try TravelPayouts first (more generous rate limits)
            if self.use_travelpayouts_fallback:
                price_data = await self._scan_with_travelpayouts(route, departure_date)
                if price_data:
                    return {
                        'route': f"{route.origin} → {route.destination}",
                        'api_used': 'TravelPayouts',
                        'prices_found': len(price_data),
                        'sample_price': price_data[0] if price_data else None,
                        'status': 'success'
                    }
            
            # Fallback to AviationStack if needed
            flight_data = await self._scan_with_aviation(route, departure_date)
            
            return {
                'route': f"{route.origin} → {route.destination}",
                'api_used': 'AviationStack',
                'flights_found': len(flight_data),
                'sample_flight': flight_data[0] if flight_data else None,
                'status': 'success' if flight_data else 'no_data'
            }
            
        except Exception as e:
            logger.error(f"Console scan error for {route.origin}-{route.destination}: {e}")
            return {
                'route': f"{route.origin} → {route.destination}",
                'status': 'error',
                'error': str(e)
            }
    
    async def _scan_with_travelpayouts(self, route: Route, departure_date: datetime) -> List[Dict]:
        """Scan using TravelPayouts API"""
        try:
            prices = await self.travelpayouts_api.get_cheap_flights(
                origin=route.origin,
                destination=route.destination,
                departure_date=departure_date
            )
            return prices[:3]  # Return top 3 results
        except Exception as e:
            logger.error(f"TravelPayouts error: {e}")
            return []
    
    async def _scan_with_aviation(self, route: Route, departure_date: datetime) -> List[Dict]:
        """Scan using AviationStack API with minimal calls"""
        try:
            flights = await self.aviation_api.search_flights(
                origin=route.origin,
                destination=route.destination,
                departure_date=departure_date,
                limit=5  # Minimal limit to conserve API calls
            )
            return flights[:3]  # Return top 3 results
        except Exception as e:
            logger.error(f"AviationStack error: {e}")
            return []
    
    async def console_scan_tier(self, tier: int) -> Dict[str, Any]:
        """Console-optimized tier scanning"""
        routes = self.db.query(Route).filter(
            Route.tier == tier,
            Route.is_active == True
        ).limit(5).all()  # Limit to 5 routes for console testing
        
        if not routes:
            return {'error': f'No active routes found for tier {tier}'}
        
        logger.info(f"📡 Console scanning {len(routes)} routes for Tier {tier}")
        
        results = []
        for i, route in enumerate(routes):
            logger.info(f"Progress: {i+1}/{len(routes)}")
            
            result = await self.scan_route_lightweight(route)
            results.append(result)
            
            # Conservative delay for console usage
            if i < len(routes) - 1:
                await asyncio.sleep(2)
        
        successful_scans = [r for r in results if r['status'] == 'success']
        
        return {
            'tier': tier,
            'routes_tested': len(routes),
            'successful_scans': len(successful_scans),
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
    
    async def quick_connectivity_test(self) -> Dict[str, Any]:
        """Quick test to verify API connectivity"""
        test_results = {}
        
        # Test TravelPayouts
        try:
            test_prices = await self.travelpayouts_api.get_cheap_flights(
                origin="CDG",
                destination="JFK", 
                departure_date=datetime.now() + timedelta(days=30)
            )
            test_results['travelpayouts'] = {
                'status': 'connected',
                'data_found': len(test_prices) > 0
            }
        except Exception as e:
            test_results['travelpayouts'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Test AviationStack
        try:
            test_flights = await self.aviation_api.search_flights(
                origin="CDG",
                destination="JFK",
                departure_date=datetime.now() + timedelta(days=30),
                limit=1
            )
            test_results['aviationstack'] = {
                'status': 'connected',
                'data_found': len(test_flights) > 0
            }
        except Exception as e:
            test_results['aviationstack'] = {
                'status': 'error',
                'error': str(e)
            }
        
        return test_results
