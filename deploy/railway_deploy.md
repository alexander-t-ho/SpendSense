# Railway Deployment Guide

Railway is a modern platform that makes deploying full-stack applications easy.

## Prerequisites

- Railway account (free tier available)
- Railway CLI installed: `npm i -g @railway/cli`
- Git repository

## Architecture

- **Backend**: FastAPI service
- **Frontend**: React static site
- **Database**: Railway PostgreSQL (or keep SQLite)

## Step 1: Create Railway Project

1. Install Railway CLI:
   ```bash
   npm i -g @railway/cli
   ```

2. Login:
   ```bash
   railway login
   ```

3. Initialize project:
   ```bash
   railway init
   ```

## Step 2: Deploy Backend

1. Create `railway.json` in project root:
   ```json
   {
     "build": {
       "builder": "NIXPACKS"
     },
     "deploy": {
       "startCommand": "uvicorn api.main:app --host 0.0.0.0 --port $PORT",
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 10
     }
   }
   ```

2. Set environment variables in Railway dashboard:
   - `JWT_SECRET_KEY`: Generate a secure secret key
   - `CORS_ORIGINS`: Your frontend URL
   - `PORT`: Railway will set this automatically

3. Deploy:
   ```bash
   railway up
   ```

## Step 3: Setup Database

### Option A: Railway PostgreSQL (Recommended)

1. Add PostgreSQL service in Railway dashboard
2. Get connection string from Railway
3. Update `ingest/schema.py` to use PostgreSQL connection
4. Run migrations:
   ```bash
   railway run python3 scripts/migrate_auth_columns.py
   railway run python3 scripts/setup_passwords.py
   ```

### Option B: Keep SQLite

1. Use Railway volume for persistent storage
2. Mount volume in service settings

## Step 4: Deploy Frontend

1. Create separate service for frontend
2. Set build command: `cd ui && npm install && npm run build`
3. Set start command: `npx serve -s ui/dist -l $PORT`
4. Set environment variable:
   - `VITE_API_URL`: Your backend Railway URL

## Step 5: Update Frontend API URL

Update `ui/src/components/AuthContext.tsx` to use environment variable:
```typescript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
```

## Cost Estimates

- **Free tier**: $5 credit/month
- **Hobby plan**: $20/month (includes more resources)
- **PostgreSQL**: Included in plans

## Advantages

- Simple deployment process
- Built-in PostgreSQL
- Automatic HTTPS
- Easy environment variable management
- GitHub integration

