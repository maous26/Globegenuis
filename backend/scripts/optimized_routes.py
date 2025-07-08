#!/usr/bin/env python3
"""
Script pour appliquer la stratégie optimisée avec 10 000 requêtes/mois
et gestion dynamique des routes saisonnières
"""

import sys
import os
from datetime import datetime
from colorama import init, Fore, Style

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.services.dynamic_route_manager import DynamicRouteManager
from app.models.flight import Route, Deal
from sqlalchemy import func, and_
import json

# Initialiser les couleurs
init(autoreset=True)


def main():
    """
    Appliquer la stratégie optimisée pour 10k requêtes/mois
    """
    
    print(f"\n{Fore.CYAN}🚀 OPTIMISATION DES ROUTES GLOBEGENIUS")
    print(f"{Fore.CYAN}Budget: 10 000 requêtes/mois (333/jour)")
    print("=" * 60)
    
    db = SessionLocal()
    manager = DynamicRouteManager(db)
    
    try:
        # 1. Analyser la situation actuelle
        print(f"\n{Fore.YELLOW}📊 Analyse de la situation actuelle...")
        analyze_current_situation(db)
        
        # 2. Calculer la distribution optimale
        print(f"\n{Fore.YELLOW}🧮 Calcul de la distribution optimale...")
        distribution = manager.calculate_optimal_scan_distribution()
        
        # 3. Afficher le plan
        display_distribution_plan(distribution)
        
        # 4. Demander confirmation
        print(f"\n{Fore.YELLOW}❓ Voulez-vous appliquer cette configuration ?")
        print(f"   {Fore.RED}Attention: Cela va modifier les fréquences de scan de toutes les routes!")
        
        response = input(f"\n{Fore.GREEN}Confirmer (oui/non) ? ").lower()
        
        if response in ['oui', 'o', 'yes', 'y']:
            # 5. Appliquer la distribution
            print(f"\n{Fore.YELLOW}⚙️  Application de la nouvelle configuration...")
            success = manager.apply_distribution(distribution)
            
            if success:
                print(f"\n{Fore.GREEN}✅ Configuration appliquée avec succès!")
                
                # 6. Créer un rapport
                create_optimization_report(distribution, manager)
                
                # 7. Afficher les prochaines étapes
                display_next_steps()
            else:
                print(f"\n{Fore.RED}❌ Erreur lors de l'application de la configuration")
        else:
            print(f"\n{Fore.YELLOW}❌ Configuration annulée")
        
    finally:
        db.close()


def analyze_current_situation(db):
    """
    Analyser la configuration actuelle des routes
    """
    
    # Compter les routes par tier
    tier_counts = db.query(
        Route.tier,
        func.count(Route.id).label('count'),
        func.sum(24 / Route.scan_interval_hours).label('daily_scans')
    ).filter(Route.is_active == True).group_by(Route.tier).all()
    
    total_daily_scans = sum(tier.daily_scans or 0 for tier in tier_counts)
    
    print(f"\n{Fore.CYAN}Configuration actuelle:")
    print(f"{'Tier':<10} {'Routes':<10} {'Scans/jour':<15} {'% du total':<10}")
    print("-" * 50)
    
    for tier in tier_counts:
        percentage = (tier.daily_scans / total_daily_scans * 100) if total_daily_scans > 0 else 0
        print(f"Tier {tier.tier:<5} {tier.count:<10} {tier.daily_scans:<15.0f} {percentage:<10.1f}%")
    
    print(f"\n{Fore.YELLOW}Total: {total_daily_scans:.0f} scans/jour")
    
    if total_daily_scans > 333:
        print(f"{Fore.RED}⚠️  PROBLÈME: {total_daily_scans:.0f} scans/jour > 333 (budget quotidien)")
        print(f"   Dépassement: {total_daily_scans - 333:.0f} scans/jour")
    
    # Analyser les performances récentes
    seven_days_ago = datetime.now().days_since(7)
    
    top_performers = db.query(
        Route.origin,
        Route.destination,
        func.count(Deal.id).label('deals')
    ).join(Deal).filter(
        Deal.detected_at >= seven_days_ago
    ).group_by(Route.origin, Route.destination).order_by(
        func.count(Deal.id).desc()
    ).limit(5).all()
    
    if top_performers:
        print(f"\n{Fore.CYAN}Top 5 routes performantes (7 derniers jours):")
        for route in top_performers:
            print(f"   {route.origin} → {route.destination}: {route.deals} deals")


def display_distribution_plan(distribution):
    """
    Afficher le plan de distribution de manière claire
    """
    
    stats = distribution['stats']
    
    print(f"\n{Fore.GREEN}✨ NOUVELLE DISTRIBUTION OPTIMISÉE")
    print("=" * 60)
    
    # Résumé
    print(f"\n{Fore.CYAN}Résumé:")
    print(f"   Routes couvertes: {stats['routes_covered']} (sur ~90 possibles)")
    print(f"   Scans quotidiens: {stats['total_daily_scans']} (budget: 333)")
    print(f"   Routes saisonnières actives: {stats['seasonal_routes_count']}")
    print(f"   Couverture: {stats['coverage_percentage']:.1f}%")
    
    # Top 10 routes
    print(f"\n{Fore.CYAN}Top 10 routes prioritaires:")
    print(f"{'Route':<20} {'Scans/jour':<12} {'Intervalle':<12} {'Type':<10}")
    print("-" * 60)
    
    for i, scan in enumerate(distribution['daily_scans'][:10]):
        route_str = f"{scan['origin']} → {scan['destination']}"
        type_str = "Saisonnier" if scan['is_seasonal'] else "Régulier"
        interval_str = f"{scan['scan_interval_hours']:.1f}h"
        
        # Colorer selon l'importance
        if i < 3:
            color = Fore.GREEN
        elif i < 6:
            color = Fore.YELLOW
        else:
            color = Fore.WHITE
            
        print(f"{color}{route_str:<20} {scan['daily_scans']:<12} {interval_str:<12} {type_str:<10}")
    
    # Distribution par tier
    print(f"\n{Fore.CYAN}Distribution par tier:")
    for tier, scans in stats['tier_distribution'].items():
        if scans > 0:
            percentage = (scans / stats['total_daily_scans']) * 100
            print(f"   Tier {tier}: {scans} scans/jour ({percentage:.1f}%)")
    
    # Recommandations
    if distribution['recommendations']:
        print(f"\n{Fore.YELLOW}💡 Recommandations:")
        for rec in distribution['recommendations']:
            print(f"   • {rec}")


