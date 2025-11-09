# Production Deployment Guide

This guide will walk you through deploying SpendSense to production.

## Prerequisites

1. **GitHub Account** - Your code should be pushed to GitHub
2. **Railway Account** (for backend) - Sign up at [railway.app](https://railway.app)
3. **Vercel Account** (for frontend) - Sign up at [vercel.com](https://vercel.com)

## Step 1: Commit and Push Your Code

```bash
git add -A
git commit -m "Prepare for production deployment"
git push origin main
```

## Step 2: Deploy Backend to Railway

### 2.1 Create Railway Project

1. Go to [railway.app](https://railway.app) and sign in
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your SpendSense repository
5. Railway will auto-detect it's a Python project

### 2.2 Configure Backend Service

1. **Set Root Directory**: Click on the service → Settings → Root Directory: Leave as root (or set to `/`)
2. **Set Start Command**: 
   ```
   uvicorn api.main:app --host 0.0.0.0 --port $PORT
   ```
3. **Set Environment Variables**:
   - `CORS_ORIGINS`: `http://localhost:3000,https://your-vercel-app.vercel.app,https://your-vercel-app-*.vercel.app`
   - (We'll update this after Vercel deployment with the actual URL)

### 2.3 Deploy Database

1. Click "New" → "Database" → "Add PostgreSQL" (or use SQLite for now)
2. If using PostgreSQL, update your connection string
3. For SQLite, the database file will be in the Railway filesystem

### 2.4 Get Your Backend URL

1. After deployment, Railway will provide a URL like: `https://your-app.up.railway.app`
2. Copy this URL - you'll need it for the frontend

## Step 3: Deploy Frontend to Vercel

### 3.1 Create Vercel Project

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click "Add New Project"
3. Import your GitHub repository
4. **Important**: Set Root Directory to `ui`

### 3.2 Configure Build Settings

- **Framework Preset**: Vite (auto-detected)
- **Build Command**: `npm run build` (auto-detected)
- **Output Directory**: `dist` (auto-detected)
- **Install Command**: `npm install` (auto-detected)

### 3.3 Set Environment Variables

Add these in Vercel Dashboard → Project Settings → Environment Variables:

- `VITE_API_URL`: `https://your-railway-backend.up.railway.app`
- `VITE_WS_BASE_URL`: `wss://your-railway-backend.up.railway.app` (optional, for WebSockets)

### 3.4 Deploy

Click "Deploy" and wait for the build to complete.

### 3.5 Get Your Frontend URL

After deployment, Vercel will provide a URL like: `https://your-project.vercel.app`
Copy this URL.

## Step 4: Update Backend CORS

1. Go back to Railway dashboard
2. Update the `CORS_ORIGINS` environment variable:
   ```
   http://localhost:3000,https://your-project.vercel.app,https://your-project-*.vercel.app
   ```
3. Redeploy the backend service

## Step 5: Test Production Deployment

1. Visit your Vercel URL
2. Test login functionality
3. Check browser console for errors
4. Verify API calls are working
5. Test key features:
   - User dashboard
   - Transaction viewing
   - Recommendations
   - Admin dashboard

## Troubleshooting

### Backend Issues

- **Build fails**: Check Railway logs
- **Database connection fails**: Verify database credentials
- **CORS errors**: Update CORS_ORIGINS with correct Vercel URL

### Frontend Issues

- **Build fails**: Check Vercel build logs
- **API calls fail**: Verify VITE_API_URL is set correctly
- **404 on refresh**: Verify vercel.json rewrite rules

## Alternative: Deploy to Render

If you prefer Render over Railway:

1. Go to [render.com](https://render.com)
2. Create a new "Web Service"
3. Connect your GitHub repo
4. Set:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables (same as Railway)
6. Deploy

## Next Steps

- Set up custom domain (optional)
- Configure monitoring and logging
- Set up database backups
- Configure CI/CD for automatic deployments

