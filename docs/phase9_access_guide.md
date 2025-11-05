# Phase 9 Features Access Guide

## Where to Find Phase 9 Features (Origin-like Insights)

Phase 9 features are **NOT** on the main Dashboard page. They are available on:

### 1. **User Detail Page** (Admin View)
- **URL**: `http://localhost:3000/user/{userId}`
- **How to access**: 
  1. Go to main Dashboard (`http://localhost:3000/`)
  2. Click "View Details" on any user
- **Features shown**:
  - ✅ Weekly Recap Card
  - ✅ Spending Analysis Card
  - ✅ Suggested Budget Card
  - ✅ Budget Tracking Card
  - ✅ Net Worth Recap Card
  - ✅ Recommendations (read-only)

### 2. **User Dashboard** (End-User View)
- **URL**: `http://localhost:3000/my-dashboard/{userId}`
- **How to access**: 
  - Direct URL with a user ID
  - Example: `http://localhost:3000/my-dashboard/eb1b2791-4a2a-4c87-bb07-cb6ba9f370a2`
- **Features shown**:
  - ✅ Weekly Recap Card
  - ✅ Spending Analysis Card
  - ✅ Suggested Budget Card
  - ✅ Budget Tracking Card
  - ✅ Net Worth Recap Card
  - ✅ Recommendations (interactive, can grant/revoke consent)

### 3. **Main Dashboard** (Admin Overview)
- **URL**: `http://localhost:3000/`
- **Features shown**:
  - ❌ NO Phase 9 features (this is just the user list)
  - Shows: Stats, User table with personas

## Quick Test Steps

1. **Start both servers**:
   ```bash
   # Terminal 1
   ./start_backend.sh
   
   # Terminal 2
   ./start_frontend.sh
   ```

2. **Get a user ID**:
   - Go to `http://localhost:3000/`
   - Click "View Details" on any user
   - The URL will be: `http://localhost:3000/user/{userId}`
   - Copy the `userId` from the URL

3. **View Phase 9 features**:
   - **Option A**: User Detail page (already open after step 2)
     - Scroll down past accounts, transactions, and features
     - You'll see "Financial Insights" section with all Phase 9 components
   
   - **Option B**: User Dashboard
     - Go to: `http://localhost:3000/my-dashboard/{userId}`
     - Replace `{userId}` with the ID from step 2
     - Scroll down to see all Phase 9 features

## Troubleshooting

### Components Not Showing

1. **Check if userId is valid**:
   - Open browser console (F12)
   - Look for errors like "Failed to fetch weekly recap"
   - Check Network tab for failed API calls

2. **Verify backend is running**:
   - Check: `http://localhost:8000/docs`
   - Should show API documentation

3. **Check API endpoints**:
   ```bash
   # Test weekly recap endpoint
   curl http://localhost:8000/api/insights/{userId}/weekly-recap
   
   # Test spending analysis
   curl http://localhost:8000/api/insights/{userId}/spending-analysis?months=6
   ```

4. **Check browser console**:
   - Open DevTools (F12)
   - Look for React errors
   - Check Network tab for API call failures

### Common Issues

**Issue**: "Failed to fetch weekly recap"
- **Solution**: Check backend is running and database has user data

**Issue**: Components show loading forever
- **Solution**: Check API endpoints are responding, verify userId is correct

**Issue**: Empty data/no charts
- **Solution**: User may not have enough transaction data. Try a different user or generate more data.

## Phase 9 Components Checklist

When viewing User Detail or User Dashboard, you should see:

1. ✅ **Weekly Recap Card**
   - Daily spending bar chart
   - Week-over-week change
   - Top spending category

2. ✅ **Spending Analysis Card**
   - 6-month income/expense line chart
   - 3 key insights
   - Buffer calculations

3. ✅ **Suggested Budget Card**
   - Historical spending vs. budget chart
   - Category breakdowns
   - Budget rationale

4. ✅ **Budget Tracking Card**
   - Circular progress gauge
   - Category progress bars
   - Budget status indicators

5. ✅ **Net Worth Recap Card**
   - Net worth trend line chart
   - Assets vs. liabilities
   - Period change indicators

6. ✅ **Recommendations Section**
   - Education recommendations
   - Partner offers
   - Consent management (User Dashboard only)

## Still Not Seeing Features?

1. Make sure you're on the **User Detail** or **User Dashboard** page, NOT the main Dashboard
2. Scroll down past the accounts and transactions sections
3. Look for the "Financial Insights" heading
4. Check browser console for errors
5. Verify backend API is responding