def create_optimization_report(distribution, manager):
    """
    Créer un rapport détaillé de l'optimisation
    """
    
    report_path = "optimization_report.json"
    
    # Obtenir le calendrier saisonnier
    seasonal_calendar = manager.get_seasonal_calendar()
    
    # Obtenir les suggestions d'ajustement
    suggestions = manager.suggest_dynamic_adjustments()
    
    report = {
        'generated_at': datetime.now().isoformat(),
        'budget': {
            'monthly_quota': 10000,
            'daily_quota': 333,
            'daily_used': distribution['stats']['total_daily_scans']
        },
        'coverage': {
            'total_routes': distribution['total_routes'],
            'covered_routes': distribution['stats']['routes_covered'],
            'coverage_percentage': distribution['stats']['coverage_percentage']
        },
        'seasonal_routes': {
            'active_count': distribution['active_seasonal_routes'],
            'calendar': seasonal_calendar
        },
        'top_routes': [
            {
                'route': f"{scan['origin']}→{scan['destination']}",
                'daily_scans': scan['daily_scans'],
                'is_seasonal': scan['is_seasonal'],
                'priority_score': scan['priority_score']
            }
            for scan in distribution['daily_scans'][:20]
        ],
        'recommendations': distribution['recommendations'],
        'dynamic_adjustments': suggestions
    }
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n{Fore.GREEN}📄 Rapport détaillé créé: {report_path}")


def display_next_steps():
    """
    Afficher les prochaines étapes pour l'utilisateur
    """
    
    print(f"\n{Fore.CYAN}🎯 PROCHAINES ÉTAPES")
    print("=" * 60)
    
    print(f"\n{Fore.YELLOW}1. Redémarrer les services pour appliquer les changements:")
    print(f"   {Fore.WHITE}# Arrêter Celery (Ctrl+C)")
    print(f"   {Fore.WHITE}# Relancer:")
    print(f"   {Fore.WHITE}celery -A app.tasks.celery_app worker --loglevel=info")
    print(f"   {Fore.WHITE}celery -A app.tasks.celery_app beat --loglevel=info")
    
    print(f"\n{Fore.YELLOW}2. Monitorer les performances:")
    print(f"   {Fore.WHITE}python scripts/monitor_scanner.py")
    
    print(f"\n{Fore.YELLOW}3. Activer l'ajustement automatique (optionnel):")
    print(f"   {Fore.WHITE}python scripts/enable_auto_optimization.py")
    
    print(f"\n{Fore.YELLOW}4. Surveiller le quota quotidien:")
    print(f"   {Fore.WHITE}Le système s'arrêtera automatiquement à 333 requêtes/jour")
    
    print(f"\n{Fore.GREEN}💡 Conseils:")
    print(f"   • Les routes saisonnières changeront automatiquement chaque mois")
    print(f"   • Vérifiez les performances chaque semaine")
    print(f"   • Ajustez les seuils de détection si trop/peu de deals")
    
    # Afficher le calendrier du mois actuel
    current_month = datetime.now().strftime('%B')
    print(f"\n{Fore.CYAN}📅 Routes saisonnières actives en {current_month}:")
    
    # Simuler quelques routes saisonnières selon le mois
    month_num = datetime.now().month
    if month_num in [6, 7, 8]:
        seasonal_examples = [
            "CDG → PMI (Palma de Majorque)",
            "CDG → IBZ (Ibiza)",
            "CDG → HER (Héraklion)",
            "CDG → DBV (Dubrovnik)"
        ]
        season = "ÉTÉ 🌴"
    elif month_num in [12, 1, 2]:
        seasonal_examples = [
            "CDG → TFS (Tenerife)",
            "CDG → VIE (Vienne - Marchés de Noël)",
            "CDG → GVA (Genève - Ski)",
            "CDG → RAK (Marrakech)"
        ]
        season = "HIVER ⛷️"
    elif month_num in [3, 4, 5]:
        seasonal_examples = [
            "CDG → AMS (Amsterdam - Tulipes)",
            "CDG → BCN (Barcelone)",
            "CDG → ROM (Rome - Pâques)",
            "CDG → ATH (Athènes)"
        ]
        season = "PRINTEMPS 🌸"
    else:
        seasonal_examples = [
            "CDG → IST (Istanbul)",
            "CDG → CAI (Le Caire)",
            "CDG → FLR (Florence)",
            "CDG → BKK (Bangkok)"
        ]
        season = "AUTOMNE 🍂"
    
    print(f"\n   Saison: {season}")
    for route in seasonal_examples[:4]:
        print(f"   • {route}")


if __name__ == "__main__":
    main()