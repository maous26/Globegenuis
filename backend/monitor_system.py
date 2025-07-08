#!/usr/bin/env python3
"""
Monitoring script to verify API calls and alerts
Standalone script without FastAPI dependencies
"""

import sqlite3
import json
from datetime import datetime, timedelta
import requests
import os

class GlobeGeniusMonitor:
    def __init__(self, db_path="globegenius.db"):
        self.db_path = db_path
        
    def get_db_connection(self):
        return sqlite3.connect(self.db_path)
    
    def check_routes_status(self):
        """Check current routes configuration"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        print("🛣️  ÉTAT DES ROUTES:")
        print("=" * 50)
        
        # Total routes
        cursor.execute("SELECT COUNT(*) FROM routes WHERE is_active = 1")
        active_routes = cursor.fetchone()[0]
        
        # Routes par tier
        tier_stats = {}
        for tier in [1, 2, 3]:
            cursor.execute("SELECT COUNT(*) FROM routes WHERE tier = ? AND is_active = 1", (tier,))
            tier_stats[tier] = cursor.fetchone()[0]
        
        print(f"📊 Routes actives: {active_routes}")
        print(f"   • Tier 1 (2h): {tier_stats[1]} routes")
        print(f"   • Tier 2 (4h): {tier_stats[2]} routes")
        print(f"   • Tier 3 (6h): {tier_stats[3]} routes")
        
        # Calcul utilisation API
        daily_calls = tier_stats[1] * 12 + tier_stats[2] * 6 + tier_stats[3] * 4
        monthly_calls = daily_calls * 30
        usage_percent = (monthly_calls / 10000) * 100
        
        print(f"\n💰 UTILISATION API:")
        print(f"   • Appels/jour: {daily_calls}")
        print(f"   • Appels/mois: {monthly_calls}")
        print(f"   • Quota utilisé: {usage_percent:.1f}%")
        
        # Top 10 routes
        cursor.execute("""
            SELECT origin, destination, tier, scan_interval_hours 
            FROM routes 
            WHERE is_active = 1 
            ORDER BY tier, origin
            LIMIT 10
        """)
        routes = cursor.fetchall()
        
        print(f"\n🔝 TOP 10 ROUTES:")
        for route in routes:
            origin, dest, tier, interval = route
            print(f"   • {origin}→{dest} (Tier {tier}, {interval}h)")
        
        conn.close()
        return {
            'active_routes': active_routes,
            'tier_stats': tier_stats,
            'daily_calls': daily_calls,
            'monthly_calls': monthly_calls,
            'usage_percent': usage_percent
        }
    
    def check_recent_deals(self, days=7):
        """Check recent deals found"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        print(f"\n💎 DEALS RÉCENTS ({days} derniers jours):")
        print("=" * 50)
        
        # Deals récents
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        cursor.execute("""
            SELECT COUNT(*) FROM deals 
            WHERE created_at >= ? AND is_active = 1
        """, (since_date,))
        recent_deals = cursor.fetchone()[0]
        
        print(f"📈 Deals trouvés: {recent_deals}")
        
        if recent_deals > 0:
            # Derniers deals
            cursor.execute("""
                SELECT d.deal_price, d.normal_price, d.discount_percentage, 
                       r.origin, r.destination, d.created_at, d.expires_at
                FROM deals d
                JOIN routes r ON d.route_id = r.id
                WHERE d.created_at >= ? AND d.is_active = 1
                ORDER BY d.created_at DESC
                LIMIT 5
            """, (since_date,))
            
            deals = cursor.fetchall()
            print(f"\n🎯 DERNIERS DEALS:")
            for deal in deals:
                price, normal, discount, origin, dest, created, expires = deal
                print(f"   • {origin}→{dest}: {price}€ (était {normal}€)")
                print(f"     Réduction: {discount:.1f}% | Créé: {created[:19]}")
        
        conn.close()
        return recent_deals
    
    def check_alerts_status(self):
        """Check alerts configuration and recent alerts"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        print(f"\n🔔 ÉTAT DES ALERTES:")
        print("=" * 50)
        
        # Vérifier si la table alerts existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='alerts'
        """)
        alerts_table_exists = cursor.fetchone() is not None
        
        if alerts_table_exists:
            # Alertes récentes
            cursor.execute("SELECT COUNT(*) FROM alerts")
            total_alerts = cursor.fetchone()[0]
            
            since_date = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute("SELECT COUNT(*) FROM alerts WHERE created_at >= ?", (since_date,))
            recent_alerts = cursor.fetchone()[0]
            
            print(f"📊 Total alertes: {total_alerts}")
            print(f"📊 Alertes récentes (7j): {recent_alerts}")
            
            if recent_alerts > 0:
                cursor.execute("""
                    SELECT a.created_at, u.email, a.is_sent
                    FROM alerts a
                    JOIN users u ON a.user_id = u.id
                    WHERE a.created_at >= ?
                    ORDER BY a.created_at DESC
                    LIMIT 5
                """, (since_date,))
                
                alerts = cursor.fetchall()
                print(f"\n📬 DERNIÈRES ALERTES:")
                for alert in alerts:
                    created, email, is_sent = alert
                    status = "✅ Envoyée" if is_sent else "⏳ En attente"
                    print(f"   • {email}: {status} | {created[:19]}")
        else:
            print("⚠️  Table alerts n'existe pas encore")
        
        conn.close()
        return alerts_table_exists
    
    def check_users_status(self):
        """Check users and their preferences"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        print(f"\n👥 UTILISATEURS:")
        print("=" * 50)
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
        active_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
        admin_users = cursor.fetchone()[0]
        
        print(f"📊 Total utilisateurs: {total_users}")
        print(f"📊 Utilisateurs actifs: {active_users}")
        print(f"📊 Administrateurs: {admin_users}")
        
        # Dernières connexions
        cursor.execute("""
            SELECT email, last_login_at, tier
            FROM users 
            WHERE last_login_at IS NOT NULL
            ORDER BY last_login_at DESC
            LIMIT 5
        """)
        
        recent_logins = cursor.fetchall()
        if recent_logins:
            print(f"\n🚪 DERNIÈRES CONNEXIONS:")
            for login in recent_logins:
                email, last_login, tier = login
                last_login_str = last_login[:19] if last_login else "Jamais"
                print(f"   • {email} (Tier {tier}): {last_login_str}")
        
        conn.close()
        return {
            'total_users': total_users,
            'active_users': active_users,
            'admin_users': admin_users
        }
    
    def test_api_connectivity(self):
        """Test if APIs are reachable"""
        print(f"\n🌐 TEST CONNECTIVITÉ API:")
        print("=" * 50)
        
        # Test API locale
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ API locale (FastAPI): OK")
            else:
                print(f"⚠️  API locale: Status {response.status_code}")
        except:
            print("❌ API locale: Non accessible")
        
        # Test API frontend
        try:
            response = requests.get("http://localhost:3000", timeout=5)
            if response.status_code == 200:
                print("✅ Frontend React: OK")
            else:
                print(f"⚠️  Frontend React: Status {response.status_code}")
        except:
            print("❌ Frontend React: Non accessible")
    
    def generate_sample_alert(self):
        """Show what a typical alert looks like"""
        print(f"\n📧 EXEMPLE D'ALERTE:")
        print("=" * 50)
        
        sample_alert = {
            "subject": "🎯 Deal trouvé: Paris → Madrid -67%",
            "recipient": "user@example.com",
            "deal": {
                "origin": "CDG",
                "destination": "MAD", 
                "normal_price": 350.00,
                "deal_price": 115.00,
                "discount_percentage": 67.1,
                "savings": 235.00,
                "airline": "Ryanair",
                "departure_date": "2025-08-15",
                "return_date": "2025-08-22",
                "expires_at": "2025-07-10 18:00:00"
            },
            "message": """
