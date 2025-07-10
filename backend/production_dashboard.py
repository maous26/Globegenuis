#!/usr/bin/env python3
"""
Production Dashboard for GlobeGenius
Real-time monitoring of FlightLabs API usage, deal detection, and system health
"""

import sys
import os
import time
from datetime import datetime, timedelta, date
import subprocess

sys.path.insert(0, '/Users/moussa/globegenius/backend')

from app.core.database import SessionLocal
from app.models.flight import Route, Deal, PriceHistory
from app.models.api_tracking import ApiCall
from app.models.user import User
from app.models.alert import Alert
from colorama import init, Fore, Style
from sqlalchemy import func, and_

# Initialize colorama
init(autoreset=True)


class ProductionDashboard:
    """Real-time production monitoring dashboard"""
    
    def __init__(self):
        self.db = SessionLocal()
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
    def print_header(self):
        """Print dashboard header"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{Fore.CYAN}{Style.BRIGHT}🚀 GLOBEGENIUS PRODUCTION DASHBOARD")
        print(f"{Fore.CYAN}{'=' * 60}")
        print(f"{Fore.WHITE}Time: {current_time} | Mode: PRODUCTION")
        print()
        
    def check_services(self):
        """Check if all services are running"""
        services = {
            "Redis": "redis-server",
            "Celery Worker": "celery.*worker",
            "Celery Beat": "celery.*beat",
            "FastAPI": "uvicorn"
        }
        
        print(f"{Fore.YELLOW}🔧 SERVICE STATUS")
        print(f"{Fore.WHITE}{'─' * 40}")
        
        all_running = True
        for service_name, process_name in services.items():
            try:
                result = subprocess.run(['pgrep', '-f', process_name], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"  ✅ {service_name}: {Fore.GREEN}Running")
                else:
                    print(f"  ❌ {service_name}: {Fore.RED}Stopped")
                    all_running = False
            except Exception:
                print(f"  ❓ {service_name}: {Fore.YELLOW}Unknown")
                all_running = False
                
        return all_running
        
    def show_api_quota(self):
        """Show FlightLabs API quota usage"""
        print(f"\n{Fore.BLUE}📊 FLIGHTLABS API QUOTA")
        print(f"{Fore.WHITE}{'─' * 40}")
        
        # Today's usage
        today = date.today()
        today_calls = self.db.query(ApiCall).filter(
            ApiCall.api_provider == 'flightlabs',
            ApiCall.called_at >= datetime.combine(today, datetime.min.time())
        ).count()
        
        # This month's usage
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_calls = self.db.query(ApiCall).filter(
            ApiCall.api_provider == 'flightlabs',
            ApiCall.called_at >= month_start
        ).count()
        
        # Calculate percentages and colors
        daily_pct = (today_calls / 333) * 100
        monthly_pct = (monthly_calls / 10000) * 100
        
        daily_color = Fore.RED if daily_pct > 90 else Fore.YELLOW if daily_pct > 70 else Fore.GREEN
        monthly_color = Fore.RED if monthly_pct > 90 else Fore.YELLOW if monthly_pct > 70 else Fore.GREEN
        
        print(f"  📅 Today: {daily_color}{today_calls}/333{Fore.WHITE} ({daily_pct:.1f}%)")
        print(f"  📈 Month: {monthly_color}{monthly_calls}/10,000{Fore.WHITE} ({monthly_pct:.1f}%)")
        print(f"  🔄 Remaining today: {Fore.CYAN}{max(0, 333 - today_calls)}")
        print(f"  🔄 Remaining month: {Fore.CYAN}{max(0, 10000 - monthly_calls):,}")
        
        # Recent API activity
        last_hour = datetime.now() - timedelta(hours=1)
        recent_calls = self.db.query(ApiCall).filter(
            ApiCall.api_provider == 'flightlabs',
            ApiCall.called_at >= last_hour
        ).count()
        
        print(f"  ⚡ Last hour: {Fore.CYAN}{recent_calls} calls")
        
        return {
            'today_calls': today_calls,
            'monthly_calls': monthly_calls,
            'recent_calls': recent_calls
        }
        
    def show_scanning_activity(self):
        """Show recent scanning activity"""
        print(f"\n{Fore.GREEN}🔍 SCANNING ACTIVITY")
        print(f"{Fore.WHITE}{'─' * 40}")
        
        # Routes by tier
        tier_stats = self.db.query(
            Route.tier,
            func.count(Route.id).label('count')
        ).filter(Route.is_active == True).group_by(Route.tier).all()
        
        total_routes = sum(stat.count for stat in tier_stats)
        print(f"  🛣️  Active routes: {Fore.WHITE}{total_routes}")
        
        for tier in tier_stats:
            print(f"     Tier {tier.tier}: {Fore.CYAN}{tier.count} routes")
            
        # Recent scans
        last_24h = datetime.now() - timedelta(hours=24)
        recent_scans = self.db.query(PriceHistory).filter(
            PriceHistory.scanned_at >= last_24h
        ).count()
        
        print(f"  📊 Scans (24h): {Fore.CYAN}{recent_scans}")
        
        return {
            'total_routes': total_routes,
            'recent_scans': recent_scans
        }
        
    def show_deals_found(self):
        """Show recent deals found"""
        print(f"\n{Fore.MAGENTA}💎 DEALS DETECTED")
        print(f"{Fore.WHITE}{'─' * 40}")
        
        # Deals today
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        deals_today = self.db.query(Deal).filter(
            Deal.detected_at >= today,
            Deal.is_active == True
        ).count()
        
        # Deals this week
        week_ago = datetime.now() - timedelta(days=7)
        deals_week = self.db.query(Deal).filter(
            Deal.detected_at >= week_ago,
            Deal.is_active == True
        ).count()
        
        # Deal types
        error_fares = self.db.query(Deal).filter(
            Deal.detected_at >= week_ago,
            Deal.is_error_fare == True,
            Deal.is_active == True
        ).count()
        
        print(f"  📅 Today: {Fore.GREEN}{deals_today} deals")
        print(f"  📊 This week: {Fore.CYAN}{deals_week} deals")
        print(f"  🎯 Error fares: {Fore.YELLOW}{error_fares} deals")
        
        # Recent top deals
        recent_deals = self.db.query(Deal).join(Route).filter(
            Deal.detected_at >= week_ago,
            Deal.is_active == True
        ).order_by(Deal.discount_percentage.desc()).limit(3).all()
        
        if recent_deals:
            print(f"\n  🏆 Top Recent Deals:")
            for deal in recent_deals:
                route = deal.route
                print(f"     {route.origin}→{route.destination}: "
                      f"{Fore.GREEN}€{deal.deal_price}{Fore.WHITE} "
                      f"(-{deal.discount_percentage:.0f}%)")
                      
        return {
            'deals_today': deals_today,
            'deals_week': deals_week,
            'error_fares': error_fares
        }
        
    def show_user_activity(self):
        """Show user activity"""
        print(f"\n{Fore.CYAN}👥 USER ACTIVITY")
        print(f"{Fore.WHITE}{'─' * 40}")
        
        # Total users
        total_users = self.db.query(User).count()
        active_users = self.db.query(User).filter(User.is_active == True).count()
        
        # Recent alerts
        last_24h = datetime.now() - timedelta(hours=24)
        alerts_sent = self.db.query(Alert).filter(
            Alert.created_at >= last_24h
        ).count()
        
        print(f"  👥 Total users: {Fore.WHITE}{total_users}")
        print(f"  ✅ Active users: {Fore.GREEN}{active_users}")
        print(f"  🔔 Alerts sent (24h): {Fore.YELLOW}{alerts_sent}")
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'alerts_sent': alerts_sent
        }
        
    def show_system_health(self):
        """Show overall system health"""
        print(f"\n{Fore.RED}🏥 SYSTEM HEALTH")
        print(f"{Fore.WHITE}{'─' * 40}")
        
        # Calculate health score
        health_score = 100
        issues = []
        
        # Check API quota
        quota_info = self.show_api_quota()
        daily_usage_pct = (quota_info['today_calls'] / 333) * 100
        if daily_usage_pct > 90:
            health_score -= 20
            issues.append("High API usage")
        elif daily_usage_pct > 70:
            health_score -= 10
            issues.append("Moderate API usage")
            
        # Check recent activity
        if quota_info['recent_calls'] == 0:
            health_score -= 15
            issues.append("No recent API activity")
            
        # Determine health status
        if health_score >= 85:
            status = f"{Fore.GREEN}EXCELLENT"
        elif health_score >= 70:
            status = f"{Fore.YELLOW}GOOD"
        elif health_score >= 50:
            status = f"{Fore.YELLOW}WARNING"
        else:
            status = f"{Fore.RED}CRITICAL"
            
        print(f"  🎯 Health Score: {status} {health_score}/100")
        
        if issues:
            print(f"  ⚠️  Issues:")
            for issue in issues:
                print(f"     • {issue}")
        else:
            print(f"  ✅ No issues detected")
            
    def run_dashboard(self):
        """Run the interactive dashboard"""
        try:
            while True:
                self.clear_screen()
                self.print_header()
                
                # Show all sections
                services_ok = self.check_services()
                self.show_api_quota()
                self.show_scanning_activity()
                self.show_deals_found()
                self.show_user_activity()
                self.show_system_health()
                
                print(f"\n{Fore.WHITE}Press Ctrl+C to exit | Refreshing in 30s...")
                time.sleep(30)
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Dashboard stopped by user")
        finally:
            self.db.close()


def main():
    """Main dashboard entry point"""
    dashboard = ProductionDashboard()
    dashboard.run_dashboard()


if __name__ == "__main__":
    main()
