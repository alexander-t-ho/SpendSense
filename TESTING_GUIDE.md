# Testing Guide: Persona-Based Recommendation System

## Prerequisites
- Backend server running on http://localhost:8000
- Frontend server running (typically http://localhost:5173)
- Database with users and transactions

## Test Flow

### Step 1: Generate Recommendations for a User

1. **Navigate to Admin Dashboard**
   - Go to http://localhost:5173 (or your frontend URL)
   - Navigate to a user's detail page

2. **Generate Recommendations**
   - On the user detail page, you should see a "Generate Recommendations (8 per persona)" button
   - Click the button
   - Wait for confirmation message: "Recommendations generated! Please review and approve them in the Recommendation Queue."

3. **Verify Generation**
   - Check the backend logs to see if recommendations were created
   - Recommendations should be stored with `approved=False`

### Step 2: Review Recommendations in Admin Queue

1. **Navigate to Recommendation Queue**
   - Go to the Operator Dashboard or Recommendation Queue page
   - You should see pending recommendations

2. **Review Each Recommendation**
   - Each recommendation should show:
     - Title
     - User name and email
     - Persona name (e.g., "Subscription-Heavy")
     - Recommendation text (filled with user-specific data)
     - Action items
     - Expected impact
     - Priority badge (HIGH/MEDIUM/LOW)
     - Rationale

3. **Test Filtering**
   - Filter by "Pending" - should show unapproved recommendations
   - Filter by "Approved" - should be empty initially
   - Filter by "Rejected" - should be empty initially
   - Filter by "All" - should show all recommendations

### Step 3: Approve Recommendations

1. **Approve a Recommendation**
   - Click the green "Approve" (✓) button on a recommendation
   - The recommendation should disappear from "Pending" view
   - Switch to "Approved" filter to see it there

2. **Reject a Recommendation**
   - Click the orange "Reject" (X) button on a recommendation
   - The recommendation should disappear from "Pending" view
   - Switch to "Rejected" filter to see it there

3. **Flag a Recommendation**
   - Click the red "Flag" button on a recommendation
   - The recommendation should disappear from "Pending" view
   - Switch to "Flagged" filter to see it there

### Step 4: View Approved Recommendations

1. **Navigate to User Detail Page**
   - Go back to the user detail page
   - Scroll to the "Recommendations" section

2. **Verify Approved Recommendations Display**
   - Only approved recommendations should be visible
   - Each should show:
     - Title
     - Personalized recommendation text (e.g., "You spend $460/month on subscriptions...")
     - Action items
     - Expected impact
     - Priority badge

### Step 5: Test Different Personas

1. **Test with Different Users**
   - Generate recommendations for users with different personas:
     - High Utilization persona
     - Subscription-Heavy persona
     - Variable Income Budgeter
     - Savings Builder
     - Balanced/Stable

2. **Verify Persona-Specific Recommendations**
   - Each persona should get recommendations relevant to their risk profile
   - Higher risk personas should get more recommendations (if dual persona)

### Step 6: Test Edge Cases

1. **User with No Approved Recommendations**
   - Generate recommendations but don't approve any
   - User should see either:
     - Fallback to original recommendation generator, OR
     - Message saying no recommendations available

2. **User with Dual Personas**
   - Find a user with two personas (e.g., 62% Balanced, 38% Subscription-Heavy)
   - Generate recommendations
   - Should see recommendations from both personas
   - Higher risk persona should get more recommendations

## Expected Behavior

### Recommendation Generation
- Generates ~8 recommendations per user
- Distributes recommendations based on persona percentages and risk levels
- Fills templates with user-specific data (e.g., actual subscription amounts)
- Stores recommendations with `approved=False`

### Admin Approval
- Can approve (✓), reject (X), or flag recommendations
- Status changes are reflected immediately
- Filtering works correctly for all statuses

### User View
- Only approved recommendations are shown
- Recommendations are personalized with actual user data
- Action items and expected impact are displayed

## Troubleshooting

### Recommendations Not Generating
- Check backend logs for errors
- Verify user has persona assignment
- Check database connection

### Recommendations Not Appearing in Queue
- Verify recommendations were created in database
- Check API endpoint: `GET /api/operator/recommendations?status=pending`
- Verify frontend is calling correct endpoint

### Approved Recommendations Not Showing
- Verify recommendations are actually approved (check database)
- Check API endpoint: `GET /api/recommendations/{user_id}/approved`
- Verify frontend is calling correct endpoint

### Schema Errors
- Run `python3 update_schema.py` to add missing columns
- Check that all new columns exist in recommendations table

## API Endpoints to Test

1. **Generate Recommendations**
   ```
   POST /api/recommendations/generate/{user_id}?num_recommendations=8
   ```

2. **Get Recommendation Queue**
   ```
   GET /api/operator/recommendations?status=pending&limit=50
   ```

3. **Approve Recommendation**
   ```
   PUT /api/operator/recommendations/{recommendation_id}/approve
   ```

4. **Reject Recommendation**
   ```
   PUT /api/operator/recommendations/{recommendation_id}/reject
   ```

5. **Get Approved Recommendations**
   ```
   GET /api/recommendations/{user_id}/approved
   ```

## Database Queries for Verification

```sql
-- Check recommendations for a user
SELECT id, title, persona_id, approved, rejected, flagged, created_at 
FROM recommendations 
WHERE user_id = 'YOUR_USER_ID';

-- Count recommendations by status
SELECT 
  COUNT(*) as total,
  SUM(CASE WHEN approved = 1 THEN 1 ELSE 0 END) as approved,
  SUM(CASE WHEN rejected = 1 THEN 1 ELSE 0 END) as rejected,
  SUM(CASE WHEN flagged = 1 THEN 1 ELSE 0 END) as flagged,
  SUM(CASE WHEN approved = 0 AND rejected = 0 AND flagged = 0 THEN 1 ELSE 0 END) as pending
FROM recommendations;
```