🎉 Excellent deal détecté !

✈️  Paris (CDG) → Madrid (MAD)
💰 Prix: 115€ (au lieu de 350€)
💸 Économie: 235€ (-67.1%)
🏢 Compagnie: Ryanair
📅 Départ: 15 août 2025
🔄 Retour: 22 août 2025
⏰ Expire: 10 juillet 2025 à 18h00

🔗 Réserver maintenant: [Lien vers booking]
            """
        }
        
        print(f"📧 Sujet: {sample_alert['subject']}")
        print(f"📤 Destinataire: {sample_alert['recipient']}")
        print(f"💌 Message:{sample_alert['message']}")
        
        return sample_alert
    
    def run_full_monitoring(self):
        """Run complete monitoring check"""
        print("🔍 GLOBE GENIUS - MONITORING COMPLET")
        print("=" * 60)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Vérifications
        routes_status = self.check_routes_status()
        deals_count = self.check_recent_deals()
        alerts_exist = self.check_alerts_status()
        users_status = self.check_users_status()
        self.test_api_connectivity()
        self.generate_sample_alert()
        
        # Résumé
        print(f"\n📋 RÉSUMÉ:")
        print("=" * 50)
        print(f"✅ Routes configurées: {routes_status['active_routes']}")
        print(f"📊 Utilisation API: {routes_status['usage_percent']:.1f}%")
        print(f"💎 Deals récents: {deals_count}")
        print(f"👥 Utilisateurs actifs: {users_status['active_users']}")
        print(f"🔔 Système d'alertes: {'✅ Configuré' if alerts_exist else '⚠️  Non configuré'}")
        
        return {
            'routes': routes_status,
            'deals': deals_count,
            'users': users_status,
            'alerts_configured': alerts_exist
        }

if __name__ == "__main__":
    monitor = GlobeGeniusMonitor()
    monitor.run_full_monitoring()
