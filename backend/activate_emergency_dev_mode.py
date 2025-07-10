#!/usr/bin/env python3
"""
Script d'urgence pour activer le mode développement sans appels API réels
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.api_tracking import ApiCall
from app.models.flight import Route, Deal, PriceHistory
from app.utils.logger import logger
import random

def create_mock_api_activity():
    """Créer des données simulées pour continuer les tests"""
    
    print("🔧 ACTIVATION DU MODE DÉVELOPPEMENT")
    print("=" * 40)
    
    db = SessionLocal()
    
    try:
        # 1. Créer des appels API simulés
        print("📊 Création d'activité API simulée...")
        
        routes = db.query(Route).filter(Route.is_active == True).limit(20).all()
        
        # Simuler des appels pour aujourd'hui avec les deux APIs
        endpoints = ["aviationstack_mock", "travelpayouts_mock"]
        
        for i in range(50):  # 50 appels aujourd'hui
            route = random.choice(routes) if routes else None
            endpoint = random.choice(endpoints)
            
            api_call = ApiCall(
                route_id=route.id if route else 1,
                endpoint=endpoint,
                method="GET", 
                status_code=200,
                response_time=random.uniform(0.3, 1.5),
                timestamp=datetime.now() - timedelta(minutes=random.randint(0, 1440)),
                quota_used=1
            )
            db.add(api_call)
        
        # Simuler des appels pour la semaine
        for day in range(7):
            for i in range(random.randint(30, 80)):
                route = random.choice(routes) if routes else None
                
                api_call = ApiCall(
                    route_id=route.id if route else 1,
                    endpoint="aviationstack_mock",
                    method="GET",
                    status_code=200,
                    response_time=random.uniform(0.3, 1.5),
                    timestamp=datetime.now() - timedelta(days=day, minutes=random.randint(0, 1440)),
                    quota_used=1
                )
                db.add(api_call)
        
        # 2. Créer des deals simulés
        print("💎 Création de deals simulés...")
        
        # Supprimer les anciens deals
        db.query(Deal).delete()
        
        deal_templates = [
            {"origin": "CDG", "destination": "JFK", "price": 299, "normal": 599, "airline": "AF"},
            {"origin": "CDG", "destination": "BCN", "price": 89, "normal": 189, "airline": "VY"},
            {"origin": "CDG", "destination": "MAD", "price": 95, "normal": 205, "airline": "IB"},
            {"origin": "CDG", "destination": "FCO", "price": 120, "normal": 250, "airline": "AZ"},
            {"origin": "CDG", "destination": "AMS", "price": 110, "normal": 220, "airline": "KL"},
            {"origin": "CDG", "destination": "BKK", "price": 450, "normal": 850, "airline": "TG"},
            {"origin": "CDG", "destination": "DXB", "price": 380, "normal": 680, "airline": "EK"},
            {"origin": "CDG", "destination": "LHR", "price": 85, "normal": 165, "airline": "BA"},
        ]
        
        for i, template in enumerate(deal_templates):
            route = db.query(Route).filter(
                Route.origin == template["origin"],
                Route.destination == template["destination"]
            ).first()
            
            if route:
                # Créer price history
                price_history = PriceHistory(
                    route_id=route.id,
                    airline=template["airline"],
                    price=template["price"],
                    currency="EUR",
                    departure_date=datetime.now() + timedelta(days=random.randint(30, 90)),
                    scanned_at=datetime.now()
                )
                db.add(price_history)
                db.flush()
                
                # Créer deal
                discount = ((template["normal"] - template["price"]) / template["normal"]) * 100
                
                deal = Deal(
                    route_id=route.id,
                    price_history_id=price_history.id,
                    normal_price=template["normal"],
                    deal_price=template["price"],
                    discount_percentage=discount,
                    anomaly_score=random.uniform(0.6, 0.9),
                    confidence_score=random.randint(70, 95),
                    expires_at=datetime.now() + timedelta(hours=random.randint(6, 48)),
                    is_active=True,
                    airline=template["airline"],
                    currency="EUR",
                    departure_date=datetime.now() + timedelta(days=random.randint(30, 90)),
                    flight_number=f"{template['airline']}{random.randint(1000, 9999)}",
                    booking_class="Economy",
                    detected_at=datetime.now() - timedelta(hours=random.randint(1, 24))
                )
                db.add(deal)
        
        db.commit()
        
        # 3. Vérifications
        total_api_calls = db.query(ApiCall).count()
        total_deals = db.query(Deal).filter(Deal.is_active == True).count()
        calls_today = db.query(ApiCall).filter(
            ApiCall.timestamp >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        print(f"\n✅ MODE DÉVELOPPEMENT ACTIVÉ:")
        print(f"   • Appels API simulés: {total_api_calls}")
        print(f"   • Appels aujourd'hui: {calls_today}")
        print(f"   • Deals actifs: {total_deals}")
        print(f"   • Status: SIMULATION ACTIVE")
        
        # 4. Créer un fichier marqueur
        with open("DEV_MODE_ACTIVE.txt", "w") as f:
            f.write(f"Mode développement activé le {datetime.now()}\n")
            f.write("Données simulées - Aucun appel API réel\n")
        
        print(f"\n🎯 VOUS POUVEZ MAINTENANT:")
        print(f"   • Tester l'admin dashboard")
        print(f"   • Voir les métriques en temps réel")
        print(f"   • Développer de nouvelles fonctionnalités")
        print(f"   • Valider l'interface utilisateur")
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de l'activation du mode dev: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def create_protection_file():
    """Créer un fichier de protection contre les appels API"""
    
    protection_content = """# PROTECTION API - NE PAS SUPPRIMER
# Ce fichier protège contre les appels API accidentels
API_PROTECTION_ENABLED=true
QUOTA_EXHAUSTED=true
DEV_MODE=true
"""
    
    with open(".env.protection", "w") as f:
        f.write(protection_content)
    
    print("🛡️  Fichier de protection créé (.env.protection)")

if __name__ == "__main__":
    print("🚨 QUOTA API ÉPUISÉ - ACTIVATION MODE DÉVELOPPEMENT")
    print("=" * 55)
    
    success = create_mock_api_activity()
    create_protection_file()
    
    if success:
        print("\n🎊 MODE DÉVELOPPEMENT ACTIVÉ AVEC SUCCÈS!")
        print("Vous pouvez maintenant continuer vos tests sans appels API réels.")
    else:
        print("\n❌ Échec de l'activation du mode développement")
    
    sys.exit(0 if success else 1)
