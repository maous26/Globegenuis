#!/usr/bin/env python3
"""
Console route scanning tool - optimized for manual testing
Usage: python3 console_scan.py [tier_number]
"""
import sys
import os
import asyncio
from datetime import datetime
from colorama import init, Fore, Style

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.services.console_scanner import ConsoleFlightScanner
from app.services.admin_service import AdminService

# Initialize colorama
init(autoreset=True)


async def main():
    """Main console scanning function"""
    
    print(f"\n{Fore.CYAN}{Style.BRIGHT}🔍 CONSOLE ROUTE SCANNER")
    print(f"{Fore.CYAN}{'=' * 50}")
    print(f"{Fore.YELLOW}Optimized for manual testing with API rate limits\n")
    
    # Get tier from command line or prompt
    tier = None
    if len(sys.argv) > 1:
        try:
            tier = int(sys.argv[1])
            if tier not in [1, 2, 3]:
                raise ValueError()
        except ValueError:
            print(f"{Fore.RED}Error: Tier must be 1, 2, or 3")
            sys.exit(1)
    else:
        try:
            tier = int(input(f"{Fore.CYAN}Enter tier to scan (1-3): "))
            if tier not in [1, 2, 3]:
                raise ValueError()
        except (ValueError, KeyboardInterrupt):
            print(f"{Fore.RED}Invalid tier or cancelled")
            sys.exit(1)
    
    # Initialize services
    db = SessionLocal()
    scanner = ConsoleFlightScanner(db)
    admin_service = AdminService(db)
    
    try:
        # First, test API connectivity
        print(f"{Fore.BLUE}🔌 Testing API connectivity...")
        connectivity = await scanner.quick_connectivity_test()
        
        for api_name, result in connectivity.items():
            status_color = Fore.GREEN if result['status'] == 'connected' else Fore.RED
            data_status = "✓ Data available" if result.get('data_found') else "⚠ No data"
            print(f"  {api_name}: {status_color}{result['status']}{Fore.WHITE} - {data_status}")
        
        # Check if any API is working
        working_apis = [api for api, result in connectivity.items() if result['status'] == 'connected']
        if not working_apis:
            print(f"{Fore.RED}❌ No APIs are working. Check your configuration.")
            return
        
        print(f"{Fore.GREEN}✓ Using {', '.join(working_apis)} for scanning\n")
        
        # Show tier info
        stats = admin_service.get_dashboard_stats()
        tier_routes = stats['routes'].get(f'tier_{tier}', 0)
        print(f"{Fore.CYAN}📊 Tier {tier} Info:")
        print(f"  Active routes: {tier_routes}")
        print(f"  Console scan limit: 5 routes (to respect API limits)\n")
        
        # Perform the scan
        print(f"{Fore.YELLOW}🚀 Starting console scan for Tier {tier}...")
        start_time = datetime.now()
        
        results = await scanner.console_scan_tier(tier)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Display results
        print(f"\n{Fore.GREEN}✅ SCAN COMPLETE")
        print(f"{Fore.WHITE}{'─' * 40}")
        print(f"Duration: {duration:.1f} seconds")
        print(f"Routes tested: {results['routes_tested']}")
        print(f"Successful scans: {results['successful_scans']}")
        
        if results['results']:
            print(f"\n{Fore.CYAN}📋 DETAILED RESULTS:")
            for i, result in enumerate(results['results'], 1):
                status_icon = "✅" if result['status'] == 'success' else "❌"
                api_used = result.get('api_used', 'Unknown')
                
                print(f"\n{i}. {status_icon} {result['route']}")
                print(f"   API: {api_used}")
                
                if result['status'] == 'success':
                    if 'prices_found' in result:
                        print(f"   Prices found: {result['prices_found']}")
                        if result.get('sample_price'):
                            price = result['sample_price']
                            print(f"   Sample: €{price.get('price', 'N/A')} via {price.get('airline', 'N/A')}")
                    
                    if 'flights_found' in result:
                        print(f"   Flights found: {result['flights_found']}")
                        if result.get('sample_flight'):
                            flight = result['sample_flight']
                            print(f"   Sample: {flight.get('airline', 'N/A')} - {flight.get('departure_time', 'N/A')}")
                
                elif result['status'] == 'error':
                    print(f"   {Fore.RED}Error: {result.get('error', 'Unknown error')}")
                
                elif result['status'] == 'no_data':
                    print(f"   {Fore.YELLOW}No data available for this route")
        
        # Recommendations
        print(f"\n{Fore.MAGENTA}💡 RECOMMENDATIONS:")
        if results['successful_scans'] == 0:
            print(f"  • All scans failed - check API keys and connectivity")
            print(f"  • Try using TravelPayouts API as primary source")
        elif results['successful_scans'] < results['routes_tested']:
            print(f"  • Some routes failed - this is normal with rate limits")
            print(f"  • Consider spacing scans further apart")
        else:
            print(f"  • All scans successful! APIs are working well")
            print(f"  • You can now use the main scanner with confidence")
        
        print(f"\n{Fore.CYAN}🔧 NEXT STEPS:")
        print(f"  • Use admin dashboard for bulk scanning")
        print(f"  • Set up Celery worker for automated scanning")
        print(f"  • Monitor console with: python3 scripts/monitor_scanner.py")
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Scan cancelled by user")
    except Exception as e:
        print(f"\n{Fore.RED}Error during scan: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
