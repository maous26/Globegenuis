#!/usr/bin/env python3

"""
Create admin_settings table in the database
"""

import sqlite3
import sys
import os

def create_admin_settings_table():
    # Path to the database
    db_path = "/Users/moussa/globegenius/backend/globegenius.db"
    
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create admin_settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                monitoring_email VARCHAR DEFAULT 'admin@globegenius.app',
                alert_notifications BOOLEAN DEFAULT 1,
                daily_reports BOOLEAN DEFAULT 1,
                api_quota_alerts BOOLEAN DEFAULT 1,
                deal_alerts BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME
            )
        ''')
        
        # Insert default settings if none exist
        cursor.execute('SELECT COUNT(*) FROM admin_settings')
        count = cursor.fetchone()[0]
        
        if count == 0:
            cursor.execute('''
                INSERT INTO admin_settings (
                    monitoring_email, 
                    alert_notifications, 
                    daily_reports, 
                    api_quota_alerts, 
                    deal_alerts
                ) VALUES (?, ?, ?, ?, ?)
            ''', ('admin@globegenius.app', True, True, True, True))
            print("✅ Default admin settings created")
        else:
            print("✅ Admin settings table already exists with data")
        
        conn.commit()
        conn.close()
        
        print("✅ Admin settings table created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin settings table: {e}")
        return False

if __name__ == "__main__":
    success = create_admin_settings_table()
    if success:
        print("🎉 Database setup complete!")
    else:
        print("❌ Database setup failed!")
        sys.exit(1)