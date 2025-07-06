#!/usr/bin/env python3
"""
Script to reset the database with new schema including password reset fields
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, Base
from app.models.user import User
from app.models.alert import Alert, AlertPreference
from app.models.flight import Route, Deal
from app.core.security import get_password_hash
from sqlalchemy.orm import sessionmaker

def reset_database():
    """Reset database and create tables with new schema"""
    try:
        print("🔄 Resetting database...")
        
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        print("✅ Dropped all tables")
        
        # Create all tables with new schema
        Base.metadata.create_all(bind=engine)
        print("✅ Created all tables with new schema")
        
        # Create session
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        # Create test users
        test_users = [
            {
                "email": "admin@globegenius.com",
                "password": "admin2024",
                "first_name": "Admin",
                "last_name": "User",
                "is_verified": True,
                "onboarding_completed": True
            },
            {
                "email": "test@example.com", 
                "password": "test1234",
                "first_name": "Test",
                "last_name": "User",
                "is_verified": True,
                "onboarding_completed": False
            }
        ]
        
        for user_data in test_users:
            existing_user = db.query(User).filter(User.email == user_data["email"]).first()
            if not existing_user:
                user = User(
                    email=user_data["email"],
                    hashed_password=get_password_hash(user_data["password"]),
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    is_verified=user_data["is_verified"],
                    onboarding_completed=user_data["onboarding_completed"]
                )
                db.add(user)
        
        # Create test routes
        test_routes = [
            {"origin": "CDG", "destination": "JFK", "origin_city": "Paris", "destination_city": "New York"},
            {"origin": "LHR", "destination": "LAX", "origin_city": "London", "destination_city": "Los Angeles"},
            {"origin": "FRA", "destination": "NRT", "origin_city": "Frankfurt", "destination_city": "Tokyo"}
        ]
        
        for route_data in test_routes:
            existing_route = db.query(Route).filter(
                Route.origin == route_data["origin"],
                Route.destination == route_data["destination"]
            ).first()
            if not existing_route:
                route = Route(**route_data)
                db.add(route)
        
        db.commit()
        db.close()
        
        print("✅ Database reset complete with test data")
        print("\nTest users created:")
        for user in test_users:
            print(f"  - {user['email']} / {user['password']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error resetting database: {str(e)}")
        return False

if __name__ == "__main__":
    success = reset_database()
    sys.exit(0 if success else 1)
