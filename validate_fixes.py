#!/usr/bin/env python3
"""
Validation script for GlobeGenius authentication and admin dashboard fixes
"""
import requests
import json
import sys
from time import sleep

BASE_URL = "http://localhost:8000/api/v1"
ADMIN_EMAIL = "admin@globegenius.app"
ADMIN_PASSWORD = "admin123"

def test_authentication():
    """Test admin authentication"""
    print("🔐 Testing authentication...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                print("✅ Authentication successful!")
                return data["access_token"]
            else:
                print("❌ No access token in response")
                print(f"Response: {data}")
                return None
        else:
            print(f"❌ Authentication failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

def test_admin_endpoints(token):
    """Test admin dashboard endpoints"""
    print("📊 Testing admin endpoints...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    endpoints = [
        ("Dashboard Stats", "/admin/dashboard/stats"),
        ("Route Performance", "/admin/routes/performance"),
        ("Seasonal Visualization", "/admin/seasonal/visualization"),
        ("User Analytics", "/admin/users/analytics"),
        ("System Health", "/admin/system/health"),
        ("API KPIs", "/admin/api/kpis")
    ]
    
    results = {}
    
    for name, endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {name}: OK")
                results[name] = {"status": "success", "data": data}
            else:
                print(f"❌ {name}: Failed ({response.status_code})")
                results[name] = {"status": "error", "code": response.status_code}
                
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
            results[name] = {"status": "error", "message": str(e)}
    
    return results

def check_services():
    """Check if services are running"""
    print("🔍 Checking service availability...")
    
    # Check backend
    try:
        response = requests.get(f"{BASE_URL}/health/")
        if response.status_code == 200:
            print("✅ Backend service is running")
        else:
            print(f"⚠️ Backend returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Backend service not accessible: {e}")
        return False
    
    # Check frontend
    try:
        response = requests.get("http://localhost:3001")
        if response.status_code == 200:
            print("✅ Frontend service is running")
        else:
            print(f"⚠️ Frontend returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Frontend service not accessible: {e}")
    
    return True

def main():
    print("🚀 GlobeGenius Validation Test")
    print("=" * 50)
    
    # Check services
    if not check_services():
        print("❌ Services not available. Please start them first.")
        sys.exit(1)
    
    # Test authentication
    token = test_authentication()
    if not token:
        print("❌ Authentication failed. Cannot proceed with admin endpoint tests.")
        sys.exit(1)
    
    # Test admin endpoints
    results = test_admin_endpoints(token)
    
    # Summary
    print("\n📋 Test Summary:")
    success_count = sum(1 for r in results.values() if r["status"] == "success")
    total_count = len(results)
    
    print(f"✅ Successful endpoints: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 All tests passed! Authentication and admin dashboard are working correctly.")
    else:
        print("⚠️ Some endpoints failed. Check the logs above for details.")
        
        # Show failed endpoints
        failed = [name for name, result in results.items() if result["status"] != "success"]
        if failed:
            print(f"❌ Failed endpoints: {', '.join(failed)}")

if __name__ == "__main__":
    main()