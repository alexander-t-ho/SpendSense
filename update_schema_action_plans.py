"""Add approved_action_plans table to database."""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys

# Database path
db_path = "data/spendsense.db"

engine = create_engine(f"sqlite:///{db_path}", echo=False)
Session = sessionmaker(bind=engine)
session = Session()

try:
    # Create table using raw SQL (simpler for SQLite)
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS approved_action_plans (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            recommendation_id TEXT NOT NULL,
            approved_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (recommendation_id) REFERENCES recommendations(id)
        )
    """))
    
    # Create indexes
    session.execute(text("CREATE INDEX IF NOT EXISTS idx_approved_action_plans_user_id ON approved_action_plans(user_id)"))
    session.execute(text("CREATE INDEX IF NOT EXISTS idx_approved_action_plans_recommendation_id ON approved_action_plans(recommendation_id)"))
    
    session.commit()
    print("✅ Created approved_action_plans table and indexes")
    
except Exception as e:
    session.rollback()
    print(f"❌ Error creating table: {e}")
    sys.exit(1)
finally:
    session.close()

