#!/bin/bash
# Script to help set VITE_API_URL in Vercel
# Note: This requires Vercel CLI to be installed and authenticated

set -e

RAILWAY_BACKEND_URL="https://web-production-d242.up.railway.app"
VERCEL_PROJECT="spend-sense-o3df"

echo "🔧 Vercel Environment Variable Setup"
echo "======================================"
echo ""
echo "This script will help you set VITE_API_URL in Vercel."
echo ""
echo "Railway Backend URL: ${RAILWAY_BACKEND_URL}"
echo "Vercel Project: ${VERCEL_PROJECT}"
echo ""

# Check if vercel CLI is available
if ! command -v vercel &> /dev/null; then
    echo "⚠️  Vercel CLI not found."
    echo ""
    echo "Option 1: Install Vercel CLI"
    echo "  npm install -g vercel"
    echo ""
    echo "Option 2: Set via Vercel Dashboard (Recommended)"
    echo "  1. Go to: https://vercel.com/dashboard"
    echo "  2. Select project: ${VERCEL_PROJECT}"
    echo "  3. Go to Settings → Environment Variables"
    echo "  4. Add:"
    echo "     Name: VITE_API_URL"
    echo "     Value: ${RAILWAY_BACKEND_URL}"
    echo "     Environment: Production (and Preview if desired)"
    echo "  5. Save and Redeploy"
    echo ""
    exit 1
fi

echo "✅ Vercel CLI found"
echo ""

# Check if logged in
if ! vercel whoami &> /dev/null; then
    echo "⚠️  Not logged in to Vercel"
    echo "Running: vercel login"
    vercel login
fi

echo "Setting VITE_API_URL environment variable..."
echo ""

# Set for production
vercel env add VITE_API_URL production <<< "${RAILWAY_BACKEND_URL}" || {
    echo "⚠️  Failed to set via CLI. Using dashboard method..."
    echo ""
    echo "Please set manually:"
    echo "  1. Go to: https://vercel.com/dashboard"
    echo "  2. Select project: ${VERCEL_PROJECT}"
    echo "  3. Settings → Environment Variables"
    echo "  4. Add VITE_API_URL = ${RAILWAY_BACKEND_URL}"
    exit 1
}

echo ""
echo "✅ VITE_API_URL set successfully!"
echo ""
echo "⚠️  IMPORTANT: Redeploy your Vercel app for changes to take effect"
echo ""
echo "You can redeploy via:"
echo "  1. Vercel Dashboard → Deployments → Click '...' → Redeploy"
echo "  2. Or push a new commit to trigger deployment"
echo ""

