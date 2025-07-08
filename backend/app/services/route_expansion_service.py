# backend/app/services/route_expansion_service.py
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.flight import Route
from app.utils.logger import logger
import random

class RouteExpansionService:
    """Service for managing route expansion and automatic route addition"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # European major hubs and destinations
        self.major_hubs = {
            "CDG": "Paris Charles de Gaulle",
            "LHR": "London Heathrow", 
            "FRA": "Frankfurt",
            "AMS": "Amsterdam",
            "FCO": "Rome Fiumicino",
            "MAD": "Madrid",
            "BCN": "Barcelona",
            "MXP": "Milan Malpensa",
            "ZUR": "Zurich",
            "VIE": "Vienna",
            "MUC": "Munich",
            "CPH": "Copenhagen"
        }
        
        # Secondary European cities
        self.secondary_cities = {
            "ORY": "Paris Orly",
            "LGW": "London Gatwick",
            "STN": "London Stansted",
            "BRU": "Brussels",
            "DUS": "Düsseldorf",
            "HAM": "Hamburg",
            "ARN": "Stockholm",
            "OSL": "Oslo",
            "HEL": "Helsinki",
            "LIS": "Lisbon",
            "OPO": "Porto",
            "ATH": "Athens",
            "PRG": "Prague",
            "WAW": "Warsaw",
            "BUD": "Budapest"
        }
        
        # French regional airports
        self.french_regional = {
            "NCE": "Nice",
            "LYS": "Lyon", 
            "MRS": "Marseille",
            "TLS": "Toulouse",
            "BOD": "Bordeaux",
            "NTE": "Nantes",
            "LIL": "Lille",
            "MPL": "Montpellier",
            "SXB": "Strasbourg",
            "BIQ": "Biarritz"
        }
        
        # Popular vacation destinations
        self.vacation_destinations = {
            "PMI": "Palma de Mallorca",
            "IBZ": "Ibiza", 
            "HER": "Heraklion",
            "RHO": "Rhodes",
            "CFU": "Corfu",
            "OLB": "Olbia",
            "CAG": "Cagliari",
            "DBV": "Dubrovnik",
            "SPU": "Split",
            "TFS": "Tenerife",
            "LPA": "Las Palmas",
            "FAO": "Faro"
        }
        
        # Long-haul destinations
        self.longhaul_destinations = {
            "JFK": "New York JFK",
            "LAX": "Los Angeles", 
            "MIA": "Miami",
            "YYZ": "Toronto",
            "YUL": "Montreal",
            "NRT": "Tokyo Narita",
            "ICN": "Seoul",
            "BKK": "Bangkok",
            "SIN": "Singapore",
            "DXB": "Dubai",
            "DOH": "Doha",
            "CAI": "Cairo",
            "CMN": "Casablanca",
            "JNB": "Johannesburg"
        }
    
    def get_current_route_stats(self) -> Dict[str, Any]:
        """Get current route statistics"""
        
        total_routes = self.db.query(Route).filter(Route.is_active == True).count()
        
        tier_stats = {}
        for tier in [1, 2, 3]:
            tier_count = self.db.query(Route).filter(
                Route.tier == tier,
                Route.is_active == True
            ).count()
            tier_stats[f"tier_{tier}"] = tier_count
        
        # Get unique origins and destinations
        origins = self.db.query(Route.origin).filter(Route.is_active == True).distinct().count()
        destinations = self.db.query(Route.destination).filter(Route.is_active == True).distinct().count()
        
        return {
            "total_routes": total_routes,
            "tier_distribution": tier_stats,
            "unique_origins": origins,
            "unique_destinations": destinations
        }
    
    def suggest_new_routes(self, count: int = 20, target_tier: int = 3) -> List[Dict[str, Any]]:
        """Suggest new routes to add based on network gaps"""
        
        # Get existing routes
        existing_routes = set()
        routes = self.db.query(Route).filter(Route.is_active == True).all()
        for route in routes:
            existing_routes.add((route.origin, route.destination))
        
        suggestions = []
        all_airports = {**self.major_hubs, **self.secondary_cities, **self.french_regional, **self.vacation_destinations}
        
        # If adding long-haul routes
        if target_tier <= 2:
            all_airports.update(self.longhaul_destinations)
        
        # Generate route suggestions
        origins = list(self.major_hubs.keys()) + list(self.french_regional.keys())
        destinations = list(all_airports.keys())
        
        for origin in origins:
            for destination in destinations:
                if origin == destination:
                    continue
                    
                # Skip if route already exists (both directions)
                if (origin, destination) in existing_routes or (destination, origin) in existing_routes:
                    continue
                
                # Calculate suggested tier based on route characteristics
                suggested_tier = self._calculate_route_tier(origin, destination)
                
                # Only suggest routes for the target tier or adjust slightly
                if abs(suggested_tier - target_tier) <= 1:
                    priority_score = self._calculate_priority_score(origin, destination)
                    
                    suggestions.append({
                        "origin": origin,
                        "destination": destination,
                        "origin_name": all_airports.get(origin, origin),
                        "destination_name": all_airports.get(destination, destination),
                        "suggested_tier": suggested_tier,
                        "priority_score": priority_score,
                        "route_type": self._classify_route_type(origin, destination),
                        "estimated_demand": self._estimate_demand(origin, destination)
                    })
        
        # Sort by priority score and return top suggestions
        suggestions.sort(key=lambda x: x["priority_score"], reverse=True)
        return suggestions[:count]
    
    def add_routes_automatically(self, route_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add multiple routes automatically"""
        
        added_routes = []
        skipped_routes = []
        errors = []
        
        for config in route_configs:
            try:
                origin = config["origin"]
                destination = config["destination"] 
                tier = config.get("tier", 3)
                
                # Check if route already exists
                existing = self.db.query(Route).filter(
                    Route.origin == origin,
                    Route.destination == destination
                ).first()
                
                if existing:
                    skipped_routes.append({
                        "route": f"{origin} → {destination}",
                        "reason": "Route already exists"
                    })
                    continue
                
                # Determine scan interval based on tier
                scan_interval_hours = {1: 2, 2: 4, 3: 6}.get(tier, 6)
                
                # Create new route
                new_route = Route(
                    origin=origin,
                    destination=destination,
                    tier=tier,
                    scan_interval_hours=scan_interval_hours,
                    is_active=True
                )
                
                self.db.add(new_route)
                self.db.flush()  # Get the ID
                
                added_routes.append({
                    "id": new_route.id,
                    "route": f"{origin} → {destination}",
                    "tier": tier,
                    "scan_interval_hours": scan_interval_hours
                })
                
            except Exception as e:
                errors.append({
                    "route": f"{config.get('origin', 'unknown')} → {config.get('destination', 'unknown')}",
                    "error": str(e)
                })
        
        # Commit all changes
        if added_routes:
            self.db.commit()
            logger.info(f"Successfully added {len(added_routes)} new routes")
        
        return {
            "added_routes": added_routes,
            "skipped_routes": skipped_routes,
            "errors": errors,
            "total_added": len(added_routes),
            "total_skipped": len(skipped_routes),
            "total_errors": len(errors)
        }
    
    def expand_network_smart(self, target_routes: int, focus_area: str = "balanced") -> Dict[str, Any]:
        """Smart network expansion to reach target number of routes"""
        
        current_stats = self.get_current_route_stats()
        current_total = current_stats["total_routes"]
        
        if current_total >= target_routes:
            return {
                "message": f"Already have {current_total} routes (target: {target_routes})",
                "added_routes": [],
                "current_stats": current_stats
            }
        
        routes_to_add = target_routes - current_total
        
        # Determine expansion strategy based on focus area
        if focus_area == "domestic":
            # Focus on French domestic and European routes
            tier_distribution = {"tier_3": 0.6, "tier_2": 0.3, "tier_1": 0.1}
        elif focus_area == "international":
            # Focus on long-haul routes
            tier_distribution = {"tier_2": 0.5, "tier_1": 0.3, "tier_3": 0.2}
        elif focus_area == "vacation":
            # Focus on vacation destinations
            tier_distribution = {"tier_3": 0.5, "tier_2": 0.4, "tier_1": 0.1}
        else:  # balanced
            tier_distribution = {"tier_3": 0.5, "tier_2": 0.3, "tier_1": 0.2}
        
        # Generate route suggestions for each tier
        route_configs = []
        
        for tier_name, percentage in tier_distribution.items():
            tier_num = int(tier_name.split("_")[1])
            tier_routes_count = int(routes_to_add * percentage)
            
            if tier_routes_count > 0:
                suggestions = self.suggest_new_routes(tier_routes_count, tier_num)
                for suggestion in suggestions:
                    route_configs.append({
                        "origin": suggestion["origin"],
                        "destination": suggestion["destination"],
                        "tier": tier_num
                    })
        
        # Add the routes
        result = self.add_routes_automatically(route_configs)
        
        # Get updated stats
        updated_stats = self.get_current_route_stats()
        
        return {
            **result,
            "expansion_strategy": focus_area,
            "target_routes": target_routes,
            "previous_stats": current_stats,
            "updated_stats": updated_stats
        }
    
    def _calculate_route_tier(self, origin: str, destination: str) -> int:
        """Calculate suggested tier for a route"""
        
        # Tier 1: Major hubs to major hubs, or high-traffic French domestic
        if (origin in self.major_hubs and destination in self.major_hubs) or \
           (origin in ["CDG", "ORY"] and destination in self.french_regional) or \
           (origin in self.french_regional and destination in ["CDG", "ORY"]):
            return 1
        
        # Tier 2: Secondary cities, some long-haul, vacation routes from major hubs
        if (origin in self.major_hubs and destination in self.longhaul_destinations) or \
           (origin in self.major_hubs and destination in self.vacation_destinations) or \
           (origin in self.secondary_cities and destination in self.major_hubs):
            return 2
        
        # Tier 3: Everything else
        return 3
    
    def _calculate_priority_score(self, origin: str, destination: str) -> float:
        """Calculate priority score for route suggestion"""
        
        score = 0.0
        
        # Higher score for major hubs
        if origin in self.major_hubs:
            score += 3.0
        elif origin in self.french_regional:
            score += 2.0
        elif origin in self.secondary_cities:
            score += 1.5
        
        if destination in self.major_hubs:
            score += 3.0
        elif destination in self.vacation_destinations:
            score += 2.5
        elif destination in self.longhaul_destinations:
            score += 2.0
        elif destination in self.secondary_cities:
            score += 1.5
        
        # Bonus for French domestic routes
        if origin in self.french_regional and destination in ["CDG", "ORY"]:
            score += 2.0
        
        # Bonus for popular vacation routes
        if origin in ["CDG", "ORY", "LYS", "NCE"] and destination in self.vacation_destinations:
            score += 1.5
        
        return score
    
    def _classify_route_type(self, origin: str, destination: str) -> str:
        """Classify the type of route"""
        
        if origin in self.french_regional and destination in ["CDG", "ORY"]:
            return "French Domestic"
        elif destination in self.vacation_destinations:
            return "Vacation/Leisure"
        elif destination in self.longhaul_destinations:
            return "Long-haul"
        elif origin in self.major_hubs and destination in self.major_hubs:
            return "European Major"
        else:
            return "European Regional"
    
    def _estimate_demand(self, origin: str, destination: str) -> str:
        """Estimate demand level for route"""
        
        priority = self._calculate_priority_score(origin, destination)
        
        if priority >= 6.0:
            return "High"
        elif priority >= 4.0:
            return "Medium"
        else:
            return "Low"
