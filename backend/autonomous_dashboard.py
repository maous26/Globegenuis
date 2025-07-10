#!/usr/bin/env python3
"""
Management Dashboard for Autonomous Call Manager
Provides real-time control and monitoring of the autonomous system
"""

import sys
import os
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any

# Add the backend path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from autonomous_call_manager import AutonomousCallManager
from app.core.database import SessionLocal
from app.models.flight import Route, Deal
from app.models.api_tracking import ApiCall
from colorama import init, Fore, Style, Back
import colorama

# Initialize colorama
init(autoreset=True)


class AutonomousDashboard:
    """Interactive dashboard for managing the autonomous call system"""
    
    def __init__(self):
        self.manager = AutonomousCallManager()
        self.db = SessionLocal()
        
    def display_main_menu(self):
        """Display the main dashboard menu"""
        self.clear_screen()
        
        print(f"{Back.BLUE}{Fore.WHITE}{Style.BRIGHT}                GLOBEGENIUS AUTONOMOUS CALL MANAGER                {Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 80}")
        
        # Get current status
        quota_status = self.manager.get_quota_status()
        strategy = self.manager.calculate_optimal_strategy(quota_status)
        
        # Status overview
        status_color = {
            'healthy': Fore.GREEN,
            'warning': Fore.YELLOW,
            'critical': Fore.RED,
            'over_limit': Fore.MAGENTA
        }.get(quota_status.status, Fore.WHITE)
        
        print(f"\n{Fore.YELLOW}📊 SYSTEM STATUS: {status_color}{quota_status.status.upper()}")
        print(f"{Fore.WHITE}   Quota Today: {quota_status.today_calls}/{quota_status.daily_limit} ({quota_status.daily_percentage:.1f}%)")
        print(f"   Quota Month: {quota_status.monthly_calls}/{quota_status.monthly_limit} ({quota_status.monthly_percentage:.1f}%)")
        print(f"   Current Strategy: {strategy.estimated_daily_usage} calls/day (Efficiency: {strategy.efficiency_score}%)")
        
        # Recent performance
        deals_today = self._get_deals_today()
        deals_week = self._get_deals_week()
        
        print(f"\n{Fore.YELLOW}🎯 PERFORMANCE:")
        print(f"   Deals Today: {Fore.GREEN}{deals_today}")
        print(f"   Deals This Week: {Fore.GREEN}{deals_week}")
        print(f"   Calls/Deal Ratio: {Fore.CYAN}{(quota_status.today_calls / max(deals_today, 1)):.1f}")
        
        # Menu options
        print(f"\n{Fore.CYAN}📋 MANAGEMENT OPTIONS:")
        print(f"   {Fore.WHITE}1. {Fore.GREEN}View Detailed Status")
        print(f"   {Fore.WHITE}2. {Fore.YELLOW}Run Optimization Now")
        print(f"   {Fore.WHITE}3. {Fore.BLUE}Adjust Strategy")
        print(f"   {Fore.WHITE}4. {Fore.MAGENTA}Route Management")
        print(f"   {Fore.WHITE}5. {Fore.CYAN}Performance Analytics")
        print(f"   {Fore.WHITE}6. {Fore.RED}Emergency Controls")
        print(f"   {Fore.WHITE}7. {Fore.WHITE}Export Settings")
        print(f"   {Fore.WHITE}0. {Fore.YELLOW}Exit")
        
        print(f"\n{Fore.WHITE}Choose option: ", end="")
        
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def _get_deals_today(self) -> int:
        """Get number of deals found today"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return self.db.query(Deal).filter(Deal.detected_at >= today).count()
    
    def _get_deals_week(self) -> int:
        """Get number of deals found this week"""
        week_ago = datetime.now() - timedelta(days=7)
        return self.db.query(Deal).filter(Deal.detected_at >= week_ago).count()
    
    def show_detailed_status(self):
        """Show detailed system status"""
        self.clear_screen()
        print(f"{Fore.CYAN}{Style.BRIGHT}📊 DETAILED SYSTEM STATUS{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 60}")
        
        # Get data
        quota_status = self.manager.get_quota_status()
        strategy = self.manager.calculate_optimal_strategy(quota_status)
        
        # Quota details
        print(f"\n{Fore.YELLOW}💰 QUOTA ANALYSIS:")
        print(f"   Status: {self._get_status_color(quota_status.status)}{quota_status.status.upper()}")
        print(f"   Daily Usage: {quota_status.today_calls}/{quota_status.daily_limit} calls")
        print(f"   Daily %: {quota_status.daily_percentage:.1f}%")
        print(f"   Monthly Usage: {quota_status.monthly_calls}/{quota_status.monthly_limit} calls")
        print(f"   Monthly %: {quota_status.monthly_percentage:.1f}%")
        print(f"   Remaining Today: {Fore.GREEN}{quota_status.remaining_today}")
        print(f"   Remaining Month: {Fore.GREEN}{quota_status.remaining_monthly}")
        
        # Strategy details
        print(f"\n{Fore.YELLOW}⚙️ CURRENT STRATEGY:")
        print(f"   Daily Budget: {strategy.daily_calls_budget} calls")
        print(f"   Estimated Usage: {strategy.estimated_daily_usage} calls/day")
        print(f"   Efficiency Score: {strategy.efficiency_score}%")
        print(f"   Tier 1 Schedule: {strategy.tier_1_frequency}")
        print(f"   Tier 2 Schedule: {strategy.tier_2_frequency}")
        print(f"   Tier 3 Schedule: {strategy.tier_3_frequency}")
        
        # Route statistics
        route_stats = self._get_route_statistics()
        print(f"\n{Fore.YELLOW}🛣️ ROUTE STATISTICS:")
        print(f"   Total Routes: {route_stats['total']}")
        print(f"   Active Routes: {route_stats['active']}")
        print(f"   Tier 1: {route_stats['tier_1']} routes")
        print(f"   Tier 2: {route_stats['tier_2']} routes")
        print(f"   Tier 3: {route_stats['tier_3']} routes")
        
        # Performance metrics
        perf_metrics = self._get_performance_metrics()
        print(f"\n{Fore.YELLOW}📈 PERFORMANCE METRICS:")
        print(f"   Deals Today: {perf_metrics['deals_today']}")
        print(f"   Deals This Week: {perf_metrics['deals_week']}")
        print(f"   Avg Deal Value: €{perf_metrics['avg_deal_value']:.0f}")
        print(f"   Best Route: {perf_metrics['best_route']}")
        print(f"   API Efficiency: {perf_metrics['api_efficiency']:.1f} deals/100 calls")
        
        input(f"\n{Fore.WHITE}Press Enter to continue...")
    
    def run_optimization(self):
        """Run optimization with progress display"""
        self.clear_screen()
        print(f"{Fore.CYAN}{Style.BRIGHT}🤖 RUNNING AUTONOMOUS OPTIMIZATION{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 60}")
        
        print(f"\n{Fore.YELLOW}⏳ Analyzing current situation...")
        quota_status = self.manager.get_quota_status()
        print(f"   ✅ Quota status: {quota_status.status}")
        
        print(f"\n{Fore.YELLOW}⏳ Calculating optimal strategy...")
        strategy = self.manager.calculate_optimal_strategy(quota_status)
        print(f"   ✅ Strategy: {strategy.estimated_daily_usage} calls/day")
        
        print(f"\n{Fore.YELLOW}⏳ Optimizing routes...")
        route_optimization = self.manager.optimize_routes()
        if route_optimization['success']:
            print(f"   ✅ Routes optimized: {route_optimization['routes_optimized']}")
        else:
            print(f"   ❌ Route optimization failed: {route_optimization.get('error', 'Unknown error')}")
        
        print(f"\n{Fore.YELLOW}⏳ Applying strategy...")
        strategy_applied = self.manager.apply_strategy(strategy)
        if strategy_applied:
            print(f"   ✅ Strategy applied successfully")
        else:
            print(f"   ❌ Failed to apply strategy")
        
        # Show results
        print(f"\n{Fore.GREEN}🎉 OPTIMIZATION COMPLETE!")
        print(f"   Daily Budget: {strategy.daily_calls_budget} calls")
        print(f"   Estimated Usage: {strategy.estimated_daily_usage} calls/day")
        print(f"   Efficiency Score: {strategy.efficiency_score}%")
        
        if route_optimization['success']:
            recommendations = route_optimization.get('recommendations', [])
            if recommendations:
                print(f"\n{Fore.YELLOW}💡 RECOMMENDATIONS:")
                for rec in recommendations:
                    print(f"   • {rec}")
        
        input(f"\n{Fore.WHITE}Press Enter to continue...")
    
    def adjust_strategy(self):
        """Manual strategy adjustment interface"""
        self.clear_screen()
        print(f"{Fore.CYAN}{Style.BRIGHT}⚙️ STRATEGY ADJUSTMENT{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 60}")
        
        quota_status = self.manager.get_quota_status()
        current_strategy = self.manager.calculate_optimal_strategy(quota_status)
        
        print(f"\n{Fore.YELLOW}Current Strategy:")
        print(f"   Daily Budget: {current_strategy.daily_calls_budget} calls")
        print(f"   Estimated Usage: {current_strategy.estimated_daily_usage} calls/day")
        
        print(f"\n{Fore.CYAN}Strategy Options:")
        print(f"   1. 🚀 Aggressive (333 calls/day - High discovery)")
        print(f"   2. ⚖️ Balanced (250 calls/day - Recommended)")
        print(f"   3. 🛡️ Conservative (150 calls/day - Safe)")
        print(f"   4. 🚨 Emergency (50 calls/day - Crisis mode)")
        print(f"   5. 🔄 Auto (Let system decide)")
        print(f"   0. ← Back")
        
        choice = input(f"\n{Fore.WHITE}Choose strategy: ")
        
        if choice == '1':
            self._apply_custom_strategy('aggressive', 333)
        elif choice == '2':
            self._apply_custom_strategy('balanced', 250)
        elif choice == '3':
            self._apply_custom_strategy('conservative', 150)
        elif choice == '4':
            self._apply_custom_strategy('emergency', 50)
        elif choice == '5':
            self._apply_auto_strategy()
        elif choice != '0':
            print(f"{Fore.RED}Invalid choice!")
            input("Press Enter to continue...")
    
    def _apply_custom_strategy(self, strategy_name: str, daily_budget: int):
        """Apply a custom strategy"""
        print(f"\n{Fore.YELLOW}Applying {strategy_name} strategy ({daily_budget} calls/day)...")
        
        # Create custom strategy based on budget
        if daily_budget >= 300:
            tier_1_freq = "0 */6"      # Every 6 hours
            tier_2_freq = "15 */8"     # Every 8 hours
            tier_3_freq = "30 */12"    # Every 12 hours
        elif daily_budget >= 200:
            tier_1_freq = "0 */8"      # Every 8 hours
            tier_2_freq = "20 */12"    # Every 12 hours
            tier_3_freq = "40 8"       # Once daily
        elif daily_budget >= 100:
            tier_1_freq = "0 */12"     # Every 12 hours
            tier_2_freq = "30 8"       # Once daily
            tier_3_freq = "45 20"      # Once daily
        else:
            tier_1_freq = "0 8"        # Once daily
            tier_2_freq = "0 14"       # Once daily
            tier_3_freq = "0 20"       # Once daily
        
        from autonomous_call_manager import CallStrategy
        custom_strategy = CallStrategy(
            daily_calls_budget=daily_budget,
            tier_1_frequency=tier_1_freq,
            tier_2_frequency=tier_2_freq,
            tier_3_frequency=tier_3_freq,
            estimated_daily_usage=int(daily_budget * 0.9),
            efficiency_score=75.0
        )
        
        success = self.manager.apply_strategy(custom_strategy)
        
        if success:
            print(f"{Fore.GREEN}✅ {strategy_name.title()} strategy applied successfully!")
        else:
            print(f"{Fore.RED}❌ Failed to apply strategy!")
        
        input("Press Enter to continue...")
    
    def _apply_auto_strategy(self):
        """Apply automatic strategy"""
        print(f"\n{Fore.YELLOW}Applying automatic strategy...")
        
        quota_status = self.manager.get_quota_status()
        strategy = self.manager.calculate_optimal_strategy(quota_status)
        success = self.manager.apply_strategy(strategy)
        
        if success:
            print(f"{Fore.GREEN}✅ Automatic strategy applied!")
            print(f"   Budget: {strategy.daily_calls_budget} calls/day")
            print(f"   Efficiency: {strategy.efficiency_score}%")
        else:
            print(f"{Fore.RED}❌ Failed to apply automatic strategy!")
        
        input("Press Enter to continue...")
    
    def route_management(self):
        """Route management interface"""
        self.clear_screen()
        print(f"{Fore.CYAN}{Style.BRIGHT}🛣️ ROUTE MANAGEMENT{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 60}")
        
        # Route statistics
        route_stats = self._get_route_statistics()
        print(f"\n{Fore.YELLOW}📊 Route Overview:")
        print(f"   Total: {route_stats['total']} | Active: {route_stats['active']}")
        print(f"   T1: {route_stats['tier_1']} | T2: {route_stats['tier_2']} | T3: {route_stats['tier_3']}")
        
        # Top performing routes
        top_routes = self._get_top_routes()
        print(f"\n{Fore.YELLOW}🏆 Top Performing Routes (Last 7 days):")
        for i, route in enumerate(top_routes[:5], 1):
            print(f"   {i}. {route['route']} - {route['deals']} deals (avg {route['discount']:.0f}% off)")
        
        print(f"\n{Fore.CYAN}Route Options:")
        print(f"   1. 📈 Run Route Optimization")
        print(f"   2. 🔄 Rebalance Tiers")
        print(f"   3. 📋 View All Routes")
        print(f"   4. ⚙️ Manual Route Adjustment")
        print(f"   0. ← Back")
        
        choice = input(f"\n{Fore.WHITE}Choose option: ")
        
        if choice == '1':
            self._run_route_optimization()
        elif choice == '2':
            self._rebalance_tiers()
        elif choice == '3':
            self._view_all_routes()
        elif choice == '4':
            self._manual_route_adjustment()
        elif choice != '0':
            print(f"{Fore.RED}Invalid choice!")
            input("Press Enter to continue...")
    
    def emergency_controls(self):
        """Emergency control interface"""
        self.clear_screen()
        print(f"{Fore.RED}{Style.BRIGHT}🚨 EMERGENCY CONTROLS{Style.RESET_ALL}")
        print(f"{Fore.RED}{'=' * 60}")
        
        quota_status = self.manager.get_quota_status()
        
        print(f"\n{Fore.YELLOW}Current Status: {self._get_status_color(quota_status.status)}{quota_status.status.upper()}")
        print(f"Daily Usage: {quota_status.today_calls}/{quota_status.daily_limit} ({quota_status.daily_percentage:.1f}%)")
        print(f"Monthly Usage: {quota_status.monthly_calls}/{quota_status.monthly_limit} ({quota_status.monthly_percentage:.1f}%)")
        
        print(f"\n{Fore.RED}Emergency Options:")
        print(f"   1. 🛑 STOP ALL SCANNING (Emergency halt)")
        print(f"   2. 🔥 CRISIS MODE (50 calls/day max)")
        print(f"   3. ⏸️ PAUSE TIER 2 & 3 (Tier 1 only)")
        print(f"   4. 🔄 FORCE OPTIMIZATION (Override safety)")
        print(f"   5. 📊 QUOTA RESET (New month)")
        print(f"   0. ← Back")
        
        choice = input(f"\n{Fore.WHITE}{Style.BRIGHT}⚠️ Choose CAREFULLY: ")
        
        if choice == '1':
            self._emergency_stop()
        elif choice == '2':
            self._crisis_mode()
        elif choice == '3':
            self._pause_lower_tiers()
        elif choice == '4':
            self._force_optimization()
        elif choice == '5':
            self._quota_reset()
        elif choice != '0':
            print(f"{Fore.RED}Invalid choice!")
            input("Press Enter to continue...")
    
    def _get_status_color(self, status: str) -> str:
        """Get color for status"""
        return {
            'healthy': Fore.GREEN,
            'warning': Fore.YELLOW,
            'critical': Fore.RED,
            'over_limit': Fore.MAGENTA
        }.get(status, Fore.WHITE)
    
    def _get_route_statistics(self) -> Dict[str, int]:
        """Get route statistics"""
        total = self.db.query(Route).count()
        active = self.db.query(Route).filter(Route.is_active == True).count()
        tier_1 = self.db.query(Route).filter(Route.tier == 1, Route.is_active == True).count()
        tier_2 = self.db.query(Route).filter(Route.tier == 2, Route.is_active == True).count()
        tier_3 = self.db.query(Route).filter(Route.tier == 3, Route.is_active == True).count()
        
        return {
            'total': total,
            'active': active,
            'tier_1': tier_1,
            'tier_2': tier_2,
            'tier_3': tier_3
        }
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = datetime.now() - timedelta(days=7)
        
        deals_today = self.db.query(Deal).filter(Deal.detected_at >= today).count()
        deals_week = self.db.query(Deal).filter(Deal.detected_at >= week_ago).count()
        
        # Average deal value
        from sqlalchemy import func
        avg_deal = self.db.query(func.avg(Deal.deal_price)).filter(Deal.detected_at >= week_ago).scalar() or 0
        
        # Best performing route
        best_route_query = self.db.query(
            Route.origin,
            Route.destination,
            func.count(Deal.id).label('deal_count')
        ).join(Deal).filter(
            Deal.detected_at >= week_ago
        ).group_by(Route.origin, Route.destination).order_by(
            func.count(Deal.id).desc()
        ).first()
        
        best_route = f"{best_route_query.origin}→{best_route_query.destination}" if best_route_query else "None"
        
        # API efficiency
        week_calls = self.db.query(ApiCall).filter(
            ApiCall.api_provider == 'flightlabs',
            ApiCall.called_at >= week_ago
        ).count()
        
        api_efficiency = (deals_week / max(week_calls, 1)) * 100
        
        return {
            'deals_today': deals_today,
            'deals_week': deals_week,
            'avg_deal_value': avg_deal,
            'best_route': best_route,
            'api_efficiency': api_efficiency
        }
    
    def _get_top_routes(self) -> List[Dict[str, Any]]:
        """Get top performing routes"""
        week_ago = datetime.now() - timedelta(days=7)
        
        from sqlalchemy import func
        top_routes = self.db.query(
            Route.origin,
            Route.destination,
            func.count(Deal.id).label('deals'),
            func.avg(Deal.discount_percentage).label('avg_discount')
        ).join(Deal).filter(
            Deal.detected_at >= week_ago
        ).group_by(Route.origin, Route.destination).order_by(
            func.count(Deal.id).desc()
        ).limit(10).all()
        
        return [
            {
                'route': f"{route.origin}→{route.destination}",
                'deals': route.deals,
                'discount': route.avg_discount or 0
            }
            for route in top_routes
        ]
    
    def _emergency_stop(self):
        """Emergency stop all scanning"""
        confirm = input(f"\n{Fore.RED}{Style.BRIGHT}⚠️ CONFIRM EMERGENCY STOP? (type 'STOP'): ")
        if confirm == 'STOP':
            # Apply emergency strategy with minimal calls
            from autonomous_call_manager import CallStrategy
            emergency_strategy = CallStrategy(
                daily_calls_budget=0,
                tier_1_frequency="0 23",  # Once at 11 PM
                tier_2_frequency="0 23",  # Disabled essentially
                tier_3_frequency="0 23",  # Disabled essentially
                estimated_daily_usage=3,
                efficiency_score=0.0
            )
            
            success = self.manager.apply_strategy(emergency_strategy)
            if success:
                print(f"{Fore.GREEN}✅ Emergency stop activated!")
            else:
                print(f"{Fore.RED}❌ Failed to apply emergency stop!")
        else:
            print(f"{Fore.YELLOW}Emergency stop cancelled.")
        
        input("Press Enter to continue...")
    
    def _crisis_mode(self):
        """Activate crisis mode"""
        self._apply_custom_strategy('crisis', 50)
    
    def run(self):
        """Run the interactive dashboard"""
        while True:
            try:
                self.display_main_menu()
                choice = input().strip()
                
                if choice == '0':
                    print(f"\n{Fore.YELLOW}Goodbye!")
                    break
                elif choice == '1':
                    self.show_detailed_status()
                elif choice == '2':
                    self.run_optimization()
                elif choice == '3':
                    self.adjust_strategy()
                elif choice == '4':
                    self.route_management()
                elif choice == '5':
                    self.show_detailed_status()  # Performance analytics (detailed status for now)
                elif choice == '6':
                    self.emergency_controls()
                elif choice == '7':
                    self.export_settings()
                else:
                    print(f"{Fore.RED}Invalid choice! Press Enter to continue...")
                    input()
                    
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Dashboard interrupted by user")
                break
            except Exception as e:
                print(f"{Fore.RED}❌ Dashboard error: {e}")
                input("Press Enter to continue...")
    
    def export_settings(self):
        """Export current settings"""
        self.clear_screen()
        print(f"{Fore.CYAN}{Style.BRIGHT}📄 EXPORT SETTINGS{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 60}")
        
        # Get current configuration
        quota_status = self.manager.get_quota_status()
        strategy = self.manager.calculate_optimal_strategy(quota_status)
        route_stats = self._get_route_statistics()
        
        config = {
            'export_date': datetime.now().isoformat(),
            'quota_status': quota_status.__dict__,
            'current_strategy': {
                'daily_budget': strategy.daily_calls_budget,
                'estimated_usage': strategy.estimated_daily_usage,
                'efficiency_score': strategy.efficiency_score,
                'tier_frequencies': {
                    'tier_1': strategy.tier_1_frequency,
                    'tier_2': strategy.tier_2_frequency,
                    'tier_3': strategy.tier_3_frequency
                }
            },
            'route_statistics': route_stats,
            'performance_metrics': self._get_performance_metrics()
        }
        
        # Save to file
        filename = f"autonomous_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = f"/Users/moussa/globegenius/backend/logs/{filename}"
        
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2, default=str)
        
        print(f"{Fore.GREEN}✅ Configuration exported to: {filepath}")
        print(f"\n{Fore.YELLOW}Exported data includes:")
        print(f"   • Current quota status")
        print(f"   • Active strategy configuration")
        print(f"   • Route statistics")
        print(f"   • Performance metrics")
        
        input("\nPress Enter to continue...")
    
    def close(self):
        """Close connections"""
        self.manager.close()
        self.db.close()


def main():
    """Main entry point"""
    dashboard = AutonomousDashboard()
    
    try:
        dashboard.run()
    finally:
        dashboard.close()


if __name__ == "__main__":
    main()
