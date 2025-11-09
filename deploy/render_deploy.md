# Render Deployment Guide

Render provides easy deployment for both backend and frontend services.

## Prerequisites

- Render account (free tier available)
- Git repository

## Architecture

- **Backend**: FastAPI Web Service
- **Frontend**: Static Site
- **Database**: Render PostgreSQL (or keep SQLite)

## Step 1: Deploy Backend

1. Go to Render Dashboard → New → Web Service
2. Connect your Git repository
3. Configure:
   - **Name**: `spendsense-api`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free or Starter

4. Set environment variables:
   - `JWT_SECRET_KEY`: Generate a secure secret key
   - `CORS_ORIGINS`: Your frontend URL (will be set after frontend deploy)
   - `PORT`: Render sets this automatically

5. Deploy

## Step 2: Setup Database

### Option A: Render PostgreSQL (Recommended)

1. Create PostgreSQL database in Render dashboard
2. Get connection string
3. Update database connection in code
4. Run migrations via Render shell:
   ```bash
   python3 scripts/migrate_auth_columns.py
   python3 scripts/setup_passwords.py
   ```

### Option B: Keep SQLite

- Use Render disk for persistent storage
- Note: Free tier has limited disk space

## Step 3: Deploy Frontend

1. Go to Render Dashboard → New → Static Site
2. Connect your Git repository
3. Configure:
   - **Name**: `spendsense-frontend`
   - **Build Command**: `cd ui && npm install && npm run build`
   - **Publish Directory**: `ui/dist`
   - **Environment**: Node

4. Set environment variable:
   - `VITE_API_URL`: Your backend Render URL

5. Deploy

## Step 4: Update CORS

Update backend `CORS_ORIGINS` environment variable with your frontend Render URL.

## Cost Estimates

- **Free tier**: Limited hours/month, sleeps after inactivity
- **Starter plan**: $7/month per service (always on)
- **PostgreSQL**: Free tier available (90 days), then $7/month

## Advantages

- Free tier available
- Easy setup
- Automatic HTTPS
- Built-in PostgreSQL option
- GitHub integration

