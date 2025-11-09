#!/bin/bash
# Quick API test script

echo "Testing Backend API on port 8000..."
echo ""

# Test root
echo "1. Testing root endpoint (/)..."
curl -s -w " - Status: %{http_code}\n" http://localhost:8000/ | head -1

# Test stats
echo ""
echo "2. Testing stats endpoint (/api/stats)..."
curl -s -w " - Status: %{http_code}\n" http://localhost:8000/api/stats | head -1

# Test login
echo ""
echo "3. Testing login endpoint (/api/auth/login)..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@spendsense.com","password":"123456"}')
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')
echo "Response: $BODY"
echo "Status: $HTTP_CODE"

# Test users list
echo ""
echo "4. Testing users endpoint (/api/users)..."
curl -s -w " - Status: %{http_code}\n" http://localhost:8000/api/users | head -1

echo ""
echo "Done!"

