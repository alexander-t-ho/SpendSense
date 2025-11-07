# API Gateway Endpoints Setup Guide

## Overview

This guide explains how to set up API Gateway endpoints for SpendSense, including both individual insight Lambda functions and the main FastAPI application.

## Architecture

### Two Types of Endpoints

1. **Individual Insights Endpoints** (Direct Lambda Integration)
   - Each insight has its own Lambda function
   - Direct integration: `/insights/{user_id}/weekly-recap` → Lambda function
   - Faster cold starts for individual endpoints
   - Functions: weekly_recap, spending_analysis, net_worth, budget_suggestion, budget_tracking

2. **Main API Endpoints** (Proxy Integration)
   - Single Lambda function hosts entire FastAPI application
   - Proxy integration: `/api/*` → Main FastAPI Lambda
   - FastAPI handles routing internally via Mangum
   - All `/api/*` endpoints available through single Lambda

## Setup Steps

### Step 1: Deploy Lambda Functions

First, deploy all Lambda functions:

```bash
# Deploy all functions (including main API)
python aws/scripts/deploy_lambda.py all

# Or deploy individually
python aws/scripts/deploy_lambda.py main_api
python aws/scripts/deploy_lambda.py weekly_recap
python aws/scripts/deploy_lambda.py spending_analysis
# ... etc
```

### Step 2: Set Up API Gateway

Run the setup script to create API Gateway and configure all endpoints:

```bash
python aws/scripts/setup_api_gateway.py
```

This script will:
- Create or find existing API Gateway
- Set up individual insights endpoints (direct Lambda integration)
- Set up main API endpoints (proxy integration with `{proxy+}`)
- Configure CORS
- Deploy API to `dev` stage

### Step 3: Verify Setup

Check the output for the API URL:

```
API Endpoint: https://{api-id}.execute-api.us-east-1.amazonaws.com/dev
```

Test the endpoints:

```bash
API_URL="https://{api-id}.execute-api.us-east-1.amazonaws.com/dev"

# Test main API
curl "$API_URL/api/stats"
curl "$API_URL/api/users"

# Test insights endpoints
curl "$API_URL/insights/{user_id}/weekly-recap"
```

## Endpoint Structure

### Insights Endpoints (Individual Lambda Functions)

```
GET /insights/{user_id}/weekly-recap
GET /insights/{user_id}/spending-analysis
GET /insights/{user_id}/net-worth
GET /insights/{user_id}/suggested-budget
GET /insights/{user_id}/budget-tracking
```

### Main API Endpoints (FastAPI Lambda - Proxy)

All FastAPI endpoints are available via proxy:

```
GET  /api/stats
GET  /api/users
GET  /api/profile/{user_id}
GET  /api/personas/{user_id}
GET  /api/personas
GET  /api/recommendations/{user_id}
POST /api/consent
DELETE /api/consent/{user_id}
GET  /api/consent/{user_id}
GET  /api/operator/recommendations
PUT  /api/operator/recommendations/{id}/approve
PUT  /api/operator/recommendations/{id}/flag
GET  /api/operator/signals/{user_id}
GET  /api/operator/traces/{user_id}
GET  /api/evaluation/metrics
... and all other FastAPI endpoints
```

## Proxy Integration Details

The main API uses a **proxy integration** with the `{proxy+}` resource:

- **Path**: `/{proxy+}` catches all paths
- **Integration**: `AWS_PROXY` type forwards entire request to Lambda
- **Routing**: FastAPI (via Mangum) handles routing internally
- **Methods**: GET, POST, PUT, DELETE, PATCH, OPTIONS all supported

## Troubleshooting

### Lambda Function Not Found

If you see "Lambda function not found", deploy the function first:

```bash
python aws/scripts/deploy_lambda.py main_api
```

### API Gateway Not Updating

If endpoints don't appear, make sure to:
1. Deploy the API: The script automatically deploys to `dev` stage
2. Check CloudWatch logs for Lambda errors
3. Verify Lambda function permissions

### CORS Issues

CORS is configured automatically. If you have issues:
- Check `CORS_ORIGINS` environment variable in Lambda
- Verify API Gateway CORS settings
- Check browser console for CORS errors

### 502 Bad Gateway

Usually means:
- Lambda function error (check CloudWatch logs)
- Lambda timeout (increase timeout in config)
- Lambda out of memory (increase memory in config)

## Next Steps

1. **Test All Endpoints**: Verify each endpoint works correctly
2. **Configure Frontend**: Update frontend to use Lambda API URL
3. **Set Up Database**: Configure database access (S3 or DynamoDB)
4. **Monitor Performance**: Check CloudWatch metrics
5. **Set Up Alarms**: Configure CloudWatch alarms for errors

## Resource Information

After setup, resource information is saved to:
- `aws/config/aws_resources.json`

This includes:
- API Gateway ID
- API URL
- Lambda function ARNs
- S3 bucket names
- DynamoDB table names

## Alternative: Separate API Gateways

If you prefer separate API Gateways:

1. **Insights API Gateway**: For individual insight functions
2. **Main API Gateway**: For FastAPI application

You can use `setup_main_api_gateway.py` for main API only:

```bash
python aws/scripts/setup_main_api_gateway.py
```




