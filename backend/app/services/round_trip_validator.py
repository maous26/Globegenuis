"""
Round-trip deal validation service for GlobeGenius
Implements the new rules for round-trip deals with stay duration and timing constraints
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.models.flight import Route, Deal, PriceHistory
from app.utils.logger import logger


class RoundTripDealValidator:
    """
    Validates round-trip deals based on the new criteria:
    - Only round-trip deals
    - Minimum stay requirements by region
    - Advance booking constraints (1-9 months)
    - Weekday patterns for short stays
    """
    
    # Regional stay requirements
    REGION_STAY_REQUIREMENTS = {
        "europe_proche": {"min": 3, "max": 7},      # Short European destinations
        "europe_populaire": {"min": 7, "max": 14},  # Popular European/North America
        "long_courrier": {"min": 15, "max": 30}     # Long-haul Asia/Oceania
    }
    
    # Advance booking constraints
    MIN_ADVANCE_DAYS = 30   # 1 month minimum
    MAX_ADVANCE_DAYS = 270  # 9 months maximum
    
    # Short stay weekday patterns
    SHORT_STAY_PATTERNS = {
        3: [(1, 4)],  # Monday to Wednesday
        4: [(2, 6)],  # Tuesday to Friday  
        5: [(3, 7)]   # Wednesday to Sunday
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_deal(self, deal: Deal, price_history: PriceHistory, route: Route) -> Dict[str, Any]:
        """
        Validate a round-trip deal against all criteria
        
        Args:
            deal: Deal object to validate
            price_history: Associated price history
            route: Route information
            
        Returns:
            Dict with validation results and updated deal flags
        """
        validation_result = {
            "is_valid": False,
            "stay_duration_valid": False,
            "timing_valid": False,
            "advance_booking_valid": False,
            "stay_nights": 0,
            "advance_days": 0,
            "validation_errors": []
        }
        
        try:
            # Must have return date for round-trip
            if not price_history.return_date:
                validation_result["validation_errors"].append("Missing return date for round-trip")
                return validation_result
            
            # Calculate stay duration
            stay_duration = self._calculate_stay_duration(
                price_history.departure_date, 
                price_history.return_date
            )
            validation_result["stay_nights"] = stay_duration
            
            # Calculate advance booking days
            advance_days = self._calculate_advance_booking_days(price_history.departure_date)
            validation_result["advance_days"] = advance_days
            
            # Validate stay duration by region
            stay_valid = self._validate_stay_duration(stay_duration, route.region)
            validation_result["stay_duration_valid"] = stay_valid
            
            # Validate timing patterns (weekdays for short stays)
            timing_valid = self._validate_timing_patterns(
                price_history.departure_date,
                price_history.return_date,
                stay_duration,
                route
            )
            validation_result["timing_valid"] = timing_valid
            
            # Validate advance booking window
            advance_valid = self._validate_advance_booking(advance_days)
            validation_result["advance_booking_valid"] = advance_valid
            
            # Overall validation
            validation_result["is_valid"] = stay_valid and timing_valid and advance_valid
            
            # Update deal fields
            self._update_deal_fields(deal, validation_result, price_history)
            
            if validation_result["is_valid"]:
                logger.info(f"Deal {deal.id} validated successfully: {stay_duration} nights, {advance_days} days advance")
            else:
                logger.warning(f"Deal {deal.id} validation failed: {validation_result['validation_errors']}")
                
        except Exception as e:
            logger.error(f"Error validating deal {deal.id}: {str(e)}")
            validation_result["validation_errors"].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    def _calculate_stay_duration(self, departure_date: datetime, return_date: datetime) -> int:
        """Calculate stay duration in nights"""
        if not departure_date or not return_date:
            return 0
        
        delta = return_date.date() - departure_date.date()
        return delta.days
    
    def _calculate_advance_booking_days(self, departure_date: datetime) -> int:
        """Calculate days between now and departure"""
        if not departure_date:
            return 0
        
        now = datetime.now()
        delta = departure_date.date() - now.date()
        return delta.days
    
    def _validate_stay_duration(self, stay_nights: int, region: str) -> bool:
        """Validate stay duration based on region requirements"""
        if not region or region not in self.REGION_STAY_REQUIREMENTS:
            return False
        
        requirements = self.REGION_STAY_REQUIREMENTS[region]
        return requirements["min"] <= stay_nights <= requirements["max"]
    
    def _validate_timing_patterns(self, departure_date: datetime, return_date: datetime, 
                                stay_nights: int, route: Route) -> bool:
        """Validate weekday patterns for short stays"""
        if not departure_date or not return_date:
            return False
        
        departure_weekday = departure_date.weekday() + 1  # 1=Monday, 7=Sunday
        return_weekday = return_date.weekday() + 1
        
        # For short stays (3-5 nights), check specific patterns
        if stay_nights in self.SHORT_STAY_PATTERNS:
            allowed_patterns = self.SHORT_STAY_PATTERNS[stay_nights]
            pattern_match = any(
                departure_weekday == start and return_weekday == end 
                for start, end in allowed_patterns
            )
            
            # Check route-specific weekday allowances
            if stay_nights == 3 and not route.allow_mon_wed:
                return False
            elif stay_nights == 4 and not route.allow_tue_fri:
                return False
            elif stay_nights == 5 and not route.allow_wed_sun:
                return False
                
            return pattern_match
        
        # For longer stays, any weekday pattern is acceptable
        return True
    
    def _validate_advance_booking(self, advance_days: int) -> bool:
        """Validate advance booking window (1-9 months)"""
        return self.MIN_ADVANCE_DAYS <= advance_days <= self.MAX_ADVANCE_DAYS
    
    def _update_deal_fields(self, deal: Deal, validation_result: Dict[str, Any], 
                          price_history: PriceHistory) -> None:
        """Update deal object with validation results"""
        deal.stay_duration_nights = validation_result["stay_nights"]
        deal.advance_booking_days = validation_result["advance_days"]
        
        if price_history.departure_date:
            deal.departure_day_of_week = price_history.departure_date.weekday() + 1
        if price_history.return_date:
            deal.return_day_of_week = price_history.return_date.weekday() + 1
        
        deal.meets_stay_requirements = validation_result["stay_duration_valid"]
        deal.meets_timing_requirements = validation_result["timing_valid"] 
        deal.meets_advance_booking = validation_result["advance_booking_valid"]
        deal.is_valid_round_trip = validation_result["is_valid"]
    
    def get_regional_routes_config(self) -> Dict[str, List[Dict]]:
        """
        Get the optimized 60-route configuration based on the strategy
        """
        return {
            "tier_1_routes": [
                # Paris CDG/ORY - Ultra Priority (12 routes)
                {"origin": "CDG", "destination": "MAD", "region": "europe_populaire", "tier": 1},
                {"origin": "CDG", "destination": "BCN", "region": "europe_populaire", "tier": 1},
                {"origin": "CDG", "destination": "LHR", "region": "europe_populaire", "tier": 1},
                {"origin": "CDG", "destination": "FCO", "region": "europe_populaire", "tier": 1},
                {"origin": "CDG", "destination": "AMS", "region": "europe_proche", "tier": 1},
                {"origin": "CDG", "destination": "JFK", "region": "long_courrier", "tier": 1},
                {"origin": "CDG", "destination": "MXP", "region": "europe_proche", "tier": 1},
                {"origin": "CDG", "destination": "LIS", "region": "europe_populaire", "tier": 1},
                {"origin": "CDG", "destination": "TXL", "region": "europe_proche", "tier": 1},
                {"origin": "CDG", "destination": "CPH", "region": "europe_populaire", "tier": 1},
                {"origin": "CDG", "destination": "ZUR", "region": "europe_proche", "tier": 1},
                {"origin": "CDG", "destination": "DUB", "region": "europe_populaire", "tier": 1},
                
                # Domestic routes (8 routes)
                {"origin": "CDG", "destination": "NCE", "region": "europe_proche", "tier": 1},
                {"origin": "CDG", "destination": "TLS", "region": "europe_proche", "tier": 1},
                {"origin": "CDG", "destination": "MRS", "region": "europe_proche", "tier": 1},
                {"origin": "CDG", "destination": "BOD", "region": "europe_proche", "tier": 1},
                {"origin": "CDG", "destination": "LYS", "region": "europe_proche", "tier": 1},
                {"origin": "CDG", "destination": "NTE", "region": "europe_proche", "tier": 1},
                {"origin": "CDG", "destination": "MPL", "region": "europe_proche", "tier": 1},
                {"origin": "CDG", "destination": "LIL", "region": "europe_proche", "tier": 1},
            ],
            
            "tier_2_routes": [
                # Regional airports (25 routes)
                # Lyon routes
                {"origin": "LYS", "destination": "MAD", "region": "europe_populaire", "tier": 2},
                {"origin": "LYS", "destination": "BCN", "region": "europe_populaire", "tier": 2},
                {"origin": "LYS", "destination": "LHR", "region": "europe_populaire", "tier": 2},
                {"origin": "LYS", "destination": "AMS", "region": "europe_proche", "tier": 2},
                {"origin": "LYS", "destination": "FCO", "region": "europe_populaire", "tier": 2},
                
                # Nice routes  
                {"origin": "NCE", "destination": "CDG", "region": "europe_proche", "tier": 2},
                {"origin": "NCE", "destination": "LHR", "region": "europe_populaire", "tier": 2},
                {"origin": "NCE", "destination": "MAD", "region": "europe_populaire", "tier": 2},
                {"origin": "NCE", "destination": "MXP", "region": "europe_proche", "tier": 2},
                {"origin": "NCE", "destination": "FCO", "region": "europe_populaire", "tier": 2},
                
                # Marseille routes
                {"origin": "MRS", "destination": "MAD", "region": "europe_populaire", "tier": 2},
                {"origin": "MRS", "destination": "BCN", "region": "europe_populaire", "tier": 2},
                {"origin": "MRS", "destination": "LHR", "region": "europe_populaire", "tier": 2},
                {"origin": "MRS", "destination": "AMS", "region": "europe_proche", "tier": 2},
                {"origin": "MRS", "destination": "FCO", "region": "europe_populaire", "tier": 2},
                
                # Long-haul strategic
                {"origin": "CDG", "destination": "LAX", "region": "long_courrier", "tier": 2},
                {"origin": "CDG", "destination": "NRT", "region": "long_courrier", "tier": 2},
                {"origin": "CDG", "destination": "CMN", "region": "europe_populaire", "tier": 2},
                {"origin": "CDG", "destination": "DXB", "region": "long_courrier", "tier": 2},
                {"origin": "CDG", "destination": "YUL", "region": "long_courrier", "tier": 2},
                
                # European secondary
                {"origin": "CDG", "destination": "PRG", "region": "europe_populaire", "tier": 2},
                {"origin": "CDG", "destination": "VIE", "region": "europe_populaire", "tier": 2},
                {"origin": "CDG", "destination": "ARN", "region": "europe_populaire", "tier": 2},
                {"origin": "CDG", "destination": "ATH", "region": "europe_populaire", "tier": 2},
                {"origin": "CDG", "destination": "IST", "region": "europe_populaire", "tier": 2},
            ],
            
            "tier_3_routes": [
                # Bordeaux/Toulouse (6 routes)
                {"origin": "BOD", "destination": "MAD", "region": "europe_populaire", "tier": 3},
                {"origin": "BOD", "destination": "LHR", "region": "europe_populaire", "tier": 3},
                {"origin": "BOD", "destination": "AMS", "region": "europe_proche", "tier": 3},
                {"origin": "TLS", "destination": "MAD", "region": "europe_populaire", "tier": 3},
                {"origin": "TLS", "destination": "LHR", "region": "europe_populaire", "tier": 3},
                {"origin": "TLS", "destination": "FCO", "region": "europe_populaire", "tier": 3},
                
                # Specialized destinations (9 routes)
                {"origin": "CDG", "destination": "RAK", "region": "europe_populaire", "tier": 3},
                {"origin": "CDG", "destination": "TUN", "region": "europe_populaire", "tier": 3},
                {"origin": "CDG", "destination": "ALG", "region": "europe_populaire", "tier": 3},
                {"origin": "CDG", "destination": "TLV", "region": "europe_populaire", "tier": 3},
                {"origin": "CDG", "destination": "GRU", "region": "long_courrier", "tier": 3},
                {"origin": "CDG", "destination": "MRU", "region": "long_courrier", "tier": 3},
                {"origin": "CDG", "destination": "FDF", "region": "long_courrier", "tier": 3},
                {"origin": "CDG", "destination": "BKK", "region": "long_courrier", "tier": 3},
                {"origin": "CDG", "destination": "SSA", "region": "long_courrier", "tier": 3},
            ]
        }


def update_routes_with_round_trip_config(db: Session) -> None:
    """
    Update existing routes with the new round-trip configuration
    """
    validator = RoundTripDealValidator(db)
    route_config = validator.get_regional_routes_config()
    
    # Update existing routes or create new ones
    all_routes = []
    for tier_name, routes in route_config.items():
        all_routes.extend(routes)
    
    for route_data in all_routes:
        existing_route = db.query(Route).filter(
            Route.origin == route_data["origin"],
            Route.destination == route_data["destination"]
        ).first()
        
        if existing_route:
            # Update existing route
            existing_route.tier = route_data["tier"]
            existing_route.region = route_data["region"]
            existing_route.route_type = "round_trip"
            existing_route.min_stay_nights = validator.REGION_STAY_REQUIREMENTS[route_data["region"]]["min"]
            existing_route.max_stay_nights = validator.REGION_STAY_REQUIREMENTS[route_data["region"]]["max"]
            existing_route.min_advance_booking_days = validator.MIN_ADVANCE_DAYS
            existing_route.max_advance_booking_days = validator.MAX_ADVANCE_DAYS
            
            # Set scan intervals based on tier
            if route_data["tier"] == 1:
                existing_route.scan_interval_hours = 4
            elif route_data["tier"] == 2:
                existing_route.scan_interval_hours = 6
            else:
                existing_route.scan_interval_hours = 12
        else:
            # Create new route
            new_route = Route(
                origin=route_data["origin"],
                destination=route_data["destination"],
                tier=route_data["tier"],
                region=route_data["region"],
                route_type="round_trip",
                min_stay_nights=validator.REGION_STAY_REQUIREMENTS[route_data["region"]]["min"],
                max_stay_nights=validator.REGION_STAY_REQUIREMENTS[route_data["region"]]["max"],
                min_advance_booking_days=validator.MIN_ADVANCE_DAYS,
                max_advance_booking_days=validator.MAX_ADVANCE_DAYS,
                scan_interval_hours=4 if route_data["tier"] == 1 else (6 if route_data["tier"] == 2 else 12)
            )
            db.add(new_route)
    
    db.commit()
    logger.info(f"Updated routes with round-trip configuration: {len(all_routes)} routes configured")
