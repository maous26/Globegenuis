#!/usr/bin/env python3
"""
Simple Autonomous Scheduler using Lightweight Quota Manager
Provides autonomous API call management without heavy dependencies
"""

import schedule
import time
import json
import os
from datetime import datetime, timedelta
from lightweight_quota_manager import LightweightQuotaManager

class SimpleAutonomousScheduler:
    """Simple autonomous scheduler using lightweight quota manager"""
    
    def __init__(self):
        self.quota_manager = LightweightQuotaManager()
        self.log_file = "/Users/moussa/globegenius/backend/logs/autonomous_scheduler.log"
        self.config_file = "/Users/moussa/globegenius/backend/logs/autonomous_config.json"
        self.is_running = False
        
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
            print(f"Failed to write to log file: {e}")
    
    def save_config(self, config: dict):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.log(f"Failed to save config: {e}")
    
    def load_config(self) -> dict:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.log(f"Failed to load config: {e}")
        
        # Default config
        return {
            'last_check': None,
            'current_mode': 'normal',
            'emergency_mode': False,
            'last_optimization': None
        }
    
    def hourly_quota_check(self):
        """Perform hourly quota check"""
        self.log("🔍 Performing hourly quota check...")
        
        try:
            quota_status = self.quota_manager.get_quota_status()
            strategy = self.quota_manager.calculate_recommended_strategy(quota_status)
            
            self.log(f"📊 Current quota status: {quota_status['status']}")
            self.log(f"   Today: {quota_status['today_calls']}/{quota_status['daily_limit']} ({quota_status['daily_percentage']:.1f}%)")
            self.log(f"   Month: {quota_status['monthly_calls']}/{quota_status['monthly_limit']} ({quota_status['monthly_percentage']:.1f}%)")
            
            # Check if we need to change strategy
            config = self.load_config()
            current_mode = config.get('current_mode', 'normal')
            recommended_mode = strategy['mode']
            
            if current_mode != recommended_mode:
                self.log(f"⚠️ Strategy change needed: {current_mode} → {recommended_mode}")
                
                if recommended_mode in ['critical', 'emergency']:
                    self.log("🚨 Applying emergency quota protection")
                    self.quota_manager.apply_emergency_mode()
                    
                config['current_mode'] = recommended_mode
                config['last_check'] = datetime.now().isoformat()
                self.save_config(config)
                
                self.log(f"✅ Strategy updated to {recommended_mode}")
            else:
                self.log(f"✅ Strategy unchanged: {current_mode}")
                
        except Exception as e:
            self.log(f"❌ Error during quota check: {e}")
    
    def daily_optimization(self):
        """Perform daily route optimization"""
        self.log("🔧 Performing daily route optimization...")
        
        try:
            # Get current stats
            route_stats = self.quota_manager.get_route_stats()
            quota_status = self.quota_manager.get_quota_status()
            
            self.log(f"📊 Route statistics:")
            self.log(f"   Active routes: {route_stats['total_active']}")
            self.log(f"   Recent deals: {route_stats['recent_deals']}")
            self.log(f"   Efficiency: {route_stats['efficiency']:.1f}%")
            
            # Run optimization
            self.quota_manager.optimize_routes()
            
            # Update config
            config = self.load_config()
            config['last_optimization'] = datetime.now().isoformat()
            self.save_config(config)
            
            self.log("✅ Daily optimization completed")
            
        except Exception as e:
            self.log(f"❌ Error during daily optimization: {e}")
    
    def weekly_analysis(self):
        """Perform weekly deep analysis"""
        self.log("📈 Performing weekly deep analysis...")
        
        try:
            # Get comprehensive stats
            quota_status = self.quota_manager.get_quota_status()
            route_stats = self.quota_manager.get_route_stats()
            
            self.log("📊 Weekly Analysis Report:")
            self.log(f"   Total API calls this month: {quota_status['monthly_calls']}")
            self.log(f"   Monthly quota usage: {quota_status['monthly_percentage']:.1f}%")
            self.log(f"   Active routes: {route_stats['total_active']}")
            self.log(f"   Deals found (7 days): {route_stats['recent_deals']}")
            self.log(f"   Overall efficiency: {route_stats['efficiency']:.1f}%")
            
            # Recommendations
            if quota_status['monthly_percentage'] > 80:
                self.log("⚠️ High monthly quota usage - consider optimization")
            elif quota_status['monthly_percentage'] < 30:
                self.log("💡 Low quota usage - consider expanding network")
            else:
                self.log("✅ Quota usage is optimal")
                
            if route_stats['efficiency'] < 50:
                self.log("⚠️ Low efficiency - route optimization recommended")
            else:
                self.log("✅ Good route efficiency")
                
        except Exception as e:
            self.log(f"❌ Error during weekly analysis: {e}")
    
    def status_check(self):
        """Quick status check"""
        self.log("📊 Quick status check...")
        
        try:
            quota_status = self.quota_manager.get_quota_status()
            self.log(f"Status: {quota_status['status']} | Today: {quota_status['today_calls']}/{quota_status['daily_limit']} | Month: {quota_status['monthly_calls']}/{quota_status['monthly_limit']}")
            
        except Exception as e:
            self.log(f"❌ Error during status check: {e}")
    
    def setup_schedule(self):
        """Setup the autonomous schedule"""
        self.log("⚙️ Setting up autonomous schedule...")
        
        # Hourly quota checks
        schedule.every().hour.do(self.hourly_quota_check)
        
        # Daily optimization at 2 AM
        schedule.every().day.at("02:00").do(self.daily_optimization)
        
        # Weekly analysis on Sundays at 1 AM
        schedule.every().sunday.at("01:00").do(self.weekly_analysis)
        
        # Status check every 15 minutes
        schedule.every(15).minutes.do(self.status_check)
        
        self.log("✅ Schedule configured:")
        self.log("   • Hourly: Quota checks")
        self.log("   • Daily 2 AM: Route optimization")
        self.log("   • Weekly Sunday 1 AM: Deep analysis")
        self.log("   • Every 15 min: Status check")
    
    def start(self):
        """Start the autonomous scheduler"""
        self.log("🚀 Starting Simple Autonomous Scheduler...")
        self.log("=" * 60)
        
        self.setup_schedule()
        self.is_running = True
        
        # Run initial status check
        self.status_check()
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            self.log("⏹️ Scheduler stopped by user")
            self.is_running = False
        except Exception as e:
            self.log(f"❌ Scheduler error: {e}")
            self.is_running = False
    
    def stop(self):
        """Stop the autonomous scheduler"""
        self.log("⏹️ Stopping autonomous scheduler...")
        self.is_running = False

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple Autonomous Scheduler")
    parser.add_argument('--start', action='store_true', help='Start the scheduler')
    parser.add_argument('--status', action='store_true', help='Show current status')
    parser.add_argument('--check', action='store_true', help='Run quota check')
    parser.add_argument('--optimize', action='store_true', help='Run optimization')
    
    args = parser.parse_args()
    
    scheduler = SimpleAutonomousScheduler()
    
    if args.start:
        scheduler.start()
    elif args.status:
        scheduler.status_check()
    elif args.check:
        scheduler.hourly_quota_check()
    elif args.optimize:
        scheduler.daily_optimization()
    else:
        print("Simple Autonomous Scheduler")
        print("Usage:")
        print("  --start     Start the autonomous scheduler")
        print("  --status    Show current status")
        print("  --check     Run quota check")
        print("  --optimize  Run optimization")

if __name__ == "__main__":
    main()
