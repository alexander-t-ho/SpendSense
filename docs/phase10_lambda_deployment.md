# Phase 10: AWS Lambda Integration & Deployment

## Overview

Phase 10 deploys the SpendSense FastAPI application to AWS Lambda, making it accessible via API Gateway. This enables serverless deployment with automatic scaling and cost-effective operation.

## Architecture

### Deployment Options

**Option 1: Full FastAPI Application (Main API)**
- Single Lambda function hosting entire FastAPI app
- Uses Mangum adapter to convert ASGI app to Lambda handler
- All endpoints accessible through single API Gateway
- **Function**: `alexho-spendsense-api-dev`
- **Memory**: 2048 MB
- **Timeout**: 300 seconds (5 minutes)

**Option 2: Individual Insight Functions (Current)**
- Separate Lambda functions for each insight type
- Faster cold starts for individual endpoints
- Better isolation and scaling
- **Functions**:
  - `alexho-spendsense-insights-weekly-recap-dev`
  - `alexho-spendsense-insights-spending-analysis-dev`
  - `alexho-spendsense-insights-budget-suggestion-dev`
  - `alexho-spendsense-insights-budget-tracking-dev`
  - `alexho-spendsense-insights-net-worth-dev`

## Implementation

### 1. Lambda Handler for Main API

**File**: `aws/lambda/api/handler.py`

Uses Mangum adapter to convert FastAPI ASGI application to Lambda-compatible handler:

```python
from mangum import Mangum
from api.main import app

handler = Mangum(app, lifespan="off")
```

### 2. CORS Configuration

Updated FastAPI app to support multiple origins via environment variable:

```python
allowed_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
```

### 3. Deployment Script Updates

- Updated `deploy_lambda.py` to handle main API function
- Packages all application modules (api, ingest, features, personas, recommend, guardrails, insights, eval)
- Supports function-specific timeout and memory settings

## Deployment Steps

### Step 1: Install Mangum

```bash
pip install mangum==0.17.0
```

### Step 2: Deploy Main API Lambda Function

```bash
# Deploy main API function
python aws/scripts/deploy_lambda.py main_api

# Or deploy all functions (including main API)
python aws/scripts/deploy_lambda.py all
```

### Step 3: Set Up API Gateway for Main API

**Option A: Create New API Gateway for Main API**
- Create separate API Gateway for full FastAPI application
- Map all routes to single Lambda function

**Option B: Use Existing API Gateway**
- Add routes to existing insights API Gateway
- Route `/api/*` endpoints to main API Lambda function

### Step 4: Configure Database Access

The Lambda function needs access to the database. Options:

1. **S3 Storage**: Upload SQLite database to S3, download on cold start
2. **DynamoDB**: Migrate data to DynamoDB (requires schema changes)
3. **RDS**: Use RDS for Lambda (requires VPC configuration)

**Recommended for Phase 10**: S3 storage with caching

### Step 5: Test Deployment

```bash
# Test Lambda function directly
aws lambda invoke \
  --function-name alexho-spendsense-api-dev \
  --payload '{"httpMethod":"GET","path":"/api/stats"}' \
  response.json

# Test via API Gateway
API_URL="https://{api-id}.execute-api.us-east-1.amazonaws.com/dev"
curl "$API_URL/api/stats"
```

## Configuration

### Environment Variables

Set in Lambda function configuration:

- `DB_PATH`: Path to database file in Lambda temp directory
- `CORS_ORIGINS`: Comma-separated list of allowed origins
- `ENVIRONMENT`: `development` or `production`
- `S3_BUCKET_PARQUET`: S3 bucket for Parquet files
- `S3_BUCKET_INSIGHTS`: S3 bucket for insights cache
- `DB_S3_KEY`: S3 key for database file

### Lambda Settings

- **Runtime**: Python 3.11
- **Memory**: 2048 MB (main API), 1024 MB (insight functions)
- **Timeout**: 300 seconds (5 minutes)
- **Handler**: `handler.lambda_handler`

## File Structure

```
aws/
├── lambda/
│   ├── api/
│   │   ├── handler.py          # Main API Lambda handler
│   │   └── requirements.txt    # Lambda-specific dependencies
│   ├── weekly_recap/
│   ├── spending_analysis/
│   ├── budget_suggestion/
│   ├── budget_tracking/
│   └── net_worth/
├── scripts/
│   ├── deploy_lambda.py        # Updated to support main API
│   └── setup_api_gateway.py   # API Gateway setup
└── config/
    └── aws_config.yaml         # Lambda configuration
```

## Challenges & Solutions

### Challenge 1: Large Package Size
**Issue**: FastAPI app with all dependencies exceeds Lambda package size limit  
**Solution**: Use Lambda Layers for common dependencies (numpy, pandas, etc.)

### Challenge 2: Cold Start Performance
**Issue**: Lambda cold starts can be slow with full application  
**Solution**: 
- Increase memory allocation (faster CPU)
- Use provisioned concurrency for production
- Optimize imports (lazy loading)

### Challenge 3: Database Access
**Issue**: SQLite file needs to be accessible from Lambda  
**Solution**: 
- Upload database to S3
- Download on cold start to `/tmp/`
- Cache in memory for warm invocations

### Challenge 4: WebSocket Support
**Issue**: API Gateway WebSocket requires separate API  
**Solution**: 
- Deploy WebSocket API separately
- Or use API Gateway v2 HTTP API with WebSocket support

## Next Steps

1. ✅ Create Lambda handler for main API
2. ✅ Add Mangum dependency
3. ✅ Update deployment script
4. ⏳ Deploy Lambda function
5. ⏳ Set up API Gateway integration
6. ⏳ Configure database access (S3)
7. ⏳ Test all endpoints
8. ⏳ Update frontend to use Lambda endpoints
9. ⏳ Document API Gateway URLs
10. ⏳ Performance testing and optimization

## Success Criteria

- ✅ Lambda function deploys successfully
- ⏳ All API endpoints accessible via API Gateway
- ⏳ Database access working (S3 download)
- ⏳ Response times <5 seconds
- ⏳ CORS configured correctly
- ⏳ Error handling working
- ⏳ Logging to CloudWatch

## Notes

- WebSocket endpoints may not work with standard API Gateway (requires WebSocket API)
- Large dependency packages may require Lambda Layers
- Database size limits may require migration to DynamoDB or RDS
- Consider using API Gateway v2 HTTP API for better performance




