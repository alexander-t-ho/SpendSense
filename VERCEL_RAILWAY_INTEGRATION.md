# Vercel + Railway Integration Guide

## ✅ Current Status

- **Railway Backend**: `https://web-production-d242.up.railway.app` ✅ Running
- **Vercel Frontend**: `https://spend-sense-o3df.vercel.app` ✅ Deployed
- **Database**: Uploaded and working (150 users)

## 🔧 Required Configuration

### Step 1: Set VITE_API_URL in Vercel

**This is CRITICAL** - The frontend needs to know where the backend is.

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project: **spend-sense-o3df**
3. Go to **Settings** → **Environment Variables**
4. Add/Update:
   - **Name**: `VITE_API_URL`
   - **Value**: `https://web-production-d242.up.railway.app`
   - **Environment**: 
     - ✅ Production
     - ✅ Preview (optional, for preview deployments)
     - ✅ Development (optional)
5. **Save**
6. **Redeploy** your Vercel app (go to Deployments → click "..." → Redeploy)

### Step 2: Verify Railway CORS

Railway CORS should already be set, but verify:

1. Go to [Railway Dashboard](https://railway.app)
2. Select project: **Leafly**
3. Select your backend service
4. Go to **Variables** tab
5. Check `CORS_ORIGINS` includes:
   ```
   http://localhost:3004,https://spend-sense-o3df.vercel.app
   ```
6. If not set, add it and restart the service

### Step 3: Test the Integration

1. **Test Backend**:
   ```bash
   curl https://web-production-d242.up.railway.app/
   # Should return: {"message":"SpendSense API","version":"1.0.0"}
   ```

2. **Test Frontend**:
   - Visit: `https://spend-sense-o3df.vercel.app`
   - Open browser console (F12)
   - Try logging in
   - Check for any CORS errors

3. **Test API Connection from Frontend**:
   - After logging in, check Network tab in browser console
   - API calls should go to: `https://web-production-d242.up.railway.app/api/...`
   - Should NOT see CORS errors

## 🐛 Troubleshooting

### Frontend can't connect to backend

**Symptoms**: Login fails, API calls timeout, CORS errors

**Solutions**:
1. ✅ Verify `VITE_API_URL` is set in Vercel (Step 1 above)
2. ✅ Verify CORS_ORIGINS includes your Vercel URL (Step 2 above)
3. ✅ Redeploy Vercel after setting environment variable
4. ✅ Check browser console for specific error messages

### CORS Errors

**Error**: `Access to fetch at '...' from origin '...' has been blocked by CORS policy`

**Solution**:
1. Check Railway `CORS_ORIGINS` includes your Vercel URL
2. Restart Railway service after updating CORS
3. Clear browser cache and try again

### Database Errors

**Error**: "Database temporarily unavailable"

**Solution**:
- Database needs to be re-uploaded after Railway redeploys
- Or set up Railway Volume for persistence (see below)

## 📋 Production Checklist

- [ ] `VITE_API_URL` set in Vercel to Railway backend URL
- [ ] Vercel app redeployed after setting environment variable
- [ ] Railway `CORS_ORIGINS` includes Vercel URL
- [ ] Railway backend is running and accessible
- [ ] Database uploaded to Railway
- [ ] Test login works from production frontend
- [ ] Test API calls work from production frontend

## 🚀 Optional: Railway Volume for Database Persistence

To prevent database loss on Railway redeploys:

1. Railway Dashboard → Your service → **Volumes** tab
2. Create volume:
   - Name: `data`
   - Mount Path: `/app/data`
   - Size: 1GB
3. Set environment variable:
   - Key: `DATABASE_PATH`
   - Value: `/app/data/spendsense.db`
4. Upload database to volume (it will persist)

## 🔗 Important URLs

- **Frontend (Vercel)**: `https://spend-sense-o3df.vercel.app`
- **Backend (Railway)**: `https://web-production-d242.up.railway.app`
- **Railway Dashboard**: https://railway.app/project/40f90415-e736-4c6a-b4e5-0769a021f9c8
- **Vercel Dashboard**: https://vercel.com/dashboard

## 📝 Environment Variables Summary

### Vercel (Frontend)
- `VITE_API_URL` = `https://web-production-d242.up.railway.app`

### Railway (Backend)
- `CORS_ORIGINS` = `http://localhost:3004,https://spend-sense-o3df.vercel.app`
- `OPENAI_API_KEY` = (your key)
- `OPENROUTER_API_KEY` = (your key)
- `DATABASE_PATH` = `data/spendsense.db` (or `/app/data/spendsense.db` if using volume)

