"""
TravelPayouts API service for cross-validation with AviationStack
"""
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from app.core.config import settings
from app.utils.logger import logger


class TravelPayoutsAPI:
    """TravelPayouts API service for price validation and cross-checking"""
    
    def __init__(self):
        self.api_token = settings.TRAVELPAYOUTS_TOKEN
        self.base_url = "https://api.travelpayouts.com"
        self.timeout = httpx.Timeout(30.0)
        
    async def validate_price(
        self,
        origin: str,
        destination: str,
        departure_date: datetime,
        aviationstack_price: float,
        tolerance_percentage: float = 20.0
    ) -> Dict[str, Any]:
        """
        Validate AviationStack price against TravelPayouts data
        
        Args:
            origin: Origin airport code
            destination: Destination airport code  
            departure_date: Departure date
            aviationstack_price: Price from AviationStack to validate
            tolerance_percentage: Acceptable price difference percentage
            
        Returns:
            Validation result with cross-API analysis
        """
        
        try:
            # Get prices from TravelPayouts
            tp_prices = await self.search_flights(origin, destination, departure_date)
            
            if not tp_prices:
                return {
                    "validated": False,
                    "reason": "no_travelpayouts_data",
                    "confidence": 0.0,
                    "price_difference": None,
                    "tp_price_range": None
                }
            
            # Find best comparable price
            tp_prices_only = [p['price'] for p in tp_prices if p['price'] > 0]
            
            if not tp_prices_only:
                return {
                    "validated": False,
                    "reason": "no_valid_tp_prices",
                    "confidence": 0.0,
                    "price_difference": None,
                    "tp_price_range": None
                }
            
            # Calculate price comparison
            min_tp_price = min(tp_prices_only)
            avg_tp_price = sum(tp_prices_only) / len(tp_prices_only)
            max_tp_price = max(tp_prices_only)
            
            # Calculate differences
            diff_vs_min = ((aviationstack_price - min_tp_price) / min_tp_price) * 100
            diff_vs_avg = ((aviationstack_price - avg_tp_price) / avg_tp_price) * 100
            
            # Validation logic
            is_validated = False
            confidence = 0.0
            reason = "price_mismatch"
            
            if abs(diff_vs_avg) <= tolerance_percentage:
                is_validated = True
                confidence = 0.9
                reason = "price_validated_avg"
            elif abs(diff_vs_min) <= tolerance_percentage:
                is_validated = True
                confidence = 0.8
                reason = "price_validated_min"
            elif aviationstack_price < min_tp_price * 0.7:  # Significantly cheaper
                is_validated = True
                confidence = 0.95
                reason = "exceptional_deal_confirmed"
            elif aviationstack_price < avg_tp_price:
                is_validated = True
                confidence = 0.7
                reason = "below_average_confirmed"
            
            return {
                "validated": is_validated,
                "reason": reason,
                "confidence": confidence,
                "price_difference": {
                    "vs_min": diff_vs_min,
                    "vs_avg": diff_vs_avg,
                    "vs_max": ((aviationstack_price - max_tp_price) / max_tp_price) * 100
                },
                "tp_price_range": {
                    "min": min_tp_price,
                    "avg": avg_tp_price,
                    "max": max_tp_price,
                    "count": len(tp_prices_only)
                },
                "aviationstack_price": aviationstack_price
            }
            
        except Exception as e:
            logger.error(f"TravelPayouts validation error: {e}")
            return {
                "validated": False,
                "reason": "validation_error",
                "confidence": 0.0,
                "error": str(e)
            }

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: datetime,
        return_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Search flights on TravelPayouts for validation purposes
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                
                # Use TravelPayouts cheap flights API
                params = {
                    "origin": origin,
                    "destination": destination,
                    "departure_date": departure_date.strftime("%Y-%m-%d"),
                    "currency": "EUR",
                    "token": self.api_token,
                    "limit": 10
                }
                
                if return_date:
                    params["return_date"] = return_date.strftime("%Y-%m-%d")
                
                response = await client.get(
                    f"{self.base_url}/aviasales/v3/prices_for_dates",
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_tp_response(data)
                else:
                    logger.warning(f"TravelPayouts API error {response.status_code}: {response.text}")
                    return []
                    
        except Exception as e:
            logger.error(f"TravelPayouts search error: {e}")
            return []

    def _parse_tp_response(self, data: Dict) -> List[Dict[str, Any]]:
        """Parse TravelPayouts API response"""
        flights = []
        
        if not data.get("success", True):
            return flights
            
        # Handle different response formats
        flight_data = data.get("data", [])
        if isinstance(flight_data, dict):
            flight_data = flight_data.values()
        
        for flight in flight_data:
            try:
                if isinstance(flight, dict):
                    price = flight.get("value") or flight.get("price")
                    if price:
                        flights.append({
                            "airline": flight.get("airline", "Unknown"),
                            "price": float(price),
                            "currency": "EUR",
                            "departure_at": flight.get("departure_at"),
                            "return_at": flight.get("return_at"),
                            "duration": flight.get("duration"),
                            "source": "travelpayouts"
                        })
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing TravelPayouts flight: {e}")
                continue
        
        return flights

    async def get_historical_validation_data(
        self,
        origin: str,
        destination: str,
        days_back: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get historical price data from TravelPayouts for improved validation
        """
        historical_data = []
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                
                # Use calendar search for historical data
                params = {
                    "origin": origin,
                    "destination": destination,
                    "currency": "eur",
                    "calendar_type": "departure_date",
                    "trip_class": 0,  # Economy
                    "token": self.api_token
                }
                
                response = await client.get(
                    f"{self.base_url}/aviasales/v3/grouped_prices",
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and data.get("data"):
                        for price_data in data["data"]:
                            historical_data.append({
                                "price": float(price_data.get("value", 0)),
                                "departure_at": price_data.get("departure_at"),
                                "found_at": price_data.get("found_at"),
                                "source": "travelpayouts_historical"
                            })
                            
        except Exception as e:
            logger.error(f"TravelPayouts historical data error: {e}")
            
        return historical_data

    async def cross_validate_deal(
        self,
        origin: str,
        destination: str,
        departure_date: datetime,
        return_date: Optional[datetime],
        deal_price: float,
        normal_price: float
    ) -> Dict[str, Any]:
        """
        Comprehensive cross-validation of a deal using TravelPayouts
        """
        
        # Get current validation
        validation = await self.validate_price(
            origin, destination, departure_date, deal_price
        )
        
        # Get historical context
        historical_data = await self.get_historical_validation_data(
            origin, destination, days_back=14
        )
        
        # Analyze historical prices
        historical_prices = [h['price'] for h in historical_data if h['price'] > 0]
        
        enhanced_validation = validation.copy()
        
        if historical_prices:
            avg_historical = sum(historical_prices) / len(historical_prices)
            min_historical = min(historical_prices)
            
            enhanced_validation["historical_context"] = {
                "avg_price_14d": avg_historical,
                "min_price_14d": min_historical,
                "vs_historical_avg": ((deal_price - avg_historical) / avg_historical) * 100,
                "vs_historical_min": ((deal_price - min_historical) / min_historical) * 100,
                "sample_size": len(historical_prices)
            }
            
            # Enhance confidence based on historical data
            if deal_price < min_historical:
                enhanced_validation["confidence"] = min(enhanced_validation["confidence"] + 0.1, 1.0)
                enhanced_validation["deal_quality"] = "exceptional"
            elif deal_price < avg_historical * 0.8:
                enhanced_validation["deal_quality"] = "great"
            elif deal_price < avg_historical * 0.9:
                enhanced_validation["deal_quality"] = "good"
            else:
                enhanced_validation["deal_quality"] = "fair"
        
        # Round-trip specific validation
        if return_date:
            rt_validation = await self.search_flights(
                origin, destination, departure_date, return_date
            )
            
            if rt_validation:
                rt_prices = [f['price'] for f in rt_validation if f['price'] > 0]
                if rt_prices:
                    enhanced_validation["round_trip_context"] = {
                        "available_rt_prices": len(rt_prices),
                        "min_rt_price": min(rt_prices),
                        "avg_rt_price": sum(rt_prices) / len(rt_prices)
                    }
        
        return enhanced_validation
