# backend/app/services/enhanced_route_manager.py
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.flight import Route, PriceHistory, Deal
from app.models.api_tracking import ApiCall, ApiQuotaUsage
from app.utils.logger import logger
import random

class EnhancedRouteManager:
    """Enhanced route manager with strict business rules for flight deals"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # French airports categorized by type
        self.french_airports = {
            "longhaul_hubs": {
                "CDG": "Paris Charles de Gaulle",  # Primary long-haul hub
                "ORY": "Paris Orly"  # Secondary long-haul hub
            },
            "european_hubs": {
                "CDG": "Paris Charles de Gaulle",
                "ORY": "Paris Orly",
                "LYS": "Lyon",
                "NCE": "Nice",
                "MRS": "Marseille"
            },
            "regional_airports": {
                "NCE": "Nice",
                "LYS": "Lyon",
                "MRS": "Marseille",
                "TLS": "Toulouse",
                "BOD": "Bordeaux",
                "NTE": "Nantes",
                "LIL": "Lille",
                "MPL": "Montpellier",
                "SXB": "Strasbourg",
                "BIQ": "Biarritz",
                "CFE": "Clermont-Ferrand",
                "BES": "Brest",
                "RNS": "Rennes",
                "EGC": "Bergerac",
                "AJA": "Ajaccio",
                "BIA": "Bastia"
            }
        }
        
        # Destination categories with travel duration rules
        self.destination_categories = {
            "european": {
                "airports": {
                    "LHR": "London", "AMS": "Amsterdam", "FCO": "Rome",
                    "BCN": "Barcelona", "MAD": "Madrid", "BER": "Berlin",
                    "VIE": "Vienna", "PRG": "Prague", "ATH": "Athens",
                    "LIS": "Lisbon", "DUB": "Dublin", "CPH": "Copenhagen",
                    "ARN": "Stockholm", "OSL": "Oslo", "HEL": "Helsinki"
                },
                "min_stay": 7,
                "max_stay": 14,
                "advance_booking": (30, 270)  # 1-9 months
            },
            "north_american": {
                "airports": {
                    "JFK": "New York", "LAX": "Los Angeles", "YYZ": "Toronto",
                    "YUL": "Montreal", "MIA": "Miami", "SFO": "San Francisco",
                    "BOS": "Boston", "ORD": "Chicago", "YVR": "Vancouver"
                },
                "min_stay": 7,
                "max_stay": 14,
                "advance_booking": (30, 270)
            },
            "asian": {
                "airports": {
                    "NRT": "Tokyo", "ICN": "Seoul", "PVG": "Shanghai",
                    "HKG": "Hong Kong", "SIN": "Singapore", "BKK": "Bangkok",
                    "DEL": "Delhi", "BOM": "Mumbai"
                },
                "min_stay": 15,
                "max_stay": 30,
                "advance_booking": (60, 300)  # 2-10 months for long-haul
            },
            "oceanian": {
                "airports": {
                    "SYD": "Sydney", "MEL": "Melbourne", "AKL": "Auckland",
                    "BNE": "Brisbane", "PER": "Perth"
                },
                "min_stay": 15,
                "max_stay": 30,
                "advance_booking": (60, 300)
            },
            "middle_eastern": {
                "airports": {
                    "DXB": "Dubai", "DOH": "Doha", "IST": "Istanbul",
                    "CAI": "Cairo", "AMM": "Amman", "TLV": "Tel Aviv"
                },
                "min_stay": 7,
                "max_stay": 14,
                "advance_booking": (30, 270)
            },
            "african": {
                "airports": {
                    "CMN": "Casablanca", "TUN": "Tunis", "JNB": "Johannesburg",
                    "CPT": "Cape Town", "NBO": "Nairobi", "ADD": "Addis Ababa"
                },
                "min_stay": 10,
                "max_stay": 21,
                "advance_booking": (45, 270)
            },
            "domestic_french": {
                "airports": {
                    "NCE": "Nice", "LYS": "Lyon", "MRS": "Marseille",
                    "TLS": "Toulouse", "BOD": "Bordeaux", "NTE": "Nantes",
                    "AJA": "Ajaccio", "BIA": "Bastia"
                },
                "min_stay": 3,  # Allow short stays for domestic
                "max_stay": 7,
                "advance_booking": (30, 180),
                "short_stay_days": ["monday", "tuesday", "wednesday"]  # Special rule for short stays
            }
        }
        
        # Seasonal patterns for destinations
        self.seasonal_patterns = {
            "winter": {  # Dec-Feb
                "priority_destinations": ["DXB", "BKK", "SIN", "SYD", "MEL", "CMN", "CAI"],
                "avoid_destinations": ["OSL", "ARN", "HEL"]
            },
            "spring": {  # Mar-May
                "priority_destinations": ["NRT", "ICN", "IST", "ATH", "BCN", "LIS"],
                "avoid_destinations": []
            },
            "summer": {  # Jun-Aug
                "priority_destinations": ["LAX", "YYZ", "CPH", "ARN", "OSL", "AKL"],
                "avoid_destinations": ["DXB", "DOH", "CAI"]
            },
            "autumn": {  # Sep-Nov
                "priority_destinations": ["JFK", "BOS", "FCO", "MAD", "DEL", "HKG"],
                "avoid_destinations": []
            }
        }

    def validate_deal_parameters(self, origin: str, destination: str, 
                               departure_date: datetime, return_date: datetime) -> Tuple[bool, str]:
        """Validate if deal parameters meet business rules"""
        
        # Calculate stay duration
        stay_duration = (return_date - departure_date).days
        
        # Calculate advance booking days
        advance_days = (departure_date - datetime.now()).days
        
        # Find destination category
        dest_category = None
        for category, data in self.destination_categories.items():
            if destination in data["airports"]:
                dest_category = category
                break
        
        if not dest_category:
            return False, f"Unknown destination: {destination}"
        
        category_rules = self.destination_categories[dest_category]
        
        # Check advance booking (no last-minute deals)
        min_advance, max_advance = category_rules["advance_booking"]
        if advance_days < min_advance:
            return False, f"Booking too close to departure. Minimum {min_advance} days required"
        if advance_days > max_advance:
            return False, f"Booking too far in advance. Maximum {max_advance} days allowed"
        
        # Check stay duration
        if stay_duration < category_rules["min_stay"]:
            # Special rules for domestic short stays
            if dest_category == "domestic_french" and stay_duration >= 3:
                departure_day = departure_date.strftime("%A").lower()
                if departure_day not in category_rules.get("short_stay_days", []):
                    return False, f"Short domestic stays must start on Monday, Tuesday, or Wednesday"
            else:
                return False, f"Stay too short. Minimum {category_rules['min_stay']} nights required"
        
        if stay_duration > category_rules["max_stay"]:
            return False, f"Stay too long. Maximum {category_rules['max_stay']} nights allowed"
        
        return True, "Valid"

    def get_optimal_routes_for_quota(self, monthly_quota: int = 10000) -> Dict[str, Any]:
        """Calculate optimal route distribution for given API quota"""
        
        # Calculate daily quota
        daily_quota = monthly_quota / 30
        
        # Reserve some quota for manual scans and buffer
        available_daily_quota = int(daily_quota * 0.9)  # Use 90% for scheduled scans
        
        # Define scan frequencies and their quota cost
        tier_configs = {
            1: {"interval_hours": 2, "daily_scans": 12},  # High priority
            2: {"interval_hours": 4, "daily_scans": 6},   # Medium priority
            3: {"interval_hours": 6, "daily_scans": 4}    # Low priority
        }
        
        # Calculate optimal distribution
        # Aim for: 10% Tier 1, 30% Tier 2, 60% Tier 3
        distribution = {
            "tier_1": int(available_daily_quota * 0.10 / tier_configs[1]["daily_scans"]),
            "tier_2": int(available_daily_quota * 0.30 / tier_configs[2]["daily_scans"]),
            "tier_3": int(available_daily_quota * 0.60 / tier_configs[3]["daily_scans"])
        }
        
        # Calculate actual daily API calls
        daily_calls = (
            distribution["tier_1"] * tier_configs[1]["daily_scans"] +
            distribution["tier_2"] * tier_configs[2]["daily_scans"] +
            distribution["tier_3"] * tier_configs[3]["daily_scans"]
        )
        
        return {
            "monthly_quota": monthly_quota,
            "daily_quota_available": available_daily_quota,
            "recommended_distribution": distribution,
            "total_routes": sum(distribution.values()),
            "estimated_daily_calls": daily_calls,
            "estimated_monthly_calls": daily_calls * 30,
            "quota_utilization": (daily_calls * 30 / monthly_quota) * 100
        }

    def select_routes_by_origin_rules(self, destination: str) -> str:
        """Select appropriate origin airport based on destination"""
        
        # Determine destination category
        dest_category = None
        for category, data in self.destination_categories.items():
            if destination in data["airports"]:
                dest_category = category
                break
        
        if not dest_category:
            return "CDG"  # Default to CDG
        
        # Apply origin selection rules
        if dest_category in ["asian", "oceanian", "north_american"]:
            # Long-haul: Primarily from Paris
            return random.choice(["CDG", "ORY"]) if random.random() > 0.8 else "CDG"
        
        elif dest_category in ["european", "middle_eastern"]:
            # European/Middle East: From major French hubs
            hubs = list(self.french_airports["european_hubs"].keys())
            return random.choice(hubs)
        
        elif dest_category == "domestic_french":
            # Domestic: From various French airports
            # Avoid same origin-destination
            airports = list(self.french_airports["regional_airports"].keys())
            airports = [a for a in airports if a != destination]
            return random.choice(airports) if airports else "CDG"
        
        return "CDG"

    def get_seasonal_priority_routes(self) -> List[Dict[str, Any]]:
        """Get priority routes based on current season"""
        
        month = datetime.now().month
        if month in [12, 1, 2]:
            season = "winter"
        elif month in [3, 4, 5]:
            season = "spring"
        elif month in [6, 7, 8]:
            season = "summer"
        else:
            season = "autumn"
        
        seasonal_config = self.seasonal_patterns[season]
        priority_routes = []
        
        for dest in seasonal_config["priority_destinations"]:
            origin = self.select_routes_by_origin_rules(dest)
            
            # Find destination category for tier assignment
            tier = 3  # Default
            for category, data in self.destination_categories.items():
                if dest in data["airports"]:
                    if category in ["asian", "oceanian"]:
                        tier = 1  # High priority for long-haul
                    elif category in ["european", "north_american"]:
                        tier = 2  # Medium priority
                    break
            
            priority_routes.append({
                "origin": origin,
                "destination": dest,
                "tier": tier,
                "season": season,
                "priority_score": 10  # High priority for seasonal routes
            })
        
        return priority_routes

    def auto_optimize_routes(self, target_api_calls: int = 10000) -> Dict[str, Any]:
        """Auto-optimize routes based on performance and API quota"""
        
        # Get current route performance
        recent_deals = self.db.query(
            Deal.route_id,
            func.count(Deal.id).label('deal_count'),
            func.avg(Deal.discount_percentage).label('avg_discount')
        ).filter(
            Deal.detected_at >= datetime.now() - timedelta(days=30)
        ).group_by(Deal.route_id).all()
        
        # Create performance map
        performance_map = {
            deal.route_id: {
                'deal_count': deal.deal_count,
                'avg_discount': float(deal.avg_discount) if deal.avg_discount else 0
            }
            for deal in recent_deals
        }
        
        # Get all active routes
        active_routes = self.db.query(Route).filter(Route.is_active == True).all()
        
        # Calculate route scores
        route_scores = []
        for route in active_routes:
            perf = performance_map.get(route.id, {'deal_count': 0, 'avg_discount': 0})
            
            # Calculate score based on deals found and average discount
            score = (perf['deal_count'] * 2) + (perf['avg_discount'] * 0.5)
            
            # Boost score for seasonal priority routes
            seasonal_routes = self.get_seasonal_priority_routes()
            for sr in seasonal_routes:
                if route.origin == sr['origin'] and route.destination == sr['destination']:
                    score *= 1.5
            
            route_scores.append({
                'route': route,
                'score': score,
                'performance': perf
            })
        
        # Sort by score
        route_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Get optimal distribution
        quota_config = self.get_optimal_routes_for_quota(target_api_calls)
        
        # Reassign tiers based on performance
        updates = []
        tier_counts = {1: 0, 2: 0, 3: 0}
        
        for i, route_data in enumerate(route_scores):
            route = route_data['route']
            
            # Assign tier based on ranking
            if tier_counts[1] < quota_config['recommended_distribution']['tier_1']:
                new_tier = 1
                tier_counts[1] += 1
            elif tier_counts[2] < quota_config['recommended_distribution']['tier_2']:
                new_tier = 2
                tier_counts[2] += 1
            else:
                new_tier = 3
                tier_counts[3] += 1
            
            if route.tier != new_tier:
                route.tier = new_tier
                route.scan_interval_hours = {1: 2, 2: 4, 3: 6}[new_tier]
                updates.append({
                    'route_id': route.id,
                    'route': f"{route.origin}→{route.destination}",
                    'old_tier': route.tier,
                    'new_tier': new_tier,
                    'score': route_data['score']
                })
        
        # Commit changes
        self.db.commit()
        
        return {
            'optimization_complete': True,
            'routes_updated': len(updates),
            'updates': updates[:10],  # Show top 10 updates
            'new_distribution': tier_counts,
            'quota_config': quota_config
        }

    def validate_and_clean_routes(self) -> Dict[str, Any]:
        """Validate all routes against business rules and clean invalid ones"""
        
        routes = self.db.query(Route).filter(Route.is_active == True).all()
        invalid_routes = []
        cleaned_count = 0
        
        for route in routes:
            # Check if route meets origin rules
            expected_origin = self.select_routes_by_origin_rules(route.destination)
            
            # For long-haul destinations, origin should be Paris
            is_longhaul = False
            for category in ["asian", "oceanian"]:
                if route.destination in self.destination_categories[category]["airports"]:
                    is_longhaul = True
                    break
            
            if is_longhaul and route.origin not in ["CDG", "ORY"]:
                invalid_routes.append({
                    'route': f"{route.origin}→{route.destination}",
                    'issue': 'Long-haul route should originate from Paris',
                    'route_id': route.id
                })
                route.is_active = False
                cleaned_count += 1
        
        self.db.commit()
        
        return {
            'total_routes_checked': len(routes),
            'invalid_routes_found': len(invalid_routes),
            'routes_deactivated': cleaned_count,
            'invalid_routes': invalid_routes[:20]  # Show first 20
        }