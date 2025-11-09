# Railway CLI Deployment - Manual Steps

Due to Node.js library issues, here are the manual CLI commands to run:

## Step 1: Verify Railway CLI Installation

The Railway CLI should be installed. Check if it's available:

```bash
# Try these paths:
~/.railway/bin/railway --version
# OR
railway --version
# OR check if it's in PATH
which railway
```

If not found, add to PATH:
```bash
export PATH="$HOME/.railway/bin:$PATH"
```

## Step 2: Login to Railway

```bash
railway login
```

This will open your browser for authentication.

## Step 3: Initialize Railway Project

**Option A: Create New Project**
```bash
cd /Users/alexho/SpendSense
railway init
# When prompted, choose "Create a new project"
# Enter project name: spendsense-backend
```

**Option B: Link to Existing Project**
```bash
cd /Users/alexho/SpendSense
railway link
# Select your existing project from the list
```

## Step 4: Set Environment Variables

```bash
# Set CORS origins (temporary - update after Vercel deploy)
railway variables set CORS_ORIGINS="http://localhost:3000"

# Optional: Set JWT secret key for production
railway variables set JWT_SECRET_KEY="your-secure-secret-key-change-this"
```

## Step 5: Verify Configuration

Your `railway.json` already has the start command configured:

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

## Step 6: Deploy

```bash
railway up
```

This will:
- Build your application
- Install dependencies from `requirements.txt`
- Deploy using the start command
- Show deployment progress

## Step 7: Get Your Deployment URL

```bash
railway domain
```

Or check status:
```bash
railway status
```

## Step 8: View Logs

```bash
# View recent logs
railway logs

# Follow logs in real-time
railway logs --follow
```

## Step 9: Update CORS After Vercel Deploy

Once you have your Vercel URL:

```bash
railway variables set CORS_ORIGINS="http://localhost:3000,https://your-vercel-app.vercel.app,https://your-vercel-app-*.vercel.app"
```

This will automatically trigger a redeploy.

## Useful Commands

```bash
# Check deployment status
railway status

# View all environment variables
railway variables

# Open Railway dashboard in browser
railway open

# Connect to service shell
railway shell

# Run a command in the service
railway run python3 scripts/setup_passwords.py

# View service information
railway service

# Redeploy
railway up
```

## Troubleshooting

**If Railway CLI not found:**
```bash
# Add to PATH (add to ~/.zshrc or ~/.bashrc for permanent)
export PATH="$HOME/.railway/bin:$PATH"

# Or use full path
~/.railway/bin/railway --version
```

**If deployment fails:**
```bash
# Check logs for errors
railway logs

# Verify environment variables
railway variables

# Check service status
railway status
```

**If you need to change start command:**
The `railway.json` file already has it configured, but you can override:
```bash
railway variables set RAILWAY_START_COMMAND="uvicorn api.main:app --host 0.0.0.0 --port $PORT"
```

## Quick Reference

All commands should be run from the project root:
```bash
cd /Users/alexho/SpendSense
```

Essential commands:
1. `railway login` - Authenticate
2. `railway init` or `railway link` - Setup project
3. `railway variables set KEY=value` - Set env vars
4. `railway up` - Deploy
5. `railway domain` - Get URL
6. `railway logs` - View logs

