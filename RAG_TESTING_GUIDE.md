# RAG Pipeline Testing Guide

This guide explains how to test the RAG (Retrieval-Augmented Generation) pipeline that enhances recommendations using OpenAI's o1-mini model.

## Overview

The RAG pipeline:
- Validates all recommendations for quality issues ($0 values, missing data, insufficient action items)
- Enhances recommendations using OpenAI's o1-mini thinking model
- Ensures all recommendations have 3-5 actionable options
- Fixes placeholder text and missing data using financial best practices
- Maintains empowering, supportive tone

## Prerequisites

1. **Backend server running**: `./start_backend.sh`
2. **Database with users**: Ensure you have users in the database
3. **OpenAI API Key** (optional but recommended): Set `OPENAI_API_KEY` environment variable

## Testing Without API Key

Even without an API key, you can test the validation and knowledge base components:

```bash
python3 test_rag_pipeline.py
```

This will test:
- ✅ Recommendation validator (detects $0 values, missing data)
- ✅ Knowledge base (retrieves financial best practices)
- ✅ RAG enhancer graceful fallback (returns original if API key missing)
- ✅ Full pipeline (generates recommendations, validates them)

**Expected Results Without API Key:**
- Recommendations will be generated but may contain:
  - `$0` values
  - Placeholder text like `{category}`
  - Some recommendations may have fewer than optimal action items

## Testing With API Key (Full RAG Enhancement)

To enable full RAG enhancement:

1. **Set your OpenAI API key:**
   ```bash
   export OPENAI_API_KEY='your-key-here'
   ```

2. **Run the test suite:**
   ```bash
   python3 test_rag_pipeline.py
   ```

3. **Test via API:**
   ```bash
   python3 test_rag_api.py
   ```

**Expected Results With API Key:**
- All recommendations enhanced with o1-mini
- No `$0` values (replaced with realistic estimates)
- No placeholder text
- All recommendations have 3-5 actionable options
- Better personalization based on user data

## Testing via API Endpoint

1. **Start the backend server:**
   ```bash
   ./start_backend.sh
   ```

2. **Generate recommendations for a user:**
   ```bash
   # Get a user ID from the database or frontend
   curl -X POST "http://localhost:8000/api/recommendations/generate/{user_id}?window_days=180&num_recommendations=8"
   ```

3. **Check the generated recommendations:**
   ```bash
   python3 test_rag_api.py
   ```

## What Gets Tested

### 1. Validator Tests
- ✅ Detects `$0` values in recommendations
- ✅ Detects missing categories
- ✅ Validates action items count (requires 3-5)
- ✅ Checks for placeholder text
- ✅ Assigns quality scores

### 2. Knowledge Base Tests
- ✅ Retrieves category-specific financial tips
- ✅ Extracts user context from data points
- ✅ Provides alternatives and savings strategies
- ✅ Handles missing data gracefully

### 3. RAG Enhancer Tests
- ✅ Graceful fallback when API key missing
- ✅ Enhances recommendations with o1-mini
- ✅ Fixes `$0` values with realistic estimates
- ✅ Ensures 3-5 actionable options
- ✅ Replaces placeholders with actual data

### 4. Full Pipeline Tests
- ✅ Generates recommendations for real users
- ✅ Validates all generated recommendations
- ✅ Checks for common issues
- ✅ Verifies action items count

## Expected Output

### Without API Key:
```
TEST 1: Recommendation Validator
✓ Valid recommendation: valid (score: 1.00)
✓ Invalid recommendation with $0: needs_regeneration (score: 0.00)
✓ Recommendation with <3 items: needs_enrichment (score: 0.80)

TEST 2: Knowledge Base
✓ Retrieved knowledge for 'Coffee' category
✓ Knowledge with user context

TEST 3: RAG Enhancer (Without API Key)
⚠️  OpenAI API key not found. RAG enhancement will be disabled.
✓ Enhancer handles missing API key gracefully

TEST 5: Full Recommendation Pipeline
✓ Generated 10 recommendations
✓ Validation results:
  - Valid: 5
  - Enhanced/Needs improvement: 5
```

### With API Key:
```
TEST 4: RAG Enhancer (With API Key)
✓ Enhanced recommendation:
  Title: Reduce Category Spending
  Text: You spend $300/month in the Restaurant category...
  Action Items: 5 items
  Expected Impact: Save up to $900/year...

✅ RAG enhancer (with API) tests passed!
```

## Troubleshooting

### Issue: "OPENAI_API_KEY not set"
**Solution**: Set the environment variable:
```bash
export OPENAI_API_KEY='your-key-here'
```

### Issue: "Backend server is not running"
**Solution**: Start the backend:
```bash
./start_backend.sh
```

### Issue: Recommendations still have $0 values
**Possible causes:**
1. API key not set - RAG enhancement is disabled
2. API call failed - Check backend logs for errors
3. Rate limiting - Wait and retry

### Issue: "Request timed out"
**Solution**: The RAG enhancement may take 30-60 seconds. Increase the timeout in the test script or wait longer.

## Verification Checklist

After running tests, verify:

- [ ] Validator correctly identifies issues
- [ ] Knowledge base returns relevant tips
- [ ] RAG enhancer works (if API key set)
- [ ] Generated recommendations have 3-5 action items
- [ ] No `$0` values in recommendations (if RAG enabled)
- [ ] No placeholder text like `{category}` (if RAG enabled)
- [ ] Recommendations are personalized with user data

## Next Steps

1. **Review recommendations in admin dashboard:**
   - Navigate to user detail page
   - Click "Generate Recommendations"
   - Review generated recommendations

2. **Approve recommendations:**
   - Go to Recommendation Queue
   - Approve high-quality recommendations
   - Check that approved recommendations appear on user dashboard

3. **Monitor quality:**
   - Check for any remaining `$0` values
   - Verify all recommendations have actionable options
   - Ensure recommendations are personalized

## Files

- `test_rag_pipeline.py` - Comprehensive test suite
- `test_rag_api.py` - Test via API endpoint
- `recommend/validator.py` - Validation logic
- `recommend/knowledge_base.py` - Financial best practices
- `recommend/rag_enhancer.py` - RAG enhancement engine
- `recommend/persona_recommendation_generator.py` - Main generator with RAG integration

