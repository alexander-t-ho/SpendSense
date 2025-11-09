# 🚀 Production Deployment - Quick Start

Follow these steps to deploy SpendSense to production.

## Prerequisites Checklist

- [ ] Code is committed and pushed to GitHub
- [ ] Railway account created ([railway.app](https://railway.app))
- [ ] Vercel account created ([vercel.com](https://vercel.com))

## Step 1: Commit Your Changes

```bash
git add -A
git commit -m "Prepare for production deployment"
git push origin main
```

## Step 2: Deploy Backend to Railway

### Option A: Via Railway Dashboard (Easiest)

1. **Go to Railway**: [railway.app](https://railway.app) → Sign in
2. **New Project** → **Deploy from GitHub repo**
3. **Select your repository**: Choose SpendSense
4. **Configure Service**:
   - **Root Directory**: 
     - Go to your service → **Settings** tab
     - Find **"Root Directory"** section
     - Leave it **empty** or set to `/` (forward slash)
     - This tells Railway to use the repository root
   - **Start Command**:
     - In the same Settings page, find **"Start Command"** section
     - Enter: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
     - Click Save (or it auto-saves)
   - **Note**: Your `railway.json` file already has the start command configured, so Railway may use that automatically
5. **Add Environment Variables** (Settings → Variables):
   - `CORS_ORIGINS`: `http://localhost:3000` (we'll update after Vercel deploy)
6. **Deploy**: Railway will auto-detect Python and deploy
7. **Get URL**: Copy your Railway URL (e.g., `https://spendsense-production.up.railway.app`)

**📖 Detailed Configuration Guide**: See `RAILWAY_CONFIGURATION.md` for step-by-step instructions with troubleshooting tips.

### Option B: Via Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Link to existing project (or create new)
railway link

# Deploy
railway up
```

## Step 3: Deploy Frontend to Vercel

### Via Vercel Dashboard

1. **Go to Vercel**: [vercel.com](https://vercel.com) → Sign in
2. **Add New Project** → **Import Git Repository**
3. **Select Repository**: Choose SpendSense
4. **Configure Project**:
   - **Root Directory**: `ui` ⚠️ **IMPORTANT**
   - Framework Preset: Vite (auto-detected)
   - Build Command: `npm run build` (auto-detected)
   - Output Directory: `dist` (auto-detected)
5. **Environment Variables**:
   - `VITE_API_URL`: `https://your-railway-backend.up.railway.app` (from Step 2)
6. **Deploy**: Click "Deploy"
7. **Get URL**: Copy your Vercel URL (e.g., `https://spendsense.vercel.app`)

### Via Vercel CLI

```bash
cd ui
npm install -g vercel
vercel login
vercel
# When prompted:
# - Set root directory to current directory (.)
# - Add environment variable VITE_API_URL
vercel env add VITE_API_URL
# Enter your Railway backend URL
vercel --prod
```

## Step 4: Update Backend CORS

1. **Go back to Railway Dashboard**
2. **Service Settings** → **Variables**
3. **Update `CORS_ORIGINS`**:
   ```
   http://localhost:3000,https://your-vercel-app.vercel.app,https://your-vercel-app-*.vercel.app
   ```
   Replace `your-vercel-app` with your actual Vercel project name
4. **Redeploy**: Railway will automatically redeploy

## Step 5: Test Production

1. Visit your Vercel URL
2. Test login: `admin@spendsense.com` / `123456`
3. Check browser console (F12) for errors
4. Verify:
   - ✅ Login works
   - ✅ Dashboard loads
   - ✅ Transactions display
   - ✅ API calls succeed
   - ✅ No CORS errors

## Troubleshooting

### Backend Issues

**Build fails on Railway:**
- Check Railway logs
- Verify `requirements.txt` is correct
- Ensure Python 3.9+ is specified

**Database not found:**
- Railway uses ephemeral storage by default
- Consider using Railway PostgreSQL (add as service)
- Or use volume for SQLite persistence

**CORS errors:**
- Verify `CORS_ORIGINS` includes your Vercel URL
- Check for typos in the URL
- Ensure no trailing slashes

### Frontend Issues

**Build fails on Vercel:**
- Check build logs in Vercel dashboard
- Verify root directory is set to `ui`
- Ensure `package.json` is in `ui/` directory

**API calls fail:**
- Verify `VITE_API_URL` is set correctly
- Check browser console for errors
- Ensure backend is running and accessible

**404 on page refresh:**
- `vercel.json` should handle this automatically
- Verify rewrite rules are in place

## Environment Variables Reference

### Backend (Railway)

| Variable | Value | Required |
|----------|-------|----------|
| `CORS_ORIGINS` | `http://localhost:3000,https://your-app.vercel.app` | ✅ Yes |
| `PORT` | Auto-set by Railway | ✅ Yes |
| `JWT_SECRET_KEY` | Generate secure key | ⚠️ Recommended |

### Frontend (Vercel)

| Variable | Value | Required |
|----------|-------|----------|
| `VITE_API_URL` | `https://your-backend.railway.app` | ✅ Yes |
| `VITE_WS_BASE_URL` | `wss://your-backend.railway.app` | ⚠️ Optional |

## Database Setup (Optional)

### Use Railway PostgreSQL

1. In Railway dashboard: **New** → **Database** → **Add PostgreSQL**
2. Get connection string from Railway
3. Update your code to use PostgreSQL instead of SQLite
4. Run migrations:
   ```bash
   railway run python3 scripts/migrate_auth_columns.py
   railway run python3 scripts/setup_passwords.py
   ```

### Keep SQLite

- Railway provides ephemeral storage
- Data will be lost on redeploy
- Use Railway volumes for persistence (paid feature)

## Custom Domain (Optional)

### Vercel Custom Domain

1. Vercel Dashboard → Project → Settings → Domains
2. Add your domain
3. Follow DNS configuration instructions

### Railway Custom Domain

1. Railway Dashboard → Service → Settings → Networking
2. Add custom domain
3. Configure DNS records

## Monitoring

- **Railway**: Built-in logs and metrics
- **Vercel**: Built-in analytics and logs
- Consider adding:
  - Sentry for error tracking
  - LogRocket for session replay
  - Analytics for user tracking

## Next Steps

- [ ] Set up custom domain
- [ ] Configure database backups
- [ ] Set up monitoring and alerts
- [ ] Configure CI/CD for auto-deployments
- [ ] Set up staging environment

## Support

- Railway Docs: [docs.railway.app](https://docs.railway.app)
- Vercel Docs: [vercel.com/docs](https://vercel.com/docs)
- Deployment Issues: Check logs in respective dashboards

