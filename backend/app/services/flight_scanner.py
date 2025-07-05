import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.flight import Route, PriceHistory, Deal
from app.services.aviation_api import AviationStackAPI
from app.services.anomaly_detector import AnomalyDetector
from app.utils.logger import logger
from app.core.config import settings


class FlightScanner:
    def __init__(self, db: Session):
        self.db = db
        self.aviation_api = AviationStackAPI()
        self.anomaly_detector = AnomalyDetector()
        
    async def scan_route(self, route: Route) -> List[Deal]:
        """Scan a single route for deals"""
        logger.info(f"Scanning route: {route.origin} -> {route.destination}")
        
        deals_found = []
        
        # Scan multiple date ranges
        for days_ahead in [7, 14, 21, 30, 45, 60, 90, 120]:
            departure_date = datetime.now() + timedelta(days=days_ahead)
            
            # Search flights
            flights = await self.aviation_api.search_flights(
                origin=route.origin,
                destination=route.destination,
                departure_date=departure_date
            )
            
            if not flights:
                continue
                
            # Simulate price data (temporary until we integrate a price API)
            # In production, you'll need FlightLabs or similar for real prices
            for flight in flights:
                price = self._simulate_price(route, departure_date)
                
                # Store price history
                price_history = PriceHistory(
                    route_id=route.id,
                    airline=flight.get("airline"),
                    price=price,
                    departure_date=departure_date,
                    flight_number=flight.get("flight_number"),
                    raw_data=flight
                )
                self.db.add(price_history)
                self.db.flush()
                
                # Check for anomalies
                is_anomaly, score, normal_price = await self._check_anomaly(
                    route, price
                )
                
                if is_anomaly:
                    discount_pct = ((normal_price - price) / normal_price) * 100
                    
                    if discount_pct >= settings.MIN_PRICE_DROP_PERCENTAGE:
                        deal = Deal(
                            route_id=route.id,
                            price_history_id=price_history.id,
                            normal_price=normal_price,
                            deal_price=price,
                            discount_percentage=discount_pct,
                            anomaly_score=score,
                            is_error_fare=discount_pct > 70,
                            confidence_score=min(score * 100, 99),
                            expires_at=datetime.now() + timedelta(hours=24)
                        )
                        self.db.add(deal)
                        deals_found.append(deal)
                        
                        logger.info(
                            f"Deal found! {route.origin}->{route.destination} "
                            f"€{price} (normal: €{normal_price}) "
                            f"-{discount_pct:.0f}%"
                        )
        
        self.db.commit()
        return deals_found
    
    async def scan_all_routes(self, tier: Optional[int] = None) -> Dict[str, Any]:
        """Scan all active routes or specific tier"""
        query = self.db.query(Route).filter(Route.is_active == True)
        
        if tier:
            query = query.filter(Route.tier == tier)
            
        routes = query.all()
        
        logger.info(f"Scanning {len(routes)} routes")
        
        total_deals = []
        for route in routes:
            deals = await self.scan_route(route)
            total_deals.extend(deals)
            
            # Small delay to avoid API rate limits
            await asyncio.sleep(1)
        
        return {
            "routes_scanned": len(routes),
            "deals_found": len(total_deals),
            "timestamp": datetime.now()
        }
    
    async def _check_anomaly(
        self, 
        route: Route, 
        current_price: float
    ) -> tuple[bool, float, float]:
        """Check if price is anomalous"""
        # Get historical prices
        historical_prices = self.db.query(PriceHistory.price).filter(
            PriceHistory.route_id == route.id,
            PriceHistory.scanned_at >= datetime.now() - timedelta(days=30)
        ).all()
        
        if len(historical_prices) < 10:
            # Not enough data, use simple threshold
            avg_price = 150 if route.destination in ["MAD", "BCN", "ROM"] else 250
            is_anomaly = current_price < (avg_price * 0.7)
            return is_anomaly, 0.5 if is_anomaly else 0.1, avg_price
        
        # Use ML anomaly detection
        prices = [p[0] for p in historical_prices]
        is_anomaly, score = self.anomaly_detector.detect_anomaly(
            prices, current_price
        )
        
        normal_price = sum(prices) / len(prices)
        
        return is_anomaly, score, normal_price
    
    def _simulate_price(self, route: Route, date: datetime) -> float:
        """Temporary price simulation - replace with real API"""
        import random
        
        base_prices = {
            # Domestic
            ("CDG", "NCE"): 80,
            ("CDG", "TLS"): 70,
            ("CDG", "MRS"): 75,
            # Europe
            ("CDG", "MAD"): 120,
            ("CDG", "BCN"): 110,
            ("CDG", "LHR"): 150,
            ("CDG", "ROM"): 130,
            # International
            ("CDG", "JFK"): 450,
            ("CDG", "LAX"): 550,
        }
        
        key = (route.origin, route.destination)
        base = base_prices.get(key, 200)
        
        # Add variations
        day_factor = 1 + (date.weekday() / 10)  # Weekends more expensive
        advance_factor = 1 - (min((date - datetime.now()).days, 60) / 200)
        random_factor = random.uniform(0.8, 1.2)
        
        # Occasionally create a deal
        if random.random() < 0.1:  # 10% chance
            random_factor = random.uniform(0.3, 0.6)  # Big discount
        
        return round(base * day_factor * advance_factor * random_factor, 2)