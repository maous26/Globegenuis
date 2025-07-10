#!/usr/bin/env python3
"""
Unified Autonomous Call Manager Control Script
Combines all autonomous management functionality in one interface
"""

import sys
import os
import json
import argparse
from datetime import datetime
from lightweight_quota_manager import LightweightQuotaManager
import schedule
import time

class UnifiedAutonomousManager:
    """Unified manager for all autonomous operations"""
    
    def __init__(self):
        self.quota_manager = LightweightQuotaManager()
        self.log_file = "/Users/moussa/globegenius/backend/logs/autonomous_manager.log"
        self.config_file = "/Users/moussa/globegenius/backend/logs/autonomous_config.json"
        
        # Colors for output
        try:
            from colorama import init, Fore, Style
            init(autoreset=True)
            self.colors = {'RED': Fore.RED, 'GREEN': Fore.GREEN, 'YELLOW': Fore.YELLOW, 
                          'BLUE': Fore.BLUE, 'CYAN': Fore.CYAN, 'WHITE': Fore.WHITE}
        except ImportError:
            self.colors = {'RED': '', 'GREEN': '', 'YELLOW': '', 'BLUE': '', 'CYAN': '', 'WHITE': ''}
        
        # Ensure log directory exists
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
    
    def log(self, message: str):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Print to console
        print(log_entry.strip())
        
        # Write to log file
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Failed to write to log: {e}")
    
    def get_status(self):
        """Get comprehensive system status"""
        print(f"\n{self.colors['CYAN']}🤖 AUTONOMOUS CALL MANAGER STATUS")
        print(f"{self.colors['CYAN']}{'=' * 50}")
        
        # Quota status
        quota_status = self.quota_manager.get_quota_status()
        route_stats = self.quota_manager.get_route_stats()
        strategy = self.quota_manager.calculate_recommended_strategy(quota_status)
        
        status_colors = {
            'healthy': self.colors['GREEN'],
            'warning': self.colors['YELLOW'],
            'critical': self.colors['RED'],
            'over_limit': self.colors['RED'],
            'unknown': self.colors['WHITE']
        }
        status_color = status_colors.get(quota_status['status'], self.colors['WHITE'])
        
        print(f"\n{self.colors['YELLOW']}📊 QUOTA STATUS: {status_color}{quota_status['status'].upper()}")
        print(f"{self.colors['WHITE']}   Today: {quota_status['today_calls']}/{quota_status['daily_limit']} ({quota_status['daily_percentage']:.1f}%)")
        print(f"   Month: {quota_status['monthly_calls']}/{quota_status['monthly_limit']} ({quota_status['monthly_percentage']:.1f}%)")
        print(f"   Remaining: {quota_status['remaining_today']} today, {quota_status['remaining_monthly']} monthly")
        
        # Route status
        print(f"\n{self.colors['YELLOW']}🛣️ ROUTE STATUS:")
        print(f"   Active Routes: {route_stats['total_active']}")
        print(f"   Tier 1: {route_stats['tier_1']} | Tier 2: {route_stats['tier_2']} | Tier 3: {route_stats['tier_3']}")
        print(f"   Deals (7 days): {route_stats['recent_deals']}")
        print(f"   Efficiency: {route_stats['efficiency']:.1f}%")
        
        # Strategy
        mode_colors = {
            'normal': self.colors['GREEN'],
            'conservative': self.colors['YELLOW'],
            'crisis': self.colors['RED'],
            'emergency': self.colors['RED']
        }
        mode_color = mode_colors.get(strategy['mode'], self.colors['WHITE'])
        
        print(f"\n{self.colors['YELLOW']}⚙️ RECOMMENDED STRATEGY: {mode_color}{strategy['mode'].upper()}")
        print(f"{self.colors['WHITE']}   {strategy['description']}")
        print(f"   Daily Budget: {strategy['daily_budget']} calls")
        print(f"   Estimated Usage: {strategy['estimated_usage']} calls/day")
        
        # System health
        print(f"\n{self.colors['YELLOW']}🏥 SYSTEM HEALTH:")
        if quota_status['status'] == 'healthy':
            print(f"   {self.colors['GREEN']}✅ System running optimally")
        elif quota_status['status'] == 'warning':
            print(f"   {self.colors['YELLOW']}⚠️ High quota usage - monitoring")
        elif quota_status['status'] == 'critical':
            print(f"   {self.colors['RED']}🚨 Critical quota usage - emergency mode needed")
        else:
            print(f"   {self.colors['RED']}❌ System over quota limit")
        
        return quota_status, route_stats, strategy
    
    def apply_emergency_mode(self):
        """Apply emergency quota conservation"""
        print(f"\n{self.colors['RED']}🚨 APPLYING EMERGENCY MODE")
        print(f"   • Reducing all scanning to minimum")
        print(f"   • Only Tier 1 routes, once daily")
        print(f"   • Estimated usage: ~20 calls/day")
        
        self.quota_manager.apply_emergency_mode()
        self.log("Emergency mode activated")
    
    def optimize_routes(self):
        """Optimize route distribution"""
        print(f"\n{self.colors['BLUE']}🔧 OPTIMIZING ROUTES")
        self.quota_manager.optimize_routes()
        self.log("Route optimization completed")
    
    def run_continuous_monitoring(self):
        """Run continuous monitoring"""
        print(f"\n{self.colors['CYAN']}🔄 STARTING CONTINUOUS MONITORING")
        print(f"   • Quota checks every hour")
        print(f"   • Status updates every 15 minutes")
        print(f"   • Press Ctrl+C to stop")
        
        def hourly_check():
            self.log("Performing hourly quota check")
            quota_status = self.quota_manager.get_quota_status()
            self.log(f"Current status: {quota_status['status']} - {quota_status['today_calls']}/{quota_status['daily_limit']} calls today")
            
            # Auto-apply emergency mode if needed
            if quota_status['status'] in ['critical', 'over_limit']:
                self.log("Auto-applying emergency mode due to quota status")
                self.apply_emergency_mode()
        
        def status_update():
            quota_status = self.quota_manager.get_quota_status()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Status: {quota_status['status']} | Today: {quota_status['today_calls']}/{quota_status['daily_limit']} | Month: {quota_status['monthly_calls']}/{quota_status['monthly_limit']}")
        
        # Setup schedule
        schedule.every().hour.do(hourly_check)
        schedule.every(15).minutes.do(status_update)
        
        # Run initial check
        hourly_check()
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print(f"\n{self.colors['YELLOW']}⏹️ Monitoring stopped by user")
            self.log("Continuous monitoring stopped")
    
    def dashboard(self):
        """Interactive dashboard"""
        while True:
            print(f"\n{self.colors['CYAN']}🎛️ AUTONOMOUS CALL MANAGER DASHBOARD")
            print(f"{self.colors['CYAN']}{'=' * 50}")
            
            # Get current status
            quota_status, route_stats, strategy = self.get_status()
            
            print(f"\n{self.colors['WHITE']}Available Commands:")
            print(f"  1. Show detailed status")
            print(f"  2. Apply emergency mode")
            print(f"  3. Optimize routes")
            print(f"  4. Start continuous monitoring")
            print(f"  5. Exit")
            
            try:
                choice = input(f"\n{self.colors['YELLOW']}Enter command (1-5): ").strip()
                
                if choice == '1':
                    self.get_status()
                elif choice == '2':
                    self.apply_emergency_mode()
                elif choice == '3':
                    self.optimize_routes()
                elif choice == '4':
                    self.run_continuous_monitoring()
                elif choice == '5':
                    print(f"{self.colors['GREEN']}👋 Goodbye!")
                    break
                else:
                    print(f"{self.colors['RED']}❌ Invalid choice")
                    
            except KeyboardInterrupt:
                print(f"\n{self.colors['YELLOW']}👋 Goodbye!")
                break
            except Exception as e:
                print(f"{self.colors['RED']}❌ Error: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Unified Autonomous Call Manager")
    parser.add_argument('--status', action='store_true', help='Show system status')
    parser.add_argument('--emergency', action='store_true', help='Apply emergency mode')
    parser.add_argument('--optimize', action='store_true', help='Optimize routes')
    parser.add_argument('--monitor', action='store_true', help='Start continuous monitoring')
    parser.add_argument('--dashboard', action='store_true', help='Open interactive dashboard')
    
    args = parser.parse_args()
    
    manager = UnifiedAutonomousManager()
    
    try:
        if args.status:
            manager.get_status()
        elif args.emergency:
            manager.apply_emergency_mode()
        elif args.optimize:
            manager.optimize_routes()
        elif args.monitor:
            manager.run_continuous_monitoring()
        elif args.dashboard:
            manager.dashboard()
        else:
            # Default: show status and available commands
            manager.get_status()
            print(f"\n{manager.colors['WHITE']}Available commands:")
            print(f"  --status      Show system status")
            print(f"  --emergency   Apply emergency mode")
            print(f"  --optimize    Optimize routes")
            print(f"  --monitor     Start continuous monitoring")
            print(f"  --dashboard   Open interactive dashboard")
            
    except KeyboardInterrupt:
        print(f"\n{manager.colors['YELLOW']}Operation interrupted by user")
    except Exception as e:
        print(f"{manager.colors['RED']}❌ Error: {e}")

if __name__ == "__main__":
    main()
