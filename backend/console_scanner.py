#!/usr/bin/env python3
"""
Production Console Scanning Tool for GlobeGenius
Uses FlightLabs API (10,000 calls/month) with TravelPayouts validation
"""

import sys
import os
import asyncio
import argparse
from datetime import datetime
from typing import Optional

# Add the backend path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.services.flight_scanner import FlightScanner
from app.services.flightlabs_api import FlightLabsAPI
from app.models.flight import Route
from app.utils.logger import logger
from colorama import init, Fore, Style
import colorama

# Initialize colorama
init(autoreset=True)


class ProductionConsoleScanner:
    """Production console scanner with real API integration"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.scanner = FlightScanner(self.db)
        self.flightlabs_api = FlightLabsAPI()
        
    def print_header(self):
        """Print scanner header"""
        print(f"\n{Fore.CYAN}{Style.BRIGHT}🚀 GLOBEGENIUS PRODUCTION SCANNER")
        print(f"{Fore.CYAN}{'=' * 60}")
        print(f"{Fore.YELLOW}FlightLabs API Integration (10,000 calls/month)")
        print(f"{Fore.GREEN}TravelPayouts Validation Active")
        print(f"{Fore.WHITE}Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

    async def test_api_connection(self):
        """Test FlightLabs API connection"""
        print(f"{Fore.CYAN}🔍 Testing FlightLabs API Connection...")
        
        try:
            result = await self.flightlabs_api.test_connection()
            
            if result['success']:
                print(f"{Fore.GREEN}✅ FlightLabs API Connected Successfully")
                print(f"   📊 Test flights found: {result['flights_found']}")
                print(f"   🛣️  Test route: {result['test_route']}")
                print(f"   📅 Test date: {result['test_date']}")
                
                quota = result['quota_status']
                print(f"   💰 Quota today: {quota['daily_usage']}/{quota['daily_limit']}")
                print(f"   📈 Quota month: {quota['monthly_usage']}/{quota['monthly_limit']}")
                print(f"   🔄 Remaining today: {quota['daily_remaining']}")
                return True
            else:
                print(f"{Fore.RED}❌ FlightLabs API Connection Failed")
                print(f"   Error: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"{Fore.RED}❌ API Test Error: {e}")
            return False

    async def scan_single_route(self, route_id: int):
        """Scan a specific route"""
        route = self.db.query(Route).filter(Route.id == route_id).first()
        
        if not route:
            print(f"{Fore.RED}❌ Route {route_id} not found")
            return
        
        print(f"{Fore.CYAN}🔍 Scanning Route: {route.origin} → {route.destination}")
        print(f"   Tier: {route.tier} | Active: {route.is_active}")
        
        try:
            deals = await self.scanner.scan_route(route)
            
            if deals:
                print(f"{Fore.GREEN}✅ Found {len(deals)} deals!")
                for i, deal in enumerate(deals, 1):
                    print(f"   {i}. €{deal.deal_price} (was €{deal.normal_price}) "
                          f"- {deal.discount_percentage:.0f}% off")
                    print(f"      {deal.airline} | Confidence: {deal.confidence_score:.0f}%")
            else:
                print(f"{Fore.YELLOW}⚠️  No deals found for this route")
                
        except Exception as e:
            print(f"{Fore.RED}❌ Scan error: {e}")

    async def scan_tier(self, tier: int):
        """Scan all routes in a tier"""
        routes = self.db.query(Route).filter(
            Route.tier == tier,
            Route.is_active == True
        ).all()
        
        if not routes:
            print(f"{Fore.RED}❌ No active routes found for Tier {tier}")
            return
        
        print(f"{Fore.CYAN}🔍 Scanning Tier {tier}: {len(routes)} routes")
        
        try:
            result = await self.scanner.scan_all_routes(tier=tier)
            
            print(f"{Fore.GREEN}✅ Tier {tier} Scan Complete!")
            print(f"   📊 Routes scanned: {result['routes_scanned']}")
            print(f"   💎 Deals found: {result['deals_found']}")
            print(f"   ⏰ Completed at: {result['timestamp'].strftime('%H:%M:%S')}")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Tier scan error: {e}")

    async def scan_all_routes(self):
        """Scan all active routes"""
        active_routes = self.db.query(Route).filter(Route.is_active == True).count()
        
        print(f"{Fore.CYAN}🔍 Scanning All Routes: {active_routes} active routes")
        print(f"{Fore.YELLOW}⚠️  This will use significant API quota!")
        
        # Ask for confirmation
        response = input(f"{Fore.WHITE}Continue? (y/N): ").strip().lower()
        if response != 'y':
            print(f"{Fore.YELLOW}Scan cancelled")
            return
        
        try:
            result = await self.scanner.scan_all_routes()
            
            print(f"{Fore.GREEN}✅ Full Scan Complete!")
            print(f"   📊 Routes scanned: {result['routes_scanned']}")
            print(f"   💎 Deals found: {result['deals_found']}")
            print(f"   ⏰ Completed at: {result['timestamp'].strftime('%H:%M:%S')}")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Full scan error: {e}")

    def show_quota_status(self):
        """Show current API quota status"""
        try:
            from datetime import date
            from app.models.api_tracking import ApiCall
            
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
            
            print(f"{Fore.CYAN}📊 FlightLabs API Quota Status:")
            print(f"   Today: {today_calls}/333 calls ({(today_calls/333)*100:.1f}%)")
            print(f"   Month: {monthly_calls}/10000 calls ({(monthly_calls/10000)*100:.1f}%)")
            print(f"   Remaining today: {max(0, 333 - today_calls)}")
            print(f"   Remaining month: {max(0, 10000 - monthly_calls)}")
            
            if today_calls > 250:
                print(f"{Fore.YELLOW}⚠️  Approaching daily limit!")
            if monthly_calls > 8000:
                print(f"{Fore.RED}⚠️  Approaching monthly limit!")
                
        except Exception as e:
            print(f"{Fore.RED}❌ Error checking quota: {e}")

    def show_routes(self, tier: Optional[int] = None):
        """Show available routes"""
        query = self.db.query(Route)
        
        if tier:
            query = query.filter(Route.tier == tier)
            print(f"{Fore.CYAN}📋 Tier {tier} Routes:")
        else:
            print(f"{Fore.CYAN}📋 All Routes:")
        
        routes = query.filter(Route.is_active == True).all()
        
        for route in routes[:20]:  # Show first 20
            status = f"{Fore.GREEN}Active" if route.is_active else f"{Fore.RED}Inactive"
            print(f"   {route.id:3d}. {route.origin} → {route.destination} "
                  f"(T{route.tier}) {status}")
        
        if len(routes) > 20:
            print(f"   ... and {len(routes) - 20} more routes")

    def close(self):
        """Close database connection"""
        self.db.close()


async def main():
    """Main console scanner interface"""
    parser = argparse.ArgumentParser(description="GlobeGenius Production Console Scanner")
    parser.add_argument('--test', action='store_true', help='Test API connection')
    parser.add_argument('--route', type=int, help='Scan specific route by ID')
    parser.add_argument('--tier', type=int, choices=[1, 2, 3], help='Scan specific tier')
    parser.add_argument('--all', action='store_true', help='Scan all routes')
    parser.add_argument('--quota', action='store_true', help='Show quota status')
    parser.add_argument('--routes', action='store_true', help='List routes')
    parser.add_argument('--routes-tier', type=int, choices=[1, 2, 3], help='List routes for tier')
    
    args = parser.parse_args()
    
    scanner = ProductionConsoleScanner()
    scanner.print_header()
    
    try:
        if args.test:
            await scanner.test_api_connection()
        elif args.route:
            await scanner.scan_single_route(args.route)
        elif args.tier:
            await scanner.scan_tier(args.tier)
        elif args.all:
            await scanner.scan_all_routes()
        elif args.quota:
            scanner.show_quota_status()
        elif args.routes:
            scanner.show_routes()
        elif args.routes_tier:
            scanner.show_routes(args.routes_tier)
        else:
            # Interactive mode
            print(f"{Fore.WHITE}Available commands:")
            print(f"  --test          Test FlightLabs API connection")
            print(f"  --route ID      Scan specific route")
            print(f"  --tier 1/2/3    Scan tier routes")
            print(f"  --all           Scan all routes")
            print(f"  --quota         Show API quota status")
            print(f"  --routes        List all routes")
            print(f"  --routes-tier N List tier routes")
            print()
            print(f"{Fore.YELLOW}Example: python3 console_scanner.py --test")
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Scanner interrupted by user")
    except Exception as e:
        print(f"{Fore.RED}❌ Scanner error: {e}")
    finally:
        scanner.close()


if __name__ == "__main__":
    asyncio.run(main())
