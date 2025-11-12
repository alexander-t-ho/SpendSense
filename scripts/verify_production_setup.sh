#!/bin/bash
# Script to verify production environment setup for SpendSense

set -e

echo "🔍 SpendSense Production Environment Verification"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
RAILWAY_URL="https://web-production-d242.up.railway.app"
VERCEL_URL="https://spend-sense-o3df.vercel.app"

echo "📋 Checking Configuration..."
echo ""

# Check 1: Railway Backend
echo "1️⃣  Checking Railway Backend..."
if curl -s -f "${RAILWAY_URL}/" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Railway backend is accessible${NC}"
    BACKEND_RESPONSE=$(curl -s "${RAILWAY_URL}/")
    echo "   Response: $BACKEND_RESPONSE"
else
    echo -e "${RED}❌ Railway backend is not accessible${NC}"
    echo "   URL: ${RAILWAY_URL}"
    echo "   Please check Railway dashboard for service status"
fi
echo ""

# Check 2: Admin User Creation
echo "2️⃣  Checking Admin User..."
ADMIN_RESPONSE=$(curl -s -X POST "${RAILWAY_URL}/api/admin/create-admin" 2>&1)
if echo "$ADMIN_RESPONSE" | grep -q "Admin user"; then
    echo -e "${GREEN}✅ Admin user endpoint is working${NC}"
    echo "   Response: $ADMIN_RESPONSE"
else
    echo -e "${YELLOW}⚠️  Admin user endpoint may have issues${NC}"
    echo "   Response: $ADMIN_RESPONSE"
fi
echo ""

# Check 3: Test Login
echo "3️⃣  Testing Login Endpoint..."
LOGIN_RESPONSE=$(curl -s -X POST "${RAILWAY_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@spendsense.com","password":"123456"}' 2>&1)

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✅ Login endpoint is working${NC}"
    echo "   Credentials: admin@spendsense.com / 123456"
else
    echo -e "${RED}❌ Login endpoint failed${NC}"
    echo "   Response: $LOGIN_RESPONSE"
    echo ""
    echo "   This could mean:"
    echo "   - Admin user doesn't exist (run step 2 first)"
    echo "   - Password is incorrect"
    echo "   - Database connection issue"
fi
echo ""

# Check 4: Vercel Frontend
echo "4️⃣  Checking Vercel Frontend..."
if curl -s -f "${VERCEL_URL}" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Vercel frontend is accessible${NC}"
else
    echo -e "${RED}❌ Vercel frontend is not accessible${NC}"
    echo "   URL: ${VERCEL_URL}"
fi
echo ""

# Check 5: Environment Variables
echo "5️⃣  Environment Variables Checklist..."
echo ""
echo "   📝 Vercel Environment Variables (check in Vercel dashboard):"
echo "      - VITE_API_URL should be set to: ${RAILWAY_URL}"
echo ""
echo "   📝 Railway Environment Variables (check in Railway dashboard):"
echo "      - CORS_ORIGINS should include: ${VERCEL_URL}"
echo "      - CORS_ORIGINS should also include: http://localhost:3004 (for local dev)"
echo ""

# Instructions
echo "📚 Next Steps:"
echo ""
echo "   If login is failing:"
echo "   1. Ensure VITE_API_URL is set in Vercel:"
echo "      - Go to Vercel Dashboard → Your Project → Settings → Environment Variables"
echo "      - Add: VITE_API_URL = ${RAILWAY_URL}"
echo "      - Redeploy your Vercel app"
echo ""
echo "   2. Ensure CORS_ORIGINS is set in Railway:"
echo "      - Go to Railway Dashboard → Your Service → Variables"
echo "      - Set: CORS_ORIGINS = http://localhost:3004,${VERCEL_URL}"
echo "      - Restart your Railway service"
echo ""
echo "   3. Create/Reset Admin User:"
echo "      curl -X POST ${RAILWAY_URL}/api/admin/create-admin"
echo ""
echo "   4. Test login:"
echo "      curl -X POST ${RAILWAY_URL}/api/auth/login \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"username\":\"admin@spendsense.com\",\"password\":\"123456\"}'"
echo ""

echo "✅ Verification complete!"
echo ""


