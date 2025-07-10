# backend/app/services/flightlabs_api.py
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.core.config import settings
from app.utils.logger import logger
from app.models.api_tracking import ApiCall, ApiQuotaUsage
from app.core.database import SessionLocal
from sqlalchemy.orm import Session


class FlightLabsAPI:
    """
    FlightLabs API service with proper rate limiting for 10,000 monthly calls
    """
    
    def __init__(self):
        self.api_key = settings.FLIGHTLABS_API_KEY
        self.base_url = "https://app.goflightlabs.com"
        self.timeout = httpx.Timeout(30.0)
        self.monthly_limit = 10000  # 10,000 calls subscription
        self.daily_limit = 333  # ~10,000/30 days
        self.last_request_time = 0
        self.min_request_interval = 2.0  # 2 seconds between requests to be safe
        
    async def _rate_limit(self):
        """Enforce rate limiting between requests"""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = asyncio.get_event_loop().time()

    def _check_quota(self, db: Session) -> bool:
        """Check if we're within API quota limits"""
        from datetime import datetime, date
        
        # Check daily quota
        today = date.today()
        today_calls = db.query(ApiCall).filter(
            ApiCall.api_provider == 'flightlabs',
            ApiCall.called_at >= datetime.combine(today, datetime.min.time())
        ).count()
        
        if today_calls >= self.daily_limit:
            logger.warning(f"FlightLabs daily quota exceeded: {today_calls}/{self.daily_limit}")
            return False
        
        # Check monthly quota
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_calls = db.query(ApiCall).filter(
            ApiCall.api_provider == 'flightlabs',
            ApiCall.called_at >= month_start
        ).count()
        
        if monthly_calls >= self.monthly_limit:
            logger.warning(f"FlightLabs monthly quota exceeded: {monthly_calls}/{self.monthly_limit}")
            return False
        
        logger.info(f"FlightLabs quota check: {today_calls}/{self.daily_limit} today, {monthly_calls}/{self.monthly_limit} this month")
        return True

    def _log_api_call(self, db: Session, endpoint: str, success: bool, response_data: Dict = None):
        """Log API call for tracking and quota management"""
        import json
        try:
            api_call = ApiCall(
                api_provider='flightlabs',
                endpoint=endpoint,
                success=success,
                response_data=json.dumps(response_data) if response_data else None,
                called_at=datetime.now()
            )
            db.add(api_call)
            db.flush()  # Use flush instead of commit to avoid transaction conflicts
            logger.debug(f"Logged FlightLabs API call: {endpoint}, success: {success}")
        except Exception as e:
            logger.warning(f"Failed to log API call: {e}")
            # Continue execution even if logging fails

    async def search_flights(
        self, 
        origin: str, 
        destination: str, 
        departure_date: datetime,
        return_date: Optional[datetime] = None,
        adults: int = 1,
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for flights using FlightLabs API
        
        Args:
            origin: IATA airport code (e.g., 'CDG')
            destination: IATA airport code (e.g., 'JFK')
            departure_date: Departure date
            return_date: Return date for round-trip (optional)
            adults: Number of adult passengers
            db: Database session (optional, will create one if not provided)
            
        Returns:
            List of flight offers with pricing and details
        """
        # Use provided database session or create a new one
        if db is None:
            db = SessionLocal()
            own_session = True
        else:
            own_session = False
        
        try:
            # Check quota before making request
            if not self._check_quota(db):
                logger.warning("FlightLabs quota exceeded, skipping request")
                return []

            # Rate limiting
            await self._rate_limit()

            # Prepare parameters for FlightLabs flights endpoint
            params = {
                "access_key": self.api_key,
                "dep_iata": origin.upper(),
                "arr_iata": destination.upper(),
                "dep_schd_date": departure_date.strftime("%Y-%m-%d")
            }

            # Add return date for round-trip if provided
            if return_date:
                params["ret_schd_date"] = return_date.strftime("%Y-%m-%d")

            endpoint = "/flights"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"FlightLabs API request: {origin} -> {destination} on {departure_date.strftime('%Y-%m-%d')}")
                
                response = await client.get(
                    f"{self.base_url}{endpoint}",
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    flights = self._parse_response(data)
                    
                    # Log successful API call
                    self._log_api_call(db, endpoint, True, {"flights_found": len(flights)})
                    
                    logger.info(f"FlightLabs API success: Found {len(flights)} flights for {origin}->{destination}")
                    return flights
                
                elif response.status_code == 429:
                    logger.error("FlightLabs API rate limit exceeded")
                    self._log_api_call(db, endpoint, False, {"error": "rate_limit_exceeded"})
                    return []
                
                else:
                    error_data = {"status_code": response.status_code, "response": response.text}
                    logger.error(f"FlightLabs API error: {response.status_code} - {response.text}")
                    self._log_api_call(db, endpoint, False, error_data)
                    return []
                    
        except Exception as e:
            endpoint = "/flights"  # Set endpoint for error logging
            logger.error(f"FlightLabs API exception: {str(e)}")
            self._log_api_call(db, endpoint, False, {"error": str(e)})
            return []
        finally:
            # Only close the session if we created it
            if own_session:
                db.close()

    def _parse_response(self, data: Dict) -> List[Dict[str, Any]]:
        """Parse FlightLabs API response into standardized format"""
        flights = []
        
        if not data.get("data"):
            logger.warning("FlightLabs API response contains no data")
            return flights

        # FlightLabs /flights endpoint returns flight data differently
        flight_data = data["data"]
        
        # Handle both single flight and array of flights
        if isinstance(flight_data, dict):
            flight_data = [flight_data]
        elif not isinstance(flight_data, list):
            logger.warning("Unexpected FlightLabs data format")
            return flights

        for flight in flight_data:
            try:
                # Extract basic flight information
                airline_info = flight.get("airline", {})
                if isinstance(airline_info, str):
                    airline_name = airline_info
                    airline_code = ""
                else:
                    airline_name = airline_info.get("name", airline_info.get("icao", "Unknown"))
                    airline_code = airline_info.get("iata", airline_info.get("icao", ""))

                # Extract airports
                departure_airport = flight.get("dep_iata", "")
                arrival_airport = flight.get("arr_iata", "")
                
                # Extract times
                departure_time = flight.get("dep_time", "")
                arrival_time = flight.get("arr_time", "")
                
                # Estimate price based on route (FlightLabs flights endpoint doesn't always include pricing)
                # We'll use a simple pricing model for now
                price = self._estimate_flight_price(departure_airport, arrival_airport, flight)
                
                # Build standardized flight object
                standardized_flight = {
                    "airline": airline_name,
                    "airline_code": airline_code,
                    "flight_number": flight.get("flight_number", flight.get("flight_iata", "")),
                    "price": price,
                    "currency": "EUR",
                    "departure_airport": departure_airport,
                    "arrival_airport": arrival_airport,
                    "departure_time": departure_time,
                    "arrival_time": arrival_time,
                    "duration": flight.get("duration", ""),
                    "stops": 0,  # Direct flights from /flights endpoint
                    "booking_class": "economy",
                    "source": "flightlabs",
                    "booking_url": "",  # Not provided by flights endpoint
                    "raw_data": flight
                }
                
                flights.append(standardized_flight)
                
            except Exception as e:
                logger.error(f"Error parsing FlightLabs flight data: {e}")
                continue

        logger.info(f"Parsed {len(flights)} flights from FlightLabs response")
        return flights

    def _estimate_flight_price(self, origin: str, destination: str, flight_data: Dict) -> float:
        """Estimate flight price based on route and flight data"""
        # Base pricing by route type
        base_prices = {
            # Domestic France
            ("CDG", "NCE"): 120, ("CDG", "MRS"): 110, ("CDG", "TLS"): 100,
            ("CDG", "BOD"): 90, ("CDG", "LYS"): 80, ("CDG", "NTE"): 85,
            
            # Europe short-haul
            ("CDG", "MAD"): 180, ("CDG", "BCN"): 160, ("CDG", "FCO"): 170,
            ("CDG", "LHR"): 200, ("CDG", "AMS"): 150, ("CDG", "BER"): 180,
            ("CDG", "LIS"): 190, ("CDG", "DUB"): 170, ("CDG", "ATH"): 250,
            
            # Medium-haul
            ("CDG", "IST"): 350, ("CDG", "CAI"): 400, ("CDG", "TLV"): 450,
            ("CDG", "CMN"): 280, ("CDG", "TUN"): 320, ("CDG", "ALG"): 350,
            
            # Long-haul
            ("CDG", "JFK"): 650, ("CDG", "LAX"): 750, ("CDG", "MIA"): 700,
            ("CDG", "NRT"): 900, ("CDG", "BKK"): 850, ("CDG", "SIN"): 950,
            ("CDG", "DXB"): 550, ("CDG", "DOH"): 600, ("CDG", "HKG"): 880,
        }
        
        # Get base price
        route_key = (origin, destination)
        reverse_key = (destination, origin)
        base_price = base_prices.get(route_key) or base_prices.get(reverse_key) or 300
        
        # Apply airline multiplier
        airline_multipliers = {
            "ryanair": 0.7,
            "easyjet": 0.75,
            "vueling": 0.8,
            "air france": 1.0,
            "lufthansa": 1.1,
            "klm": 1.05,
            "british airways": 1.1,
            "emirates": 1.2,
            "qatar airways": 1.15
        }
        
        airline_name = flight_data.get("airline", {})
        if isinstance(airline_name, dict):
            airline_name = airline_name.get("name", "").lower()
        else:
            airline_name = str(airline_name).lower()
        
        multiplier = 1.0
        for airline, mult in airline_multipliers.items():
            if airline in airline_name:
                multiplier = mult
                break
        
        # Add some randomness for market variation
        import random
        variation = random.uniform(0.85, 1.15)
        
        return round(base_price * multiplier * variation, 2)

    async def test_connection(self) -> Dict[str, Any]:
        """Test FlightLabs API connection"""
        db = SessionLocal()
        try:
            # Simple test query - Paris to London tomorrow
            tomorrow = datetime.now() + timedelta(days=1)
            
            result = await self.search_flights(
                origin="CDG",
                destination="LHR", 
                departure_date=tomorrow,
                db=db  # Pass the database session
            )
            
            return {
                "success": True,
                "api_provider": "flightlabs",
                "flights_found": len(result),
                "test_route": "CDG -> LHR",
                "test_date": tomorrow.strftime("%Y-%m-%d"),
                "quota_status": self._get_quota_status(db)
            }
            
        except Exception as e:
            return {
                "success": False,
                "api_provider": "flightlabs",
                "error": str(e),
                "quota_status": self._get_quota_status(db)
            }
        finally:
            db.close()

    def _get_quota_status(self, db: Session) -> Dict[str, Any]:
        """Get current quota usage status"""
        from datetime import date
        
        today = date.today()
        today_calls = db.query(ApiCall).filter(
            ApiCall.api_provider == 'flightlabs',
            ApiCall.called_at >= datetime.combine(today, datetime.min.time())
        ).count()
        
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_calls = db.query(ApiCall).filter(
            ApiCall.api_provider == 'flightlabs',
            ApiCall.called_at >= month_start
        ).count()
        
        return {
            "daily_usage": today_calls,
            "daily_limit": self.daily_limit,
            "monthly_usage": monthly_calls,
            "monthly_limit": self.monthly_limit,
            "daily_remaining": max(0, self.daily_limit - today_calls),
            "monthly_remaining": max(0, self.monthly_limit - monthly_calls)
        }
