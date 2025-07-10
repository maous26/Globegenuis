#!/usr/bin/env python3
"""
Script pour créer de l'activité API et tester le système de monitoring
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from app.core.database import SessionLocal
from app.models.api_tracking import ApiCall
from app.models.flight import Route
from app.utils.logger import logger
import random

def create_api_activity():
    """Créer de l'activité API factice pour tester le monitoring"""
    
    db = SessionLocal()
    
    try:
        # Obtenir quelques routes actives
        routes = db.query(Route).filter(Route.is_active == True).limit(10).all()
        
        if not routes:
            print("❌ Aucune route active trouvée")
            return False
        
        print(f"🚀 Création d'activité API pour {len(routes)} routes...")
        
        # Créer des appels API factices pour aujourd'hui
        for i in range(20):  # 20 appels API
            route = random.choice(routes)
            
            api_call = ApiCall(
                route_id=route.id,
                endpoint="aviationstack",
                method="GET",
                status_code=200,
                response_time=random.uniform(0.5, 2.0),
                created_at=datetime.now(),
                quota_used=1
            )
            
            db.add(api_call)
            
            print(f"✅ Appel API créé pour {route.origin}→{route.destination}")
        
        db.commit()
        
        # Vérifier le total
        total_calls_today = db.query(ApiCall).filter(
            ApiCall.created_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        print(f"\n📊 RÉSULTATS:")
        print(f"Appels API créés: 20")
        print(f"Total appels aujourd'hui: {total_calls_today}")
        print(f"✅ Activité API créée avec succès!")
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de la création d'activité API: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def test_scan_functionality():
    """Tester la fonctionnalité de scan directement"""
    
    print("\n🔍 Test de la fonctionnalité de scan...")
    
    # Import direct de la fonction de scan
    try:
        from app.tasks.flight_tasks import scan_tier_routes
        
        # Appel direct sans Celery
        print("Exécution d'un scan TIER 3 en mode direct...")
        result = scan_tier_routes(3)
        print(f"Résultat du scan: {result}")
        
        return True
    except Exception as e:
        print(f"❌ Erreur lors du test de scan: {e}")
        return False

if __name__ == "__main__":
    print("🎯 TEST D'ACTIVITÉ API GLOBEGENIUS")
    print("=" * 40)
    
    # Créer de l'activité API
    activity_success = create_api_activity()
    
    # Tester le scan
    scan_success = test_scan_functionality()
    
    if activity_success:
        print("\n🎊 Test d'activité API réussi!")
        print("Vérifiez maintenant l'admin dashboard pour voir l'activité.")
    else:
        print("\n❌ Échec du test d'activité API")
    
    sys.exit(0 if activity_success else 1)
