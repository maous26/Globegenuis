#!/usr/bin/env python3
"""
Script de monitoring du scanner GlobeGenius
Surveillance en temps réel des performances et de la santé du système
"""

import sys
import os
import time
from datetime import datetime, timedelta
from colorama import init, Fore, Style, Back
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.flight import Route, Deal, PriceHistory
from app.models.user import User
from app.models.alert import Alert
from app.services.admin_service import AdminService
from sqlalchemy import func, and_

# Initialiser colorama
init(autoreset=True)


class ScannerMonitor:
    """
    Moniteur en temps réel du scanner GlobeGenius
    """
    
    def __init__(self):
        self.db = SessionLocal()
        self.admin_service = AdminService(self.db)
        self.monitoring = True
        
    def run(self):
        """Lancer le monitoring en temps réel"""
        
        print(f"\n{Fore.CYAN}{Style.BRIGHT}🔍 MONITORING SCANNER GLOBEGENIUS")
        print(f"{Fore.CYAN}{'=' * 60}")
        print(f"{Fore.YELLOW}Appuyez sur Ctrl+C pour arrêter le monitoring\n")
        
        try:
            while self.monitoring:
                self.display_dashboard()
                time.sleep(30)  # Rafraîchir toutes les 30 secondes
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Monitoring arrêté par l'utilisateur")
            
        finally:
            self.db.close()
    
    def display_dashboard(self):
        """Afficher le dashboard de monitoring"""
        
        # Effacer l'écran
        os.system('clear' if os.name == 'posix' else 'cls')
        
        # Header
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"{Fore.CYAN}{Style.BRIGHT}🔍 MONITORING SCANNER GLOBEGENIUS - {current_time}")
        print(f"{Fore.CYAN}{'=' * 60}")
        
        # Statistiques générales
        self.display_general_stats()
        
        # Activité récente
        self.display_recent_activity()
        
        # Quota API
        self.display_api_quota()
        
        # Santé du système
        self.display_system_health()
        
        # Top routes performantes
        self.display_top_routes()
        
        # Dernières alertes
        self.display_recent_alerts()
        
        print(f"\n{Fore.YELLOW}Prochaine mise à jour dans 30 secondes...")
    
    def display_general_stats(self):
        """Afficher les statistiques générales"""
        
        stats = self.admin_service.get_dashboard_stats()
        
        print(f"\n{Fore.GREEN}📊 STATISTIQUES GÉNÉRALES")
        print(f"{Fore.WHITE}{'─' * 40}")
        
        # Utilisateurs
        users = stats['users']
        print(f"  👥 Utilisateurs: {Fore.WHITE}{users['total']:,} total, {Fore.GREEN}{users['active']:,} actifs")
        print(f"  📈 Nouveaux: {Fore.CYAN}{users['new_today']} aujourd'hui, {users['new_week']} cette semaine")
        
        # Routes et deals
        routes = stats['routes']
        deals = stats['deals']
        print(f"  🛣️  Routes: {Fore.WHITE}{routes['total']} total, {Fore.GREEN}{routes['active']} actives")
        print(f"  💰 Deals: {Fore.WHITE}{deals['total']} total, {Fore.GREEN}{deals['active']} actifs")
        print(f"  🎯 Deals récents: {Fore.CYAN}{deals['today']} aujourd'hui, {deals['week']} cette semaine")
        
        # Alertes
        alerts = stats['alerts']
        print(f"  🔔 Alertes: {Fore.WHITE}{alerts['total']:,} total")
        print(f"  📬 Alertes récentes: {Fore.CYAN}{alerts['today']} aujourd'hui, {alerts['week']} cette semaine")
    
    def display_recent_activity(self):
        """Afficher l'activité récente"""
        
        print(f"\n{Fore.BLUE}⚡ ACTIVITÉ RÉCENTE (dernière heure)")
        print(f"{Fore.WHITE}{'─' * 40}")
        
        # Activité de la dernière heure
        one_hour_ago = datetime.now() - timedelta(hours=1)
        
        recent_scans = self.db.query(PriceHistory).filter(
            PriceHistory.scanned_at >= one_hour_ago
        ).count()
        
        recent_deals = self.db.query(Deal).filter(
            Deal.detected_at >= one_hour_ago
        ).count()
        
        recent_alerts = self.db.query(Alert).filter(
            Alert.created_at >= one_hour_ago
        ).count()
        
        print(f"  🔍 Scans effectués: {Fore.CYAN}{recent_scans}")
        print(f"  💰 Deals détectés: {Fore.GREEN}{recent_deals}")
        print(f"  🔔 Alertes envoyées: {Fore.YELLOW}{recent_alerts}")
        
        # Taux de détection
        detection_rate = (recent_deals / max(recent_scans, 1)) * 100
        color = Fore.GREEN if detection_rate > 5 else Fore.YELLOW if detection_rate > 1 else Fore.RED
        print(f"  📈 Taux de détection: {color}{detection_rate:.2f}%")
    
    def display_api_quota(self):
        """Afficher l'utilisation du quota API"""
        
        print(f"\n{Fore.MAGENTA}📊 QUOTA API")
        print(f"{Fore.WHITE}{'─' * 40}")
        
        # Quota aujourd'hui
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        scans_today = self.db.query(PriceHistory).filter(
            PriceHistory.scanned_at >= today
        ).count()
        
        daily_limit = 333
        remaining = max(0, daily_limit - scans_today)
        usage_pct = (scans_today / daily_limit) * 100
        
        # Couleur selon l'usage
        if usage_pct < 70:
            color = Fore.GREEN
        elif usage_pct < 90:
            color = Fore.YELLOW
        else:
            color = Fore.RED
        
        print(f"  📅 Aujourd'hui: {color}{scans_today:,}/{daily_limit:,} ({usage_pct:.1f}%)")
        print(f"  🔄 Restant: {Fore.CYAN}{remaining:,} requêtes")
        
        # Prévision
        current_hour = datetime.now().hour
        if current_hour > 0:
            hourly_rate = scans_today / current_hour
            projected_daily = hourly_rate * 24
            
            if projected_daily > daily_limit:
                print(f"  ⚠️  Projection: {Fore.RED}{projected_daily:.0f} requêtes/jour (dépassement!)")
            else:
                print(f"  📈 Projection: {Fore.GREEN}{projected_daily:.0f} requêtes/jour")
    
    def display_system_health(self):
        """Afficher la santé du système"""
        
        health = self.admin_service.get_system_health()
        
        print(f"\n{Fore.CYAN}🏥 SANTÉ DU SYSTÈME")
        print(f"{Fore.WHITE}{'─' * 40}")
        
        # Status général
        status = health['status']
        if status == 'healthy':
            status_color = Fore.GREEN
            status_icon = "✅"
        elif status == 'warning':
            status_color = Fore.YELLOW
            status_icon = "⚠️"
        else:
            status_color = Fore.RED
            status_icon = "❌"
        
        print(f"  {status_icon} Status: {status_color}{status.upper()}")
        print(f"  🔍 Scans récents: {Fore.CYAN}{health['recent_scans']}")
        print(f"  💰 Deals récents: {Fore.GREEN}{health['recent_deals']}")
        print(f"  🔔 Alertes récentes: {Fore.YELLOW}{health['recent_alerts']}")
        
        # Vérifications
        if health['recent_scans'] == 0:
            print(f"  {Fore.RED}⚠️  Aucun scan dans la dernière heure!")
        if health['recent_deals'] == 0 and health['recent_scans'] > 10:
            print(f"  {Fore.YELLOW}⚠️  Aucun deal détecté récemment")
    
    def display_top_routes(self):
        """Afficher les routes les plus performantes"""
        
        print(f"\n{Fore.YELLOW}🏆 TOP ROUTES (7 derniers jours)")
        print(f"{Fore.WHITE}{'─' * 40}")
        
        # Routes les plus performantes
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        top_routes = self.db.query(
            Route.origin,
            Route.destination,
            Route.tier,
            func.count(Deal.id).label('deals_count')
        ).join(Deal).filter(
            Deal.detected_at >= seven_days_ago
        ).group_by(
            Route.origin, Route.destination, Route.tier
        ).order_by(
            func.count(Deal.id).desc()
        ).limit(5).all()
        
        if top_routes:
            for i, route in enumerate(top_routes, 1):
                tier_color = Fore.GREEN if route.tier == 1 else Fore.YELLOW if route.tier == 2 else Fore.CYAN
                print(f"  {i}. {route.origin} → {route.destination} "
                      f"({tier_color}T{route.tier}{Fore.WHITE}): {Fore.GREEN}{route.deals_count} deals")
        else:
            print(f"  {Fore.GRAY}Aucune route avec des deals récents")
    
    def display_recent_alerts(self):
        """Afficher les dernières alertes"""
        
        print(f"\n{Fore.CYAN}🔔 DERNIÈRES ALERTES")
        print(f"{Fore.WHITE}{'─' * 40}")
        
        # Dernières alertes
        recent_alerts = self.db.query(Alert).join(Deal).join(Route).order_by(
            Alert.created_at.desc()
        ).limit(3).all()
        
        if recent_alerts:
            for alert in recent_alerts:
                time_diff = datetime.now() - alert.created_at
                if time_diff.total_seconds() < 3600:  # Moins d'une heure
                    time_str = f"{int(time_diff.total_seconds() / 60)}min"
                else:
                    time_str = f"{int(time_diff.total_seconds() / 3600)}h"
                
                deal = alert.deal
                route = deal.route
                
                print(f"  🔔 {route.origin} → {route.destination} "
                      f"({Fore.GREEN}-{deal.discount_percentage:.0f}%{Fore.WHITE}) "
                      f"il y a {Fore.CYAN}{time_str}")
        else:
            print(f"  {Fore.GRAY}Aucune alerte récente")


def main():
    """Fonction principale"""
    
    try:
        monitor = ScannerMonitor()
        monitor.run()
    except Exception as e:
        print(f"{Fore.RED}Erreur: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
