#!/usr/bin/env python3
"""Simple check of database status"""

import sqlite3
import sys
from datetime import datetime

def check_database():
    try:
        # Connexion à la base de données
        conn = sqlite3.connect('globegenius.db')
        cursor = conn.cursor()
        
        print("🔍 GLOBE GENIUS - VÉRIFICATION RAPIDE")
        print("=" * 50)
        
        # Vérifier les tables existantes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📊 Tables trouvées: {', '.join(tables)}")
        
        # Vérifier les routes
        if 'routes' in tables:
            cursor.execute("SELECT COUNT(*) FROM routes")
            total_routes = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM routes WHERE is_active = 1")
            active_routes = cursor.fetchone()[0]
            
            print(f"\n🛣️  ROUTES:")
            print(f"   • Total: {total_routes}")
            print(f"   • Actives: {active_routes}")
            
            # Par tier
            for tier in [1, 2, 3]:
                cursor.execute("SELECT COUNT(*) FROM routes WHERE tier = ? AND is_active = 1", (tier,))
                count = cursor.fetchone()[0]
                interval = {1: '2h', 2: '4h', 3: '6h'}[tier]
                print(f"   • Tier {tier} ({interval}): {count} routes")
        
        # Vérifier les deals
        if 'deals' in tables:
            cursor.execute("SELECT COUNT(*) FROM deals")
            total_deals = cursor.fetchone()[0]
            print(f"\n💰 DEALS:")
            print(f"   • Total: {total_deals}")
            
            if total_deals > 0:
                cursor.execute("""
                    SELECT d.deal_price, d.normal_price, d.discount_percentage, 
                           r.origin, r.destination, d.created_at
                    FROM deals d
                    JOIN routes r ON d.route_id = r.id
                    ORDER BY d.created_at DESC
                    LIMIT 3
                """)
                recent_deals = cursor.fetchall()
                print(f"   • Derniers deals:")
                for deal in recent_deals:
                    price, normal, discount, origin, dest, created = deal
                    print(f"     - {origin}→{dest}: {price}€ (-{discount:.1f}%) | {created[:10]}")
        
        # Vérifier les utilisateurs
        if 'users' in tables:
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
            active_users = cursor.fetchone()[0]
            
            print(f"\n👥 UTILISATEURS:")
            print(f"   • Total: {total_users}")
            print(f"   • Actifs: {active_users}")
        
        conn.close()
        
        print(f"\n✅ Vérification terminée - {datetime.now().strftime('%H:%M:%S')}")
        
    except sqlite3.Error as e:
        print(f"❌ Erreur base de données: {e}")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    check_database()
