"""Lambda handler for net worth tracking insights computation."""

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
    from insights.net_worth_tracker import NetWorthTracker
except ImportError as e:
    print(f"Warning: Could not import modules: {e}")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for net worth computation."""
    try:
        path_params = event.get('pathParameters') or {}
        query_params = event.get('queryStringParameters') or {}
        
        user_id = path_params.get('user_id')
        
        if not user_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'user_id is required in path'})
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
            
            tracker = NetWorthTracker(session)
            
            # Determine if this is a POST (create snapshot) or GET (get net worth)
            http_method = event.get('httpMethod', 'GET')
            
            if http_method == 'POST':
                # Create snapshot
                snapshot_date_str = query_params.get('snapshot_date') if query_params else None
                snapshot_date = None
                if snapshot_date_str:
                    try:
                        snapshot_date = datetime.fromisoformat(snapshot_date_str)
                    except ValueError:
                        return {
                            'statusCode': 400,
                            'headers': {
                                'Content-Type': 'application/json',
                                'Access-Control-Allow-Origin': '*'
                            },
                            'body': json.dumps({'error': 'Invalid snapshot_date format. Use YYYY-MM-DD'})
                        }
                
                snapshot = tracker.create_snapshot(user_id, snapshot_date)
                session.close()
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps(snapshot, default=str)
                }
            else:
                # Get current net worth
                period = query_params.get('period', 'month') if query_params else 'month'
                
                # Get current net worth
                current = tracker.calculate_net_worth(user_id)
                
                # Get historical data
                history = tracker.get_net_worth_history(user_id, period=period)
                
                session.close()
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'current': current,
                        'history': history
                    }, default=str)
                }
            
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': f'Error computing net worth: {str(e)}',
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

