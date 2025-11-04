# SpendSense Application Deployment

## Application Information

- **Application Name**: spendsense
- **Environment**: development
- **Region**: us-east-1
- **Account ID**: 971422717446

## API Endpoints

### Local Development
- Backend API: http://localhost:8000
- Frontend: http://localhost:3000

### AWS Lambda (Production)
- API Gateway: https://43k2bhxxpi.execute-api.us-east-1.amazonaws.com/dev

## Deployment Options

### Option 1: AWS Lambda + API Gateway (Current Setup)
- Backend: Lambda functions
- API: API Gateway
- Storage: S3 + DynamoDB
- **Status**: ✅ Infrastructure ready

### Option 2: AWS App Runner
- Containerized FastAPI application
- Automatic scaling
- **Status**: ⏳ Not configured

### Option 3: AWS Elastic Beanstalk
- Platform-as-a-Service
- Easy deployment
- **Status**: ⏳ Not configured

### Option 4: AWS Amplify (Frontend)
- Static site hosting
- CI/CD pipeline
- **Status**: ⏳ Configuration ready (amplify.yml)

## Current Resources

See `aws/config/aws_resources.json` for all resource names and ARNs.

## Deployment Commands

### Backend (Lambda)
```bash
python aws/scripts/deploy_lambda.py
```

### Frontend (Amplify)
```bash
# Push to GitHub, then connect to Amplify Console
# Or use Amplify CLI:
amplify init
amplify add hosting
amplify publish
```

## Testing

### Test API Gateway
```bash
API_URL="https://43k2bhxxpi.execute-api.us-east-1.amazonaws.com/dev"
curl "$API_URL/insights/{user_id}/weekly-recap"
```

### Test Local Backend
```bash
# Start backend
cd /Users/alexho/SpendSense
uvicorn api.main:app --reload

# Test endpoint
curl http://localhost:8000/api/insights/{user_id}/weekly-recap
```

## Connection Verification

```bash
# Verify AWS connection
python aws/scripts/verify_aws_connection.py

# Check all resources
aws s3 ls | grep spendsense
aws dynamodb list-tables --region us-east-1
aws lambda list-functions --region us-east-1 | grep spendsense
```
