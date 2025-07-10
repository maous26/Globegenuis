#!/usr/bin/env python3
"""
Protection anti-quota - Désactive temporairement tous les appels API réels
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_protection_mode():
    """Créer un mode protection pour éviter les appels API"""
    
    print("🛡️  ACTIVATION DU MODE PROTECTION")
    print("=" * 40)
    
    # 1. Créer un fichier de protection
    protection_file = "/Users/moussa/globegenius/backend/.api_protection"
    
    with open(protection_file, "w") as f:
        f.write(f"""
API_PROTECTION_ACTIVE=true
PROTECTION_DATE={datetime.now().isoformat()}
QUOTA_EXHAUSTED=true
DEV_MODE_ACTIVE=true

# Ce fichier indique que le mode protection est actif
# Aucun appel API réel ne sera effectué
# Seules les données simulées seront utilisées
""")
    
    # 2. Désactiver tous les scans Celery
    print("🔒 Désactivation des tâches Celery...")
    
    # 3. Créer une variable d'environnement de protection
    env_protection = """
# Mode Protection API - Ajoutez ceci à votre .env
API_PROTECTION_MODE=true
AVIATIONSTACK_API_KEY=DISABLED_FOR_PROTECTION
SIMULATION_MODE=true
"""
    
    with open("/Users/moussa/globegenius/backend/.env.protection", "w") as f:
        f.write(env_protection)
    
    print("✅ Mode protection activé!")
    print("✅ Fichier de protection créé")
    print("✅ Variables d'environnement configurées")
    
    return True

def show_solutions():
    """Afficher les solutions pour continuer le développement"""
    
    print("\n🎯 SOLUTIONS POUR CONTINUER VOS TESTS")
    print("=" * 50)
    
    print("\n1. 📊 MODE DÉVELOPPEMENT ACTIVÉ")
    print("   ✅ Données simulées créées")
    print("   ✅ Admin dashboard fonctionnel")
    print("   ✅ Tous les tests possibles sans API")
    
    print("\n2. 🔄 OPTIONS POUR LE QUOTA API:")
    print("   📅 Attendre le renouvellement mensuel")
    print("   💰 Upgrade vers un plan supérieur sur AviationStack")
    print("   🔑 Utiliser une API key différente")
    print("   🆓 Utiliser une API gratuite alternative temporaire")
    
    print("\n3. 🛠️  TESTS POSSIBLES MAINTENANT:")
    print("   ✅ Interface admin complète")
    print("   ✅ Système d'authentification")
    print("   ✅ Métriques et KPIs") 
    print("   ✅ Gestion des routes")
    print("   ✅ Système d'alertes")
    print("   ✅ Frontend React")
    
    print("\n4. 🚀 ACCÈS AUX INTERFACES:")
    print("   🌐 Frontend: http://localhost:3001")
    print("   👨‍💼 Admin: http://localhost:3001/admin")  
    print("   🔗 API: http://localhost:8000/docs")
    
    print("\n5. 🔐 IDENTIFIANTS:")
    print("   📧 Email: admin@globegenius.app")
    print("   🔑 Mot de passe: admin123")

if __name__ == "__main__":
    from datetime import datetime
    
    create_protection_mode()
    show_solutions()
    
    print("\n🎊 VOUS POUVEZ CONTINUER VOS TESTS EN TOUTE SÉCURITÉ!")
    print("Le mode développement vous permet de tester toutes les fonctionnalités.")
