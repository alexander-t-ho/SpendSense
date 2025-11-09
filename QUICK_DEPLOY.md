# Quick Vercel Deployment Guide

## 🚀 Fastest Way to Deploy

### Step 1: Deploy Backend First
Deploy your FastAPI backend to Railway, Render, or Fly.io and get your backend URL.

### Step 2: Deploy Frontend to Vercel

**Option A: Via Vercel Dashboard (Easiest)**
1. Go to [vercel.com](https://vercel.com) and sign in
2. Click "Add New Project"
3. Import your GitHub/GitLab repository
4. **Important**: Set Root Directory to `ui`
5. Add Environment Variable:
   - Name: `VITE_API_URL`
   - Value: `https://your-backend-url.com` (your actual backend URL)
6. Click "Deploy"

**Option B: Via CLI**
```bash
cd ui
npm install -g vercel
vercel login
vercel
# When prompted, set root directory to current directory (.)
# Add environment variable when prompted
vercel env add VITE_API_URL
# Enter your backend URL
vercel --prod
```

## ✅ What's Already Configured

- ✅ `vercel.json` in root directory
- ✅ `ui/vercel.json` for ui-specific config
- ✅ Build settings configured for Vite
- ✅ SPA routing configured (rewrites for React Router)
- ✅ CORS headers configured

## 🔧 Environment Variables Needed

| Variable | Value | Required |
|----------|-------|----------|
| `VITE_API_URL` | Your backend URL (e.g., `https://api.railway.app`) | ✅ Yes |
| `VITE_WS_BASE_URL` | WebSocket URL (e.g., `wss://api.railway.app`) | ⚠️ Optional |

## 📝 Backend CORS Setup

Update your backend's `CORS_ORIGINS` environment variable to include:
```
http://localhost:3000,https://your-project.vercel.app,https://your-project-*.vercel.app
```

Or update `api/main.py` line 24:
```python
allowed_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000,https://your-project.vercel.app").split(",")
```

## ✨ Your Styling Will Be Preserved

All Tailwind CSS, custom colors, animations, and responsive design will work exactly as they do locally because:
- Tailwind compiles to static CSS during build
- CSS variables are included in the bundle
- All assets are bundled with the app

## 🐛 Common Issues

**Build fails?**
- Check that root directory is set to `ui/`
- Verify `npm run build` works locally

**API calls fail?**
- Check `VITE_API_URL` is set correctly
- Verify backend CORS includes your Vercel domain
- Check browser console for errors

**404 on page refresh?**
- The `vercel.json` rewrite rules should handle this automatically

## 📚 Full Documentation

See `deploy/vercel_deploy.md` for detailed instructions.

