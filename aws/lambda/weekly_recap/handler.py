"""Lambda handler for weekly recap insights computation."""

import json
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add project root to path for imports
# When deployed, the code will be in the Lambda package
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from ingest.schema import get_session
    from insights.weekly_recap import WeeklyRecapAnalyzer
except ImportError as e:
    # Fallback for Lambda environment
    print(f"Warning: Could not import modules: {e}")
    print("This is expected if Lambda handler is not yet fully deployed")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for weekly recap computation.
    
    Event structure (API Gateway):
    {
        "pathParameters": {"user_id": "..."},
        "queryStringParameters": {"week_start": "YYYY-MM-DD"} or null
    }
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
    
    Returns:
        API Gateway response with weekly recap data
    """
    try:
        # Extract parameters from event
        path_params = event.get('pathParameters') or {}
        query_params = event.get('queryStringParameters') or {}
        
        user_id = path_params.get('user_id')
        week_start_str = query_params.get('week_start')
        
        if not user_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'user_id is required in path'
                })
            }
        
        # Parse week_start if provided
        week_start_date = None
        if week_start_str:
            try:
                week_start_date = datetime.fromisoformat(week_start_str)
            except ValueError:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'Invalid date format. Use YYYY-MM-DD'
                    })
                }
        
        # Get database path (downloads from S3 if needed)
        try:
            from utils.db_helper import get_database_path
            db_path = get_database_path()
        except ImportError:
            # Fallback if utils not available
            db_path = os.environ.get('DB_PATH', '/tmp/spendsense.db')
        
        try:
            # Initialize database session
            session = get_session(db_path)
            
            try:
                # Compute weekly recap
                analyzer = WeeklyRecapAnalyzer(session)
                recap = analyzer.compute_weekly_recap(user_id, week_start_date)
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps(recap, default=str)
                }
            finally:
                session.close()
            
        except Exception as e:
            # Log the full error for debugging
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error in weekly_recap handler: {error_trace}")
            
            # If database access fails, return error
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': f'Error computing weekly recap: {str(e)}',
                    'traceback': error_trace if 'DEVELOPMENT' in os.environ.get('ENVIRONMENT', '') else None
                })
            }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }
