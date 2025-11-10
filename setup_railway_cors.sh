#!/bin/bash
# Script to set Railway CORS_ORIGINS with Vercel URL

set -e

VERCEL_URL="https://spend-sense-o3df.vercel.app"
CORS_VALUE="http://localhost:3004,${VERCEL_URL}"

echo "🔧 Railway CORS Configuration"
echo "============================="
echo ""
echo "Vercel URL: ${VERCEL_URL}"
echo "CORS_ORIGINS: ${CORS_VALUE}"
echo ""

# Check if Railway is linked
if ! railway status &> /dev/null; then
    echo "⚠️  Railway project not linked."
    echo ""
    echo "Please link your Railway project first:"
    echo "  1. Run: railway link"
    echo "  2. Select your project: 'respectful-surprise' (SpendSense backend)"
    echo "  3. Then run this script again: ./setup_railway_cors.sh"
    echo ""
    exit 1
fi

echo "✅ Railway project is linked"
echo ""

# Show current variables
echo "📋 Current CORS_ORIGINS:"
railway variables 2>&1 | grep -i CORS_ORIGINS || echo "  (not currently set)"
echo ""

# Set CORS_ORIGINS
echo "🔄 Setting CORS_ORIGINS..."
railway variables --set "CORS_ORIGINS=${CORS_VALUE}"

echo ""
echo "✅ CORS_ORIGINS updated successfully!"
echo ""
echo "Updated to: ${CORS_VALUE}"
echo ""
echo "⚠️  Important: Restart your Railway service for changes to take effect!"
echo "   You can do this in the Railway dashboard or run: railway restart"
echo ""

