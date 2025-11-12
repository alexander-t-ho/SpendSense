# Production Fix Complete ✅

## Problem
The frontend was using hardcoded `/api/...` paths that only work with Vite's local proxy. In production on Vercel, these paths don't work because there's no backend proxy - the frontend needs to call the Railway backend directly.

## Solution
All API calls now use `API_BASE_URL` from `services/api.ts`, which:
- Uses `VITE_API_URL` environment variable in production (points to Railway backend)
- Falls back to `/api` for local development (uses Vite proxy)

## Files Fixed

### 1. `ui/src/services/api.ts`
- ✅ Exported `API_BASE_URL` constant

### 2. `ui/src/components/ActionableRecommendation.tsx`
- ✅ Added import for `API_BASE_URL`
- ✅ Fixed 11 hardcoded `/api/...` paths:
  - `/api/user/${userId}/subscriptions/cancelled`
  - `/api/user/${userId}/subscriptions`
  - `/api/user/${userId}/subscriptions/cancel`
  - `/api/user/${userId}/subscriptions/uncancel`
  - `/api/user/${userId}/recommendations/${recommendationId}/feedback` (3 instances)
  - `/api/user/${userId}/action-plans/${recommendationId}`
  - `/api/user/${userId}/action-plans/approve` (2 instances)
  - `/api/user/${userId}/action-plans/${recommendationId}/cancel`

### 3. `ui/src/components/ui/admin-landing-page.tsx`
- ✅ Added import for `API_BASE_URL`
- ✅ Removed local `API_BASE_URL` definition
- ✅ Fixed 3 hardcoded paths:
  - `/api/operator/recommendations/${recommendationId}/approve`
  - `/api/operator/recommendations/${recommendationId}/reject`
  - `/api/operator/recommendations/${recommendationId}/flag`

### 4. `ui/src/pages/UserDetail.tsx`
- ✅ Added import for `API_BASE_URL`
- ✅ Removed local `API_BASE_URL` definition
- ✅ Fixed 3 hardcoded paths:
  - `/api/operator/recommendations/${recommendationId}/approve`
  - `/api/operator/recommendations/${recommendationId}/reject`
  - `/api/operator/recommendations/${recommendationId}/flag`

### 5. `ui/src/components/admin/RecommendationsDropdown.tsx`
- ✅ Added import for `API_BASE_URL`
- ✅ Fixed: `/api/operator/recommendations?status=all&user_id=${userId}&limit=100`

### 6. `ui/src/components/UserBudgetDisplay.tsx`
- ✅ Added import for `API_BASE_URL`
- ✅ Fixed: `/api/insights/${userId}/budget`

### 7. `ui/src/components/SuggestedBudgetCard.tsx`
- ✅ Added import for `API_BASE_URL`
- ✅ Fixed: `/api/insights/${userId}/budget`

### 8. `ui/src/components/AuthContext.tsx`
- ✅ Added import for `API_BASE_URL`
- ✅ Fixed login endpoint: `/api/auth/login`
- ✅ Fixed user info endpoint: `/api/auth/me`

## Next Steps

### ⚠️ CRITICAL: Set VITE_API_URL in Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select project: **spend-sense-o3df** (or your project name)
3. Go to **Settings** → **Environment Variables**
4. Add new variable:
   - **Name**: `VITE_API_URL`
   - **Value**: `https://web-production-d242.up.railway.app`
   - **Environment**: Production (and Preview if you want)
5. Click **Save**
6. **Redeploy** your Vercel app (or wait for next deployment)

### Verify After Deployment

1. **Login Test**:
   - Go to production URL
   - Try logging in with `admin@spendsense.com` / `123456`
   - Should work without 401 errors

2. **Recommendations Test**:
   - After logging in, go to a user detail page
   - Click "Generate Recommendations"
   - Should work without 405 errors

3. **Other Features**:
   - Budget saving
   - Subscription cancellation
   - Action plans
   - All should work correctly

## How It Works

### Local Development
- `VITE_API_URL` is not set
- `API_BASE_URL` = `/api`
- Vite proxy forwards `/api/*` to `http://127.0.0.1:8001/api/*`
- ✅ Works with local backend

### Production (Vercel)
- `VITE_API_URL` = `https://web-production-d242.up.railway.app`
- `API_BASE_URL` = `https://web-production-d242.up.railway.app/api`
- All API calls go directly to Railway backend
- ✅ Works with production backend

## Summary

✅ All hardcoded `/api/...` paths replaced with `${API_BASE_URL}/...`
✅ Centralized API base URL configuration
✅ Works in both local and production environments
⚠️ **Must set `VITE_API_URL` in Vercel before deploying**

