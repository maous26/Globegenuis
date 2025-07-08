#!/usr/bin/env python3
"""
Script pour créer le fichier dynamic_route_manager.py avec tout le contenu nécessaire
"""

import os
import sys

# Contenu complet du fichier dynamic_route_manager.py
DYNAMIC_ROUTE_MANAGER_CONTENT = '''# backend/app/services/dynamic_route_manager.py
"""
Gestionnaire intelligent de routes pour GlobeGenius
Optimisé pour 10 000 requêtes/mois avec gestion dynamique des routes saisonnières
"""

from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import math
from app.models.flight import Route, Deal, PriceHistory
from app.utils.logger import logger


class DynamicRouteManager:
    """
    Gestionnaire intelligent qui adapte les routes et fréquences de scan
    selon le budget de 10k requêtes/mois et les saisons
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.monthly_quota = 10000
        self.daily_quota = 333  # 10k / 30 jours
        
        # Configuration des saisons pour les routes saisonnières
        self.seasonal_periods = {
            'summer': {
                'months': [6, 7, 8],  # Juin, Juillet, Août
                'routes': [
                    # Îles méditerranéennes
                    ('CDG', 'PMI'),  # Palma de Majorque
                    ('CDG', 'IBZ'),  # Ibiza
                    ('CDG', 'HER'),  # Héraklion (Crète)
                    ('CDG', 'RHO'),  # Rhodes
                    ('CDG', 'CFU'),  # Corfou
                    ('CDG', 'OLB'),  # Olbia (Sardaigne)
                    ('CDG', 'CAG'),  # Cagliari (Sardaigne)
                    # Côte adriatique
                    ('CDG', 'DBV'),  # Dubrovnik
                    ('CDG', 'SPU'),  # Split
                    # Depuis autres villes françaises
                    ('NCE', 'PMI'),  # Nice → Majorque
                    ('MRS', 'HER'),  # Marseille → Crète
                    ('BOD', 'IBZ'),  # Bordeaux → Ibiza
                ]
            },
            'winter': {
                'months': [12, 1, 2],  # Décembre, Janvier, Février
                'routes': [
                    # Destinations ski/montagne
                    ('CDG', 'GVA'),  # Genève (Alpes)
                    ('CDG', 'ZRH'),  # Zurich (Alpes)
                    ('CDG', 'INN'),  # Innsbruck
                    # Destinations soleil d'hiver
                    ('CDG', 'TFS'),  # Tenerife
                    ('CDG', 'LPA'),  # Las Palmas
                    ('CDG', 'FUE'),  # Fuerteventura
                    ('CDG', 'ACE'),  # Lanzarote
                    # Marchés de Noël
                    ('CDG', 'VIE'),  # Vienne
                    ('CDG', 'PRG'),  # Prague
                    ('CDG', 'BUD'),  # Budapest
                ]
            },
            'spring': {
                'months': [3, 4, 5],  # Mars, Avril, Mai
                'routes': [
                    # City breaks printaniers
                    ('CDG', 'AMS'),  # Amsterdam (tulipes)
                    ('CDG', 'BCN'),  # Barcelone
                    ('CDG', 'LIS'),  # Lisbonne
                    ('CDG', 'SEV'),  # Séville
                    ('CDG', 'NAP'),  # Naples
                    # Pâques/vacances scolaires
                    ('CDG', 'ROM'),  # Rome
                    ('CDG', 'ATH'),  # Athènes
                ]
            },
            'autumn': {
                'months': [9, 10, 11],  # Septembre, Octobre, Novembre
                'routes': [
                    # Indian summer
                    ('CDG', 'IST'),  # Istanbul
                    ('CDG', 'CAI'),  # Le Caire
                    ('CDG', 'AMM'),  # Amman
                    # Destinations culturelles
                    ('CDG', 'FLR'),  # Florence
                    ('CDG', 'VCE'),  # Venise
                    # Long-courriers fin d'année
                    ('CDG', 'BKK'),  # Bangkok
                    ('CDG', 'HKT'),  # Phuket
                ]
            },
            'yearround_events': {
                'months': 'all',
                'routes': [
                    # Routes événementielles (ajustées selon calendrier)
                    ('CDG', 'MCO'),  # Orlando (Disney)
                    ('CDG', 'LAS'),  # Las Vegas (conventions)
                    ('CDG', 'DXB'),  # Dubai (shopping festivals)
                ]
            }
        }
        
        # Stratégie de scan adaptée au budget
        self.scan_strategies = {
            'performance_based': True,  # Ajuster selon performance
            'seasonal_boost': 1.5,      # Boost pour routes saisonnières actives
            'min_scans_per_day': {
                'tier1': 4,  # Au lieu de 12
                'tier2': 2,  # Au lieu de 6
                'tier3': 1   # Au lieu de 4
            }
        }
    
    def calculate_optimal_scan_distribution(self) -> Dict[str, any]:
        """
        Calculer la distribution optimale des scans selon le budget de 333/jour
        """
        
        logger.info("📊 Calcul de la distribution optimale des scans")
        
        # Récupérer toutes les routes actives
        all_routes = self.db.query(Route).filter(Route.is_active == True).all()
        
        # Ajouter les routes saisonnières actives
        seasonal_routes = self._get_active_seasonal_routes()
        
        # Calculer le score de priorité pour chaque route
        route_priorities = []
        
        for route in all_routes:
            priority_score = self._calculate_route_priority(route)
            route_priorities.append({
                'route': route,
                'score': priority_score,
                'origin': route.origin,
                'destination': route.destination,
                'tier': route.tier,
                'is_seasonal': False
            })
        
        # Ajouter les routes saisonnières avec un boost
        for origin, destination in seasonal_routes:
            # Vérifier si la route existe déjà
            existing = next((r for r in route_priorities 
                           if r['origin'] == origin and r['destination'] == destination), None)
            
            if existing:
                # Booster la route existante
                existing['score'] *= self.scan_strategies['seasonal_boost']
                existing['is_seasonal'] = True
            else:
                # Créer une route saisonnière temporaire
                route_priorities.append({
                    'route': None,  # Route virtuelle
                    'score': 100 * self.scan_strategies['seasonal_boost'],  # Score élevé
                    'origin': origin,
                    'destination': destination,
                    'tier': 2,  # Tier par défaut
                    'is_seasonal': True
                })
        
        # Trier par score décroissant
        route_priorities.sort(key=lambda x: x['score'], reverse=True)
        
        # Distribuer les 333 scans quotidiens
        daily_scans = self._distribute_daily_scans(route_priorities)
        
        # Calculer les statistiques
        stats = self._calculate_distribution_stats(daily_scans)
        
        return {
            'daily_scans': daily_scans,
            'total_routes': len(route_priorities),
            'active_seasonal_routes': len([r for r in route_priorities if r['is_seasonal']]),
            'daily_quota_used': sum(scan['daily_scans'] for scan in daily_scans),
            'stats': stats,
            'recommendations': self._generate_recommendations(daily_scans, stats)
        }
    
    def _calculate_route_priority(self, route: Route) -> float:
        """
        Calculer le score de priorité d'une route basé sur plusieurs facteurs
        """
        
        base_score = {1: 100, 2: 50, 3: 25}[route.tier]
        
        # Analyser la performance sur les 30 derniers jours
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        # Nombre de deals trouvés
        deals_count = self.db.query(func.count(Deal.id)).filter(
            and_(
                Deal.route_id == route.id,
                Deal.detected_at >= thirty_days_ago
            )
        ).scalar() or 0
        
        # Valeur moyenne des deals
        avg_discount = self.db.query(func.avg(Deal.discount_percentage)).filter(
            and_(
                Deal.route_id == route.id,
                Deal.detected_at >= thirty_days_ago
            )
        ).scalar() or 0
        
        # Temps depuis le dernier deal
        last_deal = self.db.query(Deal.detected_at).filter(
            Deal.route_id == route.id
        ).order_by(Deal.detected_at.desc()).first()
        
        if last_deal:
            days_since_last_deal = (datetime.now() - last_deal[0]).days
            freshness_factor = 1 + (days_since_last_deal / 30)  # Plus c'est vieux, plus on veut scanner
        else:
            freshness_factor = 2  # Jamais eu de deal, priorité haute pour découvrir
        
        # Calculer le score final
        performance_score = deals_count * 10  # Chaque deal vaut 10 points
        value_score = avg_discount / 10  # Les gros discounts valent plus
        
        final_score = base_score * freshness_factor + performance_score + value_score
        
        return final_score
    
    def _get_active_seasonal_routes(self) -> List[Tuple[str, str]]:
        """
        Déterminer quelles routes saisonnières sont actives maintenant
        """
        
        current_month = datetime.now().month
        active_routes = []
        
        for season, config in self.seasonal_periods.items():
            if season == 'yearround_events':
                # Routes actives toute l'année mais avec variations
                active_routes.extend(config['routes'])
            elif current_month in config['months']:
                # Routes de la saison actuelle
                active_routes.extend(config['routes'])
                logger.info(f"🌴 Saison {season} active : {len(config['routes'])} routes ajoutées")
        
        # Ajouter des routes spéciales selon événements
        special_routes = self._get_event_based_routes()
        active_routes.extend(special_routes)
        
        return active_routes
    
    def _get_event_based_routes(self) -> List[Tuple[str, str]]:
        """
        Ajouter des routes basées sur des événements spéciaux
        (festivals, événements sportifs, etc.)
        """
        
        special_routes = []
        current_date = datetime.now()
        
        # Exemples d'événements (à enrichir avec un calendrier réel)
        events = {
            'Carnaval de Venise': {
                'dates': [(2, 10), (2, 28)],  # 10-28 février
                'routes': [('CDG', 'VCE'), ('NCE', 'VCE')]
            },
            'Oktoberfest': {
                'dates': [(9, 15), (10, 5)],  # Mi-sept à début oct
                'routes': [('CDG', 'MUC'), ('MRS', 'MUC')]
            },
            'Art Basel Miami': {
                'dates': [(12, 1), (12, 10)],  # Début décembre
                'routes': [('CDG', 'MIA')]
            }
        }
        
        for event, config in events.items():
            start_month, start_day = config['dates'][0]
            end_month, end_day = config['dates'][1]
            
            # Vérifier si on est dans la période
            if self._is_date_in_range(current_date, start_month, start_day, end_month, end_day):
                special_routes.extend(config['routes'])
                logger.info(f"🎉 Événement actif: {event}")
        
        return special_routes
    
    def _is_date_in_range(self, date: datetime, start_month: int, start_day: int, 
                          end_month: int, end_day: int) -> bool:
        """
        Vérifier si une date est dans une plage (gère le passage d'année)
        """
        
        current_year = date.year
        
        # Créer les dates de début et fin
        start_date = datetime(current_year, start_month, start_day)
        
        if end_month < start_month:  # Passage d'année (ex: déc → jan)
            end_date = datetime(current_year + 1, end_month, end_day)
        else:
            end_date = datetime(current_year, end_month, end_day)
        
        # Ajuster si nécessaire pour les dates passées
        if date < start_date and end_month < start_month:
            start_date = datetime(current_year - 1, start_month, start_day)
            end_date = datetime(current_year, end_month, end_day)
        
        return start_date <= date <= end_date
    
    def _distribute_daily_scans(self, route_priorities: List[Dict]) -> List[Dict]:
        """
        Distribuer intelligemment les 333 scans quotidiens
        """
        
        daily_scans = []
        remaining_budget = self.daily_quota
        
        # Phase 1 : Garantir le minimum pour les top routes
        for i, route_info in enumerate(route_priorities):
            if remaining_budget <= 0:
                break
            
            # Déterminer le nombre de scans
            if i < 10:  # Top 10 routes
                scans = 8  # 8 scans/jour pour le top 10
            elif i < 30:  # Top 30 routes
                scans = 4  # 4 scans/jour pour les suivantes
            elif i < 60:  # Top 60 routes
                scans = 2  # 2 scans/jour
            else:
                scans = 1  # 1 scan/jour pour le reste
            
            # Ajuster si route saisonnière
            if route_info['is_seasonal']:
                scans = int(scans * 1.5)  # 50% de scans en plus
            
            # Respecter le budget
            scans = min(scans, remaining_budget)
            
            if scans > 0:
                daily_scans.append({
                    'origin': route_info['origin'],
                    'destination': route_info['destination'],
                    'tier': route_info['tier'],
                    'is_seasonal': route_info['is_seasonal'],
                    'priority_score': route_info['score'],
                    'daily_scans': scans,
                    'scan_interval_hours': 24 / scans
                })
                
                remaining_budget -= scans
        
        # Phase 2 : Si il reste du budget, l'allouer aux meilleures routes
        if remaining_budget > 0 and daily_scans:
            extra_per_route = remaining_budget // min(10, len(daily_scans))
            for i in range(min(10, len(daily_scans))):
                daily_scans[i]['daily_scans'] += extra_per_route
                daily_scans[i]['scan_interval_hours'] = 24 / daily_scans[i]['daily_scans']
        
        return daily_scans
    
    def _calculate_distribution_stats(self, daily_scans: List[Dict]) -> Dict:
        """
        Calculer des statistiques sur la distribution
        """
        
        total_scans = sum(scan['daily_scans'] for scan in daily_scans)
        seasonal_scans = sum(scan['daily_scans'] for scan in daily_scans if scan['is_seasonal'])
        
        tier_distribution = {1: 0, 2: 0, 3: 0}
        for scan in daily_scans:
            tier_distribution[scan['tier']] += scan['daily_scans']
        
        return {
            'total_daily_scans': total_scans,
            'routes_covered': len(daily_scans),
            'seasonal_routes_count': len([s for s in daily_scans if s['is_seasonal']]),
            'seasonal_scans_percentage': (seasonal_scans / total_scans * 100) if total_scans > 0 else 0,
            'tier_distribution': tier_distribution,
            'average_scans_per_route': total_scans / len(daily_scans) if daily_scans else 0,
            'coverage_percentage': (len(daily_scans) / 90) * 100  # Sur ~90 routes possibles
        }
    
    def _generate_recommendations(self, daily_scans: List[Dict], stats: Dict) -> List[str]:
        """
        Générer des recommandations pour optimiser encore plus
        """
        
        recommendations = []
        
        # Vérifier la couverture
        if stats['coverage_percentage'] < 50:
            recommendations.append(
                "⚠️ Couverture faible : seulement {:.0f}% des routes sont scannées. "
                "Considérez d'augmenter votre budget FlightLabs à 20k requêtes/mois (98€)."
                .format(stats['coverage_percentage'])
            )
        
        # Vérifier l'équilibre saisonnier
        if stats['seasonal_scans_percentage'] > 40:
            recommendations.append(
                "📈 {:.0f}% des scans vont vers des routes saisonnières. "
                "C'est bien adapté à la saison actuelle !"
                .format(stats['seasonal_scans_percentage'])
            )
        
        # Routes non scannées
        unscanned_count = 90 - stats['routes_covered']
        if unscanned_count > 30:
            recommendations.append(
                f"🔍 {unscanned_count} routes ne sont pas scannées du tout. "
                "Activez le mode 'rotation' pour scanner ces routes 1 fois par semaine."
            )
        
        # Performance des tiers
        tier1_percentage = (stats['tier_distribution'][1] / stats['total_daily_scans']) * 100
        if tier1_percentage < 40:
            recommendations.append(
                "📊 Seulement {:.0f}% des scans vont vers les routes Tier 1. "
                "Considérez de réévaluer les tiers basés sur la performance récente."
                .format(tier1_percentage)
            )
        
        return recommendations
    
    def apply_distribution(self, distribution: Dict) -> bool:
        """
        Appliquer la nouvelle distribution aux routes dans la base de données
        """
        
        try:
            for scan_config in distribution['daily_scans']:
                # Trouver ou créer la route
                route = self.db.query(Route).filter(
                    and_(
                        Route.origin == scan_config['origin'],
                        Route.destination == scan_config['destination']
                    )
                ).first()
                
                if route:
                    # Mettre à jour l'intervalle
                    route.scan_interval_hours = int(scan_config['scan_interval_hours'])
                    logger.info(
                        f"Route {route.origin}→{route.destination} : "
                        f"{scan_config['daily_scans']} scans/jour "
                        f"(toutes les {route.scan_interval_hours}h)"
                    )
                elif scan_config['is_seasonal']:
                    # Créer une route saisonnière temporaire
                    route = Route(
                        origin=scan_config['origin'],
                        destination=scan_config['destination'],
                        tier=scan_config['tier'],
                        scan_interval_hours=int(scan_config['scan_interval_hours']),
                        is_active=True,
                        is_seasonal=True  # Si tu as ce champ dans ton modèle
                    )
                    self.db.add(route)
                    logger.info(f"Nouvelle route saisonnière créée : {route.origin}→{route.destination}")
            
            # Désactiver les routes non présentes dans la distribution
            all_routes = self.db.query(Route).filter(Route.is_active == True).all()
            distributed_routes = {(s['origin'], s['destination']) for s in distribution['daily_scans']}
            
            for route in all_routes:
                if (route.origin, route.destination) not in distributed_routes:
                    route.is_active = False
                    logger.info(f"Route désactivée (hors budget) : {route.origin}→{route.destination}")
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'application de la distribution : {e}")
            self.db.rollback()
            return False
    
    def get_seasonal_calendar(self) -> Dict[str, List[Dict]]:
        """
        Générer un calendrier des routes saisonnières pour l'année
        """
        
        calendar = {}
        
        for month in range(1, 13):
            month_name = datetime(2024, month, 1).strftime('%B')
            active_routes = []
            
            # Vérifier chaque saison
            for season, config in self.seasonal_periods.items():
                if season == 'yearround_events' or month in config.get('months', []):
                    for origin, dest in config['routes']:
                        active_routes.append({
                            'route': f"{origin}→{dest}",
                            'season': season,
                            'type': 'seasonal'
                        })
            
            calendar[month_name] = active_routes
        
        return calendar
    
    def suggest_dynamic_adjustments(self) -> List[Dict]:
        """
        Suggérer des ajustements dynamiques basés sur les performances temps réel
        """
        
        suggestions = []
        
        # Analyser les routes surperformantes (beaucoup de deals)
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        top_performers = self.db.query(
            Route.origin,
            Route.destination,
            func.count(Deal.id).label('deal_count'),
            func.avg(Deal.discount_percentage).label('avg_discount')
        ).join(Deal).filter(
            Deal.detected_at >= seven_days_ago
        ).group_by(
            Route.origin, Route.destination
        ).having(
            func.count(Deal.id) >= 3  # Au moins 3 deals en 7 jours
        ).order_by(
            func.count(Deal.id).desc()
        ).limit(10).all()
        
        for route in top_performers:
            suggestions.append({
                'type': 'increase_frequency',
                'route': f"{route.origin}→{route.destination}",
                'reason': f"{route.deal_count} deals trouvés cette semaine (moy: {route.avg_discount:.0f}%)",
                'action': "Augmenter à 8-10 scans/jour"
            })
        
        # Analyser les routes sous-performantes
        underperformers = self.db.query(Route).filter(
            and_(
                Route.is_active == True,
                ~Route.deals.any(Deal.detected_at >= seven_days_ago)
            )
        ).all()
        
        for route in underperformers[:5]:  # Top 5 sous-performants
            suggestions.append({
                'type': 'decrease_frequency',
                'route': f"{route.origin}→{route.destination}",
                'reason': "Aucun deal trouvé cette semaine",
                'action': "Réduire à 1 scan/jour ou désactiver temporairement"
            })
        
        return suggestions


def create_seasonal_routes_config() -> Dict:
    """
    Créer une configuration complète des routes saisonnières
    basée sur les données du marché français
    """
    
    return {
        'seasonal_routes': {
            'summer_beach': {
                'active_months': [6, 7, 8],
                'description': 'Destinations plage été',
                'routes': [
                    # Baléares
                    {'origin': 'CDG', 'destination': 'PMI', 'airline_focus': ['Vueling', 'Ryanair']},
                    {'origin': 'CDG', 'destination': 'IBZ', 'airline_focus': ['Vueling', 'Transavia']},
                    {'origin': 'CDG', 'destination': 'MAH', 'airline_focus': ['Vueling']},  # Minorque
                    
                    # Grèce
                    {'origin': 'CDG', 'destination': 'HER', 'airline_focus': ['Aegean', 'Transavia']},
                    {'origin': 'CDG', 'destination': 'RHO', 'airline_focus': ['Aegean', 'Ryanair']},
                    {'origin': 'CDG', 'destination': 'CFU', 'airline_focus': ['Transavia', 'Ryanair']},
                    {'origin': 'CDG', 'destination': 'JTR', 'airline_focus': ['Transavia']},  # Santorin
                    {'origin': 'CDG', 'destination': 'JMK', 'airline_focus': ['Transavia']},  # Mykonos
                    
                    # Croatie
                    {'origin': 'CDG', 'destination': 'DBV', 'airline_focus': ['Croatia Airlines', 'Transavia']},
                    {'origin': 'CDG', 'destination': 'SPU', 'airline_focus': ['Croatia Airlines', 'easyJet']},
                    {'origin': 'CDG', 'destination': 'ZAD', 'airline_focus': ['Ryanair']},
                    
                    # Italie
                    {'origin': 'CDG', 'destination': 'OLB', 'airline_focus': ['Volotea', 'easyJet']},
                    {'origin': 'CDG', 'destination': 'CAG', 'airline_focus': ['Ryanair', 'Volotea']},
                    {'origin': 'CDG', 'destination': 'CTA', 'airline_focus': ['Transavia', 'Ryanair']},  # Catane
                    {'origin': 'CDG', 'destination': 'PMO', 'airline_focus': ['Ryanair', 'easyJet']},  # Palerme
                    
                    # Portugal
                    {'origin': 'CDG', 'destination': 'FAO', 'airline_focus': ['Transavia', 'Ryanair']},
                    {'origin': 'CDG', 'destination': 'FNC', 'airline_focus': ['Transavia', 'TAP']},  # Madère
                ]
            },
            'winter_sun': {
                'active_months': [11, 12, 1, 2, 3],
                'description': 'Destinations soleil hiver',
                'routes': [
                    # Canaries
                    {'origin': 'CDG', 'destination': 'TFS', 'airline_focus': ['Transavia', 'Vueling']},
                    {'origin': 'CDG', 'destination': 'LPA', 'airline_focus': ['Transavia', 'Vueling']},
                    {'origin': 'CDG', 'destination': 'ACE', 'airline_focus': ['Transavia', 'Vueling']},
                    {'origin': 'CDG', 'destination': 'FUE', 'airline_focus': ['Transavia', 'Ryanair']},
                    
                    # Afrique du Nord
                    {'origin': 'CDG', 'destination': 'RAK', 'airline_focus': ['Transavia', 'Ryanair']},
                    {'origin': 'CDG', 'destination': 'AGA', 'airline_focus': ['Transavia', 'Royal Air Maroc']},
                    {'origin': 'CDG', 'destination': 'ESU', 'airline_focus': ['Transavia']},  # Essaouira
                    
                    # Égypte/Jordanie
                    {'origin': 'CDG', 'destination': 'HRG', 'airline_focus': ['Transavia']},  # Hurghada
                    {'origin': 'CDG', 'destination': 'SSH', 'airline_focus': ['Transavia']},  # Sharm el-Sheikh
                    {'origin': 'CDG', 'destination': 'AQJ', 'airline_focus': ['Transavia', 'Ryanair']},  # Aqaba
                ]
            },
            'ski_season': {
                'active_months': [12, 1, 2, 3],
                'description': 'Destinations ski',
                'routes': [
                    {'origin': 'CDG', 'destination': 'GVA', 'airline_focus': ['easyJet', 'Air France']},
                    {'origin': 'CDG', 'destination': 'ZRH', 'airline_focus': ['Swiss', 'easyJet']},
                    {'origin': 'CDG', 'destination': 'INN', 'airline_focus': ['Transavia', 'Austrian']},
                    {'origin': 'CDG', 'destination': 'SZG', 'airline_focus': ['Transavia', 'Austrian']},  # Salzbourg
                    {'origin': 'CDG', 'destination': 'TRN', 'airline_focus': ['Ryanair']},  # Turin
                    {'origin': 'CDG', 'destination': 'BGY', 'airline_focus': ['Ryanair']},  # Bergame
                ]
            },
            'christmas_markets': {
                'active_months': [11, 12],
                'description': 'Marchés de Noël',
                'routes': [
                    {'origin': 'CDG', 'destination': 'VIE', 'airline_focus': ['Austrian', 'Transavia']},
                    {'origin': 'CDG', 'destination': 'PRG', 'airline_focus': ['Czech Airlines', 'Transavia']},
                    {'origin': 'CDG', 'destination': 'BUD', 'airline_focus': ['Wizz Air', 'Ryanair']},
                    {'origin': 'CDG', 'destination': 'NUE', 'airline_focus': ['Lufthansa']},  # Nuremberg
                    {'origin': 'CDG', 'destination': 'STR', 'airline_focus': ['Eurowings']},  # Stuttgart
                    {'origin': 'CDG', 'destination': 'DRS', 'airline_focus': ['Transavia']},  # Dresde
                ]
            },
            'easter_holidays': {
                'active_months': [3, 4],
                'description': 'Vacances de Pâques',
                'routes': [
                    {'origin': 'CDG', 'destination': 'FCO', 'airline_focus': ['Vueling', 'Ryanair']},
                    {'origin': 'CDG', 'destination': 'ATH', 'airline_focus': ['Aegean', 'Transavia']},
                    {'origin': 'CDG', 'destination': 'TLV', 'airline_focus': ['Transavia', 'El Al']},
                    {'origin': 'CDG', 'destination': 'JER', 'airline_focus': ['easyJet']},  # Jerusalem
                ]
            },
            'theme_parks': {
                'active_months': [4, 5, 6, 7, 8, 10],  # Vacances scolaires
                'description': 'Parcs d\\'attractions',
                'routes': [
                    {'origin': 'CDG', 'destination': 'MCO', 'airline_focus': ['Air France', 'XL Airways']},  # Orlando
                    {'origin': 'CDG', 'destination': 'CPH', 'airline_focus': ['SAS', 'Transavia']},  # Copenhague (Tivoli)
                    {'origin': 'CDG', 'destination': 'BCN', 'airline_focus': ['Vueling', 'Transavia']},  # Port Aventura
                ]
            }
        }
    }
'''

