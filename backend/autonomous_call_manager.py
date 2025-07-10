#!/usr/bin/env python3
"""
Autonomous Call Manager for GlobeGenius
Automatically optimizes API call distribution based on quota usage, route performance, and business value
"""

import sys
import os
from datetime import datetime, timedelta, date
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Add the backend path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.services.dynamic_route_manager import DynamicRouteManager
from app.models.flight import Route, Deal
from app.models.api_tracking import ApiCall
from app.tasks.celery_app import app as celery_app
from app.utils.logger import logger
from colorama import init, Fore, Style
import colorama

# Initialize colorama
init(autoreset=True)


@dataclass
class QuotaStatus:
    """Current quota usage status"""
    today_calls: int
    daily_limit: int
    monthly_calls: int
    monthly_limit: int
    daily_percentage: float
    monthly_percentage: float
    remaining_today: int
    remaining_monthly: int
    status: str  # 'healthy', 'warning', 'critical', 'over_limit'


@dataclass
class CallStrategy:
    """Recommended call distribution strategy"""
    daily_calls_budget: int
    tier_1_frequency: str  # cron expression
    tier_2_frequency: str
    tier_3_frequency: str
    estimated_daily_usage: int
    efficiency_score: float


class AutonomousCallManager:
    """
    Autonomous system that manages API calls intelligently:
    - Monitors quota usage in real-time
    - Adjusts scan frequencies based on performance
    - Optimizes route distribution seasonally
    - Prevents quota overruns
    - Maximizes deal discovery efficiency
    """
    
    def __init__(self):
        self.db = SessionLocal()
        self.route_manager = DynamicRouteManager(self.db)
        
        # Configuration thresholds
        self.quota_thresholds = {
            'healthy': 70,      # < 70% usage = healthy
            'warning': 85,      # 70-85% = warning
            'critical': 95,     # 85-95% = critical
            'emergency': 100    # > 95% = emergency mode
        }
        
        # Call strategies for different quota levels
        self.strategies = {
            'aggressive': {'multiplier': 1.2, 'tier_boost': True},
            'normal': {'multiplier': 1.0, 'tier_boost': False},
            'conservative': {'multiplier': 0.7, 'tier_boost': False},
            'emergency': {'multiplier': 0.3, 'tier_boost': False}
        }

    def get_quota_status(self) -> QuotaStatus:
        """Get current quota usage status"""
        try:
            today = date.today()
            today_calls = self.db.query(ApiCall).filter(
                ApiCall.api_provider == 'flightlabs',
                ApiCall.called_at >= datetime.combine(today, datetime.min.time())
            ).count()
            
            month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            monthly_calls = self.db.query(ApiCall).filter(
                ApiCall.api_provider == 'flightlabs',
                ApiCall.called_at >= month_start
            ).count()
            
            daily_limit = 333  # 10k monthly / 30 days
            monthly_limit = 10000
            
            daily_percentage = (today_calls / daily_limit) * 100
            monthly_percentage = (monthly_calls / monthly_limit) * 100
            
            # Determine status
            max_percentage = max(daily_percentage, monthly_percentage)
            if max_percentage >= self.quota_thresholds['emergency']:
                status = 'over_limit'
            elif max_percentage >= self.quota_thresholds['critical']:
                status = 'critical'
            elif max_percentage >= self.quota_thresholds['warning']:
                status = 'warning'
            else:
                status = 'healthy'
            
            return QuotaStatus(
                today_calls=today_calls,
                daily_limit=daily_limit,
                monthly_calls=monthly_calls,
                monthly_limit=monthly_limit,
                daily_percentage=daily_percentage,
                monthly_percentage=monthly_percentage,
                remaining_today=max(0, daily_limit - today_calls),
                remaining_monthly=max(0, monthly_limit - monthly_calls),
                status=status
            )
            
        except Exception as e:
            logger.error(f"Error getting quota status: {e}")
            return QuotaStatus(0, 333, 0, 10000, 0, 0, 333, 10000, 'unknown')

    def calculate_optimal_strategy(self, quota_status: QuotaStatus) -> CallStrategy:
        """Calculate optimal call distribution strategy based on current quota"""
        
        # Determine base strategy from quota status
        if quota_status.status == 'over_limit':
            base_strategy = 'emergency'
            daily_budget = min(50, quota_status.remaining_today)  # Emergency: max 50 calls/day
        elif quota_status.status == 'critical':
            base_strategy = 'conservative'
            daily_budget = min(200, quota_status.remaining_today)  # Conservative mode
        elif quota_status.status == 'warning':
            base_strategy = 'normal'
            daily_budget = min(280, quota_status.remaining_today)  # Slightly reduced
        else:  # healthy
            base_strategy = 'aggressive'
            daily_budget = 333  # Full quota usage
        
        strategy_config = self.strategies[base_strategy]
        
        # Adjust daily budget based on strategy
        adjusted_budget = int(daily_budget * strategy_config['multiplier'])
        
        # Calculate tier frequencies based on budget
        if adjusted_budget >= 300:  # Full capacity
            tier_1_freq = "0 */6"      # Every 6 hours (4x/day)
            tier_2_freq = "15 */8"     # Every 8 hours (3x/day)
            tier_3_freq = "30 */12"    # Every 12 hours (2x/day)
            estimated_usage = 300
        elif adjusted_budget >= 200:  # Reduced capacity
            tier_1_freq = "0 */8"      # Every 8 hours (3x/day)
            tier_2_freq = "20 */12"    # Every 12 hours (2x/day)
            tier_3_freq = "40 8"       # Once daily at 8:40 AM
            estimated_usage = 180
        elif adjusted_budget >= 100:  # Conservative mode
            tier_1_freq = "0 */12"     # Every 12 hours (2x/day)
            tier_2_freq = "30 8"       # Once daily at 8:30 AM
            tier_3_freq = "45 20"      # Once daily at 8:45 PM
            estimated_usage = 100
        else:  # Emergency mode
            tier_1_freq = "0 8"        # Once daily at 8 AM
            tier_2_freq = "0 14"       # Once daily at 2 PM
            tier_3_freq = "0 20"       # Once daily at 8 PM
            estimated_usage = 50
        
        # Calculate efficiency score
        efficiency_score = self._calculate_efficiency_score(quota_status, adjusted_budget)
        
        return CallStrategy(
            daily_calls_budget=adjusted_budget,
            tier_1_frequency=tier_1_freq,
            tier_2_frequency=tier_2_freq,
            tier_3_frequency=tier_3_freq,
            estimated_daily_usage=estimated_usage,
            efficiency_score=efficiency_score
        )

    def _calculate_efficiency_score(self, quota_status: QuotaStatus, budget: int) -> float:
        """Calculate efficiency score based on quota usage and deal discovery"""
        try:
            # Base efficiency from quota utilization
            quota_efficiency = min(1.0, budget / 333)
            
            # Deal discovery rate (last 7 days)
            seven_days_ago = datetime.now() - timedelta(days=7)
            recent_deals = self.db.query(Deal).filter(
                Deal.detected_at >= seven_days_ago
            ).count()
            
            recent_calls = self.db.query(ApiCall).filter(
                ApiCall.api_provider == 'flightlabs',
                ApiCall.called_at >= seven_days_ago
            ).count()
            
            # Deals per API call ratio
            deal_efficiency = (recent_deals / max(recent_calls, 1)) * 100
            
            # Combined efficiency score (0-100)
            efficiency = (quota_efficiency * 50) + min(deal_efficiency * 50, 50)
            
            return round(efficiency, 1)
            
        except Exception as e:
            logger.error(f"Error calculating efficiency: {e}")
            return 50.0  # Default moderate efficiency

    def apply_strategy(self, strategy: CallStrategy) -> bool:
        """Apply the calculated strategy to Celery schedule"""
        try:
            # Update Celery beat schedule
            new_schedule = {
                "scan-tier-1-routes": {
                    "task": "app.tasks.flight_tasks.scan_tier_routes",
                    "schedule": self._cron_from_frequency(strategy.tier_1_frequency),
                    "args": (1,)
                },
                "scan-tier-2-routes": {
                    "task": "app.tasks.flight_tasks.scan_tier_routes", 
                    "schedule": self._cron_from_frequency(strategy.tier_2_frequency),
                    "args": (2,)
                },
                "scan-tier-3-routes": {
                    "task": "app.tasks.flight_tasks.scan_tier_routes",
                    "schedule": self._cron_from_frequency(strategy.tier_3_frequency),
                    "args": (3,)
                },
                "process-alerts": {
                    "task": "app.tasks.email_tasks.process_pending_alerts",
                    "schedule": self._cron_from_frequency("*/45")  # Every 45 minutes
                },
                "clean-expired-deals": {
                    "task": "app.tasks.flight_tasks.clean_expired_deals",
                    "schedule": self._cron_from_frequency("0 3")  # Daily at 3 AM
                }
            }
            
            # Update the Celery app configuration
            celery_app.conf.beat_schedule = new_schedule
            
            logger.info(f"✅ Applied new call strategy: {strategy.estimated_daily_usage} calls/day")
            return True
            
        except Exception as e:
            logger.error(f"Error applying strategy: {e}")
            return False

    def _cron_from_frequency(self, frequency: str) -> object:
        """Convert frequency string to crontab object"""
        from celery.schedules import crontab
        
        parts = frequency.split()
        if len(parts) == 2:
            minute, hour = parts
            if '/' in hour:
                return crontab(minute=int(minute), hour=hour)
            else:
                return crontab(minute=int(minute), hour=int(hour))
        elif len(parts) == 1:
            if '/' in parts[0]:
                return crontab(minute=parts[0])
            else:
                return crontab(minute=0, hour=int(parts[0]))
        else:
            return crontab(minute=0, hour="*/12")  # Default fallback

    def optimize_routes(self) -> Dict[str, Any]:
        """Run intelligent route optimization"""
        try:
            logger.info("🧠 Running intelligent route optimization...")
            
            # Get optimal distribution from Dynamic Route Manager
            distribution = self.route_manager.calculate_optimal_scan_distribution()
            
            # Apply the distribution
            success = self.route_manager.apply_distribution(distribution)
            
            if success:
                logger.info(f"✅ Route optimization applied: {distribution['stats']['routes_covered']} routes optimized")
                return {
                    'success': True,
                    'routes_optimized': distribution['stats']['routes_covered'],
                    'daily_scans': distribution['stats']['total_daily_scans'],
                    'seasonal_routes': distribution['active_seasonal_routes'],
                    'recommendations': distribution['recommendations']
                }
            else:
                return {'success': False, 'error': 'Failed to apply route distribution'}
                
        except Exception as e:
            logger.error(f"Error in route optimization: {e}")
            return {'success': False, 'error': str(e)}

    def run_autonomous_optimization(self) -> Dict[str, Any]:
        """Run full autonomous optimization cycle"""
        logger.info("🤖 Starting autonomous call management optimization...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'quota_status': None,
            'strategy_applied': None,
            'routes_optimized': None,
            'recommendations': []
        }
        
        try:
            # 1. Check quota status
            quota_status = self.get_quota_status()
            results['quota_status'] = quota_status.__dict__
            
            # 2. Calculate optimal strategy
            strategy = self.calculate_optimal_strategy(quota_status)
            
            # 3. Apply strategy if needed
            strategy_applied = self.apply_strategy(strategy)
            results['strategy_applied'] = {
                'success': strategy_applied,
                'daily_budget': strategy.daily_calls_budget,
                'estimated_usage': strategy.estimated_daily_usage,
                'efficiency_score': strategy.efficiency_score
            }
            
            # 4. Optimize routes
            route_optimization = self.optimize_routes()
            results['routes_optimized'] = route_optimization
            
            # 5. Generate recommendations
            recommendations = self._generate_recommendations(quota_status, strategy)
            results['recommendations'] = recommendations
            
            logger.info("✅ Autonomous optimization completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Error in autonomous optimization: {e}")
            results['error'] = str(e)
            return results

    def _generate_recommendations(self, quota_status: QuotaStatus, strategy: CallStrategy) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Quota recommendations
        if quota_status.status == 'over_limit':
            recommendations.append("🚨 URGENT: Monthly quota exceeded! Consider upgrading to 20k calls/month plan.")
            recommendations.append("⏸️ Temporarily pause Tier 3 routes to conserve quota.")
        elif quota_status.status == 'critical':
            recommendations.append("⚠️ Critical quota usage. Switch to conservative scanning mode.")
            recommendations.append("📊 Focus only on Tier 1 routes for remainder of month.")
        elif quota_status.status == 'warning':
            recommendations.append("⚡ High quota usage. Monitor closely and optimize underperforming routes.")
        
        # Efficiency recommendations
        if strategy.efficiency_score < 30:
            recommendations.append("📈 Low efficiency detected. Review route performance and consider tier adjustments.")
        elif strategy.efficiency_score > 80:
            recommendations.append("🎯 High efficiency! Consider adding more high-performing routes.")
        
        # Seasonal recommendations
        current_month = datetime.now().month
        if current_month in [6, 7, 8]:  # Summer
            recommendations.append("☀️ Summer season: Boost Mediterranean and vacation routes.")
        elif current_month in [11, 12, 1, 2]:  # Winter
            recommendations.append("🏖️ Winter season: Focus on warm destinations and ski resorts.")
        
        return recommendations

    def display_status(self):
        """Display current system status"""
        print(f"\n{Fore.CYAN}{Style.BRIGHT}🤖 AUTONOMOUS CALL MANAGER STATUS")
        print(f"{Fore.CYAN}{'=' * 60}")
        
        # Get current status
        quota_status = self.get_quota_status()
        strategy = self.calculate_optimal_strategy(quota_status)
        
        # Quota status
        quota_color = {
            'healthy': Fore.GREEN,
            'warning': Fore.YELLOW,
            'critical': Fore.RED,
            'over_limit': Fore.MAGENTA
        }.get(quota_status.status, Fore.WHITE)
        
        print(f"\n{Fore.YELLOW}📊 QUOTA STATUS:")
        print(f"   Status: {quota_color}{quota_status.status.upper()}")
        print(f"   Today: {quota_status.today_calls}/{quota_status.daily_limit} ({quota_status.daily_percentage:.1f}%)")
        print(f"   Month: {quota_status.monthly_calls}/{quota_status.monthly_limit} ({quota_status.monthly_percentage:.1f}%)")
        print(f"   Remaining: {quota_status.remaining_today} today, {quota_status.remaining_monthly} monthly")
        
        # Strategy
        print(f"\n{Fore.YELLOW}⚙️ CURRENT STRATEGY:")
        print(f"   Daily Budget: {strategy.daily_calls_budget} calls")
        print(f"   Estimated Usage: {strategy.estimated_daily_usage} calls/day")
        print(f"   Efficiency Score: {strategy.efficiency_score}%")
        print(f"   Tier 1: {strategy.tier_1_frequency}")
        print(f"   Tier 2: {strategy.tier_2_frequency}")
        print(f"   Tier 3: {strategy.tier_3_frequency}")
        
        # Recommendations
        recommendations = self._generate_recommendations(quota_status, strategy)
        if recommendations:
            print(f"\n{Fore.YELLOW}💡 RECOMMENDATIONS:")
            for rec in recommendations:
                print(f"   • {rec}")

    def close(self):
        """Close database connection"""
        self.db.close()


