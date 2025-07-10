#!/usr/bin/env python3
"""
Automated scheduler for Autonomous Call Manager
Runs optimization checks every hour and applies adjustments as needed
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import schedule
import time
import logging

# Add the backend path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from autonomous_call_manager import AutonomousCallManager
from app.utils.logger import logger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/moussa/globegenius/backend/logs/autonomous_manager.log'),
        logging.StreamHandler()
    ]
)


class AutonomousScheduler:
    """Scheduler that runs autonomous call management at regular intervals"""
    
    def __init__(self):
        self.manager = AutonomousCallManager()
        self.last_optimization = None
        self.consecutive_failures = 0
        
    def run_hourly_check(self):
        """Run every hour - quick quota check and light optimizations"""
        try:
            logger.info("🕐 Running hourly autonomous check...")
            
            quota_status = self.manager.get_quota_status()
            
            # If quota is critical or over limit, take immediate action
            if quota_status.status in ['critical', 'over_limit']:
                logger.warning(f"⚠️ Quota status: {quota_status.status} - Applying emergency strategy")
                strategy = self.manager.calculate_optimal_strategy(quota_status)
                success = self.manager.apply_strategy(strategy)
                
                if success:
                    logger.info(f"✅ Emergency strategy applied: {strategy.estimated_daily_usage} calls/day")
                    self.consecutive_failures = 0
                else:
                    self.consecutive_failures += 1
                    logger.error(f"❌ Failed to apply emergency strategy (failure #{self.consecutive_failures})")
            
            # Log current status
            logger.info(f"📊 Quota: {quota_status.today_calls}/{quota_status.daily_limit} today, "
                       f"{quota_status.monthly_calls}/{quota_status.monthly_limit} monthly ({quota_status.status})")
            
        except Exception as e:
            self.consecutive_failures += 1
            logger.error(f"❌ Hourly check failed (failure #{self.consecutive_failures}): {e}")
    
    def run_daily_optimization(self):
        """Run daily - full optimization including route adjustments"""
        try:
            logger.info("🌅 Running daily autonomous optimization...")
            
            results = self.manager.run_autonomous_optimization()
            
            if results.get('strategy_applied', {}).get('success', False):
                logger.info(f"✅ Daily optimization completed successfully")
                logger.info(f"   Routes optimized: {results.get('routes_optimized', {}).get('routes_optimized', 'N/A')}")
                logger.info(f"   Daily budget: {results.get('strategy_applied', {}).get('daily_budget', 'N/A')} calls")
                logger.info(f"   Efficiency: {results.get('strategy_applied', {}).get('efficiency_score', 'N/A')}%")
                
                self.last_optimization = datetime.now()
                self.consecutive_failures = 0
                
                # Log recommendations
                recommendations = results.get('recommendations', [])
                if recommendations:
                    logger.info("💡 Recommendations:")
                    for rec in recommendations:
                        logger.info(f"   • {rec}")
            else:
                self.consecutive_failures += 1
                logger.error(f"❌ Daily optimization failed (failure #{self.consecutive_failures})")
                
        except Exception as e:
            self.consecutive_failures += 1
            logger.error(f"❌ Daily optimization failed (failure #{self.consecutive_failures}): {e}")
    
    def run_weekly_deep_analysis(self):
        """Run weekly - deep performance analysis and route rebalancing"""
        try:
            logger.info("📊 Running weekly deep analysis...")
            
            # Get performance suggestions
            suggestions = self.manager.route_manager.suggest_dynamic_adjustments()
            
            if suggestions:
                logger.info(f"📈 Found {len(suggestions)} performance suggestions:")
                for suggestion in suggestions:
                    logger.info(f"   • {suggestion['type']}: {suggestion['route']} - {suggestion['reason']}")
            
            # Run full optimization
            self.run_daily_optimization()
            
            logger.info("✅ Weekly analysis completed")
            
        except Exception as e:
            logger.error(f"❌ Weekly analysis failed: {e}")
    
    def check_system_health(self):
        """Check if the system is functioning properly"""
        try:
            # Check if too many consecutive failures
            if self.consecutive_failures >= 5:
                logger.error(f"🚨 SYSTEM ALERT: {self.consecutive_failures} consecutive failures detected!")
                logger.error("   Manual intervention may be required")
                # Could send email alert here
                
            # Check if optimization hasn't run in too long
            if self.last_optimization:
                hours_since_optimization = (datetime.now() - self.last_optimization).total_seconds() / 3600
                if hours_since_optimization > 48:  # 2 days
                    logger.warning(f"⚠️ No successful optimization in {hours_since_optimization:.1f} hours")
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
    
    def start_scheduler(self):
        """Start the autonomous scheduler"""
        logger.info("🚀 Starting Autonomous Call Manager Scheduler")
        logger.info("   Hourly checks: Every hour")
        logger.info("   Daily optimization: 6:00 AM")
        logger.info("   Weekly analysis: Sunday 7:00 AM")
        
        # Schedule jobs
        schedule.every().hour.do(self.run_hourly_check)
        schedule.every().day.at("06:00").do(self.run_daily_optimization)
        schedule.every().sunday.at("07:00").do(self.run_weekly_deep_analysis)
        schedule.every(30).minutes.do(self.check_system_health)
        
        # Run initial optimization
        self.run_daily_optimization()
        
        # Main scheduler loop
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                logger.info("🛑 Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Scheduler error: {e}")
                time.sleep(300)  # Wait 5 minutes before retrying
    
    def run_once(self):
        """Run optimization once and exit"""
        logger.info("🔄 Running one-time autonomous optimization...")
        results = self.manager.run_autonomous_optimization()
        
        if results.get('strategy_applied', {}).get('success', False):
            logger.info("✅ One-time optimization completed successfully")
        else:
            logger.error("❌ One-time optimization failed")
        
        return results


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Autonomous Call Manager Scheduler")
    parser.add_argument('--daemon', action='store_true', help='Run as daemon (continuous scheduling)')
    parser.add_argument('--once', action='store_true', help='Run optimization once and exit')
    parser.add_argument('--status', action='store_true', help='Show scheduler status')
    
    args = parser.parse_args()
    
    scheduler = AutonomousScheduler()
    
    try:
        if args.daemon:
            scheduler.start_scheduler()
        elif args.once:
            results = scheduler.run_once()
            print(f"Optimization completed. Check logs for details.")
        elif args.status:
            # Show current status
            quota_status = scheduler.manager.get_quota_status()
            print(f"📊 Current Status:")
            print(f"   Quota: {quota_status.status} ({quota_status.daily_percentage:.1f}% daily, {quota_status.monthly_percentage:.1f}% monthly)")
            print(f"   Last optimization: {scheduler.last_optimization or 'Never'}")
            print(f"   Consecutive failures: {scheduler.consecutive_failures}")
        else:
            print("Usage:")
            print("  --daemon    Run continuously (recommended for production)")
            print("  --once      Run optimization once")
            print("  --status    Show current status")
            
    except Exception as e:
        logger.error(f"❌ Scheduler error: {e}")
    finally:
        scheduler.manager.close()


if __name__ == "__main__":
    main()
