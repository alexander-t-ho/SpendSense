#!/usr/bin/env python3
"""Create AWS application configuration for SpendSense.

This script creates an application configuration that can be used with
AWS App Runner, Elastic Beanstalk, or other AWS application services.

Usage:
    python aws/scripts/create_application.py
"""

import boto3
import json
import yaml
from pathlib import Path
from botocore.exceptions import ClientError

# Load configuration
CONFIG_PATH = Path(__file__).parent.parent / "config" / "aws_config.yaml"
RESOURCES_PATH = Path(__file__).parent.parent / "config" / "aws_resources.json"

with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

try:
    with open(RESOURCES_PATH, 'r') as f:
        resources = json.load(f)
except FileNotFoundError:
    print("❌ aws_resources.json not found. Run setup_aws_resources.py first.")
    exit(1)

aws_config = config['aws']
region = aws_config['region']
profile = aws_config.get('profile', 'default')

session = boto3.Session(profile_name=profile, region_name=region)
sts_client = session.client('sts')


def create_application_config():
    """Create application configuration file for AWS deployment."""
    print("=" * 60)
    print("Creating AWS Application Configuration")
    print("=" * 60)
    print()
    
    # Get account information
    try:
        identity = sts_client.get_caller_identity()
        account_id = identity['Account']
        user_arn = identity['Arn']
        
        print(f"Account ID: {account_id}")
        print(f"User ARN: {user_arn}")
        print()
    except Exception as e:
        print(f"❌ Error getting account info: {e}")
        return
    
    # Create application configuration
    app_config = {
        'application_name': 'spendsense',
        'environment': config['environment'],
        'region': region,
        'account_id': account_id,
        'aws_resources': resources,
        'api_endpoints': {
            'local': 'http://localhost:8000',
            'lambda': resources.get('api_gateway', {}).get('api_url', 'N/A')
        },
        'deployment': {
            'backend': {
                'type': 'lambda',
                'functions': list(resources['lambda_functions'].values())
            },
            'frontend': {
                'type': 's3_static_hosting',
                'bucket': resources['s3_buckets'].get('frontend', 'N/A')
            },
            'database': {
                'type': 'sqlite_local',
                'path': 'data/spendsense.db',
                'note': 'For production, consider RDS or DynamoDB'
            }
        }
    }
    
    # Save application config
    app_config_path = Path(__file__).parent.parent / "config" / "application_config.json"
    with open(app_config_path, 'w') as f:
        json.dump(app_config, f, indent=2)
    
    print("✅ Application configuration created:")
    print(f"   {app_config_path}")
    print()
    
    # Create AWS Amplify configuration (optional)
    create_amplify_config(app_config)
    
    # Create deployment documentation
    create_deployment_docs(app_config)
    
    print("=" * 60)
    print("✅ Application Configuration Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Review application_config.json")
    print("2. Deploy backend: python aws/scripts/deploy_lambda.py")
    print("3. Deploy frontend: See aws/DEPLOYMENT_GUIDE.md")
    print("4. Test endpoints: See aws/DEPLOYMENT_GUIDE.md")


def create_amplify_config(app_config):
    """Create AWS Amplify configuration for frontend deployment."""
    amplify_config_path = Path(__file__).parent.parent.parent / "amplify.yml"
    
    amplify_config = """version: 1
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
  cache:
    paths:
      - ui/node_modules/**/*
"""
    
    with open(amplify_config_path, 'w') as f:
        f.write(amplify_config)
    
    print("✅ Created AWS Amplify configuration:")
    print(f"   {amplify_config_path}")
    print()


def create_deployment_docs(app_config):
    """Create deployment documentation."""
    docs_path = Path(__file__).parent.parent / "APPLICATION_DEPLOYMENT.md"
    
    docs = f"""# SpendSense Application Deployment

## Application Information

- **Application Name**: {app_config['application_name']}
- **Environment**: {app_config['environment']}
- **Region**: {app_config['region']}
- **Account ID**: {app_config['account_id']}

## API Endpoints

### Local Development
- Backend API: {app_config['api_endpoints']['local']}
- Frontend: http://localhost:3000

### AWS Lambda (Production)
- API Gateway: {app_config['api_endpoints']['lambda']}

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
API_URL="{app_config['api_endpoints']['lambda']}"
curl "$API_URL/insights/{{user_id}}/weekly-recap"
```

### Test Local Backend
```bash
# Start backend
cd /Users/alexho/SpendSense
uvicorn api.main:app --reload

# Test endpoint
curl http://localhost:8000/api/insights/{{user_id}}/weekly-recap
```

## Connection Verification

```bash
# Verify AWS connection
python aws/scripts/verify_aws_connection.py

# Check all resources
aws s3 ls | grep spendsense
aws dynamodb list-tables --region {region}
aws lambda list-functions --region {region} | grep spendsense
```
"""
    
    with open(docs_path, 'w') as f:
        f.write(docs)
    
    print("✅ Created deployment documentation:")
    print(f"   {docs_path}")
    print()


if __name__ == "__main__":
    create_application_config()

