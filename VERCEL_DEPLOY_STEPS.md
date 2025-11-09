# Vercel Frontend Deployment - Step by Step

## Prerequisites
- ✅ Backend deployed on Railway (DONE)
- Railway backend URL (get from Railway dashboard)

## Step 1: Get Your Railway Backend URL

From your Railway dashboard:
1. Go to your project: https://railway.com/project/0448ee28-a801-4a80-a809-92bf400cbcbc
2. Click on your service
3. Go to the "Settings" tab
4. Scroll to "Networking" section
5. Copy your Railway domain (e.g., `https://web-production-xxxx.up.railway.app`)

**OR** check the "Deployments" tab - the URL is shown there.

## Step 2: Deploy Frontend to Vercel

### Option A: Via Vercel Dashboard (Recommended)

1. **Go to Vercel**: https://vercel.com → Sign in (use GitHub if possible)

2. **Add New Project**:
   - Click "Add New..." → "Project"
   - Or go to: https://vercel.com/new

3. **Import Git Repository**:
   - Select "Import Git Repository"
   - Choose your `alexander-t-ho/SpendSense` repository
   - Click "Import"

4. **Configure Project Settings**:
   
   **⚠️ CRITICAL: Root Directory**
   - Click "Edit" next to "Root Directory"
   - Change from `/` to `ui`
   - This tells Vercel to build from the `ui/` folder
   
   **Framework Preset**: 
   - Should auto-detect as "Vite"
   - If not, select "Vite" manually
   
   **Build Settings** (should auto-detect):
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Install Command: `npm install`

5. **Add Environment Variables**:
   - Click "Environment Variables"
   - Add new variable:
     - **Name**: `VITE_API_URL`
     - **Value**: Your Railway backend URL (from Step 1)
       - Example: `https://web-production-xxxx.up.railway.app`
     - **Environment**: Production, Preview, Development (select all)
   - Click "Save"

6. **Deploy**:
   - Click "Deploy"
   - Wait for build to complete (usually 1-2 minutes)

7. **Get Your Vercel URL**:
   - After deployment, you'll see your URL
   - Example: `https://spendsense.vercel.app` or `https://spendsense-xxxx.vercel.app`

### Option B: Via Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Navigate to UI directory
cd /Users/alexho/SpendSense/ui

# Login to Vercel
vercel login

# Deploy (will prompt for configuration)
vercel

# When prompted:
# - Set up and deploy? Yes
# - Which scope? (select your account)
# - Link to existing project? No (or Yes if you created one)
# - Project name: spendsense (or your choice)
# - Directory: . (current directory)
# - Override settings? No

# Add environment variable
vercel env add VITE_API_URL production
# Enter your Railway backend URL when prompted

# Deploy to production
vercel --prod
```

## Step 3: Update Backend CORS Configuration

After you have your Vercel URL, update Railway CORS settings:

### Via Railway Dashboard:
1. Go to Railway dashboard
2. Click on your service
3. Go to "Settings" → "Variables"
4. Find `CORS_ORIGINS` variable
5. Click "Edit"
6. Update value to:
   ```
   http://localhost:3000,https://your-vercel-app.vercel.app,https://your-vercel-app-*.vercel.app
   ```
   Replace `your-vercel-app` with your actual Vercel project name
7. Save - Railway will automatically redeploy

### Via Railway CLI:
```bash
railway login
railway link
railway variables --set "CORS_ORIGINS=http://localhost:3000,https://your-vercel-app.vercel.app,https://your-vercel-app-*.vercel.app"
```

## Step 4: Test Production Deployment

1. Visit your Vercel URL
2. Test login:
   - Email: `admin@spendsense.com`
   - Password: `123456`
3. Check browser console (F12) for errors
4. Verify:
   - ✅ Login works
   - ✅ Dashboard loads
   - ✅ API calls succeed
   - ✅ No CORS errors
   - ✅ Transactions display
   - ✅ Recommendations work

## Troubleshooting

### Build Fails on Vercel
- Check build logs in Vercel dashboard
- Verify root directory is set to `ui`
- Ensure `package.json` exists in `ui/` directory

### API Calls Fail
- Verify `VITE_API_URL` is set correctly in Vercel
- Check Railway backend is running
- Verify CORS_ORIGINS includes your Vercel URL

### CORS Errors
- Make sure CORS_ORIGINS includes your Vercel URL
- Check for typos in the URL
- Ensure no trailing slashes
- Wait for Railway to redeploy after CORS update

### 404 on Page Refresh
- `vercel.json` should handle this automatically
- Verify rewrite rules are in place

## Quick Checklist

- [ ] Get Railway backend URL
- [ ] Deploy frontend to Vercel
- [ ] Set `VITE_API_URL` environment variable
- [ ] Get Vercel URL
- [ ] Update `CORS_ORIGINS` in Railway
- [ ] Test login and functionality
- [ ] Verify no errors in browser console

