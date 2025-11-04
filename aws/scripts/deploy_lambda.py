#!/usr/bin/env python3
"""Deploy Lambda functions for SpendSense insights computation.

This script packages and deploys Lambda functions for:
- Weekly recap computation
- Spending analysis
- Net worth tracking
- Budget suggestion
- Budget tracking

Usage:
    python aws/scripts/deploy_lambda.py [function_name]
    python aws/scripts/deploy_lambda.py  # Deploy all functions
"""

import boto3
import json
import yaml
import zipfile
import shutil
import sys
from pathlib import Path
from typing import Optional

# Load configuration
CONFIG_PATH = Path(__file__).parent.parent / "config" / "aws_config.yaml"
RESOURCES_PATH = Path(__file__).parent.parent / "config" / "aws_resources.json"

with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

with open(RESOURCES_PATH, 'r') as f:
    resources = json.load(f)

aws_config = config['aws']
region = aws_config['region']
profile = aws_config.get('profile', 'default')

session = boto3.Session(profile_name=profile, region_name=region)
lambda_client = session.client('lambda')
iam_client = session.client('iam')

lambda_role_arn = resources['iam_roles']['lambda_arn']


def create_deployment_package(function_name: str, function_dir: Path) -> Path:
    """Create a deployment package (zip file) for a Lambda function.
    
    Args:
        function_name: Name of the function
        function_dir: Directory containing the function code
    
    Returns:
        Path to the zip file
    """
    print(f"  Creating deployment package for {function_name}...")
    
    # Create temporary directory for packaging
    package_dir = Path(__file__).parent.parent / "lambda" / function_name / ".package"
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy function code
    for file in function_dir.glob("*.py"):
        shutil.copy(file, package_dir)
    
    # Copy insights module (shared code)
    insights_dir = Path(__file__).parent.parent.parent / "insights"
    if insights_dir.exists():
        shutil.copytree(insights_dir, package_dir / "insights", dirs_exist_ok=True)
    
    # Copy ingest module (for database access)
    ingest_dir = Path(__file__).parent.parent.parent / "ingest"
    if ingest_dir.exists():
        shutil.copytree(ingest_dir, package_dir / "ingest", dirs_exist_ok=True)
    
    # Copy utils module (for database helper)
    utils_dir = Path(__file__).parent.parent / "lambda" / "utils"
    if utils_dir.exists():
        shutil.copytree(utils_dir, package_dir / "utils", dirs_exist_ok=True)
    
    # Install dependencies if requirements.txt exists
    requirements_file = function_dir / "requirements.txt"
    if requirements_file.exists():
        print(f"  Installing dependencies from {requirements_file}...")
        # Install dependencies into package directory
        import subprocess
        try:
            # Use --platform manylinux2014_x86_64 for Lambda compatibility
            # Exclude numpy source directory to avoid import issues
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', 
                '-r', str(requirements_file),
                '-t', str(package_dir),
                '--platform', 'manylinux2014_x86_64',
                '--only-binary=:all:',
                '--quiet', '--disable-pip-version-check',
                '--no-cache-dir'
            ])
            print(f"  ✅ Dependencies installed")
            
            # Clean up any numpy source directories that might have been created
            numpy_dirs = list(package_dir.glob('numpy*'))
            for numpy_dir in numpy_dirs:
                if numpy_dir.is_dir() and (numpy_dir / 'setup.py').exists():
                    shutil.rmtree(numpy_dir)
                    print(f"  Removed numpy source directory: {numpy_dir.name}")
        except subprocess.CalledProcessError as e:
            # Fallback: try without platform specification
            try:
                print(f"  Retrying without platform specification...")
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', 
                    '-r', str(requirements_file),
                    '-t', str(package_dir),
                    '--quiet', '--disable-pip-version-check',
                    '--no-cache-dir'
                ])
                print(f"  ✅ Dependencies installed (fallback)")
            except subprocess.CalledProcessError as e2:
                print(f"  ⚠️  Warning: Could not install all dependencies: {e2}")
                print(f"  Some dependencies may need to be added to Lambda layer")
    
    # Create zip file
    zip_path = function_dir / f"{function_name}-deployment.zip"
    if zip_path.exists():
        zip_path.unlink()
    
    # Exclude numpy source directories when creating zip
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in package_dir.rglob("*"):
            if file_path.is_file():
                # Skip numpy source files (setup.py, etc.)
                if 'numpy' in file_path.parts and file_path.name == 'setup.py':
                    continue
                if file_path.parent.name == 'numpy' and file_path.parent.parent == package_dir:
                    # Skip top-level numpy directory if it's a source directory
                    if (file_path.parent / 'setup.py').exists():
                        continue
                arcname = file_path.relative_to(package_dir)
                zipf.write(file_path, arcname)
    
    # Clean up
    shutil.rmtree(package_dir)
    
    return zip_path


