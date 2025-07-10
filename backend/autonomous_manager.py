#!/usr/bin/env python3
"""
Working Autonomous Call Manager
Simplified version that works with the current setup
"""

import sys
import os
import json
from datetime import datetime
from lightweight_quota_manager import LightweightQuotaManager

def main():
    """Main function for autonomous call manager"""
    
    # Initialize components
    manager = LightweightQuotaManager()
    
    # Colors for output
    try:
        from colorama import init, Fore, Style
        init(autoreset=True)
        colors = {'RED': Fore.RED, 'GREEN': Fore.GREEN, 'YELLOW': Fore.YELLOW, 
                  'BLUE': Fore.BLUE, 'CYAN': Fore.CYAN, 'WHITE': Fore.WHITE}
    except ImportError:
        colors = {'RED': '', 'GREEN': '', 'YELLOW': '', 'BLUE': '', 'CYAN': '', 'WHITE': ''}
    
    print(f"\n{colors['CYAN']}🤖 AUTONOMOUS CALL MANAGER")
    print(f"{colors['CYAN']}{'=' * 50}")
    
    # Get system status
    quota_status = manager.get_quota_status()
    route_stats = manager.get_route_stats()
    strategy = manager.calculate_recommended_strategy(quota_status)
    
    # Status colors
    status_colors = {
        'healthy': colors['GREEN'],
        'warning': colors['YELLOW'],
        'critical': colors['RED'],
        'over_limit': colors['RED']
    }
    status_color = status_colors.get(quota_status['status'], colors['WHITE'])
    
    print(f"\n{colors['YELLOW']}📊 QUOTA STATUS: {status_color}{quota_status['status'].upper()}")
    print(f"{colors['WHITE']}   Today: {quota_status['today_calls']}/{quota_status['daily_limit']} ({quota_status['daily_percentage']:.1f}%)")
    print(f"   Month: {quota_status['monthly_calls']}/{quota_status['monthly_limit']} ({quota_status['monthly_percentage']:.1f}%)")
    print(f"   Remaining: {quota_status['remaining_today']} today, {quota_status['remaining_monthly']} monthly")
    
    # Route status
    print(f"\n{colors['YELLOW']}🛣️ ROUTE STATUS:")
    print(f"   Active Routes: {route_stats['total_active']}")
    print(f"   Tier 1: {route_stats['tier_1']} | Tier 2: {route_stats['tier_2']} | Tier 3: {route_stats['tier_3']}")
    print(f"   Deals (7 days): {route_stats['recent_deals']}")
    print(f"   Efficiency: {route_stats['efficiency']:.1f}%")
    
    # Strategy
    mode_colors = {
        'normal': colors['GREEN'],
        'conservative': colors['YELLOW'],
        'crisis': colors['RED'],
        'emergency': colors['RED']
    }
    mode_color = mode_colors.get(strategy['mode'], colors['WHITE'])
    
    print(f"\n{colors['YELLOW']}⚙️ RECOMMENDED STRATEGY: {mode_color}{strategy['mode'].upper()}")
    print(f"{colors['WHITE']}   {strategy['description']}")
    print(f"   Daily Budget: {strategy['daily_budget']} calls")
    print(f"   Estimated Usage: {strategy['estimated_usage']} calls/day")
    print(f"   Efficiency: {strategy['efficiency_score']:.1f}%")
    
    # System health
    print(f"\n{colors['YELLOW']}🏥 SYSTEM HEALTH:")
    if quota_status['status'] == 'healthy':
        print(f"   {colors['GREEN']}✅ System running optimally")
        print(f"   {colors['WHITE']}• Consider expanding network if needed")
    elif quota_status['status'] == 'warning':
        print(f"   {colors['YELLOW']}⚠️ High quota usage detected")
        print(f"   {colors['WHITE']}• Monitor closely")
        print(f"   {colors['WHITE']}• Optimize underperforming routes")
    elif quota_status['status'] == 'critical':
        print(f"   {colors['RED']}🚨 Critical quota usage")
        print(f"   {colors['WHITE']}• Apply emergency mode immediately")
        print(f"   {colors['WHITE']}• Focus only on Tier 1 routes")
    else:
        print(f"   {colors['RED']}❌ System over quota limit")
        print(f"   {colors['WHITE']}• Immediate action required")
    
    # Command line actions
    import argparse
    parser = argparse.ArgumentParser(description="Autonomous Call Manager")
    parser.add_argument('--status', action='store_true', help='Show status (default)')
    parser.add_argument('--emergency', action='store_true', help='Apply emergency mode')
    parser.add_argument('--optimize', action='store_true', help='Optimize routes')
    parser.add_argument('--quota', action='store_true', help='Show quota info only')
    
    args = parser.parse_args()
    
    if args.emergency:
        print(f"\n{colors['RED']}🚨 APPLYING EMERGENCY MODE")
        print(f"   • Reducing scanning to minimum")
        print(f"   • Only Tier 1 routes, once daily")
        print(f"   • Estimated usage: ~20 calls/day")
        manager.apply_emergency_mode()
        
    elif args.optimize:
        print(f"\n{colors['BLUE']}🔧 OPTIMIZING ROUTES")
        manager.optimize_routes()
        
    elif args.quota:
        print(f"\n{colors['CYAN']}📊 QUOTA SUMMARY")
        print(f"   Status: {quota_status['status']}")
        print(f"   Today: {quota_status['today_calls']}/{quota_status['daily_limit']} ({quota_status['daily_percentage']:.1f}%)")
        print(f"   Month: {quota_status['monthly_calls']}/{quota_status['monthly_limit']} ({quota_status['monthly_percentage']:.1f}%)")
        
    else:
        # Show available commands
        print(f"\n{colors['WHITE']}Available commands:")
        print(f"  python3 autonomous_manager.py --status      Show full status")
        print(f"  python3 autonomous_manager.py --quota       Show quota only")
        print(f"  python3 autonomous_manager.py --emergency   Apply emergency mode")
        print(f"  python3 autonomous_manager.py --optimize    Optimize routes")
        print(f"\n{colors['CYAN']}💡 TIP: Use 'python3 lightweight_quota_manager.py' for detailed analysis")
    
    print(f"\n{colors['CYAN']}🎯 System is autonomous and quota-aware!")
    print(f"{colors['WHITE']}   Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
