"""
Service de scan simulé pour le développement sans API réelle
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.models.flight import Route, Deal, PriceHistory
from app.models.api_tracking import ApiCall
from app.utils.logger import logger
from sqlalchemy.orm import Session

class MockFlightScanner:
    """Scanner simulé qui génère des données réalistes sans appels API"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def scan_route(self, route: Route) -> Dict[str, Any]:
        """Simuler un scan de route avec des données réalistes"""
        
        logger.info(f"🔧 SCAN SIMULÉ: {route.origin}→{route.destination}")
        
        # Enregistrer l'appel API simulé
        api_call = ApiCall(
            route_id=route.id,
            endpoint="mock_aviationstack",
            method="GET",
            status_code=200,
            response_time=random.uniform(0.2, 1.0),
            timestamp=datetime.now(),
            quota_used=0  # Pas de quota utilisé en mode mock
        )
        self.db.add(api_call)
        
        # Générer des prix simulés
        base_prices = {
            "CDG_JFK": 550, "CDG_LAX": 650, "CDG_BKK": 750,
            "CDG_BCN": 150, "CDG_MAD": 160, "CDG_FCO": 200,
            "CDG_AMS": 180, "CDG_LHR": 120, "CDG_DXB": 480
        }
        
        route_key = f"{route.origin}_{route.destination}"
        base_price = base_prices.get(route_key, 300)
        
        # Simuler des variations de prix
        normal_price = base_price + random.randint(-50, 100)
        
        # 30% de chance d'avoir un deal
        has_deal = random.random() < 0.3
        
        if has_deal:
            # Deal avec 20-60% de réduction
            discount = random.uniform(0.2, 0.6)
            deal_price = normal_price * (1 - discount)
            
            # Créer price history
            price_history = PriceHistory(
                route_id=route.id,
                airline=random.choice(["AF", "KL", "LH", "BA", "IB", "AZ"]),
                price=deal_price,
                currency="EUR",
                departure_date=datetime.now() + timedelta(days=random.randint(30, 90)),
                scanned_at=datetime.now()
            )
            self.db.add(price_history)
            self.db.flush()
            
            # Créer deal
            deal = Deal(
                route_id=route.id,
                price_history_id=price_history.id,
                normal_price=normal_price,
                deal_price=deal_price,
                discount_percentage=discount * 100,
                anomaly_score=random.uniform(0.5, 0.9),
                confidence_score=random.randint(60, 95),
                expires_at=datetime.now() + timedelta(hours=random.randint(6, 48)),
                is_active=True,
                airline=price_history.airline,
                currency="EUR",
                departure_date=price_history.departure_date,
                flight_number=f"{price_history.airline}{random.randint(1000, 9999)}",
                booking_class="Economy",
                detected_at=datetime.now()
            )
            self.db.add(deal)
            
            logger.info(f"💎 Deal simulé trouvé: {deal_price:.0f}€ (au lieu de {normal_price:.0f}€)")
            
            return {
                "success": True,
                "deal_found": True,
                "deal_price": deal_price,
                "normal_price": normal_price,
                "discount": discount * 100,
                "simulated": True
            }
        else:
            # Pas de deal, juste enregistrer le prix normal
            price_history = PriceHistory(
                route_id=route.id,
                airline=random.choice(["AF", "KL", "LH", "BA", "IB", "AZ"]),
                price=normal_price,
                currency="EUR",
                departure_date=datetime.now() + timedelta(days=random.randint(30, 90)),
                scanned_at=datetime.now()
            )
            self.db.add(price_history)
            
            return {
                "success": True,
                "deal_found": False,
                "price": normal_price,
                "simulated": True
            }
    
    def scan_multiple_routes(self, routes: List[Route]) -> Dict[str, Any]:
        """Scanner plusieurs routes en mode simulé"""
        
        results = {
            "total_scanned": len(routes),
            "deals_found": 0,
            "api_calls_made": len(routes),
            "simulated": True,
            "routes_scanned": []
        }
        
        for route in routes:
            result = self.scan_route(route)
            results["routes_scanned"].append({
                "route": f"{route.origin}→{route.destination}",
                "result": result
            })
            
            if result.get("deal_found"):
                results["deals_found"] += 1
        
        self.db.commit()
        
        logger.info(f"🔧 Scan simulé terminé: {results['deals_found']} deals sur {results['total_scanned']} routes")
        
        return results
