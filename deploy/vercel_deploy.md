# Vercel Deployment Guide for SpendSense Frontend

This guide will help you deploy the SpendSense frontend to Vercel.

## Prerequisites

1. A Vercel account (sign up at [vercel.com](https://vercel.com))
2. Your code pushed to a GitHub, GitLab, or Bitbucket repository
3. Your backend API deployed and accessible via HTTPS (Railway, Render, Fly.io, etc.)

## Step 1: Deploy Your Backend First

Before deploying the frontend, ensure your backend is deployed and accessible:

- **Recommended platforms**: Railway, Render, Fly.io, or AWS Lambda
- **Backend URL**: Note your production backend URL (e.g., `https://spendsense-api.railway.app`)

## Step 2: Prepare Your Repository

1. Ensure all your code is committed and pushed to your repository
2. Make sure the `ui/` directory contains all frontend code
3. Verify `ui/package.json` has the correct build scripts

## Step 3: Deploy to Vercel

### Option A: Deploy via Vercel Dashboard (Recommended)

1. **Go to Vercel Dashboard**
   - Visit [vercel.com/dashboard](https://vercel.com/dashboard)
   - Click "Add New Project"

2. **Import Your Repository**
   - Connect your Git provider (GitHub, GitLab, or Bitbucket)
   - Select your SpendSense repository
   - Click "Import"

3. **Configure Project Settings**
   - **Root Directory**: Set to `ui` (click "Edit" next to Root Directory)
   - **Framework Preset**: Select "Vite" (or it will auto-detect)
   - **Build Command**: `npm run build` (should auto-detect)
   - **Output Directory**: `dist` (should auto-detect)
   - **Install Command**: `npm install` (should auto-detect)

4. **Set Environment Variables**
   - Click "Environment Variables"
   - Add the following:
     ```
     VITE_API_URL=https://your-backend-url.com
     ```
     Replace `https://your-backend-url.com` with your actual backend URL
   - Optionally add:
     ```
     VITE_WS_BASE_URL=wss://your-backend-url.com
     ```
     (Only if you're using WebSockets and your backend supports WSS)

5. **Deploy**
   - Click "Deploy"
   - Wait for the build to complete
   - Your app will be live at `https://your-project.vercel.app`

### Option B: Deploy via Vercel CLI

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Navigate to UI Directory**
   ```bash
   cd ui
   ```

4. **Deploy**
   ```bash
   vercel
   ```
   - Follow the prompts
   - When asked for root directory, confirm it's the current directory
   - When asked for build settings, confirm or adjust as needed

5. **Set Environment Variables**
   ```bash
   vercel env add VITE_API_URL
   ```
   - Enter your backend URL when prompted
   - Select "Production", "Preview", and "Development" environments

6. **Redeploy with Environment Variables**
   ```bash
   vercel --prod
   ```

## Step 4: Configure Backend CORS

Make sure your backend allows requests from your Vercel domain:

1. Update your backend's CORS configuration to include:
   ```python
   allowed_origins = [
       "http://localhost:3000",
       "https://your-project.vercel.app",
       "https://your-project-*.vercel.app"  # For preview deployments
   ]
   ```

2. Or use environment variable in your backend:
   ```python
   allowed_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
   ```

## Step 5: Verify Deployment

1. **Check Your Live Site**
   - Visit your Vercel deployment URL
   - Test login functionality
   - Verify API calls are working

2. **Check Browser Console**
   - Open DevTools (F12)
   - Check for any CORS errors or API connection issues
   - Verify environment variables are loaded correctly

3. **Test Key Features**
   - User login
   - Dashboard loading
   - Transaction viewing
   - Recommendations display

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API base URL | `https://spendsense-api.railway.app` |
| `VITE_WS_BASE_URL` | WebSocket base URL (optional) | `wss://spendsense-api.railway.app` |

## Troubleshooting

### Build Fails

- **Error**: "Cannot find module"
  - **Solution**: Ensure all dependencies are in `ui/package.json`
  - Run `npm install` locally to verify

- **Error**: "Build command failed"
  - **Solution**: Check build logs in Vercel dashboard
  - Verify `npm run build` works locally

### API Calls Fail

- **Error**: CORS errors
  - **Solution**: Update backend CORS to include Vercel domain

- **Error**: 404 on API endpoints
  - **Solution**: Verify `VITE_API_URL` is set correctly
  - Check that backend is accessible at that URL

### Styling Issues

- **Issue**: Styles not loading
  - **Solution**: Tailwind CSS should compile automatically
  - Check that `tailwind.config.js` is in the `ui/` directory
  - Verify `index.css` imports Tailwind directives

### Routing Issues

- **Issue**: 404 on page refresh
  - **Solution**: The `vercel.json` rewrite rules should handle this
  - Verify `vercel.json` is in the root or `ui/` directory

## Custom Domain (Optional)

1. Go to your project settings in Vercel
2. Click "Domains"
3. Add your custom domain
4. Follow DNS configuration instructions
5. Update `VITE_API_URL` if needed

## Continuous Deployment

Vercel automatically deploys on every push to your main branch:
- **Production**: Deploys from `main` or `master` branch
- **Preview**: Deploys from pull requests and other branches

## Updating Environment Variables

1. Go to Project Settings → Environment Variables
2. Add or update variables
3. Redeploy the project (or wait for next deployment)

## Support

- [Vercel Documentation](https://vercel.com/docs)
- [Vite Deployment Guide](https://vitejs.dev/guide/static-deploy.html#vercel)

