# backend/init_db.py
#!/usr/bin/env python3
"""Initialize database with routes and sample data for GlobeGenius"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from app.core.database import SessionLocal, engine, Base
from app.models.user import User, UserTier
from app.models.flight import Route, PriceHistory, Deal
from app.models.alert import AlertPreference
from app.core.security import get_password_hash
from app.utils.logger import logger


def init_database():
    """Initialize database with routes and sample data"""
    
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if already initialized
        existing_routes = db.query(Route).count()
        if existing_routes > 0:
            logger.info(f"Database already initialized with {existing_routes} routes")
            return
        
        logger.info("Initializing routes...")
        
        # TIER 1 - Ultra Priority Routes (20 routes) - Every 2 hours
        tier1_routes = [
            # From Paris CDG/ORY (12 routes)
            ("CDG", "MAD", 1),  # Paris → Madrid
            ("CDG", "BCN", 1),  # Paris → Barcelona
            ("CDG", "LHR", 1),  # Paris → London
            ("CDG", "FCO", 1),  # Paris → Rome (FCO)
            ("CDG", "AMS", 1),  # Paris → Amsterdam
            ("CDG", "JFK", 1),  # Paris → New York JFK
            ("CDG", "MXP", 1),  # Paris → Milan
            ("CDG", "LIS", 1),  # Paris → Lisbon
            ("CDG", "BER", 1),  # Paris → Berlin
            ("CDG", "CPH", 1),  # Paris → Copenhagen
            ("CDG", "ZRH", 1),  # Paris → Zurich
            ("CDG", "DUB", 1),  # Paris → Dublin
            
            # French Domestic Routes (8 routes)
            ("CDG", "NCE", 1),  # Paris → Nice
            ("CDG", "TLS", 1),  # Paris → Toulouse
            ("CDG", "MRS", 1),  # Paris → Marseille
            ("CDG", "BOD", 1),  # Paris → Bordeaux
            ("CDG", "LYS", 1),  # Paris → Lyon
            ("CDG", "NTE", 1),  # Paris → Nantes
            ("CDG", "MPL", 1),  # Paris → Montpellier
            ("CDG", "LIL", 1),  # Paris → Lille
        ]
        
        # TIER 2 - Priority Routes (25 routes) - Every 4 hours
        tier2_routes = [
            # From Lyon (5 routes)
            ("LYS", "MAD", 2),  # Lyon → Madrid
            ("LYS", "BCN", 2),  # Lyon → Barcelona
            ("LYS", "LHR", 2),  # Lyon → London
            ("LYS", "AMS", 2),  # Lyon → Amsterdam
            ("LYS", "FCO", 2),  # Lyon → Rome
            
            # From Nice (5 routes)
            ("NCE", "CDG", 2),  # Nice → Paris
            ("NCE", "LHR", 2),  # Nice → London
            ("NCE", "MAD", 2),  # Nice → Madrid
            ("NCE", "MXP", 2),  # Nice → Milan
            ("NCE", "FCO", 2),  # Nice → Rome
            
            # From Marseille (5 routes)
            ("MRS", "MAD", 2),  # Marseille → Madrid
            ("MRS", "BCN", 2),  # Marseille → Barcelona
            ("MRS", "LHR", 2),  # Marseille → London
            ("MRS", "AMS", 2),  # Marseille → Amsterdam
            ("MRS", "FCO", 2),  # Marseille → Rome
            
            # Long-Haul Strategic (5 routes)
            ("CDG", "LAX", 2),  # Paris → Los Angeles
            ("CDG", "NRT", 2),  # Paris → Tokyo
            ("CDG", "CMN", 2),  # Paris → Casablanca
            ("CDG", "ALG", 2),  # Paris → Algiers
            ("CDG", "DXB", 2),  # Paris → Dubai
            
            # European Secondary (5 routes)
            ("CDG", "PRG", 2),  # Paris → Prague
            ("CDG", "VIE", 2),  # Paris → Vienna
            ("CDG", "ARN", 2),  # Paris → Stockholm
            ("CDG", "HEL", 2),  # Paris → Helsinki
            ("CDG", "ATH", 2),  # Paris → Athens
        ]
        
        # TIER 3 - Complementary Routes (15 routes) - Every 6-8 hours
        tier3_routes = [
            # From Bordeaux (3 routes)
            ("BOD", "MAD", 3),  # Bordeaux → Madrid
            ("BOD", "LHR", 3),  # Bordeaux → London
            ("BOD", "AMS", 3),  # Bordeaux → Amsterdam
            
            # From Toulouse (3 routes)
            ("TLS", "MAD", 3),  # Toulouse → Madrid
            ("TLS", "LHR", 3),  # Toulouse → London
            ("TLS", "FCO", 3),  # Toulouse → Rome
            
            # Specialized Destinations (9 routes)
            ("CDG", "RAK", 3),  # Paris → Marrakech
            ("CDG", "TUN", 3),  # Paris → Tunis
            ("CDG", "IST", 3),  # Paris → Istanbul
            ("CDG", "TLV", 3),  # Paris → Tel Aviv
            ("CDG", "YUL", 3),  # Paris → Montreal
            ("CDG", "GRU", 3),  # Paris → São Paulo
            ("CDG", "MRU", 3),  # Paris → Mauritius
            ("CDG", "FDF", 3),  # Paris → Martinique
            ("CDG", "BKK", 3),  # Paris → Bangkok
        ]
        
        # Insert all routes
        all_routes = tier1_routes + tier2_routes + tier3_routes
        
        for origin, destination, tier in all_routes:
            # Set scan interval based on tier
            scan_interval = {1: 2, 2: 4, 3: 6}[tier]
            
            route = Route(
                origin=origin,
                destination=destination,
                tier=tier,
                scan_interval_hours=scan_interval,
                is_active=True
            )
            db.add(route)
        
        db.commit()
        logger.info(f"Successfully added {len(all_routes)} routes")
        
        # Create sample admin user
        logger.info("Creating sample admin user...")
        admin_user = User(
            email="admin@globegenius.com",
            hashed_password=get_password_hash("globegenius2024"),
            first_name="Admin",
            last_name="GlobeGenius",
            tier=UserTier.PREMIUM_PLUS,
            is_active=True,
            is_verified=True,
            onboarding_completed=True,
            home_airports=["CDG", "ORY"],
            favorite_destinations=["NYC", "BKK", "TOK", "BCN"],
            travel_types=["leisure", "business"]
        )
        db.add(admin_user)
        db.commit()
        
        # Create alert preferences for admin
        alert_pref = AlertPreference(
            user_id=admin_user.id,
            min_discount_percentage=30.0,
            max_price_europe=200.0,
            max_price_international=800.0,
            max_alerts_per_week=10
        )
        db.add(alert_pref)
        
        # Create some sample price history and deals
        logger.info("Creating sample price history and deals...")
        
        # Get some routes for sample data
        sample_routes = db.query(Route).filter(Route.tier == 1).limit(5).all()
        
        for route in sample_routes:
            # Create price history
            base_price = {
                ("CDG", "NCE"): 150,
                ("CDG", "MAD"): 180,
                ("CDG", "BCN"): 160,
                ("CDG", "JFK"): 650,
                ("CDG", "BKK"): 850,
            }.get((route.origin, route.destination), 200)
            
            # Generate historical prices
            for days_ago in range(30, 0, -1):
                # Random variation
                variation = 1 + (0.3 * (days_ago % 7 - 3) / 10)
                historical_price = base_price * variation
                
                price_history = PriceHistory(
                    route_id=route.id,
                    airline="Air France",
                    price=historical_price,
                    currency="EUR",
                    departure_date=datetime.now() + timedelta(days=30),
                    scanned_at=datetime.now() - timedelta(days=days_ago)
                )
                db.add(price_history)
            
            # Create a sample deal
            if route.destination in ["MAD", "BCN", "JFK"]:
                deal_price = base_price * 0.4  # 60% off
                normal_price = base_price
                
                latest_price_history = PriceHistory(
                    route_id=route.id,
                    airline="Iberia" if route.destination == "MAD" else "Air France",
                    price=deal_price,
                    currency="EUR",
                    departure_date=datetime.now() + timedelta(days=45),
                    scanned_at=datetime.now()
                )
                db.add(latest_price_history)
                db.flush()
                
                deal = Deal(
                    route_id=route.id,
                    price_history_id=latest_price_history.id,
                    normal_price=normal_price,
                    deal_price=deal_price,
                    discount_percentage=60,
                    anomaly_score=0.85,
                    is_error_fare=True if route.destination == "JFK" else False,
                    confidence_score=85,
                    expires_at=datetime.now() + timedelta(hours=24),
                    is_active=True
                )
                db.add(deal)
        
        db.commit()
        
        logger.info("Database initialization complete!")
        logger.info("Admin credentials: admin@globegenius.com / globegenius2024")
        
        # Print summary
        total_routes = db.query(Route).count()
        total_deals = db.query(Deal).count()
        
        logger.info(f"""
        Summary:
        - Total routes: {total_routes}
        - Tier 1 routes: {len(tier1_routes)}
        - Tier 2 routes: {len(tier2_routes)}
        - Tier 3 routes: {len(tier3_routes)}
        - Active deals: {total_deals}
        """)
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_database()