def deploy_lambda_function(function_key: str, function_config: dict):
    """Deploy a single Lambda function.
    
    Args:
        function_key: Key of the function in config
        function_config: Function configuration
    """
    function_name = function_config['name']
    function_dir = Path(__file__).parent.parent / "lambda" / function_key
    
    print(f"\nDeploying {function_name}...")
    
    if not function_dir.exists():
        print(f"  ⚠️  Function directory not found: {function_dir}")
        print(f"  Creating placeholder structure...")
        function_dir.mkdir(parents=True, exist_ok=True)
        (function_dir / "handler.py").write_text("""# Placeholder Lambda handler
def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': 'Lambda function structure ready - implementation pending'
    }
""")
        print(f"  ✅ Created placeholder structure")
        return
    
    # Create deployment package
    zip_path = create_deployment_package(function_key, function_dir)
    zip_size = zip_path.stat().st_size
    print(f"  ✅ Created deployment package: {zip_path.name} ({zip_size / 1024 / 1024:.2f} MB)")
    
    # Read zip file
    with open(zip_path, 'rb') as f:
        zip_content = f.read()
    
    lambda_config = config['lambda']
    
    try:
        # Check if function exists
        try:
            lambda_client.get_function(FunctionName=function_name)
            # Function exists, update it
            print(f"  Updating existing function...")
            
            # Update code first
            lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_content
            )
            print(f"  ✅ Code updated")
            
            # Wait a moment for code update to complete
            import time
            time.sleep(2)
            
            # Update configuration with retry
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    lambda_client.update_function_configuration(
                        FunctionName=function_name,
                        Runtime=lambda_config['runtime'],
                        Timeout=lambda_config['timeout'],
                        MemorySize=lambda_config['memory'],
                        Handler=function_config['handler'],
                        Description=function_config['description'],
                        Environment={
                            'Variables': {
                                'DB_PATH': '/tmp/spendsense.db',
                                'ENVIRONMENT': config['environment'],
                                'S3_BUCKET_PARQUET': resources.get('s3_buckets', {}).get('parquet_data', ''),
                                'S3_BUCKET_INSIGHTS': resources.get('s3_buckets', {}).get('insights', ''),
                                'S3_BUCKET_HISTORICAL': resources.get('s3_buckets', {}).get('historical', ''),
                                'DB_S3_KEY': 'database/spendsense.db',
                                'DYNAMODB_TABLE_METADATA': resources.get('dynamodb_tables', {}).get('insights_metadata', ''),
                                'DYNAMODB_TABLE_USER_PREFS': resources.get('dynamodb_tables', {}).get('user_preferences', '')
                                # Note: AWS_REGION is automatically available in Lambda runtime, don't set it
                            }
                        }
                    )
                    print(f"  ✅ Configuration updated")
                    break
                except lambda_client.exceptions.ResourceConflictException as e:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 5
                        print(f"  ⏳ Update in progress, waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                    else:
                        print(f"  ⚠️  Could not update configuration (update still in progress), but code is updated")
                        print(f"  ✅ Function code updated: {function_name}")
            
            print(f"  ✅ Updated function: {function_name}")
            
        except lambda_client.exceptions.ResourceNotFoundException:
            # Function doesn't exist, create it
            print(f"  Creating new function...")
            lambda_client.create_function(
                FunctionName=function_name,
                Runtime=lambda_config['runtime'],
                Role=lambda_role_arn,
                Handler=function_config['handler'],
                Code={'ZipFile': zip_content},
                Description=function_config['description'],
                Timeout=lambda_config['timeout'],
                MemorySize=lambda_config['memory'],
                Environment={
                    'Variables': {
                        'DB_PATH': '/tmp/spendsense.db',  # Lambda temp directory
                        'ENVIRONMENT': config['environment'],
                        'S3_BUCKET_PARQUET': resources.get('s3_buckets', {}).get('parquet_data', ''),
                        'S3_BUCKET_INSIGHTS': resources.get('s3_buckets', {}).get('insights', ''),
                        'S3_BUCKET_HISTORICAL': resources.get('s3_buckets', {}).get('historical', ''),
                        'DB_S3_KEY': 'database/spendsense.db',
                        'DYNAMODB_TABLE_METADATA': resources.get('dynamodb_tables', {}).get('insights_metadata', ''),
                        'DYNAMODB_TABLE_USER_PREFS': resources.get('dynamodb_tables', {}).get('user_preferences', '')
                        # Note: AWS_REGION is automatically available in Lambda runtime, don't set it
                    }
                },
                Tags={
                    'Environment': config['environment'],
                    'Project': 'SpendSense',
                    'Owner': 'AlexHo'
                }
            )
            print(f"  ✅ Created function: {function_name}")
            
    except Exception as e:
        print(f"  ❌ Error deploying function {function_name}: {e}")
        raise


def main():
    """Main deployment function."""
    function_to_deploy = sys.argv[1] if len(sys.argv) > 1 else None
    
    print("=" * 60)
    print("SpendSense Lambda Function Deployment")
    print("=" * 60)
    print(f"Region: {region}")
    print(f"Profile: {profile}")
    print("=" * 60)
    
    lambda_functions = config['lambda']['functions']
    
    if function_to_deploy and function_to_deploy.lower() != 'all':
        if function_to_deploy not in lambda_functions:
            print(f"❌ Function '{function_to_deploy}' not found in configuration")
            print(f"Available functions: {list(lambda_functions.keys())}")
            sys.exit(1)
        deploy_lambda_function(function_to_deploy, lambda_functions[function_to_deploy])
    else:
        # Deploy all functions
        for function_key, function_config in lambda_functions.items():
            deploy_lambda_function(function_key, function_config)
    
    print("\n" + "=" * 60)
    print("✅ Lambda Deployment Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Set up API Gateway: python aws/scripts/setup_api_gateway.py")
    print("2. Test Lambda functions in AWS Console")


if __name__ == "__main__":
    main()

