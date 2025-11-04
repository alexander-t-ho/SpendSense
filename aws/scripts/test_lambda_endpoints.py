#!/usr/bin/env python3
"""Test Lambda functions via API Gateway endpoints."""

import requests
import json
import sys
from pathlib import Path

# Load resources
RESOURCES_PATH = Path(__file__).parent.parent / "config" / "aws_resources.json"
with open(RESOURCES_PATH, 'r') as f:
    resources = json.load(f)

api_url = resources['api_gateway']['api_url']
stage = resources['api_gateway']['stage']

def get_user_id():
    """Get a user ID from the database."""
    import sqlite3
    db_path = Path(__file__).parent.parent.parent / "data" / "spendsense.db"
    
    if not db_path.exists():
        print("❌ Database not found. Please generate data first.")
        return None
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users LIMIT 1')
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None

def test_endpoint(endpoint_path: str, user_id: str = None, params: dict = None):
    """Test an API Gateway endpoint.
    
    Args:
        endpoint_path: Path like 'insights/{user_id}/weekly-recap'
        user_id: User ID to test with
        params: Query parameters
    """
    if user_id:
        url_path = endpoint_path.replace('{user_id}', user_id)
    else:
        url_path = endpoint_path
    
    url = f"{api_url}/{url_path}"
    
    try:
        print(f"\nTesting: {url_path}")
        print(f"  URL: {url}")
        
        response = requests.get(url, params=params, timeout=30)
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"  ✅ Success!")
                print(f"  Response preview: {json.dumps(data, indent=2)[:500]}...")
                return True
            except json.JSONDecodeError:
                print(f"  ⚠️  Response is not JSON: {response.text[:200]}")
                return False
        else:
            print(f"  ❌ Error: {response.status_code}")
            print(f"  Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Request failed: {e}")
        return False

def main():
    """Test all Lambda endpoints."""
    print("=" * 60)
    print("Testing Lambda Functions via API Gateway")
    print("=" * 60)
    print(f"API URL: {api_url}")
    print("=" * 60)
    
    # Get user ID
    user_id = get_user_id()
    if not user_id:
        print("\n❌ No user ID available. Please provide one as argument:")
        print("   python test_lambda_endpoints.py <user_id>")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    
    print(f"\nUsing User ID: {user_id}")
    
    # Test endpoints
    endpoints = [
        ('insights/{user_id}/weekly-recap', None),
        ('insights/{user_id}/spending-analysis', {'months': 6}),
        ('insights/{user_id}/net-worth', {'period': 'month'}),
        ('insights/{user_id}/suggested-budget', None),
        ('insights/{user_id}/budget-tracking', None),
    ]
    
    results = []
    for endpoint, params in endpoints:
        success = test_endpoint(endpoint, user_id, params)
        results.append((endpoint, success))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for endpoint, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {endpoint}")
    
    print("=" * 60)
    print(f"Results: {passed}/{total} endpoints passed")
    print("=" * 60)
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())

