#!/usr/bin/env python3

import sqlite3
from datetime import datetime

print("🔍 GLOBE GENIUS - STATUT SYSTÈME")
print("=" * 40)
print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

try:
    # Connexion DB
    conn = sqlite3.connect('globegenius.db')
    cursor = conn.cursor()
    
    # Routes
    cursor.execute("SELECT COUNT(*) FROM routes WHERE is_active = 1")
    active_routes = cursor.fetchone()[0]
    print(f"🛣️  Routes actives: {active_routes}")
    
    # Par tier
    for tier in [1, 2, 3]:
        cursor.execute("SELECT COUNT(*) FROM routes WHERE tier = ? AND is_active = 1", (tier,))
        count = cursor.fetchone()[0]
        freq = {1: "2h", 2: "4h", 3: "6h"}[tier]
        calls = count * {1: 12, 2: 6, 3: 4}[tier]
        print(f"   Tier {tier} ({freq}): {count} routes = {calls} appels/jour")
    
    # Quota total
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN tier = 1 THEN 12 ELSE 0 END) +
            SUM(CASE WHEN tier = 2 THEN 6 ELSE 0 END) +
            SUM(CASE WHEN tier = 3 THEN 4 ELSE 0 END)
        FROM routes WHERE is_active = 1
    """)
    daily_calls = cursor.fetchone()[0] or 0
    monthly_calls = daily_calls * 30
    quota_percent = (monthly_calls / 10000) * 100
    
    print(f"\n💰 QUOTA API:")
    print(f"   Appels/jour: {daily_calls}")
    print(f"   Appels/mois: {monthly_calls}")
    print(f"   Utilisation: {quota_percent:.1f}%")
    
    # Deals
    cursor.execute("SELECT COUNT(*) FROM deals")
    total_deals = cursor.fetchone()[0]
    print(f"\n💎 Deals: {total_deals}")
    
    # Utilisateurs
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
    active_users = cursor.fetchone()[0]
    print(f"👥 Utilisateurs actifs: {active_users}")
    
    conn.close()
    print(f"\n✅ Système configuré et prêt!")
    
except Exception as e:
    print(f"❌ Erreur: {e}")

print(f"\n📧 EXEMPLE D'ALERTE:")
print("Subject: 🎯 Deal trouvé: Paris → Madrid -67%")
print("To: user@example.com")
print("---")
print("🎉 Excellent deal détecté!")
print("")
print("✈️  Paris (CDG) → Madrid (MAD)")
print("💰 Prix: 115€ (au lieu de 350€)")
print("💸 Économie: 235€ (-67.1%)")
print("🏢 Compagnie: Ryanair")
print("📅 Départ: 15 août 2025")
print("🔄 Retour: 22 août 2025")
print("⏰ Expire: 10 juillet 2025 à 18h00")
print("")
print("🔗 [Lien pour réserver]")
print("---")
print("Cordialement, L'équipe GlobeGenius")
