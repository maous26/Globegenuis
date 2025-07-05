import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from app.core.config import settings
from app.utils.logger import logger


class AviationStackAPI:
    def __init__(self):
        self.api_key = settings.AVIATIONSTACK_API_KEY
        self.base_url = settings.AVIATIONSTACK_BASE_URL
        self.timeout = httpx.Timeout(30.0)
        
    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: datetime,
        return_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search flights between origin and destination
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            params = {
                "access_key": self.api_key,
                "dep_iata": origin,
                "arr_iata": destination,
                "flight_date": departure_date.strftime("%Y-%m-%d"),
                "limit": limit
            }
            
            try:
                response = await client.get(
                    f"{self.base_url}/flights",
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("data"):
                    return self._parse_flights(data["data"])
                return []
                
            except httpx.HTTPError as e:
                logger.error(f"API error searching flights {origin}-{destination}: {e}")
                return []
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return []
    
    def _parse_flights(self, raw_flights: List[Dict]) -> List[Dict[str, Any]]:
        """Parse and normalize flight data"""
        parsed_flights = []
        
        for flight in raw_flights:
            try:
                parsed = {
                    "airline": flight.get("airline", {}).get("name"),
                    "airline_iata": flight.get("airline", {}).get("iata"),
                    "flight_number": flight.get("flight", {}).get("iata"),
                    "departure_airport": flight.get("departure", {}).get("iata"),
                    "departure_time": flight.get("departure", {}).get("scheduled"),
                    "arrival_airport": flight.get("arrival", {}).get("iata"),
                    "arrival_time": flight.get("arrival", {}).get("scheduled"),
                    "price": None,  # AviationStack doesn't provide prices
                    "raw_data": flight
                }
                parsed_flights.append(parsed)
            except Exception as e:
                logger.warning(f"Error parsing flight: {e}")
                continue
                
        return parsed_flights
    
    async def get_historical_prices(
        self,
        origin: str,
        destination: str,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """Get historical price data for anomaly detection"""
        historical_data = []
        tasks = []
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for days_ago in range(1, days_back + 1):
                date = datetime.now() - timedelta(days=days_ago)
                task = self._fetch_day_data(client, origin, destination, date)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    historical_data.extend(result)
                    
        return historical_data
    
    async def _fetch_day_data(
        self,
        client: httpx.AsyncClient,
        origin: str,
        destination: str,
        date: datetime
    ) -> List[Dict]:
        """Fetch data for a specific day"""
        try:
            params = {
                "access_key": self.api_key,
                "dep_iata": origin,
                "arr_iata": destination,
                "flight_date": date.strftime("%Y-%m-%d")
            }
            
            response = await client.get(f"{self.base_url}/flights", params=params)
            response.raise_for_status()
            data = response.json()
            
            return data.get("data", [])
        except Exception as e:
            logger.warning(f"Error fetching data for {date}: {e}")
            return []