"""Admin routes."""

import uuid
from fastapi import APIRouter, HTTPException, Query, status, UploadFile, File
from sqlalchemy import func

from ingest.schema import get_session, User, Account, Transaction
from api.auth import get_password_hash
from api.utils import get_db_path

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/create-admin")
def create_admin_user():
    """Temporary endpoint to create admin user in production. Remove after use."""
    db_path = get_db_path()
    session = get_session(db_path)
    try:
        admin_email = "admin@spendsense.com"
        admin_user = session.query(User).filter(
            (User.email == admin_email) | (User.username == admin_email)
        ).first()
        
        if admin_user:
            # Update existing user
            admin_user.username = admin_email
            admin_user.password_hash = get_password_hash("123456")
            admin_user.is_admin = True
            session.commit()
            return {"message": "Admin user updated", "email": admin_email, "password": "123456"}
        else:
            # Create new admin user
            admin_user = User(
                id=str(uuid.uuid4()),
                name="Admin User",
                email=admin_email,
                username=admin_email,
                password_hash=get_password_hash("123456"),
                is_admin=True
            )
            session.add(admin_user)
            session.commit()
            return {"message": "Admin user created", "email": admin_email, "password": "123456"}
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error creating admin user: {error_details}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating admin user: {str(e)}"
        )
    finally:
        session.close()


@router.post("/generate-users")
def generate_users_in_production(
    num_users: int = Query(1, description="Number of users to generate per batch (default 1, max 2)")
):
    """Temporary endpoint to generate users in production. Remove after use.
    
    Note: Generate in very small batches (1-2 users) to avoid timeouts.
    Call this endpoint multiple times to generate more users.
    
    Example: Call 150 times with ?num_users=1 to generate 150 users.
    """
    from ingest.generator import SyntheticDataGenerator
    from ingest.loader import DataLoader
    
    # Limit batch size to very small to avoid timeouts
    if num_users > 2:
        num_users = 2
    if num_users < 1:
        num_users = 1
    
    db_path = get_db_path()
    
    try:
        # Generate users (small batch)
        print(f"Generating {num_users} user(s)...")
        generator = SyntheticDataGenerator(num_users=num_users)
        data = generator.generate_all()
        
        # Load into database
        print(f"Loading {num_users} user(s) into database...")
        loader = DataLoader(db_path=db_path)
        
        # Convert generated data to DataFrames
        import pandas as pd
        
        users_df = pd.DataFrame(data.get("users", []))
        accounts_df = pd.DataFrame(data.get("accounts", []))
        transactions_df = pd.DataFrame(data.get("transactions", []))
        liabilities_df = pd.DataFrame(data.get("liabilities", []))
        
        # Load users
        users_loaded = 0
        if not users_df.empty:
            loader.load_users(users_df)
            users_loaded = len(users_df)
        
        # Load accounts
        accounts_loaded = 0
        if not accounts_df.empty:
            loader.load_accounts(accounts_df)
            accounts_loaded = len(accounts_df)
        
        # Load transactions
        transactions_loaded = 0
        if not transactions_df.empty:
            loader.load_transactions(transactions_df)
            transactions_loaded = len(transactions_df)
        
        # Load liabilities
        liabilities_loaded = 0
        if not liabilities_df.empty:
            loader.load_liabilities(liabilities_df)
            liabilities_loaded = len(liabilities_df)
        
        loader.close()
        
        # Set passwords for newly created users
        session = get_session(db_path)
        try:
            password_hash = get_password_hash("123456")
            # Only update users that don't have passwords (newly created)
            new_users = session.query(User).filter(User.password_hash == None).all()
            updated_count = 0
            for user in new_users:
                if not user.username:
                    user.username = user.email
                user.password_hash = password_hash
                updated_count += 1
            session.commit()
            
            total_users = session.query(func.count(User.id)).scalar()
            
            return {
                "success": True,
                "message": f"Successfully generated and loaded {num_users} user(s)",
                "batch_size": num_users,
                "users_created": users_loaded,
                "accounts_created": accounts_loaded,
                "transactions_created": transactions_loaded,
                "liabilities_created": liabilities_loaded,
                "passwords_set": updated_count,
                "total_users_in_db": total_users,
                "next_batch": f"Call again with ?num_users=1 to generate more users",
                "remaining_to_150": max(0, 150 - total_users)
            }
        finally:
            session.close()
            
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error generating users: {error_details}")
        # Return detailed error for debugging
        return {
            "success": False,
            "error": "Failed to generate users",
            "message": str(e),
            "traceback": error_details[:500] if error_details else "No traceback available",
            "db_path": db_path
        }


@router.post("/upload-database")
async def upload_database(file: UploadFile = File(...)):
    """Temporary endpoint to upload database file to production. Remove after use.
    
    Upload your local database file (data/spendsense.db) to Railway.
    This avoids needing to use Railway CLI linking.
    
    Usage:
        curl -X POST https://web-production-ebdc6.up.railway.app/api/admin/upload-database \
          -F "file=@data/spendsense.db"
    
    Note: This streams the file to avoid memory issues with large files.
    """
    db_path = get_db_path()
    file_size = 0
    
    try:
        # Ensure directory exists
        from pathlib import Path
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Stream file in chunks to avoid memory issues
        CHUNK_SIZE = 1024 * 1024  # 1MB chunks
        with open(db_path, 'wb') as f:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                f.write(chunk)
                file_size += len(chunk)
                # Safety limit: 50MB max
                if file_size > 50 * 1024 * 1024:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="File too large. Maximum size is 50MB."
                    )
        
        # Verify the database
        session = get_session(db_path)
        try:
            user_count = session.query(func.count(User.id)).scalar()
            account_count = session.query(func.count(Account.id)).scalar()
            transaction_count = session.query(func.count(Transaction.id)).scalar()
            
            return {
                "success": True,
                "message": "Database uploaded successfully",
                "database_path": db_path,
                "file_size_bytes": file_size,
                "users": user_count,
                "accounts": account_count,
                "transactions": transaction_count
            }
        finally:
            session.close()
            
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error uploading database: {error_details}")
        # Clean up partial file if it exists
        try:
            from pathlib import Path
            if Path(db_path).exists():
                Path(db_path).unlink()
        except:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading database: {str(e)}"
        )

