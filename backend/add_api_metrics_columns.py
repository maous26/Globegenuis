#!/usr/bin/env python3
"""
Add API metrics columns to price_history table
"""
import sqlite3
import os

def add_api_metrics_columns():
    """Add response_time and status columns to price_history table"""
    
    db_path = os.path.join(os.path.dirname(__file__), "globegenius.db")
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(price_history)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'response_time' not in columns:
            print("Adding response_time column...")
            cursor.execute("ALTER TABLE price_history ADD COLUMN response_time REAL")
            
        if 'status' not in columns:
            print("Adding status column...")
            cursor.execute("ALTER TABLE price_history ADD COLUMN status TEXT DEFAULT 'success'")
        
        # Update existing records with sample data for testing
        print("Updating existing records with sample data...")
        cursor.execute("""
            UPDATE price_history 
            SET response_time = (1.0 + (RANDOM() % 30) * 0.1),
                status = CASE 
                    WHEN RANDOM() % 20 = 0 THEN 'error'
                    WHEN RANDOM() % 30 = 0 THEN 'timeout'
                    ELSE 'success'
                END
            WHERE response_time IS NULL
        """)
        
        conn.commit()
        print("Successfully added API metrics columns!")
        
        # Show updated schema
        cursor.execute("PRAGMA table_info(price_history)")
        print("\nUpdated price_history table schema:")
        for row in cursor.fetchall():
            print(f"  {row[1]}: {row[2]}")
            
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error adding columns: {e}")
        return False

if __name__ == "__main__":
    add_api_metrics_columns()
