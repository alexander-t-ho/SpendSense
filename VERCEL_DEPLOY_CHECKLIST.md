# Vercel Deployment Checklist - Steps 1-3

## ✅ Step 1: Get Railway Backend URL (COMPLETED)
- Railway project: https://railway.com/project/0448ee28-a801-4a80-a809-92bf400cbcbc
- Get your Railway backend URL from the Railway dashboard

## 🔄 Step 2: Deploy Frontend to Vercel (IN PROGRESS)

### Go to Vercel Dashboard:
1. **Visit**: https://vercel.com
2. **Sign in** (use GitHub if possible for easier integration)

### Add New Project:
1. Click **"Add New..."** → **"Project"**
   - Or go directly to: https://vercel.com/new

2. **Import Git Repository**:
   - Select **"Import Git Repository"**
   - Choose your `alexander-t-ho/SpendSense` repository
   - Click **"Import"**

### ⚠️ CRITICAL: Configure Project Settings

3. **Root Directory** (MOST IMPORTANT):
   - Click **"Edit"** next to "Root Directory"
   - Change from `/` to `ui`
   - This tells Vercel to build from the `ui/` folder

4. **Framework Preset**:
   - Should auto-detect as **"Vite"**
   - If not, select **"Vite"** manually

5. **Build Settings** (should auto-detect, but verify):
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`

### Add Environment Variables:

6. **Before deploying, add environment variable**:
   - Click **"Environment Variables"** section
   - Click **"Add"** or **"Add New"**
   - Add:
     - **Name**: `VITE_API_URL`
     - **Value**: Your Railway backend URL (from Step 1)
       - Example: `https://web-production-xxxx.up.railway.app`
     - **Environment**: Select all three:
       - ☑️ Production
       - ☑️ Preview  
       - ☑️ Development
   - Click **"Save"**

### Deploy:

7. **Click "Deploy"**
   - Wait for build to complete (usually 1-2 minutes)
   - Watch the build logs for any errors

8. **Get Your Vercel URL**:
   - After successful deployment, you'll see your URL
   - Example: `https://spendsense.vercel.app` or `https://spendsense-xxxx.vercel.app`
   - **Copy this URL** - you'll need it for Step 3

## ⏸️ Step 3: Update Backend CORS Configuration (STOP HERE)

**After you have your Vercel URL from Step 2, we'll update Railway CORS settings.**

### What to do:
1. Go to Railway dashboard: https://railway.com/project/0448ee28-a801-4a80-a809-92bf400cbcbc
2. Click on your service
3. Go to **"Settings"** → **"Variables"**
4. Find `CORS_ORIGINS` variable
5. Click **"Edit"**
6. Update value to include your Vercel URL:
   ```
   http://localhost:3000,https://your-vercel-app.vercel.app,https://your-vercel-app-*.vercel.app
   ```
   Replace `your-vercel-app` with your actual Vercel project name/URL
7. **Save** - Railway will automatically redeploy

---

## ✅ Verification Checklist for Vercel Dashboard:

Before proceeding to Step 3, verify in Vercel:

- [ ] Project is imported from GitHub
- [ ] **Root Directory is set to `ui`** (CRITICAL!)
- [ ] Framework is detected as "Vite"
- [ ] Build Command: `npm run build`
- [ ] Output Directory: `dist`
- [ ] Environment variable `VITE_API_URL` is set with Railway URL
- [ ] Build completed successfully (check build logs)
- [ ] You have your Vercel deployment URL

## 🐛 If Build Fails:

1. Check build logs in Vercel dashboard
2. Verify root directory is set to `ui`
3. Ensure `package.json` exists in `ui/` directory
4. Check that `ui/src/lib/utils.ts` is in the repository (should be now!)

## 📝 Notes:

- The `lib/utils.ts` file is now committed to git
- All TypeScript errors should be resolved
- The build should succeed on Vercel

