"""Lambda handler for spending analysis insights computation."""

import json
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from ingest.schema import get_session, User
    from insights.spending_analysis import SpendingAnalysisAnalyzer
except ImportError as e:
    print(f"Warning: Could not import modules: {e}")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for spending analysis computation."""
    try:
        path_params = event.get('pathParameters') or {}
        query_params = event.get('queryStringParameters') or {}
        
        user_id = path_params.get('user_id')
        months = int(query_params.get('months', 6)) if query_params else 6
        
        if not user_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'user_id is required in path'})
            }
        
        if months < 1 or months > 12:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'months must be between 1 and 12'})
            }
        
        # Get database path from environment
        # Get database path (downloads from S3 if needed)
        try:
            from utils.db_helper import get_database_path
            db_path = get_database_path()
        except ImportError:
            # Fallback if utils not available
            db_path = os.environ.get('DB_PATH', '/tmp/spendsense.db')
        
        try:
            session = get_session(db_path)
            
            # Check if user exists
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return {
                    'statusCode': 404,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'User not found'})
                }
            
            # Compute spending analysis
            analyzer = SpendingAnalysisAnalyzer(session)
            analysis = analyzer.compute_spending_analysis(user_id, months)
            
            session.close()
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(analysis, default=str)
            }
            
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': f'Error computing spending analysis: {str(e)}',
                    'note': 'Lambda function structure ready - database access needs to be configured'
                })
            }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }

