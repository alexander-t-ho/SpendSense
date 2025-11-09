#!/usr/bin/env python3
"""Script to set passwords for all users and create admin user."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingest.schema import get_session, User, init_db
import bcrypt

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    # Ensure password is bytes
    password_bytes = password.encode('utf-8')
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    # Return as string
    return hashed.decode('utf-8')

def setup_passwords(db_path: str = "data/spendsense.db", admin_email: str = "admin@spendsense.com"):
    """Set passwords for all users and create admin user."""
    # Initialize database
    init_db(db_path)
    session = get_session(db_path)
    
    try:
        # Hash password once
        password_hash = get_password_hash("123456")
        
        # Update all existing users
        users = session.query(User).all()
        updated_count = 0
        for user in users:
            # Set username to email if not set
            if not user.username:
                user.username = user.email
            
            # Set password hash
            user.password_hash = password_hash
            updated_count += 1
        
        session.commit()
        print(f"Updated {updated_count} existing users with password '123456'")
        
        # Create admin user if doesn't exist
        admin_user = session.query(User).filter(
            (User.email == admin_email) | (User.username == admin_email)
        ).first()
        
        if not admin_user:
            import uuid
            admin_user = User(
                id=str(uuid.uuid4()),
                name="Admin User",
                email=admin_email,
                username=admin_email,
                password_hash=password_hash,
                is_admin=True
            )
            session.add(admin_user)
            session.commit()
            print(f"Created admin user: {admin_email} with password '123456'")
        else:
            # Update existing admin user
            admin_user.username = admin_email
            admin_user.password_hash = password_hash
            admin_user.is_admin = True
            session.commit()
            print(f"Updated admin user: {admin_email} with password '123456'")
        
        print("\nAll users can now login with:")
        print("  Username: their email address")
        print("  Password: 123456")
        print(f"\nAdmin login:")
        print(f"  Username: {admin_email}")
        print(f"  Password: 123456")
        
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Set passwords for all users")
    parser.add_argument("--db-path", type=str, default="data/spendsense.db", help="Database path")
    parser.add_argument("--admin-email", type=str, default="admin@spendsense.com", help="Admin email")
    
    args = parser.parse_args()
    setup_passwords(args.db_path, args.admin_email)

