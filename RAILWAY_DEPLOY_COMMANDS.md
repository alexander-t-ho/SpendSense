# Railway Deployment Commands - Step 3 and Beyond

Since you have your Railway project link, here are the exact commands to run:

## Step 3: Set Environment Variables

**First, make sure you're logged in:**
```bash
railway login
```

**Then set environment variables using the correct syntax:**

```bash
# Set CORS origins
railway variables --set CORS_ORIGINS="http://localhost:3000"

# Optional: Set JWT secret key
railway variables --set JWT_SECRET_KEY="your-secure-secret-key-change-this"
```

**Alternative syntax (if the above doesn't work):**
```bash
railway variables add CORS_ORIGINS "http://localhost:3000"
```

## Step 4: Link to Your Project (if not already linked)

Since you have the project URL, you can link directly:

```bash
railway link
# Select your project from the list, or
# Use the project ID from your URL: 0448ee28-a801-4a80-a809-92bf400cbcbc
```

## Step 5: Deploy

```bash
railway up
```

This will:
- Build your application
- Install dependencies from `requirements.txt`
- Deploy using the start command from `railway.json`
- Show deployment progress

## Step 6: Get Your Deployment URL

```bash
railway domain
```

Or check the Railway dashboard at your project URL.

## Step 7: View Logs

```bash
# View recent logs
railway logs

# Follow logs in real-time
railway logs --follow
```

## Step 8: Verify Deployment

Check your service is running:
```bash
railway status
```

## After Vercel Deployment - Update CORS

Once you have your Vercel URL:

```bash
railway variables --set CORS_ORIGINS="http://localhost:3000,https://your-vercel-app.vercel.app,https://your-vercel-app-*.vercel.app"
```

## Quick Command Reference

```bash
# Login (if needed)
railway login

# Link to project
railway link

# Set environment variable
railway variables --set KEY="value"

# View all variables
railway variables

# Deploy
railway up

# Get URL
railway domain

# View logs
railway logs

# Check status
railway status

# Open dashboard
railway open
```

## Troubleshooting

**If "Unauthorized" error:**
```bash
railway login
```

**If variables command fails, try:**
```bash
railway variables add KEY "value"
```

**To view help:**
```bash
railway variables --help
railway --help
```

