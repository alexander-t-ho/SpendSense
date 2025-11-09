#!/usr/bin/env python3
"""Test script to verify all backend API endpoints are working."""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_endpoint(method, endpoint, data=None, headers=None, description=""):
    """Test an API endpoint."""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n{'='*60}")
    print(f"Testing: {method} {endpoint}")
    if description:
        print(f"Description: {description}")
    print(f"{'='*60}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=5)
        else:
            print(f"❌ Unsupported method: {method}")
            return False
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code < 400:
            try:
                result = response.json()
                print(f"Response: {json.dumps(result, indent=2)[:500]}...")
            except:
                print(f"Response: {response.text[:200]}")
            print("✅ SUCCESS")
            return True
        else:
            print(f"❌ FAILED")
            try:
                error = response.json()
                print(f"Error: {json.dumps(error, indent=2)}")
            except:
                print(f"Error: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ FAILED - Cannot connect to {BASE_URL}")
        print("   Make sure the backend server is running on port 8000")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ FAILED - Request timed out")
        return False
    except Exception as e:
        print(f"❌ FAILED - {str(e)}")
        return False

def main():
    print("="*60)
    print("Backend API Test Suite")
    print("="*60)
    
    results = []
    
    # Test root endpoint
    results.append(("Root", test_endpoint("GET", "/", description="Root endpoint")))
    
    # Test stats endpoint
    results.append(("Stats", test_endpoint("GET", "/api/stats", description="Get statistics")))
    
    # Test auth endpoints
    print("\n" + "="*60)
    print("AUTHENTICATION ENDPOINTS")
    print("="*60)
    
    # Test login with admin
    login_data = {
        "username": "admin@spendsense.com",
        "password": "123456"
    }
    login_result = test_endpoint("POST", "/api/auth/login", data=login_data, description="Admin login")
    results.append(("Admin Login", login_result))
    
    token = None
    if login_result:
        try:
            response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, timeout=5)
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                print(f"\n✅ Got access token: {token[:20]}...")
        except:
            pass
    
    # Test /api/auth/me with token
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        results.append(("Get Current User", test_endpoint("GET", "/api/auth/me", headers=headers, description="Get current user info")))
    
    # Test logout
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        results.append(("Logout", test_endpoint("POST", "/api/auth/logout", headers=headers, description="Logout")))
    
    # Test users endpoint
    print("\n" + "="*60)
    print("USER ENDPOINTS")
    print("="*60)
    
    results.append(("List Users", test_endpoint("GET", "/api/users", description="List all users")))
    
    # Test a specific user endpoint (get first user if available)
    try:
        response = requests.get(f"{BASE_URL}/api/users", timeout=5)
        if response.status_code == 200:
            users = response.json()
            if users and len(users) > 0:
                first_user_id = users[0].get("id")
                if first_user_id:
                    results.append(("Get User Detail", test_endpoint("GET", f"/api/users/{first_user_id}", description=f"Get user {first_user_id}")))
    except:
        pass
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)

