#!/usr/bin/env python3
"""Initialize database with routes and sample data"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine
from app.core.database import Base
from app.models import Route, User
from app.core.security import get_password_hash

# Create all tables
Base.metadata.create_all(bind=engine)

# Routes populaires à monitorer
ROUTES = [
    # Tier 1 - Routes très populaires (scan toutes les 2h)
    {"origin": "CDG", "destination": "JFK", "tier": 1},  # Paris - New York
    {"origin": "CDG", "destination": "LAX", "tier": 1},  # Paris - Los Angeles  
    {"origin": "CDG", "destination": "BKK", "tier": 1},  # Paris - Bangkok
    {"origin": "CDG", "destination": "DXB", "tier": 1},  # Paris - Dubai
    {"origin": "CDG", "destination": "SIN", "tier": 1},  # Paris - Singapore
    
    # Tier 2 - Routes populaires (scan toutes les 4h)
    {"origin": "CDG", "destination": "MIA", "tier": 2},  # Paris - Miami
    {"origin": "CDG", "destination": "CUN", "tier": 2},  # Paris - Cancun
    {"origin": "CDG", "destination": "NRT", "tier": 2},  # Paris - Tokyo
    {"origin": "CDG", "destination": "SYD", "tier": 2},  # Paris - Sydney
    {"origin": "CDG", "destination": "GRU", "tier": 2},  # Paris - Sao Paulo
    {"origin": "CDG", "destination": "JNB", "tier": 2},  # Paris - Johannesburg
    {"origin": "CDG", "destination": "DEL", "tier": 2},  # Paris - Delhi
    {"origin": "CDG", "destination": "PVG", "tier": 2},  # Paris - Shanghai
    
    # Europe depuis Paris (Tier 2)
    {"origin": "CDG", "destination": "BCN", "tier": 2},  # Paris - Barcelone
    {"origin": "CDG", "destination": "MAD", "tier": 2},  # Paris - Madrid
    {"origin": "CDG", "destination": "FCO", "tier": 2},  # Paris - Rome
    {"origin": "CDG", "destination": "LHR", "tier": 2},  # Paris - Londres
    {"origin": "CDG", "destination": "AMS", "tier": 2},  # Paris - Amsterdam
    {"origin": "CDG", "destination": "BER", "tier": 2},  # Paris - Berlin
    
    # Tier 3 - Routes moins fréquentes (scan toutes les 6h)
    {"origin": "CDG", "destination": "ICN", "tier": 3},  # Paris - Seoul
    {"origin": "CDG", "destination": "HND", "tier": 3},  # Paris - Tokyo Haneda
    {"origin": "CDG", "destination": "MEX", "tier": 3},  # Paris - Mexico
    {"origin": "CDG", "destination": "EZE", "tier": 3},  # Paris - Buenos Aires
    {"origin": "CDG", "destination": "CAI", "tier": 3},  # Paris - Cairo
    {"origin": "CDG", "destination": "IST", "tier": 3},  # Paris - Istanbul
    
    # Autres hubs français
    {"origin": "NCE", "destination": "JFK", "tier": 3},  # Nice - New York
    {"origin": "LYS", "destination": "DXB", "tier": 3},  # Lyon - Dubai
    {"origin": "MRS", "destination": "BKK", "tier": 3},  # Marseille - Bangkok
    
    # Routes domestiques France
    {"origin": "CDG", "destination": "NCE", "tier": 3},  # Paris - Nice
    {"origin": "CDG", "destination": "MRS", "tier": 3},  # Paris - Marseille
    {"origin": "CDG", "destination": "TLS", "tier": 3},  # Paris - Toulouse
]


def init_db():
    db = SessionLocal()
    
    try:
        # Ajouter les routes
        print("🛫 Ajout des routes...")
        routes_added = 0
        
        for route_data in ROUTES:
            # Vérifier si la route existe déjà
            existing = db.query(Route).filter(
                Route.origin == route_data["origin"],
                Route.destination == route_data["destination"]
            ).first()
            
            if not existing:
                route = Route(
                    origin=route_data["origin"],
                    destination=route_data["destination"],
                    tier=route_data["tier"],
                    scan_interval_hours=2 if route_data["tier"] == 1 else 
                                       4 if route_data["tier"] == 2 else 6
                )
                db.add(route)
                routes_added += 1
                print(f"  ✓ {route.origin} → {route.destination} (Tier {route.tier})")
        
        # Créer un utilisateur admin de test
        print("\n👤 Création utilisateur admin...")
        admin_user = db.query(User).filter(User.email == "admin@globegenius.com").first()
        
        if not admin_user:
            admin_user = User(
                email="admin@globegenius.com",
                hashed_password=get_password_hash("admin2024"),
                first_name="Admin",
                last_name="GlobeGenius",
                is_active=True,
                is_verified=True,
                onboarding_completed=True,
                home_airports=["CDG", "ORY"],
                favorite_destinations=["JFK", "BKK", "DXB"],
                travel_types=["business", "leisure"]
            )
            db.add(admin_user)
            print("  ✓ Admin créé (admin@globegenius.com / admin2024)")
        
        # Créer un utilisateur de test
        print("\n👤 Création utilisateur test...")
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        
        if not test_user:
            test_user = User(
                email="test@example.com",
                hashed_password=get_password_hash("test1234"),
                first_name="Test",
                last_name="User",
                is_active=True,
                is_verified=True,
                onboarding_completed=False,  # Pour tester l'onboarding
                home_airports=["CDG"],
                favorite_destinations=["NYC", "BCN"],
                travel_types=["leisure"]
            )
            db.add(test_user)
            print("  ✓ Utilisateur test créé (test@example.com / test1234)")
        
        db.commit()
        
        print(f"\n✅ Base de données initialisée avec succès!")
        print(f"   - {routes_added} nouvelles routes ajoutées")
        print(f"   - Total: {db.query(Route).count()} routes dans la base")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Initialisation de la base de données GlobeGenius...")
    init_db()