async def main():
    """Main entry point for autonomous call manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description="GlobeGenius Autonomous Call Manager")
    parser.add_argument('--status', action='store_true', help='Show current status')
    parser.add_argument('--optimize', action='store_true', help='Run full optimization')
    parser.add_argument('--quota', action='store_true', help='Show quota status only')
    parser.add_argument('--apply-strategy', action='store_true', help='Apply current optimal strategy')
    
    args = parser.parse_args()
    
    manager = AutonomousCallManager()
    
    try:
        if args.status:
            manager.display_status()
        elif args.optimize:
            print(f"{Fore.CYAN}🤖 Running autonomous optimization...")
            results = manager.run_autonomous_optimization()
            print(f"{Fore.GREEN}✅ Optimization completed!")
            print(f"   Routes optimized: {results.get('routes_optimized', {}).get('routes_optimized', 'N/A')}")
            print(f"   Daily calls budget: {results.get('strategy_applied', {}).get('daily_budget', 'N/A')}")
            print(f"   Efficiency score: {results.get('strategy_applied', {}).get('efficiency_score', 'N/A')}%")
        elif args.quota:
            quota = manager.get_quota_status()
            print(f"{Fore.CYAN}📊 Quota Status: {quota.status}")
            print(f"   Today: {quota.today_calls}/{quota.daily_limit} ({quota.daily_percentage:.1f}%)")
            print(f"   Month: {quota.monthly_calls}/{quota.monthly_limit} ({quota.monthly_percentage:.1f}%)")
        elif args.apply_strategy:
            quota = manager.get_quota_status()
            strategy = manager.calculate_optimal_strategy(quota)
            success = manager.apply_strategy(strategy)
            if success:
                print(f"{Fore.GREEN}✅ Strategy applied: {strategy.estimated_daily_usage} calls/day")
            else:
                print(f"{Fore.RED}❌ Failed to apply strategy")
        else:
            # Interactive mode
            manager.display_status()
            print(f"\n{Fore.WHITE}Available commands:")
            print(f"  --status      Show detailed status")
            print(f"  --optimize    Run full autonomous optimization")
            print(f"  --quota       Show quota status only")
            print(f"  --apply-strategy Apply current optimal strategy")
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Manager interrupted by user")
    except Exception as e:
        print(f"{Fore.RED}❌ Manager error: {e}")
    finally:
        manager.close()


if __name__ == "__main__":
    asyncio.run(main())
