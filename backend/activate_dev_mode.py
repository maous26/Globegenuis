#!/usr/bin/env python3
"""
Mode développement - Simulateur API pour continuer les tests sans consommer le quota
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.api_tracking import ApiCall
from app.models.flight import Route, Deal, PriceHistory
from app.utils.logger import logger
import random

class MockAPISimulator:
    """Simulateur d'API pour tests sans consommer le quota"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def create_mock_api_activity(self, days_back=7):
        """Créer une activité API simulée sur plusieurs jours"""
        
        print("🎭 MODE DÉVELOPPEMENT - Simulation d'activité API")
        print("=" * 50)
        
        try:
            # Obtenir des routes actives
            routes = self.db.query(Route).filter(Route.is_active == True).limit(20).all()
            
            if not routes:
                print("❌ Aucune route active trouvée")
                return False
            
            # Simuler l'activité des derniers jours
            for day in range(days_back):
                date = datetime.now() - timedelta(days=day)
                
                # Simuler des appels selon notre configuration optimisée
                daily_calls = {
                    1: 30 * 6,  # Tier 1: 30 routes × 6 scans = 180 appels
                    2: 25 * 4,  # Tier 2: 25 routes × 4 scans = 100 appels  
                    3: 20 * 2   # Tier 3: 20 routes × 2 scans = 40 appels
                }
                
                for tier, calls_count in daily_calls.items():
                    tier_routes = [r for r in routes if r.tier == tier]
                    
                    for _ in range(min(calls_count, len(tier_routes) * 6)):
                        route = random.choice(tier_routes)
                        
                        # Simuler un appel API réussi
                        api_call = ApiCall(
                            route_id=route.id,
                            endpoint="aviationstack_mock",
                            method="GET",
                            status_code=200,
                            response_time=random.uniform(0.5, 2.0),
                            timestamp=date.replace(
                                hour=random.randint(0, 23),
                                minute=random.randint(0, 59)
                            ),
                            quota_used=1
                        )
                        self.db.add(api_call)
                
                print(f"✅ Jour {day+1}: {sum(daily_calls.values())} appels API simulés")
            
            self.db.commit()
            
            # Statistiques finales
            total_calls = self.db.query(ApiCall).count()
            today_calls = self.db.query(ApiCall).filter(
                ApiCall.timestamp >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            ).count()
            
            print(f"\n📊 RÉSUMÉ DE LA SIMULATION:")
            print(f"Total appels API simulés: {total_calls}")
            print(f"Appels aujourd'hui: {today_calls}")
            print("✅ Simulation terminée avec succès!")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur simulation: {e}")
            self.db.rollback()
            return False
        finally:
            self.db.close()
    
    def create_mock_deals(self):
        """Créer des deals factices pour les tests"""
        
        print("\n💎 Création de deals factices...")
        
        try:
            db = SessionLocal()
            
            # Routes populaires pour les deals
            popular_routes = [
                ('CDG', 'JFK'), ('CDG', 'BCN'), ('CDG', 'MAD'),
                ('CDG', 'FCO'), ('CDG', 'AMS'), ('CDG', 'LHR')
            ]
            
            for i, (origin, dest) in enumerate(popular_routes):
                route = db.query(Route).filter(
                    Route.origin == origin,
                    Route.destination == dest
                ).first()
                
                if route:
                    # Prix normal et prix réduit
                    normal_price = random.uniform(150, 500)
                    deal_price = normal_price * random.uniform(0.4, 0.7)  # 30-60% de réduction
                    
                    # Créer l'historique de prix
                    price_history = PriceHistory(
                        route_id=route.id,
                        airline=random.choice(["AF", "LH", "BA", "IB"]),
                        price=deal_price,
                        currency="EUR",
                        departure_date=datetime.now() + timedelta(days=random.randint(30, 90)),
                        scanned_at=datetime.now()
                    )
                    db.add(price_history)
                    db.flush()
                    
                    # Créer le deal
                    deal = Deal(
                        route_id=route.id,
                        price_history_id=price_history.id,
                        normal_price=normal_price,
                        deal_price=deal_price,
                        discount_percentage=((normal_price - deal_price) / normal_price) * 100,
                        anomaly_score=random.uniform(0.6, 0.9),
                        confidence_score=random.randint(70, 95),
                        expires_at=datetime.now() + timedelta(hours=random.randint(12, 48)),
                        is_active=True,
                        detected_at=datetime.now()
                    )
                    db.add(deal)
                    
                    print(f"✅ Deal créé: {origin}→{dest} - {deal_price:.0f}€ (au lieu de {normal_price:.0f}€)")
            
            db.commit()
            db.close()
            
            print("💎 Deals factices créés avec succès!")
            return True
            
        except Exception as e:
            logger.error(f"Erreur création deals: {e}")
            return False

def main():
    """Fonction principale pour activer le mode développement"""
    
    print("🚀 ACTIVATION DU MODE DÉVELOPPEMENT")
    print("=" * 50)
    print("Ce mode permet de continuer les tests sans consommer votre quota API")
    print("")
    
    simulator = MockAPISimulator()
    
    # Créer l'activité API simulée
    api_success = simulator.create_mock_api_activity(days_back=7)
    
    # Créer des deals factices
    deals_success = simulator.create_mock_deals()
    
    if api_success and deals_success:
        print("\n🎊 MODE DÉVELOPPEMENT ACTIVÉ AVEC SUCCÈS!")
        print("\nVous pouvez maintenant:")
        print("✅ Tester l'admin dashboard avec des données réalistes")
        print("✅ Vérifier les KPIs et métriques")
        print("✅ Tester toutes les fonctionnalités sans consommer l'API")
        print("\n🔗 Accédez à l'admin dashboard: http://localhost:3001/admin")
        return True
    else:
        print("\n❌ Erreur lors de l'activation du mode développement")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
