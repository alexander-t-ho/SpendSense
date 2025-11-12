# Quick Railway CORS Setup

## Step 1: Link Railway Project

Run this command and select your project:
```bash
railway link
```

**Select the project that contains your backend service** (likely "Leafly" - this is the SpendSense backend project).

## Step 2: Set CORS

Once linked, run:
```bash
./setup_railway_cors.sh
```

Or manually:
```bash
railway variables --set "CORS_ORIGINS=http://localhost:3004,https://spend-sense-o3df.vercel.app"
```

## Step 3: Restart Railway Service

Restart your Railway service for changes to take effect:
- Go to Railway dashboard → Your service → Click "Restart"
- Or use CLI: `railway restart` (if available)

## Verify

Test your backend:
```bash
curl https://web-production-d242.up.railway.app/
```

Should return: `{"message":"SpendSense API","version":"1.0.0"}`

## Alternative: Use Railway Dashboard

If CLI doesn't work:
1. Go to https://railway.app
2. Open your project
3. Click on your backend service
4. Go to **Variables** tab
5. Add/update `CORS_ORIGINS` = `http://localhost:3004,https://spend-sense-o3df.vercel.app`
6. Save and restart service

