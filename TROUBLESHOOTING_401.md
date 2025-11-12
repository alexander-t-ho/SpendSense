# Troubleshooting 401 Unauthorized Error

## ✅ Backend is Working!

The backend login endpoint works correctly:
- Admin user exists: `admin@spendsense.com`
- Password reset: `123456`
- Login via API works: ✅

## 🔍 Why You're Getting 401 from Vercel

The 401 error from Vercel production is likely because:

### Issue 1: VITE_API_URL Not Set (Most Likely)

**Symptom**: Frontend tries to call `/api/auth/login` (relative path) instead of `https://web-production-d242.up.railway.app/api/auth/login`

**Solution**:
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select project: **spend-sense-o3df**
3. **Settings** → **Environment Variables**
4. Add:
   - Name: `VITE_API_URL`
   - Value: `https://web-production-d242.up.railway.app`
   - Environment: Production
5. **Save**
6. **Redeploy**: Deployments → "..." → Redeploy

### Issue 2: Frontend Not Redeployed

Even if `VITE_API_URL` is set, you must redeploy for it to take effect.

**Solution**: Redeploy your Vercel app after setting the environment variable.

### Issue 3: Wrong Credentials

**Solution**: Use these exact credentials:
- Email: `admin@spendsense.com`
- Password: `123456`

## 🧪 How to Verify

### 1. Check if VITE_API_URL is Set

Open browser console on your Vercel site and run:
```javascript
console.log(import.meta.env.VITE_API_URL)
```

**Expected**: `https://web-production-d242.up.railway.app`  
**If undefined**: VITE_API_URL is not set or not redeployed

### 2. Check Network Requests

1. Open browser DevTools (F12)
2. Go to **Network** tab
3. Try to login
4. Check the login request URL

**Correct**: `https://web-production-d242.up.railway.app/api/auth/login`  
**Wrong**: `/api/auth/login` (relative path - means VITE_API_URL not set)

### 3. Test Backend Directly

```bash
curl -X POST https://web-production-d242.up.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@spendsense.com","password":"123456"}'
```

**Expected**: Returns access_token and user data ✅

## 📋 Quick Fix Checklist

- [ ] `VITE_API_URL` set in Vercel = `https://web-production-d242.up.railway.app`
- [ ] Vercel app **redeployed** after setting env var
- [ ] Using correct credentials: `admin@spendsense.com` / `123456`
- [ ] Check browser console for actual error message
- [ ] Check Network tab to see where API calls are going

## 🎯 Most Common Fix

**90% of the time**, the issue is:
1. `VITE_API_URL` not set in Vercel
2. Or Vercel not redeployed after setting it

**Fix**: Set `VITE_API_URL` in Vercel dashboard and redeploy!

