# Railway CLI Deployment Guide

Complete step-by-step guide to deploy using Railway CLI.

## Step 1: Install Railway CLI

```bash
npm install -g @railway/cli
```

Or using Homebrew (macOS):
```bash
brew install railway
```

## Step 2: Login to Railway

```bash
railway login
```

This will open your browser to authenticate.

## Step 3: Initialize Railway Project

```bash
# Navigate to your project root
cd /Users/alexho/SpendSense

# Initialize Railway project
railway init
```

When prompted:
- Choose "Create a new project" or "Link to existing project"
- Enter project name (e.g., "spendsense-backend")

## Step 4: Link to Existing Project (if needed)

If you already created a project in the dashboard:

```bash
railway link
```

Select your project from the list.

## Step 5: Set Environment Variables

```bash
# Set CORS origins (temporary, update after Vercel deploy)
railway variables set CORS_ORIGINS="http://localhost:3000"

# Optional: Set JWT secret key for production
railway variables set JWT_SECRET_KEY="your-secure-secret-key-here"
```

## Step 6: Verify Configuration

Your `railway.json` already has the start command configured, but you can verify:

```bash
cat railway.json
```

Should show:
```json
{
  "deploy": {
    "startCommand": "uvicorn api.main:app --host 0.0.0.0 --port $PORT"
  }
}
```

## Step 7: Deploy

```bash
railway up
```

This will:
1. Build your application
2. Install dependencies from `requirements.txt`
3. Deploy using the start command from `railway.json`
4. Show deployment logs

## Step 8: Get Your Deployment URL

```bash
railway domain
```

Or check the Railway dashboard for your service URL.

## Step 9: View Logs

```bash
railway logs
```

Or follow logs in real-time:
```bash
railway logs --follow
```

## Step 10: Update Environment Variables (After Vercel Deploy)

Once you have your Vercel URL:

```bash
railway variables set CORS_ORIGINS="http://localhost:3000,https://your-vercel-app.vercel.app,https://your-vercel-app-*.vercel.app"
```

This will trigger a redeploy automatically.

## Useful CLI Commands

```bash
# Check status
railway status

# View all environment variables
railway variables

# Open Railway dashboard
railway open

# Connect to service shell
railway shell

# Run a command in the service
railway run python3 scripts/setup_passwords.py

# View service info
railway service
```

## Troubleshooting

**If deployment fails:**
```bash
# Check logs
railway logs

# Verify variables
railway variables

# Redeploy
railway up
```

**If you need to change start command:**
Edit `railway.json` or set via CLI:
```bash
railway variables set RAILWAY_START_COMMAND="uvicorn api.main:app --host 0.0.0.0 --port $PORT"
```

**If Python version issues:**
Create `runtime.txt` in root:
```
python-3.11
```

## Next Steps

After successful deployment:
1. Copy your Railway URL
2. Deploy frontend to Vercel
3. Update CORS_ORIGINS with Vercel URL
4. Test the full stack

