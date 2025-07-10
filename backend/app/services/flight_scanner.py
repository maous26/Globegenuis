import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.flight import Route, PriceHistory, Deal
from app.services.flightlabs_api import FlightLabsAPI
from app.services.anomaly_detector import AnomalyDetector
from app.services.round_trip_validator import RoundTripDealValidator
from app.services.dual_api_validator import DualAPIValidator
from app.utils.logger import logger
from app.core.config import settings


class FlightScanner:
    def __init__(self, db: Session):
        self.db = db
        self.flightlabs_api = FlightLabsAPI()
        self.anomaly_detector = AnomalyDetector()
        self.round_trip_validator = RoundTripDealValidator(db)
        self.dual_validator = DualAPIValidator(db)  # Dual API validation with TravelPayouts
        
    async def scan_route(self, route: Route) -> List[Deal]:
        """Scan a single route for round-trip deals (enhanced for intelligent routing)"""
        logger.info(f"Scanning intelligent round-trip route: {route.origin} -> {route.destination}")
        
        # Work with both new round-trip routes and existing intelligent routes
        if hasattr(route, 'route_type') and route.route_type != "round_trip":
            logger.warning(f"Skipping non-round-trip route: {route.origin}-{route.destination}")
            return []
        
        deals_found = []
        
        # Use intelligent constraints if available, otherwise use defaults
        min_advance = getattr(route, 'min_advance_booking_days', 30)
        max_advance = getattr(route, 'max_advance_booking_days', 270)
        min_stay = getattr(route, 'min_stay_nights', 3)
        max_stay = getattr(route, 'max_stay_nights', 14)
        
        # STRATEGIC SCANNING: Reduce API calls by scanning fewer date combinations
        # Focus on popular travel periods and optimal booking windows
        strategic_days_ahead = [30, 45, 60, 90, 120]  # Strategic booking windows
        
        for days_ahead in strategic_days_ahead:
            if days_ahead < min_advance or days_ahead > max_advance:
                continue
                
            departure_date = datetime.now() + timedelta(days=days_ahead)
            
            # Focus on 2-3 strategic stay durations instead of 5
            strategic_stays = [min_stay, (min_stay + max_stay) // 2, max_stay]
            
            for stay_nights in strategic_stays:
                if stay_nights < min_stay or stay_nights > max_stay:
                    continue
                    
                return_date = departure_date + timedelta(days=stay_nights)
                
                # Check if weekday pattern is valid for short stays
                if not self._is_valid_weekday_pattern(departure_date, return_date, stay_nights, route):
                    continue
                
                # Search round-trip flights using FlightLabs
                try:
                    # Use FlightLabs for round-trip search with our database session
                    flights = await self.flightlabs_api.search_flights(
                        origin=route.origin,
                        destination=route.destination,
                        departure_date=departure_date,
                        return_date=return_date,
                        db=self.db  # Pass the scanner's database session
                    )
                    
                    if not flights:
                        continue
                    
                    # Process each flight found
                    for flight in flights[:3]:  # Limit to top 3 results per date combination
                        deal = await self._process_flight_deal(
                            route, flight, departure_date, return_date, stay_nights
                        )
                        if deal:
                            deals_found.append(deal)
                            
                    # Small delay to respect rate limits
                    await asyncio.sleep(1)
                                
                except Exception as e:
                    logger.error(f"Error scanning {route.origin}-{route.destination}: {e}")
                    continue
        
        self.db.commit()
        logger.info(f"Found {len(deals_found)} valid round-trip deals for {route.origin}-{route.destination}")
        return deals_found
    
    async def scan_all_routes(self, tier: Optional[int] = None) -> Dict[str, Any]:
        """Scan all active routes or specific tier"""
        query = self.db.query(Route).filter(Route.is_active == True)
        
        if tier:
            query = query.filter(Route.tier == tier)
            
        routes = query.all()
        
        logger.info(f"Scanning {len(routes)} routes (strategic mode)")
        
        total_deals = []
        for i, route in enumerate(routes):
            logger.info(f"Scanning route {i+1}/{len(routes)}: {route.origin} -> {route.destination}")
            
            deals = await self.scan_route(route)
            total_deals.extend(deals)
            
            # Strategic delay between routes to respect API limits
            if i < len(routes) - 1:  # Don't delay after the last route
                await asyncio.sleep(3)  # 3 seconds between routes
        
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
    
    def _is_valid_weekday_pattern(self, departure_date: datetime, return_date: datetime, 
                                 stay_nights: int, route: Route) -> bool:
        """Check if weekday pattern is valid for short stays (compatible with intelligent routes)"""
        departure_weekday = departure_date.weekday() + 1  # 1=Monday, 7=Sunday
        return_weekday = return_date.weekday() + 1
        
        # For short stays (3-5 nights), check specific patterns
        if stay_nights == 3:
            # Monday to Wednesday
            allowed = getattr(route, 'allow_mon_wed', True)
            return (departure_weekday == 1 and return_weekday == 4 and allowed)
        elif stay_nights == 4:
            # Tuesday to Friday
            allowed = getattr(route, 'allow_tue_fri', True)
            return (departure_weekday == 2 and return_weekday == 6 and allowed)
        elif stay_nights == 5:
            # Wednesday to Sunday
            allowed = getattr(route, 'allow_wed_sun', True)
            return (departure_weekday == 3 and return_weekday == 7 and allowed)
        
        # For longer stays, any weekday pattern is acceptable
        return True
    
    async def _process_round_trip_combination(self, route: Route, outbound: Dict, return_flight: Dict,
                                            departure_date: datetime, return_date: datetime, 
                                            stay_nights: int) -> Optional[Deal]:
        """Process a round-trip flight combination and create deal if valid"""
        try:
            # Calculate combined price
            outbound_price = self._simulate_price(route, departure_date)
            return_price = self._simulate_price(route, return_date, is_return=True)
            total_price = outbound_price + return_price
            
            # Store combined price history
            price_history = PriceHistory(
                route_id=route.id,
                airline=f"{outbound.get('airline', 'XX')}/{return_flight.get('airline', 'XX')}",
                price=total_price,
                departure_date=departure_date,
                return_date=return_date,
                flight_number=f"{outbound.get('flight_number', '')}/{return_flight.get('flight_number', '')}",
                raw_data={
                    "outbound": outbound,
                    "return": return_flight,
                    "stay_nights": stay_nights,
                    "round_trip": True
                }
            )
            self.db.add(price_history)
            self.db.flush()
            
            # Check for anomalies in round-trip pricing
            is_anomaly, score, normal_price = await self._check_round_trip_anomaly(
                route, total_price, stay_nights
            )
            
            if is_anomaly:
                discount_pct = ((normal_price - total_price) / normal_price) * 100
                
                # Only create deals with significant savings
                if discount_pct >= settings.MIN_PRICE_DROP_PERCENTAGE:
                    deal = Deal(
                        route_id=route.id,
                        price_history_id=price_history.id,
                        normal_price=normal_price,
                        deal_price=total_price,
                        discount_percentage=discount_pct,
                        anomaly_score=score,
                        is_error_fare=discount_pct > 70,
                        confidence_score=min(score * 100, 99),
                        expires_at=datetime.now() + timedelta(hours=48),  # Longer expiry for round-trips
                        stay_duration_nights=stay_nights
                    )
                    self.db.add(deal)
                    self.db.flush()
                    
                    # 1. Validate the deal using round-trip validator
                    validation_result = self.round_trip_validator.validate_deal(deal, price_history, route)
                    
                    if validation_result["is_valid"]:
                        # 2. NEW: Cross-validate with dual API system (TravelPayouts + AviationStack)
                        dual_validation = await self.dual_validator.validate_deal_comprehensive(
                            route=route,
                            deal_price=total_price,
                            normal_price=normal_price,
                            departure_date=departure_date,
                            return_date=return_date
                        )
                        
                        # Update confidence score based on dual validation
                        if dual_validation["is_valid"]:
                            # Use dual API confidence score
                            deal.confidence_score = dual_validation["confidence_score"] * 100
                            
                            logger.info(
                                f"✅ VALIDATED DEAL! {route.origin}↔{route.destination} "
                                f"€{total_price} (normal: €{normal_price}) "
                                f"-{discount_pct:.0f}% | {stay_nights} nights | "
                                f"Confidence: {dual_validation['confidence_score']:.2f} | "
                                f"TravelPayouts: {dual_validation['travelpayouts_validation'].get('validated', False)}"
                            )
                            return deal
                        else:
                            logger.warning(
                                f"❌ Deal failed dual API validation: {route.origin}↔{route.destination} "
                                f"€{total_price} | Reason: {dual_validation['recommendation']} | "
                                f"Confidence: {dual_validation['confidence_score']:.2f}"
                            )
                            # Remove deal that failed cross-validation
                            self.db.delete(deal)
                    else:
                        logger.debug(f"Deal validation failed round-trip rules: {validation_result['validation_errors']}")
                        # Remove invalid deal
                        self.db.delete(deal)
                        
        except Exception as e:
            logger.error(f"Error processing round-trip combination: {e}")
            
        return None
    
    async def _check_round_trip_anomaly(self, route: Route, price: float, stay_nights: int) -> tuple:
        """Check for price anomalies in round-trip combinations"""
        # Enhanced anomaly detection for round-trips
        # This should be based on historical round-trip pricing data
        
        # Base normal price calculation (simplified)
        base_price = self._calculate_base_round_trip_price(route, stay_nights)
        
        # Apply seasonal and stay duration adjustments
        adjusted_normal_price = base_price * self._get_stay_duration_multiplier(stay_nights)
        
        # Calculate anomaly score
        price_ratio = price / adjusted_normal_price
        
        # Lower prices indicate better deals
        if price_ratio < 0.7:  # 30%+ discount
            score = 1.0 - price_ratio  # Higher score for better deals
            return True, score, adjusted_normal_price
        elif price_ratio < 0.85:  # 15%+ discount
            score = 0.7 * (1.0 - price_ratio)
            return True, score, adjusted_normal_price
        
        return False, 0.0, adjusted_normal_price
    
    def _calculate_base_round_trip_price(self, route: Route, stay_nights: int) -> float:
        """Calculate base round-trip price for the route"""
        # This should use historical data - simplified for now
        
        # Base pricing by region and tier
        base_prices = {
            "europe_proche": {1: 180, 2: 220, 3: 280},
            "europe_populaire": {1: 320, 2: 380, 3: 450},
            "long_courrier": {1: 650, 2: 800, 3: 950}
        }
        
        region = route.region or "europe_populaire"
        tier = route.tier or 3
        
        return base_prices.get(region, base_prices["europe_populaire"]).get(tier, 400)
    
    def _get_stay_duration_multiplier(self, stay_nights: int) -> float:
        """Get price multiplier based on stay duration"""
        # Longer stays often have better per-night rates
        if stay_nights <= 3:
            return 1.2  # Short stays cost more per night
        elif stay_nights <= 7:
            return 1.0  # Standard pricing
        elif stay_nights <= 14:
            return 0.95  # Slight discount for medium stays
        else:
            return 0.9  # Better rates for long stays
    
    def _simulate_price(self, route: Route, date: datetime, is_return: bool = False) -> float:
        """Simulate flight pricing (replace with real API in production)"""
        import random
        
        # Base price by route tier and region for individual flight legs
        base_price = self._calculate_base_round_trip_price(route, 7) / 2  # Individual leg price
        
        # Add randomness to simulate market fluctuations
        variation = random.uniform(0.7, 1.4)
        price = base_price * variation
        
        # Return flights sometimes cost more
        if is_return:
            price *= random.uniform(0.9, 1.1)
        
        return round(price, 2)
    
    async def _process_flight_deal(self, route: Route, flight: Dict, departure_date: datetime, 
                                  return_date: datetime, stay_nights: int) -> Optional[Deal]:
        """Process a flight from FlightLabs into a potential deal"""
        try:
            # Extract flight data
            total_price = flight['price']
            airline = flight['airline']
            
            # Create price history entry
            price_history = PriceHistory(
                route_id=route.id,
                airline=airline,
                price=total_price,
                currency=flight.get('currency', 'EUR'),
                departure_date=departure_date,
                return_date=return_date,
                flight_number=flight.get('flight_number', ''),
                booking_class=flight.get('booking_class', 'economy'),
                raw_data=flight
            )
            self.db.add(price_history)
            self.db.flush()

            # Check for anomaly (price drop)
            is_anomaly, anomaly_score, normal_price = await self._check_anomaly(route, total_price)
            
            if is_anomaly and anomaly_score > 0.7:  # High confidence anomaly
                # Calculate discount percentage
                discount_percentage = ((normal_price - total_price) / normal_price) * 100
                
                if discount_percentage >= 30:  # Minimum 30% discount
                    # Validate with TravelPayouts (dual validation)
                    is_valid = await self.dual_validator.validate_deal(
                        origin=route.origin,
                        destination=route.destination,
                        price=total_price,
                        departure_date=departure_date,
                        return_date=return_date
                    )
                    
                    if is_valid:
                        # Create deal
                        deal = Deal(
                            route_id=route.id,
                            price_history_id=price_history.id,
                            deal_price=total_price,
                            normal_price=normal_price,
                            discount_percentage=discount_percentage,
                            confidence_score=anomaly_score,
                            departure_date=departure_date,
                            return_date=return_date,
                            stay_duration_nights=stay_nights,
                            advance_booking_days=(departure_date - datetime.now()).days,
                            airline=airline,
                            flight_details=flight.get('raw_data', {}),
                            booking_url=flight.get('booking_url', ''),
                            is_error_fare=discount_percentage >= 70,
                            is_round_trip_valid=True,
                            dual_api_validated=True
                        )
                        
                        self.db.add(deal)
                        logger.info(f"New deal found: {route.origin}->{route.destination} at €{total_price} (-{discount_percentage:.0f}%)")
                        return deal
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing flight deal: {e}")
            return None

    # ...existing code...