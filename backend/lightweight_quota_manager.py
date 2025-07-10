#!/usr/bin/env python3
"""
Lightweight Autonomous Call Manager
Streamlined version for immediate use without heavy dependencies
"""

import sqlite3
import sys
import os
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional
import json

# Add the backend path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    # Fallback color definitions
    class Fore:
        RED = GREEN = YELLOW = BLUE = CYAN = WHITE = MAGENTA = ""
    class Style:
        BRIGHT = RESET_ALL = ""


class LightweightQuotaManager:
    """Lightweight quota manager using direct SQLite access"""
    
    def __init__(self):
        self.db_path = "/Users/moussa/globegenius/backend/globegenius.db"
        self.daily_limit = 333
        self.monthly_limit = 10000
        
    def get_quota_status(self) -> Dict[str, Any]:
        """Get current quota status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Today's calls
            today = date.today()
            today_start = datetime.combine(today, datetime.min.time())
            
            cursor.execute("""
                SELECT COUNT(*) FROM api_calls 
                WHERE api_provider = 'flightlabs' 
                AND called_at >= ?
            """, (today_start,))
            today_calls = cursor.fetchone()[0] or 0
            
            # Monthly calls
            month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            cursor.execute("""
                SELECT COUNT(*) FROM api_calls 
                WHERE api_provider = 'flightlabs' 
                AND called_at >= ?
            """, (month_start,))
            monthly_calls = cursor.fetchone()[0] or 0
            
            # Calculate percentages and status
            daily_percentage = (today_calls / self.daily_limit) * 100
            monthly_percentage = (monthly_calls / self.monthly_limit) * 100
            
            max_percentage = max(daily_percentage, monthly_percentage)
            if max_percentage >= 100:
                status = 'over_limit'
            elif max_percentage >= 95:
                status = 'critical'
            elif max_percentage >= 85:
                status = 'warning'
            else:
                status = 'healthy'
            
            conn.close()
            
            return {
                'today_calls': today_calls,
                'daily_limit': self.daily_limit,
                'monthly_calls': monthly_calls,
                'monthly_limit': self.monthly_limit,
                'daily_percentage': daily_percentage,
                'monthly_percentage': monthly_percentage,
                'remaining_today': max(0, self.daily_limit - today_calls),
                'remaining_monthly': max(0, self.monthly_limit - monthly_calls),
                'status': status
            }
            
        except Exception as e:
            print(f"Error getting quota status: {e}")
            return {
                'today_calls': 0, 'daily_limit': 333, 'monthly_calls': 0, 
                'monthly_limit': 10000, 'daily_percentage': 0, 'monthly_percentage': 0,
                'remaining_today': 333, 'remaining_monthly': 10000, 'status': 'unknown'
            }
    
    def get_route_stats(self) -> Dict[str, Any]:
        """Get route statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Route counts by tier
            cursor.execute("SELECT tier, COUNT(*) FROM routes WHERE is_active = 1 GROUP BY tier")
            tier_counts = dict(cursor.fetchall())
            
            # Total routes
            cursor.execute("SELECT COUNT(*) FROM routes WHERE is_active = 1")
            total_active = cursor.fetchone()[0] or 0
            
            # Recent deals
            week_ago = datetime.now() - timedelta(days=7)
            cursor.execute("SELECT COUNT(*) FROM deals WHERE detected_at >= ?", (week_ago,))
            recent_deals = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'total_active': total_active,
                'tier_1': tier_counts.get(1, 0),
                'tier_2': tier_counts.get(2, 0),
                'tier_3': tier_counts.get(3, 0),
                'recent_deals': recent_deals
            }
            
        except Exception as e:
            print(f"Error getting route stats: {e}")
            return {'total_active': 0, 'tier_1': 0, 'tier_2': 0, 'tier_3': 0, 'recent_deals': 0}
    
    def calculate_recommended_strategy(self, quota_status: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate recommended API call strategy"""
        status = quota_status['status']
        remaining_daily = quota_status['remaining_today']
        
        if status == 'over_limit':
            # Emergency mode - minimal calls
            strategy = {
                'mode': 'emergency',
                'daily_budget': min(20, remaining_daily),
                'tier_1_scans': 1,  # Once daily
                'tier_2_scans': 0,  # Disabled
                'tier_3_scans': 0,  # Disabled
                'description': 'Emergency mode - quota exceeded'
            }
        elif status == 'critical':
            # Crisis mode - very conservative
            strategy = {
                'mode': 'crisis',
                'daily_budget': min(80, remaining_daily),
                'tier_1_scans': 2,  # Twice daily
                'tier_2_scans': 1,  # Once daily
                'tier_3_scans': 0,  # Disabled
                'description': 'Crisis mode - approaching quota limit'
            }
        elif status == 'warning':
            # Conservative mode
            strategy = {
                'mode': 'conservative',
                'daily_budget': min(180, remaining_daily),
                'tier_1_scans': 3,  # 3 times daily
                'tier_2_scans': 2,  # 2 times daily
                'tier_3_scans': 1,  # Once daily
                'description': 'Conservative mode - high quota usage'
            }
        else:
            # Normal mode
            strategy = {
                'mode': 'normal',
                'daily_budget': 333,
                'tier_1_scans': 4,  # 4 times daily (every 6h)
                'tier_2_scans': 3,  # 3 times daily (every 8h)
                'tier_3_scans': 2,  # 2 times daily (every 12h)
                'description': 'Normal mode - healthy quota usage'
            }
        
        # Calculate estimated daily usage based on active routes
        route_stats = self.get_route_stats()
        estimated_usage = (
            route_stats['tier_1'] * strategy['tier_1_scans'] +
            route_stats['tier_2'] * strategy['tier_2_scans'] +
            route_stats['tier_3'] * strategy['tier_3_scans']
        )
        
        strategy['estimated_usage'] = estimated_usage
        strategy['efficiency_score'] = min(100, (strategy['daily_budget'] / max(estimated_usage, 1)) * 50)
        
        return strategy
    
    def display_status(self):
        """Display current system status"""
        quota_status = self.get_quota_status()
        route_stats = self.get_route_stats()
        strategy = self.calculate_recommended_strategy(quota_status)
        
        # Colors based on status
        status_colors = {
            'healthy': Fore.GREEN,
            'warning': Fore.YELLOW,
            'critical': Fore.RED,
            'over_limit': Fore.MAGENTA,
            'unknown': Fore.WHITE
        }
        status_color = status_colors.get(quota_status['status'], Fore.WHITE)
        
        print(f"\n{Fore.CYAN}{Style.BRIGHT}🤖 GLOBEGENIUS QUOTA MANAGER{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 50}")
        
        # Quota Status
        print(f"\n{Fore.YELLOW}📊 QUOTA STATUS: {status_color}{quota_status['status'].upper()}")
        print(f"{Fore.WHITE}   Today: {quota_status['today_calls']}/{quota_status['daily_limit']} ({quota_status['daily_percentage']:.1f}%)")
        print(f"   Month: {quota_status['monthly_calls']}/{quota_status['monthly_limit']} ({quota_status['monthly_percentage']:.1f}%)")
        print(f"   Remaining: {quota_status['remaining_today']} today, {quota_status['remaining_monthly']} monthly")
        
        # Route Status
        print(f"\n{Fore.YELLOW}🛣️ ROUTE STATUS:")
        print(f"   Active Routes: {route_stats['total_active']}")
        print(f"   Tier 1: {route_stats['tier_1']} | Tier 2: {route_stats['tier_2']} | Tier 3: {route_stats['tier_3']}")
        print(f"   Deals (7 days): {route_stats['recent_deals']}")
        
        # Recommended Strategy
        mode_color = {
            'normal': Fore.GREEN,
            'conservative': Fore.YELLOW,
            'crisis': Fore.RED,
            'emergency': Fore.MAGENTA
        }.get(strategy['mode'], Fore.WHITE)
        
        print(f"\n{Fore.YELLOW}⚙️ RECOMMENDED STRATEGY: {mode_color}{strategy['mode'].upper()}")
        print(f"{Fore.WHITE}   {strategy['description']}")
        print(f"   Daily Budget: {strategy['daily_budget']} calls")
        print(f"   Estimated Usage: {strategy['estimated_usage']} calls/day")
        print(f"   Efficiency: {strategy['efficiency_score']:.1f}%")
        print(f"   Scanning Schedule:")
        print(f"     • Tier 1: {strategy['tier_1_scans']} times/day")
        print(f"     • Tier 2: {strategy['tier_2_scans']} times/day")
        print(f"     • Tier 3: {strategy['tier_3_scans']} times/day")
        
        # Recommendations
        print(f"\n{Fore.YELLOW}💡 RECOMMENDATIONS:")
        if quota_status['status'] == 'over_limit':
            print(f"   🚨 URGENT: Monthly quota exceeded!")
            print(f"   • Consider upgrading to 20k calls/month")
            print(f"   • Pause Tier 2 & 3 routes immediately")
        elif quota_status['status'] == 'critical':
            print(f"   ⚠️ Critical quota usage detected")
            print(f"   • Enable conservative mode")
            print(f"   • Focus only on Tier 1 routes")
        elif quota_status['status'] == 'warning':
            print(f"   ⚡ High quota usage")
            print(f"   • Monitor closely")
            print(f"   • Optimize underperforming routes")
        else:
            print(f"   ✅ System running optimally")
            print(f"   • Consider expanding network")
        
        return quota_status, strategy
    
    def apply_emergency_mode(self):
        """Apply emergency quota conservation"""
        print(f"\n{Fore.RED}🚨 APPLYING EMERGENCY MODE")
        print(f"   • Reducing all scanning to minimum")
        print(f"   • Only Tier 1 routes, once daily")
        print(f"   • Estimated usage: ~20 calls/day")
        
        # In a real implementation, this would update Celery schedules
        # For now, we'll just save the recommendation
        emergency_config = {
            'applied_at': datetime.now().isoformat(),
            'mode': 'emergency',
            'tier_1_frequency': 'once_daily',
            'tier_2_frequency': 'disabled',
            'tier_3_frequency': 'disabled',
            'daily_budget': 20
        }
        
        try:
            config_path = "/Users/moussa/globegenius/backend/logs/emergency_config.json"
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(emergency_config, f, indent=2)
            print(f"{Fore.GREEN}   ✅ Emergency configuration saved")
            print(f"   📄 Config saved to: {config_path}")
        except Exception as e:
            print(f"{Fore.RED}   ❌ Failed to save config: {e}")
        
        return True
    
    def optimize_routes(self):
        """Optimize route distribution based on performance"""
        print(f"\n{Fore.YELLOW}🧠 OPTIMIZING ROUTE DISTRIBUTION...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get route performance data
            week_ago = datetime.now() - timedelta(days=7)
            cursor.execute("""
                SELECT r.id, r.origin, r.destination, r.tier, COUNT(d.id) as deals_count
                FROM routes r
                LEFT JOIN deals d ON r.id = d.route_id AND d.detected_at >= ?
                WHERE r.is_active = 1
                GROUP BY r.id, r.origin, r.destination, r.tier
                ORDER BY deals_count DESC, r.tier ASC
            """, (week_ago,))
            
            routes = cursor.fetchall()
            
            print(f"   📊 Analyzed {len(routes)} active routes")
            
            # Identify top performers
            top_performers = [r for r in routes if r[4] >= 3]  # 3+ deals in last week
            underperformers = [r for r in routes if r[4] == 0]  # No deals
            
            print(f"   🏆 Top performers: {len(top_performers)} routes")
            print(f"   ⚠️ Underperformers: {len(underperformers)} routes")
            
            # Show top 5 performers
            if top_performers:
                print(f"\n   {Fore.GREEN}Top 5 performing routes:")
                for i, route in enumerate(top_performers[:5], 1):
                    print(f"     {i}. {route[1]}→{route[2]} (T{route[3]}) - {route[4]} deals")
            
            # Show bottom 5 underperformers
            if underperformers:
                print(f"\n   {Fore.RED}Underperforming routes (0 deals):")
                for i, route in enumerate(underperformers[:5], 1):
                    print(f"     {i}. {route[1]}→{route[2]} (T{route[3]})")
            
            # Save optimization report
            optimization_report = {
                'analyzed_at': datetime.now().isoformat(),
                'total_routes': len(routes),
                'top_performers': len(top_performers),
                'underperformers': len(underperformers),
                'recommendations': []
            }
            
            if len(underperformers) > len(routes) * 0.3:  # More than 30% underperforming
                optimization_report['recommendations'].append("Consider deactivating consistently underperforming routes")
            
            if len(top_performers) < len(routes) * 0.1:  # Less than 10% performing well
                optimization_report['recommendations'].append("Review route selection and tier assignments")
            
            conn.close()
            
            # Save report
            report_path = "/Users/moussa/globegenius/backend/logs/optimization_report.json"
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            with open(report_path, 'w') as f:
                json.dump(optimization_report, f, indent=2, default=str)
            
            print(f"\n   ✅ Optimization analysis complete")
            print(f"   📄 Report saved to: {report_path}")
            
            return optimization_report
            
        except Exception as e:
            print(f"{Fore.RED}   ❌ Optimization failed: {e}")
            return None


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Lightweight GlobeGenius Quota Manager")
    parser.add_argument('--status', action='store_true', help='Show system status')
    parser.add_argument('--quota', action='store_true', help='Show quota only')
    parser.add_argument('--emergency', action='store_true', help='Apply emergency mode')
    parser.add_argument('--optimize', action='store_true', help='Optimize routes')
    
    args = parser.parse_args()
    
    manager = LightweightQuotaManager()
    
    try:
        if args.quota:
            quota_status = manager.get_quota_status()
            print(f"📊 Quota Status: {quota_status['status']}")
            print(f"   Today: {quota_status['today_calls']}/{quota_status['daily_limit']} ({quota_status['daily_percentage']:.1f}%)")
            print(f"   Month: {quota_status['monthly_calls']}/{quota_status['monthly_limit']} ({quota_status['monthly_percentage']:.1f}%)")
        elif args.emergency:
            manager.apply_emergency_mode()
        elif args.optimize:
            manager.optimize_routes()
        elif args.status:
            manager.display_status()
        else:
            # Interactive mode
            manager.display_status()
            print(f"\n{Fore.WHITE}Available commands:")
            print(f"  --status      Show detailed status")
            print(f"  --quota       Show quota only")
            print(f"  --emergency   Apply emergency mode")
            print(f"  --optimize    Optimize routes")
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Manager interrupted by user")
    except Exception as e:
        print(f"{Fore.RED}❌ Manager error: {e}")


if __name__ == "__main__":
    main()
