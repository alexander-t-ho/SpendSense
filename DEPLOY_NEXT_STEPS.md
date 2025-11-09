# Next Steps: Deploy Frontend to Vercel

## ✅ Completed
- Backend deployed successfully on Railway

## 📋 Next Steps

### Step 1: Get Your Railway Backend URL

You can find this in your Railway dashboard:
- Go to: https://railway.com/project/0448ee28-a801-4a80-a809-92bf400cbcbc
- Click on your service
- Check the "Settings" → "Networking" section
- Or check the "Deployments" tab for the URL
- Your URL will look like: `https://web-production-xxxx.up.railway.app`

### Step 2: Deploy Frontend to Vercel

**Option A: Via Vercel Dashboard (Easiest)**

1. Go to https://vercel.com and sign in
2. Click "Add New..." → "Project"
3. Import your `alexander-t-ho/SpendSense` repository
4. **IMPORTANT**: Set **Root Directory** to `ui`
5. Add environment variable:
   - Name: `VITE_API_URL`
   - Value: Your Railway backend URL (from Step 1)
6. Click "Deploy"
7. Copy your Vercel URL (e.g., `https://spendsense.vercel.app`)

**Option B: Via Vercel CLI**

```bash
cd /Users/alexho/SpendSense/ui
vercel login
vercel
# When prompted, set root directory to current directory
# Add environment variable VITE_API_URL with your Railway URL
vercel --prod
```

### Step 3: Update CORS in Railway

After you have your Vercel URL, update Railway CORS:

**Via Railway Dashboard:**
1. Go to Railway → Your Service → Settings → Variables
2. Update `CORS_ORIGINS` to:
   ```
   http://localhost:3000,https://your-vercel-app.vercel.app,https://your-vercel-app-*.vercel.app
   ```
3. Replace `your-vercel-app` with your actual Vercel project name

**Via CLI:**
```bash
railway login
railway link
railway variables --set "CORS_ORIGINS=http://localhost:3000,https://your-vercel-app.vercel.app,https://your-vercel-app-*.vercel.app"
```

### Step 4: Test

1. Visit your Vercel URL
2. Test login: `admin@spendsense.com` / `123456`
3. Verify everything works!

## 📖 Detailed Guide

See `VERCEL_DEPLOY_STEPS.md` for complete step-by-step instructions.

