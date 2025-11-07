"""Lambda handler for main SpendSense FastAPI application."""

import json
import os
import sys
from typing import Dict, Any

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from mangum import Mangum
    from api.main import app
    
    # Create Mangum handler
    handler = Mangum(app, lifespan="off")
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure mangum is installed: pip install mangum")
    raise


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for FastAPI application.
    
    This handler uses Mangum to convert FastAPI ASGI app to Lambda-compatible format.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
    
    Returns:
        API Gateway response
    """
    try:
        # Handle the request through Mangum
        response = handler(event, context)
        return response
    except Exception as e:
        print(f"Error in Lambda handler: {e}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'detail': str(e)
            })
        }




