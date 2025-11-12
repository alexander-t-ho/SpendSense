# Production Fix Guide - Context Menu Errors & 401 Login

## Issues Fixed

### 1. Context Menu Errors (Browser Extensions)
**Problem**: Console showing "Unchecked runtime.lastError: Cannot create item with duplicate id" errors from browser extensions like LastPass.

**Solution**: Enhanced error suppression in `ui/src/main.tsx` to catch all browser extension context menu errors. These errors are harmless and come from browser extensions, not your application.

**Status**: ✅ Fixed - Errors will now be suppressed in the console.

### 2. 401 Login Error
**Problem**: Login endpoint returning 401 Unauthorized in production.

**Root Causes**:
1. `VITE_API_URL` not set in Vercel environment variables
2. `CORS_ORIGINS` not configured correctly in Railway
3. Admin user doesn't exist in production database

## Quick Fix Steps

### Step 1: Set Vercel Environment Variable

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project: **spend-sense-o3df**
3. Go to **Settings** → **Environment Variables**
4. Add/Update:
   - **Name**: `VITE_API_URL`
   - **Value**: `https://web-production-d242.up.railway.app`
   - **Environment**: Production (and Preview if needed)
5. **Save**
6. **Redeploy**: Go to Deployments → Click "..." on latest deployment → Redeploy

### Step 2: Configure Railway CORS

1. Go to [Railway Dashboard](https://railway.app)
2. Open your backend service
3. Go to **Variables** tab
4. Add/Update:
   - **Name**: `CORS_ORIGINS`
   - **Value**: `http://localhost:3004,https://spend-sense-o3df.vercel.app`
5. **Save**
6. **Restart** your Railway service (click Restart button)

### Step 3: Create Admin User

Run this command to create/reset the admin user:

```bash
curl -X POST https://web-production-d242.up.railway.app/api/admin/create-admin
```

Expected response:
```json
{
  "message": "Admin user created",
  "email": "admin@spendsense.com",
  "password": "123456"
}
```

### Step 4: Verify Setup

Run the verification script:

```bash
./scripts/verify_production_setup.sh
```

Or test manually:

```bash
# Test backend
curl https://web-production-d242.up.railway.app/

# Test login
curl -X POST https://web-production-d242.up.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@spendsense.com","password":"123456"}'
```

## Login Credentials

- **Email**: `admin@spendsense.com`
- **Password**: `123456`

## Verification Checklist

- [ ] `VITE_API_URL` is set in Vercel (Production environment)
- [ ] Vercel app has been redeployed after setting `VITE_API_URL`
- [ ] `CORS_ORIGINS` is set in Railway with your Vercel URL
- [ ] Railway service has been restarted after updating CORS
- [ ] Admin user exists (run `/api/admin/create-admin`)
- [ ] Backend is accessible: `curl https://web-production-d242.up.railway.app/`
- [ ] Login endpoint works: Test with curl command above

## Troubleshooting

### Still Getting 401 Error?

1. **Check Browser Console**:
   - Open DevTools (F12) → Console
   - Look for the login request URL
   - Should be: `https://web-production-d242.up.railway.app/api/auth/login`
   - If it's `/api/auth/login` (relative), `VITE_API_URL` is not set

2. **Check Network Tab**:
   - Open DevTools (F12) → Network
   - Try to login
   - Check the login request:
     - **Status**: Should be 200 (not 401)
     - **Request URL**: Should point to Railway backend
     - **CORS errors**: If you see CORS errors, check Railway `CORS_ORIGINS`

3. **Verify Environment Variable**:
   - In browser console on your Vercel site, run:
   ```javascript
   console.log(import.meta.env.VITE_API_URL)
   ```
   - Should output: `https://web-production-d242.up.railway.app`
   - If `undefined`, variable is not set or app not redeployed

### Still Seeing Context Menu Errors?

These errors are from browser extensions (LastPass, password managers, etc.) and are now suppressed. If you still see them:

1. They're harmless - they don't affect your application
2. The suppression code is in `ui/src/main.tsx`
3. After redeploying, they should be hidden

### CORS Errors?

If you see CORS errors in the browser console:

1. Check Railway `CORS_ORIGINS` includes your Vercel URL
2. Make sure there are no trailing slashes
3. Restart Railway service after updating
4. Format: `http://localhost:3004,https://spend-sense-o3df.vercel.app`

## Code Changes Made

1. **`ui/src/main.tsx`**: Enhanced error suppression for browser extension errors
2. **`ui/src/components/AuthContext.tsx`**: Improved error handling with better diagnostics for 401 errors
3. **`api/main.py`**: Improved CORS configuration to handle multiple origins better

## Testing After Fix

1. Visit your Vercel URL: `https://spend-sense-o3df.vercel.app`
2. Try to login with: `admin@spendsense.com` / `123456`
3. Check browser console - should see no context menu errors
4. Login should succeed without 401 error

## Need Help?

If issues persist:
1. Run `./scripts/verify_production_setup.sh` for diagnostics
2. Check Railway logs for backend errors
3. Check Vercel deployment logs for build errors
4. Verify all environment variables are set correctly


