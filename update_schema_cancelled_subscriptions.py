"""Migration script to add cancelled_subscriptions table."""

from sqlalchemy import create_engine, text
from ingest.schema import get_engine, Base, CancelledSubscription
from sqlalchemy import inspect

def migrate_cancelled_subscriptions():
    """Add cancelled_subscriptions table if it doesn't exist."""
    engine = get_engine()
    
    # Check if table exists
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    if 'cancelled_subscriptions' not in existing_tables:
        print("Creating cancelled_subscriptions table...")
        CancelledSubscription.__table__.create(engine)
        print("✅ Created cancelled_subscriptions table")
    else:
        print("✅ cancelled_subscriptions table already exists")
    
    # Check if index exists
    with engine.connect() as conn:
        indexes = inspector.get_indexes('cancelled_subscriptions')
        index_names = [idx['name'] for idx in indexes]
        
        if 'ix_cancelled_subscriptions_user_id' not in index_names:
            print("Creating index on user_id...")
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cancelled_subscriptions_user_id ON cancelled_subscriptions(user_id)"))
            conn.commit()
            print("✅ Created index on user_id")
        else:
            print("✅ Index on user_id already exists")

if __name__ == "__main__":
    migrate_cancelled_subscriptions()