def create_dynamic_route_manager():
    """
    Créer le fichier dynamic_route_manager.py avec tout le contenu nécessaire
    """
    # Déterminer le chemin du fichier
    backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    file_path = os.path.join(backend_path, 'app', 'services', 'dynamic_route_manager.py')
    
    print(f"📁 Création du fichier : {file_path}")
    
    # Créer le répertoire si nécessaire
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Écrire le contenu
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(DYNAMIC_ROUTE_MANAGER_CONTENT)
    
    print(f"✅ Fichier créé avec succès!")
    print(f"   Taille : {len(DYNAMIC_ROUTE_MANAGER_CONTENT)} caractères")
    print(f"   Classes exportées : DynamicRouteManager, create_seasonal_routes_config")
    
    # Vérifier que le fichier est importable
    try:
        # Ajouter le backend au path
        sys.path.insert(0, backend_path)
        
        # Tenter l'import
        from app.services.dynamic_route_manager import DynamicRouteManager, create_seasonal_routes_config
        
        print(f"\n✅ Import test réussi!")
        print(f"   DynamicRouteManager : OK")
        print(f"   create_seasonal_routes_config : OK")
        
        return True
        
    except ImportError as e:
        print(f"\n❌ Erreur d'import : {e}")
        print(f"   Vérifiez que tous les modules requis sont installés")
        return False


if __name__ == "__main__":
    print("🚀 Script de création du fichier dynamic_route_manager.py")
    print("=" * 60)
    
    success = create_dynamic_route_manager()
    
    if success:
        print(f"\n🎯 Prochaine étape :")
        print(f"   Relancez votre script de visualisation :")
        print(f"   python visualize_seasonal_strategy.py")
    else:
        print(f"\n⚠️  Des problèmes ont été détectés.")
        print(f"   Vérifiez les erreurs ci-dessus.")