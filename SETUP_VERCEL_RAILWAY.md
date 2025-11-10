# Vercel + Railway Setup Instructions

## Current Configuration

✅ **Vercel Frontend URL**: `https://spend-sense-e93qywztx-alexander-hos-projects.vercel.app`  
✅ **Railway Backend URL**: `https://web-production-d242.up.railway.app`  
✅ **VITE_API_URL**: Already set in Vercel environment variables

## Step 2: Update Railway CORS

Your Railway backend needs to allow requests from your Vercel frontend. 

### Option A: Using Railway Dashboard (Recommended)

1. Go to https://railway.app
2. Open your project
3. Click on your backend service
4. Go to **Variables** tab
5. Find or add `CORS_ORIGINS`
6. Set the value to:
   ```
   http://localhost:3004,https://spend-sense-e93qywztx-alexander-hos-projects.vercel.app
   ```
7. Save and restart your service

### Option B: Using Railway CLI

First, link your project:
```bash
railway link
```

Then set the CORS variable:
```bash
railway variables set CORS_ORIGINS="http://localhost:3004,https://spend-sense-e93qywztx-alexander-hos-projects.vercel.app"
```

Or use the provided script:
```bash
./update_railway_cors.sh
```

## Step 3: Verify Backend is Running

Test your Railway backend:
```bash
curl https://web-production-d242.up.railway.app/
```

Expected response: `{"message":"SpendSense API","version":"1.0.0"}`

If you get a 502 error, your Railway service may be down. Check:
1. Railway dashboard → Your service → Deployments
2. Check logs for errors
3. Restart the service if needed

## Step 4: Test the Connection

1. Visit your Vercel URL: https://spend-sense-e93qywztx-alexander-hos-projects.vercel.app
2. Try logging in
3. Check browser console (F12) for any CORS errors

## Troubleshooting

### If login still times out:

1. **Check Vercel Environment Variable**:
   ```bash
   vercel env ls
   ```
   Make sure `VITE_API_URL` is set to: `https://web-production-d242.up.railway.app`

2. **Check Railway CORS**:
   - Make sure `CORS_ORIGINS` includes your Vercel URL
   - Restart Railway service after updating

3. **Check Railway Service Status**:
   - Go to Railway dashboard
   - Check if service is running
   - Check deployment logs

4. **Test API directly**:
   ```bash
   curl -X POST https://web-production-d242.up.railway.app/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"test@example.com","password":"test123"}'
   ```

## Next Steps

After completing Step 2 (updating Railway CORS), your login should work!

