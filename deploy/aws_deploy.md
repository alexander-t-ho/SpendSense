# AWS Deployment Guide

This guide covers deploying SpendSense to AWS using Lambda (backend) and Amplify (frontend).

## Prerequisites

- AWS CLI configured with appropriate credentials
- AWS account with permissions for Lambda, API Gateway, Amplify, S3, and RDS (optional)
- Node.js and Python installed locally

## Architecture

- **Backend**: FastAPI on AWS Lambda via API Gateway
- **Frontend**: React app on AWS Amplify
- **Database**: SQLite in S3 (or migrate to RDS PostgreSQL for production)

## Step 1: Database Setup

### Option A: SQLite in S3 (Simple)
1. Upload database to S3:
   ```bash
   aws s3 cp data/spendsense.db s3://your-bucket/spendsense.db
   ```

2. Update Lambda environment variables:
   - `DB_PATH`: `s3://your-bucket/spendsense.db`
   - Or download on Lambda cold start

### Option B: RDS PostgreSQL (Recommended for Production)
1. Create RDS PostgreSQL instance
2. Migrate data from SQLite to PostgreSQL
3. Update connection string in Lambda environment variables

## Step 2: Backend Deployment (Lambda)

1. Package Lambda function:
   ```bash
   cd api
   pip install -r ../requirements.txt -t .
   zip -r lambda-deployment.zip . -x "*.pyc" "__pycache__/*"
   ```

2. Create Lambda function:
   ```bash
   aws lambda create-function \
     --function-name spendsense-api \
     --runtime python3.11 \
     --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-execution-role \
     --handler api.main.handler \
     --zip-file fileb://lambda-deployment.zip \
     --environment Variables="{JWT_SECRET_KEY=your-secret-key,CORS_ORIGINS=https://your-amplify-url}"
   ```

3. Create API Gateway:
   - Use existing `aws/scripts/setup_main_api_gateway.py` or create via console
   - Connect Lambda function to API Gateway

4. Update environment variables:
   - `JWT_SECRET_KEY`: Generate a secure secret key
   - `CORS_ORIGINS`: Your Amplify frontend URL
   - `DB_PATH`: Database path (S3 or RDS connection string)

## Step 3: Frontend Deployment (Amplify)

1. Connect repository to Amplify:
   - Go to AWS Amplify Console
   - Connect your Git repository
   - Amplify will detect `amplify.yml` configuration

2. Configure build settings (already in `amplify.yml`):
   ```yaml
   version: 1
   frontend:
     phases:
       preBuild:
         commands:
           - cd ui
           - npm install
       build:
         commands:
           - npm run build
     artifacts:
       baseDirectory: ui/dist
       files:
         - '**/*'
   ```

3. Set environment variables:
   - `VITE_API_URL`: Your API Gateway URL
   - Update `ui/src/components/AuthContext.tsx` to use environment variable

4. Deploy:
   - Amplify will automatically deploy on push to main branch
   - Or trigger manual deployment from console

## Step 4: Update Frontend API URL

Update `ui/src/components/AuthContext.tsx`:
```typescript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
```

Update all fetch calls to use `API_URL` instead of hardcoded localhost.

## Step 5: Database Migration

Run migration and password setup:
```bash
python3 scripts/migrate_auth_columns.py
python3 scripts/setup_passwords.py
```

Upload updated database to S3 (if using SQLite).

## Environment Variables Summary

### Lambda (Backend)
- `JWT_SECRET_KEY`: Secret key for JWT tokens
- `CORS_ORIGINS`: Comma-separated list of allowed origins
- `DB_PATH`: Database path or connection string

### Amplify (Frontend)
- `VITE_API_URL`: API Gateway endpoint URL

## Cost Estimates

- **Lambda**: Pay per request (~$0.20 per 1M requests)
- **API Gateway**: $3.50 per million requests
- **Amplify**: Free tier includes 1000 build minutes/month
- **S3**: ~$0.023 per GB storage
- **RDS** (if used): ~$15-50/month for small instance

## Troubleshooting

1. **CORS errors**: Ensure `CORS_ORIGINS` includes your Amplify URL
2. **Database access**: Ensure Lambda has S3 read permissions (if using S3)
3. **Cold starts**: Consider provisioned concurrency for Lambda
4. **API Gateway timeout**: Increase timeout in API Gateway settings

