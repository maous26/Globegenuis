#!/usr/bin/env python3

"""
Create sample deals in the database for testing the admin dashboard
"""

import sqlite3
import sys
import os
from datetime import datetime, timedelta
import random

def create_sample_deals():
    # Path to the database
    db_path = "/Users/moussa/globegenius/backend/globegenius.db"
    
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get some route IDs
        cursor.execute('SELECT id, origin, destination, tier FROM routes LIMIT 10')
        routes = cursor.fetchall()
        
        if not routes:
            print("No routes found in database")
            return False
        
        print(f"Found {len(routes)} routes to create deals for")
        
        # Create sample deals
        deals_created = 0
        
        for route in routes:
            route_id, origin, destination, tier = route
            
            # Create 1-3 deals per route
            num_deals = random.randint(1, 3)
            
            for i in range(num_deals):
                # Generate realistic deal data
                original_price = random.randint(150, 800)
                discount_percent = random.randint(15, 60)
                deal_price = original_price * (1 - discount_percent / 100)
                
                departure_date = datetime.now() + timedelta(days=random.randint(7, 60))
                return_date = departure_date + timedelta(days=random.randint(2, 14))
                detected_at = datetime.now() - timedelta(hours=random.randint(1, 48))
                expires_at = detected_at + timedelta(days=random.randint(1, 7))
                
                airlines = ['Air France', 'KLM', 'Lufthansa', 'British Airways', 'Ryanair', 'EasyJet']
                airline = random.choice(airlines)
                
                deal_types = ['flash_sale', 'early_bird', 'last_minute', 'weekend_special']
                deal_type = random.choice(deal_types)
                
                cursor.execute('''
                    INSERT INTO deals (
                        route_id, deal_price, original_price, departure_date, 
                        return_date, detected_at, expires_at, is_active, 
                        booking_url, deal_type, airline, currency
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    route_id,
                    round(deal_price, 2),
                    round(original_price, 2),
                    departure_date.isoformat(),
                    return_date.isoformat(),
                    detected_at.isoformat(),
                    expires_at.isoformat(),
                    True,
                    f"https://booking.example.com/deal/{route_id}-{i}",
                    deal_type,
                    airline,
                    'EUR'
                ))
                
                deals_created += 1
        
        conn.commit()
        conn.close()
        
        print(f"✅ Created {deals_created} sample deals successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating sample deals: {e}")
        return False

if __name__ == "__main__":
    success = create_sample_deals()
    if success:
        print("🎉 Sample deals created successfully!")
    else:
        print("❌ Failed to create sample deals!")
        sys.exit(1)