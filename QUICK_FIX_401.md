# Quick Fix for 401 Error in Production

## The Problem

You're getting a 401 "Unauthorized" error when logging in from Vercel production.

## Root Cause

The 401 error means the backend is receiving the request but rejecting the credentials. This can happen if:

1. **Database was reset** (Railway containers are ephemeral)
2. **Password hash doesn't match** (password needs to be reset)
3. **VITE_API_URL not set** (frontend not connecting to backend)

## ✅ Quick Fix Steps

### Step 1: Reset Admin Password

Run this command to reset the admin password:

```bash
curl -X POST https://web-production-d242.up.railway.app/api/admin/create-admin
```

This will create/update the admin user with password `123456`.

### Step 2: Verify VITE_API_URL is Set

**Critical**: The frontend must know where the backend is!

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select project: **spend-sense-o3df**
3. **Settings** → **Environment Variables**
4. Check if `VITE_API_URL` exists
5. If not, add it:
   - Name: `VITE_API_URL`
   - Value: `https://web-production-d242.up.railway.app`
   - Environment: Production
6. **Save and Redeploy**

### Step 3: Test Login

**Credentials**:
- Email: `admin@spendsense.com`
- Password: `123456`

**Test via API** (to verify backend):
```bash
curl -X POST https://web-production-d242.up.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@spendsense.com","password":"123456"}'
```

**Test via Frontend**:
1. Visit: `https://spend-sense-o3df.vercel.app/login`
2. Enter credentials
3. Check browser console (F12) → Network tab
4. Verify request goes to: `https://web-production-d242.up.railway.app/api/auth/login`

## 🔍 Debugging

### Check if VITE_API_URL is Set

Open browser console on your Vercel site:
```javascript
console.log(import.meta.env.VITE_API_URL)
```

**If undefined**: VITE_API_URL is not set or app not redeployed

### Check Network Request

1. Open DevTools (F12)
2. Network tab
3. Try to login
4. Look at the login request:
   - **Correct**: `https://web-production-d242.up.railway.app/api/auth/login`
   - **Wrong**: `/api/auth/login` (means VITE_API_URL not set)

### Check Error Response

In Network tab, click on the failed login request:
- Look at **Response** tab
- Should show: `{"detail":"Incorrect username or password"}`

## 🎯 Most Likely Issue

**90% chance**: `VITE_API_URL` is not set in Vercel, so the frontend is trying to call `/api/auth/login` (relative path) which doesn't exist in production.

**Fix**: Set `VITE_API_URL` in Vercel dashboard and redeploy!

## 📝 Complete Checklist

- [ ] Reset admin password: `curl -X POST https://web-production-d242.up.railway.app/api/admin/create-admin`
- [ ] Verify `VITE_API_URL` is set in Vercel
- [ ] Redeploy Vercel app after setting env var
- [ ] Test login with: `admin@spendsense.com` / `123456`
- [ ] Check browser console for actual error
- [ ] Verify Network tab shows correct API URL

