"""FastAPI application for SpendSense."""

import os
import uuid
from fastapi import FastAPI, HTTPException, Query, Body, WebSocket, WebSocketDisconnect, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
import bcrypt
from jose import JWTError, jwt

from ingest.schema import get_session, User, Account, Transaction, Liability, CancelledSubscription, ApprovedActionPlan, Recommendation
from features.pipeline import FeaturePipeline
from api.websocket import manager

app = FastAPI(title="SpendSense API", version="1.0.0")

# CORS middleware
# Allow origins from environment variable for Lambda, fallback to localhost for local dev
allowed_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication setup
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

security = HTTPBearer()

# Pydantic models for authentication
class LoginRequest(BaseModel):
    username: str  # Email or username
    password: str

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    username: Optional[str]
    is_admin: bool

# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """Hash a password."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get the current authenticated user from JWT token."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    session = get_session()
    try:
        user = session.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    finally:
        session.close()


@app.get("/")
def root():
    return {"message": "SpendSense API", "version": "1.0.0"}


# Authentication endpoints
@app.post("/api/auth/register", response_model=TokenResponse)
def register(request: RegisterRequest):
    """Register a new user."""
    session = get_session()
    try:
        # Check if user already exists
        existing_user = session.query(User).filter(
            (User.email == request.email) | (User.username == request.email)
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        user = User(
            id=str(uuid.uuid4()),
            name=request.name,
            email=request.email,
            username=request.email,  # Use email as username
            password_hash=get_password_hash(request.password),
            is_admin=False
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # Create access token
        access_token = create_access_token(data={"sub": user.username or user.email})
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "username": user.username,
                "is_admin": user.is_admin
            }
        )
    finally:
        session.close()


@app.post("/api/auth/login", response_model=TokenResponse)
def login(request: LoginRequest):
    """Login and get access token."""
    session = get_session()
    try:
        # Find user by username (email) or email
        user = session.query(User).filter(
            (User.username == request.username) | (User.email == request.username)
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password
        if not user.password_hash or not verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token = create_access_token(data={"sub": user.username or user.email})
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "username": user.username,
                "is_admin": user.is_admin
            }
        )
    finally:
        session.close()


@app.post("/api/auth/logout")
def logout(current_user: User = Depends(get_current_user)):
    """Logout (client should discard token)."""
    return {"message": "Successfully logged out"}


@app.get("/api/auth/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        username=current_user.username,
        is_admin=current_user.is_admin
    )


@app.get("/api/stats")
def get_stats():
    """Get overall statistics."""
    session = get_session()
    try:
        total_users = session.query(func.count(User.id)).scalar()
        total_accounts = session.query(func.count(Account.id)).scalar()
        total_transactions = session.query(func.count(Transaction.id)).scalar()
        total_liabilities = session.query(func.count(Liability.id)).scalar()
        
        return {
            "total_users": total_users or 0,
            "total_accounts": total_accounts or 0,
            "total_transactions": total_transactions or 0,
            "total_liabilities": total_liabilities or 0,
        }
    finally:
        session.close()


@app.get("/api/users")
def get_users():
    """Get all users with account counts and persona information (admin only)."""
    from personas.assigner import PersonaAssigner
    
    session = get_session()
    try:
        users = session.query(User).all()
        assigner = PersonaAssigner(session)
        result = []
        
        for user in users:
            account_count = session.query(func.count(Account.id)).filter(
                Account.user_id == user.id
            ).scalar()
            
            # Get persona assignment (always compute fresh to get dual personas)
            persona_assignment_data = assigner.assign_persona(user.id)
            
            # Build persona object with dual persona support
            persona_obj = {
                "id": persona_assignment_data.get('primary_persona'),
                "name": persona_assignment_data.get('primary_persona_name'),
                "risk": persona_assignment_data.get('primary_persona_risk', 0),
                "risk_level": persona_assignment_data.get('risk_level', persona_assignment_data.get('primary_persona_risk_level', 'VERY_LOW')),
                "total_risk_points": persona_assignment_data.get('total_risk_points', 0.0),
                "top_personas": persona_assignment_data.get('top_personas', []),
                "all_matching_personas": persona_assignment_data.get('all_matching_personas', []),
                "primary_persona": persona_assignment_data.get('primary_persona'),
                "primary_persona_name": persona_assignment_data.get('primary_persona_name'),
                "primary_persona_percentage": persona_assignment_data.get('primary_persona_percentage', 100),
                "secondary_persona": persona_assignment_data.get('secondary_persona'),
                "secondary_persona_name": persona_assignment_data.get('secondary_persona_name'),
                "secondary_persona_percentage": persona_assignment_data.get('secondary_persona_percentage', 0),
                "rationale": persona_assignment_data.get('rationale')
            }
            
            result.append({
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "account_count": account_count or 0,
                "persona": persona_obj
            })
        
        assigner.close()
        return result
    finally:
        session.close()


@app.get("/api/correlation")
def get_correlation_analysis(
    user_id: Optional[str] = Query(None, description="Optional user ID to filter"),
    method: str = Query("pearson", description="Correlation method: pearson, spearman, or kendall"),
    min_correlation: float = Query(0.3, description="Minimum correlation threshold")
):
    """Get correlation analysis for all variables.
    
    Args:
        user_id: Optional user ID to filter
        method: Correlation method (pearson, spearman, kendall)
        min_correlation: Minimum correlation threshold
    
    Returns:
        Correlation analysis results
    """
    from features.correlation import CorrelationAnalyzer
    
    session = get_session()
    try:
        analyzer = CorrelationAnalyzer(session)
        results = analyzer.compute_correlation_matrix(
            user_id=user_id,
            method=method,
            min_correlation=min_correlation
        )
        return results
    finally:
        session.close()


@app.get("/api/spending-patterns/{user_id}/day-of-week")
def get_day_of_week_spending(
    user_id: str,
    window_days: int = Query(180, description="Analysis window in days")
):
    """Get spending patterns by day of week using correlation analysis.
    
    Args:
        user_id: User ID
        window_days: Number of days to analyze
    
    Returns:
        Day-of-week spending patterns and insights
    """
    from features.spending_patterns import SpendingPatternAnalyzer
    from datetime import datetime, timedelta
    
    session = get_session()
    try:
        analyzer = SpendingPatternAnalyzer(session)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=window_days)
        results = analyzer.analyze_day_of_week_spending(user_id, start_date, end_date)
        return results
    finally:
        session.close()


@app.get("/api/spending-patterns/{user_id}/frequent-locations")
def get_frequent_locations(
    user_id: str,
    window_days: int = Query(180, description="Analysis window in days"),
    min_occurrences: int = Query(3, description="Minimum visits to be considered frequent"),
    min_total_spend: float = Query(50.0, description="Minimum total spending at location")
):
    """Get frequent purchase locations (merchants) beyond subscriptions.
    
    Args:
        user_id: User ID
        window_days: Number of days to analyze
        min_occurrences: Minimum number of visits
        min_total_spend: Minimum total spending
    
    Returns:
        Frequent merchant patterns and insights
    """
    from features.spending_patterns import SpendingPatternAnalyzer
    from datetime import datetime, timedelta
    
    session = get_session()
    try:
        analyzer = SpendingPatternAnalyzer(session)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=window_days)
        results = analyzer.detect_frequent_purchase_locations(
            user_id, start_date, end_date, window_days, min_occurrences, min_total_spend
        )
        return results
    finally:
        session.close()


@app.get("/api/correlation/groups")
def get_group_correlations():
    """Get correlation analysis for variable groups.
    
    Returns:
        Group-based correlation analysis
    """
    from features.correlation import CorrelationAnalyzer
    
    session = get_session()
    try:
        analyzer = CorrelationAnalyzer(session)
        results = analyzer.analyze_feature_relationships()
        return results
    finally:
        session.close()


@app.get("/api/profile/{user_id}")
def get_user_profile(
    user_id: str,
    transaction_window: int = Query(30, description="Transaction window in days (30 or 180)")
):
    """Get detailed user profile with accounts and features.
    
    Args:
        user_id: User ID
        transaction_window: Number of days for transaction history (30 or 180)
    """
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get accounts
        accounts = session.query(Account).filter(Account.user_id == user_id).all()
        accounts_data = []
        
        for account in accounts:
            account_dict = {
                "id": account.id,
                "account_id": account.account_id,
                "name": account.name,
                "type": account.type,
                "subtype": account.subtype,
                "current": account.current,
                "available": account.available,
                "limit": account.limit,
                "iso_currency_code": account.iso_currency_code,
            }
            
            # Add credit card specific fields from Account model
            if account.type == "credit":
                if account.amount_due is not None:
                    account_dict["amount_due"] = account.amount_due
                if account.minimum_payment_due is not None:
                    account_dict["minimum_payment_due"] = account.minimum_payment_due
                
                # Get liability details for credit cards
                liability = session.query(Liability).filter(
                    Liability.account_id == account.id,
                    Liability.liability_type == "credit_card"
                ).first()
                
                if liability:
                    account_dict["liability"] = {
                        "apr_type": liability.apr_type,
                        "apr_percentage": liability.apr_percentage,
                        "minimum_payment_amount": liability.minimum_payment_amount,
                        "last_payment_amount": liability.last_payment_amount,
                        "last_payment_date": liability.last_payment_date.isoformat() if liability.last_payment_date else None,
                        "is_overdue": liability.is_overdue,
                        "next_payment_due_date": liability.next_payment_due_date.isoformat() if liability.next_payment_due_date else None,
                        "last_statement_balance": liability.last_statement_balance,
                    }
            
            # Add loan-specific fields if present
            if account.interest_rate is not None:
                account_dict["interest_rate"] = account.interest_rate
            if account.next_payment_due_date:
                account_dict["next_payment_due_date"] = account.next_payment_due_date.isoformat()
            
            accounts_data.append(account_dict)
        
        # Get transactions for all accounts (support both 30 and 180 days)
        from datetime import datetime, timedelta
        # Use query parameter for transaction window
        start_date = datetime.now() - timedelta(days=transaction_window)
        transactions = session.query(Transaction).join(Account).filter(
            and_(
                Account.user_id == user_id,
                Transaction.date >= start_date
            )
        ).order_by(
            Transaction.pending.desc(),  # Pending transactions first (True before False)
            Transaction.date.desc()  # Then by date descending
        ).all()
        
        transactions_data = []
        for tx in transactions:
            transactions_data.append({
                "account_id": tx.account.account_id,  # Use account's 12-digit ID
                "account_type": tx.account.type,  # checking, credit, etc.
                "account_subtype": tx.account.subtype,  # checking, credit_card, etc.
                "account_name": tx.account.name,  # Account name for reference
                "date": tx.date.isoformat(),
                "amount": tx.amount,
                "merchant_name": tx.merchant_name,
                "merchant_entity_id": tx.merchant_entity_id,
                "payment_channel": tx.payment_channel,
                "primary_category": tx.primary_category,
                "detailed_category": tx.detailed_category,
                "pending": tx.pending,
            })
        
        # Get features (30-day and 180-day)
        features_30d = None
        features_180d = None
        
        try:
            pipeline = FeaturePipeline()
            features_30d = pipeline.compute_features_for_user(user_id, 30)
            features_180d = pipeline.compute_features_for_user(user_id, 180)
            pipeline.close()
        except Exception as e:
            print(f"Error computing features: {e}")
            # Features will be None if computation fails
        
        # Get persona/risk analysis
        from personas.assigner import PersonaAssigner
        assigner = PersonaAssigner(session)
        persona_data = assigner.assign_persona(user_id, 180)
        assigner.close()
        
        # Calculate income from payroll transactions over 180 days
        # Use FeaturePipeline's income features which already computed this for features_180d
        income_180d = 0.0
        yearly_income = 0.0
        payroll_count = 0
        use_feature_pipeline_data = False
        
        if features_180d and features_180d.get('income'):
            income_features = features_180d['income']
            # Calculate 180-day total from payroll transactions
            if income_features.get('has_payroll_detected', False):
                avg_income_per_pay = income_features.get('average_income_per_pay', 0.0)
                total_payroll_transactions = income_features.get('total_payroll_transactions', 0)
                
                # Only use FeaturePipeline data if we have valid values
                if avg_income_per_pay > 0 and total_payroll_transactions > 0:
                    payroll_count = total_payroll_transactions
                    # Calculate 180-day total: average per pay * number of pays
                    income_180d = avg_income_per_pay * total_payroll_transactions
                    # Scale to yearly: (180-day income / 180) * 365
                    yearly_income = (income_180d / 180.0) * 365.0
                    use_feature_pipeline_data = True
        
        # Fallback: if FeaturePipeline didn't find payroll OR returned zero/invalid values, try direct query
        if not use_feature_pipeline_data or income_180d == 0.0:
            from features.income import IncomeAnalyzer
            income_analyzer = IncomeAnalyzer(session)
            payroll_start_date = datetime.now() - timedelta(days=180)
            payroll_end_date = datetime.now()
            
            # Use IncomeAnalyzer to detect payroll
            payroll_transactions = income_analyzer.detect_payroll_ach(user_id, payroll_start_date, payroll_end_date)
            
            # If still no payroll, try all depository accounts
            if not payroll_transactions:
                depository_accounts = [acc for acc in accounts if acc.type == 'depository']
                depository_account_ids = [acc.id for acc in depository_accounts]
                
                if depository_account_ids:
                    payroll_tx_objects = session.query(Transaction).filter(
                        and_(
                            Transaction.account_id.in_(depository_account_ids),
                            Transaction.date >= payroll_start_date,
                            Transaction.date <= payroll_end_date,
                            Transaction.amount > 0,
                            or_(
                                Transaction.merchant_name.like("%PAYROLL%"),
                                Transaction.merchant_name.like("%DEPOSIT%"),
                                Transaction.primary_category == "Transfer In"
                            ),
                            Transaction.amount >= 1000
                        )
                    ).all()
                    
                    account_id_map = {acc.id: acc.account_id for acc in depository_accounts}
                    payroll_transactions = [
                        {
                            "date": tx.date,
                            "amount": tx.amount,
                            "account_id": account_id_map.get(tx.account_id, tx.account_id),
                            "transaction_id": tx.transaction_id
                        }
                        for tx in payroll_tx_objects
                    ]
            
            if payroll_transactions:
                payroll_count = len(payroll_transactions)
                income_180d = sum(tx["amount"] for tx in payroll_transactions)
                yearly_income = (income_180d / 180.0) * 365.0
        
        # Build persona object with dual persona support
        persona_obj = {
            "id": persona_data.get("primary_persona"),
            "name": persona_data.get("primary_persona_name"),
            "risk": persona_data.get("primary_persona_risk", 0),
            "risk_level": persona_data.get("risk_level", persona_data.get("primary_persona_risk_level", "VERY_LOW")),
            "total_risk_points": persona_data.get("total_risk_points", 0.0),
            "top_personas": persona_data.get("top_personas", []),
            "all_matching_personas": persona_data.get("all_matching_personas", []),
            "primary_persona": persona_data.get("primary_persona"),
            "primary_persona_name": persona_data.get("primary_persona_name"),
            "primary_persona_percentage": persona_data.get("primary_persona_percentage", 100),
            "secondary_persona": persona_data.get("secondary_persona"),
            "secondary_persona_name": persona_data.get("secondary_persona_name"),
            "secondary_persona_percentage": persona_data.get("secondary_persona_percentage", 0),
            "rationale": persona_data.get("rationale"),
            "all_matched_personas": persona_data.get("assigned_personas", []),
            "decision_trace": persona_data.get("decision_trace", {})
        }
        
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "accounts": accounts_data,
            "transactions": transactions_data,
            "features_30d": features_30d,
            "features_180d": features_180d,
            "persona": persona_obj,
            "income": {
                "180_day_total": round(income_180d, 2),
                "yearly_estimated": round(yearly_income, 2),
                "payroll_count_180d": payroll_count
            }
        }
    finally:
        session.close()


@app.get("/api/features/parquet")
def get_features_from_parquet(
    window_days: int = Query(30, description="Time window in days (30 or 180)")
):
    """Get all features from Parquet files (faster than computing on-the-fly).
    
    Args:
        window_days: Time window in days (30 or 180)
    
    Returns:
        All user features from Parquet file
    """
    import polars as pl
    from pathlib import Path
    
    parquet_path = Path("data/features") / f"features_{window_days}d.parquet"
    
    if not parquet_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Parquet file not found for {window_days}-day window. Run feature computation first."
        )
    
    try:
        df = pl.read_parquet(parquet_path)
        # Convert to dict format for JSON response
        return {
            "window_days": window_days,
            "total_users": len(df),
            "features": df.to_dicts()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading Parquet file: {str(e)}"
        )


@app.get("/api/insights/{user_id}/weekly-recap")
def get_weekly_recap(
    user_id: str,
    week_start: Optional[str] = Query(None, description="Week start date (YYYY-MM-DD), defaults to current week")
):
    """Get weekly spending recap for a user.
    
    Args:
        user_id: User ID
        week_start: Week start date (YYYY-MM-DD), defaults to current week's Monday
    
    Returns:
        Weekly recap data with daily breakdown and insights
    """
    from insights.weekly_recap import WeeklyRecapAnalyzer
    from datetime import datetime
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Parse week_start if provided
        week_start_date = None
        if week_start:
            try:
                week_start_date = datetime.fromisoformat(week_start)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        analyzer = WeeklyRecapAnalyzer(session)
        recap = analyzer.compute_weekly_recap(user_id, week_start_date)
        
        return recap
    finally:
        session.close()


@app.get("/api/insights/{user_id}/spending-analysis")
def get_spending_analysis(
    user_id: str,
    months: int = Query(6, description="Number of months to analyze (default 6)")
):
    """Get 6-month spending analysis for a user.
    
    Args:
        user_id: User ID
        months: Number of months to analyze (default 6)
    
    Returns:
        6-month spending analysis with monthly breakdown and insights
    """
    from insights.spending_analysis import SpendingAnalysisAnalyzer
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if months < 1 or months > 12:
            raise HTTPException(status_code=400, detail="Months must be between 1 and 12")
        
        analyzer = SpendingAnalysisAnalyzer(session)
        analysis = analyzer.compute_spending_analysis(user_id, months)
        
        return analysis
    finally:
        session.close()


@app.get("/api/insights/{user_id}/suggested-budget")
def get_suggested_budget(
    user_id: str,
    month: Optional[str] = Query(None, description="Month in YYYY-MM format (defaults to next month)"),
    lookback_months: int = Query(6, description="Number of months to analyze (default 6)")
):
    """Get AI-suggested monthly budget for a user.
    
    Args:
        user_id: User ID
        month: Month in YYYY-MM format (defaults to next month)
        lookback_months: Number of months to analyze for suggestions
    
    Returns:
        Suggested budget with category breakdown
    """
    from insights.budget_calculator import BudgetCalculator
    from datetime import datetime
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        month_date = None
        if month:
            try:
                month_date = datetime.strptime(month, "%Y-%m")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")
        
        calculator = BudgetCalculator(session)
        budget = calculator.suggest_budget(user_id, month_date, lookback_months)
        
        # Calculate budget constraints
        # Min: Minimum spending over last 3 months
        # Max: Available funds (income or account balance)
        from datetime import timedelta
        from ingest.schema import Account, Transaction
        from sqlalchemy import and_
        
        # Get last 3 months of spending
        three_months_ago = datetime.now() - timedelta(days=90)
        accounts = session.query(Account).filter(Account.user_id == user_id).all()
        account_ids = [acc.id for acc in accounts]
        
        min_spending = 0.0
        max_budget = 0.0
        
        if account_ids:
            # Get monthly spending for last 3 months
            monthly_spending = []
            for i in range(3):
                month_start = (datetime.now() - timedelta(days=30 * (i + 1))).replace(day=1)
                if month_start.month == 12:
                    month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)
                
                transactions = session.query(Transaction).filter(
                    and_(
                        Transaction.account_id.in_(account_ids),
                        Transaction.date >= month_start,
                        Transaction.date <= month_end,
                        Transaction.amount < 0  # Only expenses
                    )
                ).all()
                
                month_total = sum(abs(tx.amount) for tx in transactions)
                monthly_spending.append(month_total)
            
            # Minimum spending is the lowest month
            min_spending = min(monthly_spending) if monthly_spending else 0.0
            
        # CRITICAL: Budget is based ONLY on payroll transactions (80% of monthly average from income analysis)
        # Calculate monthly average from 180-day payroll: (180-day total / 180) * 365 / 12
        # This matches the "Monthly Average" shown in the Income Analysis card
        # Budget is 80% of the monthly average
        depository_accounts = [acc for acc in accounts if acc.type == 'depository']
        depository_account_ids = [acc.id for acc in depository_accounts]
        
        monthly_income = 0.0
        if depository_account_ids:
            # Get payroll transactions using flexible pattern matching (same as IncomeAnalyzer)
            # This matches transactions with "PAYROLL" or "DEPOSIT" in merchant name, or "Transfer In" category
            payroll_start_date = datetime.now() - timedelta(days=180)
            payroll_transactions = session.query(Transaction).filter(
                and_(
                    Transaction.account_id.in_(depository_account_ids),
                    Transaction.date >= payroll_start_date,
                    Transaction.amount > 0,  # Only positive amounts (deposits)
                    or_(
                        Transaction.merchant_name.like("%PAYROLL%"),
                        Transaction.merchant_name.like("%DEPOSIT%"),
                        Transaction.primary_category == "Transfer In"
                    ),
                    Transaction.amount >= 1000  # Reasonable minimum for payroll
                )
            ).all()
            
            # Calculate monthly average from payroll (same as income analysis)
            # Formula: (180-day payroll total / 180) * 365 / 12
            if payroll_transactions:
                income_180d = sum(tx.amount for tx in payroll_transactions)
                yearly_income = (income_180d / 180.0) * 365.0
                monthly_income = yearly_income / 12.0
        
        # Fallback to FeaturePipeline if no transaction-based income found
        if monthly_income <= 0:
            from features.pipeline import FeaturePipeline
            import os
            db_path = os.environ.get('DATABASE_PATH', 'data/spendsense.db')
            feature_pipeline = FeaturePipeline(db_path)
            features = feature_pipeline.compute_features_for_user(user_id, 90)
            income_features = features.get('income', {})
            avg_income_per_pay = income_features.get('average_income_per_pay', 0.0)
            frequency = income_features.get('payment_frequency', {}).get('frequency', 'monthly')
            if avg_income_per_pay > 0:
                if frequency == 'weekly':
                    monthly_income = avg_income_per_pay * 4.33
                elif frequency == 'biweekly':
                    monthly_income = avg_income_per_pay * 2.17
                elif frequency == 'monthly':
                    monthly_income = avg_income_per_pay
                else:
                    monthly_income = income_features.get('minimum_monthly_income', 0.0)
            else:
                monthly_income = income_features.get('minimum_monthly_income', 0.0)
        
        # Max budget is 100% of monthly income (monthly average from payroll)
        # Users can set up to 100% of monthly income, but validation will prevent exceeding it
        max_budget = monthly_income if monthly_income > 0 else 0.0
        
        # Add constraints to budget response
        budget['min_budget'] = min_spending
        budget['max_budget'] = max_budget
        budget['monthly_income'] = monthly_income  # Include for frontend display
        
        return budget
    finally:
        session.close()


@app.get("/api/insights/{user_id}/budget-history")
def get_budget_history(
    user_id: str,
    months: int = Query(6, description="Number of months to retrieve (default 6)")
):
    """Get budget history for a user (for charting).
    
    Args:
        user_id: User ID
        months: Number of months to retrieve
    
    Returns:
        Budget history data with monthly spending and income
    """
    from insights.budget_calculator import BudgetCalculator
    from datetime import datetime, timedelta
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        calculator = BudgetCalculator(session)
        history = []
        
        # Get historical data for each month
        end_date = datetime.now()
        for i in range(months):
            month_date = end_date - timedelta(days=30 * i)
            month_key = month_date.strftime("%Y-%m")
            
            # Calculate spending and income for this month
            from ingest.schema import Account, Transaction
            from sqlalchemy import and_
            
            accounts = session.query(Account).filter(Account.user_id == user_id).all()
            account_ids = [acc.id for acc in accounts]
            
            if account_ids:
                month_start = month_date.replace(day=1)
                if month_date.month == 12:
                    month_end = month_date.replace(year=month_date.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    month_end = month_date.replace(month=month_date.month + 1, day=1) - timedelta(days=1)
                
                transactions = session.query(Transaction).filter(
                    and_(
                        Transaction.account_id.in_(account_ids),
                        Transaction.date >= month_start,
                        Transaction.date <= month_end
                    )
                ).all()
                
                total_spending = abs(sum(tx.amount for tx in transactions if tx.amount < 0))
                total_income = sum(tx.amount for tx in transactions if tx.amount > 0)
                
                history.append({
                    "month": month_key,
                    "total_spending": total_spending,
                    "total_income": total_income,
                    "net_flow": total_income - total_spending
                })
        
        history.reverse()  # Oldest first
        return {"history": history}
    finally:
        session.close()


@app.post("/api/insights/{user_id}/budget")
def set_user_budget(
    user_id: str,
    amount: float = Body(...),
    month: str = Body(...)
):
    """Set a user's monthly budget.
    
    Args:
        user_id: User ID
        amount: Budget amount
        month: Month in YYYY-MM format
    
    Returns:
        Confirmation of saved budget
    """
    from ingest.schema import Budget
    from datetime import datetime
    import uuid
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Parse month
        try:
            month_date = datetime.strptime(month, "%Y-%m")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")
        
        # Calculate period start and end
        period_start = month_date.replace(day=1)
        if month_date.month == 12:
            period_end = month_date.replace(year=month_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            period_end = month_date.replace(month=month_date.month + 1, day=1) - timedelta(days=1)
        
        # CRITICAL: Budget is based ONLY on payroll transactions (80% of monthly average from income analysis)
        # Calculate monthly average from 180-day payroll: (180-day total / 180) * 365 / 12
        # This matches the "Monthly Average" shown in the Income Analysis card
        # Budget is 80% of the monthly average
        accounts = session.query(Account).filter(Account.user_id == user_id).all()
        depository_accounts = [acc for acc in accounts if acc.type == 'depository']
        depository_account_ids = [acc.id for acc in depository_accounts]
        
        monthly_income = 0.0
        if depository_account_ids:
            # Get payroll transactions using flexible pattern matching (same as IncomeAnalyzer)
            # This matches transactions with "PAYROLL" or "DEPOSIT" in merchant name, or "Transfer In" category
            payroll_start_date = datetime.now() - timedelta(days=180)
            payroll_transactions = session.query(Transaction).filter(
                and_(
                    Transaction.account_id.in_(depository_account_ids),
                    Transaction.date >= payroll_start_date,
                    Transaction.amount > 0,  # Only positive amounts (deposits)
                    or_(
                        Transaction.merchant_name.like("%PAYROLL%"),
                        Transaction.merchant_name.like("%DEPOSIT%"),
                        Transaction.primary_category == "Transfer In"
                    ),
                    Transaction.amount >= 1000  # Reasonable minimum for payroll
                )
            ).all()
            
            # Calculate monthly average from payroll (same as income analysis)
            # Formula: (180-day payroll total / 180) * 365 / 12
            if payroll_transactions:
                income_180d = sum(tx.amount for tx in payroll_transactions)
                yearly_income = (income_180d / 180.0) * 365.0
                monthly_income = yearly_income / 12.0
        
        # Fallback to FeaturePipeline if no transaction-based income found
        if monthly_income <= 0:
            from features.pipeline import FeaturePipeline
            import os
            db_path = os.environ.get('DATABASE_PATH', 'data/spendsense.db')
            feature_pipeline = FeaturePipeline(db_path)
            features = feature_pipeline.compute_features_for_user(user_id, 90)
            income_features = features.get('income', {})
            avg_income_per_pay = income_features.get('average_income_per_pay', 0.0)
            frequency = income_features.get('payment_frequency', {}).get('frequency', 'monthly')
            if avg_income_per_pay > 0:
                if frequency == 'weekly':
                    monthly_income = avg_income_per_pay * 4.33
                elif frequency == 'biweekly':
                    monthly_income = avg_income_per_pay * 2.17
                elif frequency == 'monthly':
                    monthly_income = avg_income_per_pay
                else:
                    monthly_income = income_features.get('minimum_monthly_income', 0.0)
            else:
                monthly_income = income_features.get('minimum_monthly_income', 0.0)
        
        # Validate: Budget cannot exceed monthly income (100% of monthly average)
        # Calculate available funds (checking + savings) for months-until-zero calculation
        depository_accounts = [acc for acc in accounts if acc.type == 'depository']
        available_funds = sum(acc.available or acc.current or 0 for acc in depository_accounts)
        
        # Check if budget exceeds monthly income
        if monthly_income > 0 and amount > monthly_income:
            # Calculate monthly deficit
            monthly_deficit = amount - monthly_income
            
            # Calculate months until funds run out
            months_until_zero = 0
            if monthly_deficit > 0 and available_funds > 0:
                months_until_zero = available_funds / monthly_deficit
            elif monthly_deficit > 0:
                months_until_zero = 0  # Already out of money
            
            # Round to 1 decimal place, but show at least 1 month if it's less
            months_until_zero = max(1, round(months_until_zero, 1))
            
            # Return error with specific messages
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "This budget is projected to exceed your predicted monthly income",
                    "message": f"If you proceed with this budget you will have $0 in {months_until_zero:.1f} months",
                    "monthly_income": monthly_income,
                    "requested_budget": amount,
                    "monthly_deficit": monthly_deficit,
                    "available_funds": available_funds,
                    "months_until_zero": months_until_zero
                }
            )
        
        # Suggested budget is 80% of monthly income, but user can set up to 100%
        # No need to cap here - we just validate it doesn't exceed 100%
        
        # Check if budget already exists for this month
        existing_budget = session.query(Budget).filter(
            and_(
                Budget.user_id == user_id,
                Budget.category.is_(None),  # Overall budget
                Budget.period_start == period_start,
                Budget.period_end == period_end
            )
        ).first()
        
        if existing_budget:
            # Update existing budget
            existing_budget.amount = amount
            existing_budget.updated_at = datetime.now()
        else:
            # Create new budget
            budget = Budget(
                id=str(uuid.uuid4()),
                user_id=user_id,
                category=None,  # Overall budget
                amount=amount,
                period_start=period_start,
                period_end=period_end,
                is_suggested=False,  # User-defined
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            session.add(budget)
        
        session.commit()
        
        return {
            "user_id": user_id,
            "month": month,
            "amount": amount,
            "message": "Budget saved successfully"
        }
    finally:
        session.close()


@app.post("/api/insights/{user_id}/generate-budget")
def generate_budget(
    user_id: str,
    month: Optional[str] = Query(None, description="Month in YYYY-MM format (defaults to current month)")
):
    """Generate and save a suggested budget for a user based on their financial data.
    
    Args:
        user_id: User ID
        month: Month in YYYY-MM format (defaults to current month)
    
    Returns:
        Generated budget with category breakdown
    """
    from insights.budget_calculator import BudgetCalculator
    from ingest.schema import Budget
    from datetime import datetime, timedelta
    import uuid
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Parse month or use current month
        if month:
            try:
                month_date = datetime.strptime(month, "%Y-%m")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")
        else:
            month_date = datetime.now().replace(day=1)
        
        # Calculate period
        period_start = month_date.replace(day=1)
        if month_date.month == 12:
            period_end = month_date.replace(year=month_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            period_end = month_date.replace(month=month_date.month + 1, day=1) - timedelta(days=1)
        
        # Generate suggested budget
        calculator = BudgetCalculator(session)
        suggested_budget = calculator.suggest_budget(user_id, month_date, lookback_months=6)
        
        # CRITICAL: Ensure total_budget is 80% of monthly average income
        # Calculate monthly income to validate and cap if needed
        accounts = session.query(Account).filter(Account.user_id == user_id).all()
        depository_accounts = [acc for acc in accounts if acc.type == 'depository']
        depository_account_ids = [acc.id for acc in depository_accounts]
        
        monthly_income = 0.0
        if depository_account_ids:
            payroll_start_date = datetime.now() - timedelta(days=180)
            payroll_transactions = session.query(Transaction).filter(
                and_(
                    Transaction.account_id.in_(depository_account_ids),
                    Transaction.date >= payroll_start_date,
                    Transaction.amount > 0,
                    or_(
                        Transaction.merchant_name.like("%PAYROLL%"),
                        Transaction.merchant_name.like("%DEPOSIT%"),
                        Transaction.primary_category == "Transfer In"
                    ),
                    Transaction.amount >= 1000
                )
            ).all()
            
            if payroll_transactions:
                income_180d = sum(tx.amount for tx in payroll_transactions)
                yearly_income = (income_180d / 180.0) * 365.0
                monthly_income = yearly_income / 12.0
        
        # Cap total_budget at 80% of monthly_income (budget is 80% of monthly average)
        if monthly_income > 0:
            max_budget = monthly_income * 0.80
            if suggested_budget['total_budget'] > max_budget:
                # Scale down category budgets proportionally
                scale_factor = max_budget / suggested_budget['total_budget']
                suggested_budget['total_budget'] = max_budget
                if suggested_budget.get('category_budgets'):
                    for category in suggested_budget['category_budgets']:
                        suggested_budget['category_budgets'][category] *= scale_factor
        
        # Check if budget already exists for this month
        existing_budget = session.query(Budget).filter(
            and_(
                Budget.user_id == user_id,
                Budget.category.is_(None),  # Overall budget
                Budget.period_start == period_start,
                Budget.period_end == period_end
            )
        ).first()
        
        # Store overall budget
        if existing_budget:
            existing_budget.amount = suggested_budget['total_budget']
            existing_budget.updated_at = datetime.now()
            overall_budget_id = existing_budget.id
        else:
            overall_budget_id = str(uuid.uuid4())
            overall_budget = Budget(
                id=overall_budget_id,
                user_id=user_id,
                category=None,
                amount=suggested_budget['total_budget'],
                period_start=period_start,
                period_end=period_end,
                is_suggested=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            session.add(overall_budget)
        
        # Delete existing category budgets for this month
        session.query(Budget).filter(
            and_(
                Budget.user_id == user_id,
                Budget.category.isnot(None),
                Budget.period_start == period_start,
                Budget.period_end == period_end
            )
        ).delete()
        
        # Store category budgets (including 20% for savings or debt repayment)
        category_budget_ids = []
        for category, amount in suggested_budget.get('category_budgets', {}).items():
            cat_budget_id = str(uuid.uuid4())
            cat_budget = Budget(
                id=cat_budget_id,
                user_id=user_id,
                category=category,
                amount=amount,
                period_start=period_start,
                period_end=period_end,
                is_suggested=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            session.add(cat_budget)
            category_budget_ids.append(cat_budget_id)
        
        session.commit()
        
        return {
            "user_id": user_id,
            "month": month_date.strftime("%Y-%m"),
            "total_budget": suggested_budget['total_budget'],
            "category_budgets": suggested_budget.get('category_budgets', {}),
            "rationale": suggested_budget.get('rationale', ''),
            "budget_id": overall_budget_id,
            "category_budget_ids": category_budget_ids,
            "message": "Budget generated and saved successfully"
        }
    finally:
        session.close()


@app.get("/api/insights/{user_id}/budget-tracking")
def get_budget_tracking(
    user_id: str,
    month: Optional[str] = Query(None, description="Month in YYYY-MM format (defaults to current month)")
):
    """Get budget tracking status for a user.
    
    Args:
        user_id: User ID
        month: Month in YYYY-MM format (defaults to current month)
    
    Returns:
        Budget tracking data with budget vs actual spending
    """
    from insights.budget_tracker import BudgetTracker
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        tracker = BudgetTracker(session)
        tracking = tracker.track_budget(user_id, month)
        
        return tracking
    finally:
        session.close()


@app.get("/api/insights/{user_id}/net-worth")
def get_net_worth(
    user_id: str,
    period: str = Query("month", description="Period: week or month")
):
    """Get current net worth for a user.
    
    Args:
        user_id: User ID
        period: Period for historical data (week or month)
    
    Returns:
        Current net worth and historical data
    """
    from insights.net_worth_tracker import NetWorthTracker
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        tracker = NetWorthTracker(session)
        
        # Get current net worth
        current = tracker.calculate_net_worth(user_id)
        
        # Get historical data
        history = tracker.get_net_worth_history(user_id, period=period)
        
        return {
            "current": current,
            "history": history
        }
    finally:
        session.close()


@app.get("/api/insights/{user_id}/net-worth-history")
def get_net_worth_history(
    user_id: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    period: str = Query("month", description="Period: week or month")
):
    """Get historical net worth data for a user.
    
    Args:
        user_id: User ID
        start_date: Start date (YYYY-MM-DD, defaults to 6 months ago)
        end_date: End date (YYYY-MM-DD, defaults to now)
        period: Aggregation period (week, month)
    
    Returns:
        Historical net worth snapshots
    """
    from insights.net_worth_tracker import NetWorthTracker
    from datetime import datetime
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        start = None
        end = None
        
        if start_date:
            try:
                start = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
        
        if end_date:
            try:
                end = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")
        
        tracker = NetWorthTracker(session)
        history = tracker.get_net_worth_history(user_id, start, end, period)
        
        return history
    finally:
        session.close()


@app.get("/api/personas/{user_id}")
def get_user_persona(
    user_id: str,
    window_days: int = Query(180, description="Time window in days for feature computation (default 180)")
):
    """Get persona assignment for a user.
    
    Args:
        user_id: User ID
        window_days: Time window for feature computation (30 or 180)
    
    Returns:
        Persona assignment with rationale and decision trace
    """
    from personas.assigner import PersonaAssigner
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if window_days not in [30, 180]:
            raise HTTPException(status_code=400, detail="window_days must be 30 or 180")
        
        assigner = PersonaAssigner(session)
        assignment = assigner.assign_persona(user_id, window_days)
        assigner.close()
        
        return assignment
    finally:
        session.close()


@app.get("/api/personas")
def get_all_personas(
    window_days: int = Query(180, description="Time window in days for feature computation (default 180)")
):
    """Get persona assignments for all users.
    
    Args:
        window_days: Time window for feature computation (30 or 180)
    
    Returns:
        List of persona assignments for all users
    """
    from personas.assigner import PersonaAssigner
    
    session = get_session()
    try:
        if window_days not in [30, 180]:
            raise HTTPException(status_code=400, detail="window_days must be 30 or 180")
        
        assigner = PersonaAssigner(session)
        assignments = assigner.assign_all_users(window_days)
        assigner.close()
        
        return {
            "total_users": len(assignments),
            "assignments": assignments
        }
    finally:
        session.close()


# More specific routes must come BEFORE the general route to avoid route conflicts
@app.post("/api/recommendations/generate/{user_id}")
def generate_persona_recommendations(
    user_id: str,
    window_days: int = Query(180, description="Time window for feature computation (default 180)"),
    num_recommendations: int = Query(8, description="Number of recommendations to generate (default 8)")
):
    """Generate persona-based recommendations for a user and store them in the database.
    
    Args:
        user_id: User ID
        window_days: Time window for feature computation (30 or 180)
        num_recommendations: Number of recommendations to generate
    
    Returns:
        Dictionary with generated recommendations count
    """
    from recommend.persona_recommendation_generator import PersonaRecommendationGenerator
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if window_days not in [30, 180]:
            raise HTTPException(status_code=400, detail="window_days must be 30 or 180")
        
        generator = PersonaRecommendationGenerator(session)
        try:
            recommendations = generator.generate_and_store_recommendations(
                user_id,
                window_days,
                num_recommendations
            )
            return {
                "user_id": user_id,
                "generated_count": len(recommendations),
                "recommendations": recommendations,
                "message": f"Generated {len(recommendations)} recommendations (pending admin approval)"
            }
        finally:
            generator.close()
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error generating recommendations: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")
    finally:
        session.close()


@app.get("/api/user/{user_id}/subscriptions")
def get_user_subscriptions(user_id: str):
    """Get user's active subscriptions/recurring merchants.
    
    Args:
        user_id: User ID
    
    Returns:
        List of recurring subscriptions with details
    """
    from features.subscriptions import SubscriptionDetector
    from datetime import datetime, timedelta
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get subscriptions from last 180 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        detector = SubscriptionDetector(session)
        recurring_merchants = detector.detect_recurring_merchants(user_id, start_date, end_date)
        
        # Additional filtering: exclude any merchants that might be loans (double-check)
        loan_keywords = ['mortgage', 'student loan', 'studentloan', 'loan payment', 'loan servicer']
        
        subscriptions = []
        for merchant in recurring_merchants:
            merchant_lower = merchant["merchant_name"].lower()
            # Skip if it's clearly a loan (already filtered in detector, but double-check)
            if any(keyword in merchant_lower for keyword in loan_keywords):
                continue
            
            subscriptions.append({
                "merchant_name": merchant["merchant_name"],
                "average_amount": merchant["average_amount"],
                "cadence": merchant["cadence"],
                "occurrences": merchant["occurrences"],
                "last_transaction": merchant["last_transaction"].isoformat() if merchant.get("last_transaction") else None,
                "first_transaction": merchant["first_transaction"].isoformat() if merchant.get("first_transaction") else None,
            })
        
        # Get cancelled subscriptions for this user
        cancelled_subs = session.query(CancelledSubscription).filter(
            CancelledSubscription.user_id == user_id
        ).all()
        cancelled_merchant_names = {sub.merchant_name for sub in cancelled_subs}
        
        # Mark which subscriptions are cancelled
        for sub in subscriptions:
            sub["cancelled"] = sub["merchant_name"] in cancelled_merchant_names
        
        return {
            "user_id": user_id,
            "subscriptions": subscriptions,
            "total": len(subscriptions),
            "cancelled_count": len(cancelled_merchant_names)
        }
    finally:
        session.close()


@app.post("/api/user/{user_id}/subscriptions/cancel")
async def cancel_subscription(user_id: str, request: Dict[str, Any] = Body(...)):
    """Cancel a subscription for a user.
    
    Args:
        user_id: User ID
        request: Request body containing merchant_name
    
    Returns:
        Cancellation confirmation
    """
    from datetime import datetime
    import uuid
    
    merchant_name = request.get("merchant_name")
    if not merchant_name:
        raise HTTPException(status_code=400, detail="merchant_name is required")
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if already cancelled
        existing = session.query(CancelledSubscription).filter(
            and_(
                CancelledSubscription.user_id == user_id,
                CancelledSubscription.merchant_name == merchant_name
            )
        ).first()
        
        if existing:
            return {
                "user_id": user_id,
                "merchant_name": merchant_name,
                "cancelled": True,
                "cancelled_at": existing.cancelled_at.isoformat(),
                "message": "Subscription already cancelled"
            }
        
        # Create cancellation record
        cancelled_sub = CancelledSubscription(
            id=str(uuid.uuid4()),
            user_id=user_id,
            merchant_name=merchant_name,
            cancelled_at=datetime.now()
        )
        session.add(cancelled_sub)
        session.commit()
        
        # Broadcast cancellation via WebSocket
        from api.websocket import manager
        await manager.broadcast_subscription_cancellation(
            user_id=user_id,
            merchant_name=merchant_name,
            cancelled=True
        )
        
        return {
            "user_id": user_id,
            "merchant_name": merchant_name,
            "cancelled": True,
            "cancelled_at": cancelled_sub.cancelled_at.isoformat(),
            "message": "Subscription cancelled successfully"
        }
    finally:
        session.close()


@app.post("/api/user/{user_id}/subscriptions/uncancel")
async def uncancel_subscription(user_id: str, request: Dict[str, Any] = Body(...)):
    """Uncancel a subscription for a user (restore it).
    
    Args:
        user_id: User ID
        request: Request body containing merchant_name
    
    Returns:
        Uncancel confirmation
    """
    merchant_name = request.get("merchant_name")
    if not merchant_name:
        raise HTTPException(status_code=400, detail="merchant_name is required")
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Find and delete cancellation record
        cancelled_sub = session.query(CancelledSubscription).filter(
            and_(
                CancelledSubscription.user_id == user_id,
                CancelledSubscription.merchant_name == merchant_name
            )
        ).first()
        
        if not cancelled_sub:
            return {
                "user_id": user_id,
                "merchant_name": merchant_name,
                "cancelled": False,
                "message": "Subscription was not cancelled"
            }
        
        session.delete(cancelled_sub)
        session.commit()
        
        # Broadcast uncancellation via WebSocket
        from api.websocket import manager
        await manager.broadcast_subscription_cancellation(
            user_id=user_id,
            merchant_name=merchant_name,
            cancelled=False
        )
        
        return {
            "user_id": user_id,
            "merchant_name": merchant_name,
            "cancelled": False,
            "message": "Subscription uncancelled successfully"
        }
    finally:
        session.close()


@app.get("/api/user/{user_id}/action-plans/{recommendation_id}")
def get_approved_action_plan(user_id: str, recommendation_id: str):
    """Get approved action plan for a recommendation.
    
    Args:
        user_id: User ID
        recommendation_id: Recommendation ID
    
    Returns:
        Approved action plan data or 404 if not approved
    """
    from sqlalchemy import and_
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        approved_plan = session.query(ApprovedActionPlan).filter(
            and_(
                ApprovedActionPlan.user_id == user_id,
                ApprovedActionPlan.recommendation_id == recommendation_id,
                ApprovedActionPlan.status == 'active'
            )
        ).first()
        
        if not approved_plan:
            raise HTTPException(status_code=404, detail="Action plan not approved")
        
        return {
            "id": approved_plan.id,
            "user_id": approved_plan.user_id,
            "recommendation_id": approved_plan.recommendation_id,
            "approved_at": approved_plan.approved_at.isoformat(),
            "status": approved_plan.status,
            "created_at": approved_plan.created_at.isoformat()
        }
    finally:
        session.close()


@app.post("/api/user/{user_id}/action-plans/approve")
async def approve_action_plan(user_id: str, request: Dict[str, Any] = Body(...)):
    """Approve an action plan for a recommendation.
    
    Args:
        user_id: User ID
        request: Request body containing recommendation_id
    
    Returns:
        Approval confirmation
    """
    from datetime import datetime
    import uuid
    from sqlalchemy import and_
    
    recommendation_id = request.get("recommendation_id")
    if not recommendation_id:
        raise HTTPException(status_code=400, detail="recommendation_id is required")
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if recommendation exists and is approved by admin
        recommendation = session.query(Recommendation).filter(
            and_(
                Recommendation.id == recommendation_id,
                Recommendation.user_id == user_id,
                Recommendation.approved == True
            )
        ).first()
        
        if not recommendation:
            raise HTTPException(status_code=404, detail="Recommendation not found or not approved")
        
        # Check if already approved
        existing = session.query(ApprovedActionPlan).filter(
            and_(
                ApprovedActionPlan.user_id == user_id,
                ApprovedActionPlan.recommendation_id == recommendation_id,
                ApprovedActionPlan.status == 'active'
            )
        ).first()
        
        if existing:
            return {
                "user_id": user_id,
                "recommendation_id": recommendation_id,
                "approved": True,
                "approved_at": existing.approved_at.isoformat(),
                "message": "Action plan already approved"
            }
        
        # Create approval record
        approved_plan = ApprovedActionPlan(
            id=str(uuid.uuid4()),
            user_id=user_id,
            recommendation_id=recommendation_id,
            approved_at=datetime.now(),
            status='active'
        )
        session.add(approved_plan)
        session.commit()
        
        return {
            "user_id": user_id,
            "recommendation_id": recommendation_id,
            "approved": True,
            "approved_at": approved_plan.approved_at.isoformat(),
            "message": "Action plan approved successfully"
        }
    finally:
        session.close()


@app.post("/api/user/{user_id}/action-plans/{recommendation_id}/cancel")
async def cancel_action_plan(user_id: str, recommendation_id: str):
    """Cancel an approved action plan.
    
    Args:
        user_id: User ID
        recommendation_id: Recommendation ID
    
    Returns:
        Cancellation confirmation
    """
    from datetime import datetime
    from sqlalchemy import and_
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        approved_plan = session.query(ApprovedActionPlan).filter(
            and_(
                ApprovedActionPlan.user_id == user_id,
                ApprovedActionPlan.recommendation_id == recommendation_id,
                ApprovedActionPlan.status == 'active'
            )
        ).first()
        
        if not approved_plan:
            raise HTTPException(status_code=404, detail="Active action plan not found")
        
        approved_plan.status = 'cancelled'
        approved_plan.updated_at = datetime.now()
        session.commit()
        
        return {
            "user_id": user_id,
            "recommendation_id": recommendation_id,
            "cancelled": True,
            "message": "Action plan cancelled successfully"
        }
    finally:
        session.close()


@app.get("/api/user/{user_id}/subscriptions/cancelled")
def get_cancelled_subscriptions(user_id: str):
    """Get list of cancelled subscriptions for a user.
    
    Args:
        user_id: User ID
    
    Returns:
        List of cancelled merchant names
    """
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        cancelled_subs = session.query(CancelledSubscription).filter(
            CancelledSubscription.user_id == user_id
        ).all()
        
        return {
            "user_id": user_id,
            "cancelled_merchants": [
                {
                    "merchant_name": sub.merchant_name,
                    "cancelled_at": sub.cancelled_at.isoformat()
                }
                for sub in cancelled_subs
            ],
            "total": len(cancelled_subs)
        }
    finally:
        session.close()


@app.post("/api/budgets/generate-all")
def generate_budgets_for_all_users():
    """Generate budgets for all users (for testing purposes).
    
    This endpoint will generate RAG-based budgets for all users in the system.
    Budgets are capped at 90% of monthly income.
    
    Returns:
        Dictionary with generation results
    """
    from recommend.budget_generator import RAGBudgetGenerator
    from datetime import datetime, timedelta
    from ingest.schema import Budget
    from sqlalchemy import and_
    import os
    
    session = get_session()
    try:
        users = session.query(User).all()
        db_path = os.environ.get("DATABASE_PATH", "data/spendsense.db")
        generator = RAGBudgetGenerator(db_path=db_path)
        
        results = {
            "total_users": len(users),
            "generated": 0,
            "skipped": 0,
            "failed": 0,
            "errors": []
        }
        
        current_month = datetime.now().strftime("%Y-%m")
        month_start = datetime.now().replace(day=1)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)
        
        for user in users:
            try:
                # Check if budget already exists for current month
                existing = session.query(Budget).filter(
                    and_(
                        Budget.user_id == user.id,
                        Budget.category.is_(None),
                        Budget.period_start <= month_end,
                        Budget.period_end >= month_start
                    )
                ).first()
                
                if not existing:
                    generator.generate_user_budget(session, user.id, current_month)
                    results["generated"] += 1
                else:
                    results["skipped"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "user_id": user.id,
                    "error": str(e)
                })
        
        session.commit()
        
        return results
    finally:
        session.close()


@app.post("/api/operator/recommendations/generate-custom")
def generate_custom_recommendation(request: Dict[str, Any] = Body(...)):
    """Generate a custom recommendation from an admin prompt using RAG.
    
    Request body:
        - user_id: User ID
        - admin_prompt: Admin's prompt describing what recommendation to create
        - context_data: Optional context data (e.g., {"category": "streaming", "subscriptions": ["YouTube Premium", "HBO Max", "Spotify"]})
        - window_days: Optional time window for feature computation (default 180)
    
    Returns:
        Generated recommendation dictionary ready for review
    """
    from recommend.custom_recommendation_generator import CustomRecommendationGenerator
    import os
    
    user_id = request.get('user_id')
    admin_prompt = request.get('admin_prompt')
    context_data = request.get('context_data')
    window_days = request.get('window_days', 180)
    
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    if not admin_prompt:
        raise HTTPException(status_code=400, detail="admin_prompt is required")
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        db_path = os.environ.get("DATABASE_PATH", "data/spendsense.db")
        generator = CustomRecommendationGenerator(db_path=db_path)
        
        recommendation_type = request.get('recommendation_type', 'actionable_recommendation')
        
        recommendation = generator.generate_from_prompt(
            user_id=user_id,
            admin_prompt=admin_prompt,
            context_data=context_data,
            window_days=window_days,
            recommendation_type=recommendation_type
        )
        
        # Store the recommendation in the database
        from ingest.schema import Recommendation
        import uuid
        
        rec_id = recommendation.get('id', str(uuid.uuid4()))
        rec = Recommendation(
            id=rec_id,
            user_id=user_id,
            recommendation_type=recommendation_type,
            title=recommendation.get('title', 'Custom Recommendation'),
            description=recommendation.get('recommendation_text', '') or recommendation.get('description', ''),
            rationale=recommendation.get('rationale', 'Generated from admin prompt'),
            content_id='admin_custom',
            persona_id='admin_custom',
            action_items=recommendation.get('action_items', []),
            expected_impact=recommendation.get('expected_impact', ''),
            priority=recommendation.get('priority', 'medium'),
            approved=False,  # Requires admin approval
            flagged=False,
            rejected=False,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        session.add(rec)
        session.commit()
        session.refresh(rec)
        
        # Add database ID to returned recommendation
        recommendation['id'] = rec.id
        recommendation['approved'] = False
        recommendation['rejected'] = False
        recommendation['flagged'] = False
        
        return {
            "success": True,
            "recommendation": recommendation
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendation: {str(e)}")
    finally:
        session.close()


@app.get("/api/user/{user_id}/recommendations/{recommendation_id}/feedback")
def get_recommendation_feedback(user_id: str, recommendation_id: str):
    """Get user feedback for a specific recommendation.
    
    Args:
        user_id: User ID
        recommendation_id: Recommendation ID
    
    Returns:
        User feedback data
    """
    from ingest.schema import UserFeedback
    from sqlalchemy import and_
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        feedback = session.query(UserFeedback).filter(
            and_(
                UserFeedback.user_id == user_id,
                UserFeedback.insight_id == recommendation_id,
                UserFeedback.insight_type == 'recommendation'
            )
        ).order_by(UserFeedback.created_at.desc()).first()
        
        if not feedback:
            return {"feedback": None}
        
        return {
            "feedback": "agreed" if feedback.feedback_type == "like" else "rejected",
            "created_at": feedback.created_at.isoformat() if feedback.created_at else None
        }
    finally:
        session.close()


@app.post("/api/user/{user_id}/recommendations/{recommendation_id}/feedback")
async def submit_recommendation_feedback(user_id: str, recommendation_id: str, request: Dict[str, Any] = Body(...)):
    """Submit user feedback for a recommendation (agree/reject).
    
    Args:
        user_id: User ID
        recommendation_id: Recommendation ID
        request: Request body containing feedback ('agreed' or 'rejected')
    
    Returns:
        Confirmation message
    """
    from ingest.schema import UserFeedback, Recommendation
    from sqlalchemy import and_
    import uuid
    from datetime import datetime
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify recommendation exists and is approved
        recommendation = session.query(Recommendation).filter(
            and_(
                Recommendation.id == recommendation_id,
                Recommendation.user_id == user_id,
                Recommendation.approved == True
            )
        ).first()
        
        if not recommendation:
            raise HTTPException(status_code=404, detail="Recommendation not found or not approved")
        
        feedback_value = request.get('feedback')
        if feedback_value not in ['agreed', 'rejected']:
            raise HTTPException(status_code=400, detail="feedback must be 'agreed' or 'rejected'")
        
        # Check for existing feedback
        existing = session.query(UserFeedback).filter(
            and_(
                UserFeedback.user_id == user_id,
                UserFeedback.insight_id == recommendation_id,
                UserFeedback.insight_type == 'recommendation'
            )
        ).first()
        
        if existing:
            # Update existing feedback
            existing.feedback_type = 'like' if feedback_value == 'agreed' else 'dislike'
            existing.updated_at = datetime.utcnow()
        else:
            # Create new feedback
            feedback = UserFeedback(
                id=str(uuid.uuid4()),
                user_id=user_id,
                insight_id=recommendation_id,
                insight_type='recommendation',
                feedback_type='like' if feedback_value == 'agreed' else 'dislike',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(feedback)
        
        # If user rejects, mark recommendation as user_rejected (set rejected=True, rejected_by=user_id)
        # This makes it visible to admin as "user rejected" instead of "pending"
        if feedback_value == 'rejected':
            recommendation.rejected = True
            recommendation.rejected_by = user_id  # Mark as user rejection
            recommendation.rejected_at = datetime.utcnow()
            # Clear approved status if it was approved
            recommendation.approved = False
            recommendation.approved_at = None
            recommendation.approved_by = None
        elif feedback_value == 'agreed':
            # If user agrees, clear any previous user rejection
            if recommendation.rejected_by == user_id:
                recommendation.rejected = False
                recommendation.rejected_by = None
                recommendation.rejected_at = None
        
        session.commit()
        
        # Broadcast feedback update via WebSocket
        from api.websocket import manager
        await manager.broadcast_recommendation_feedback(user_id, recommendation_id, feedback_value)
        
        return {
            "user_id": user_id,
            "recommendation_id": recommendation_id,
            "feedback": feedback_value,
            "message": f"Feedback submitted: {feedback_value}"
        }
    finally:
        session.close()


@app.get("/api/recommendations/{user_id}/approved")
def get_approved_recommendations(user_id: str):
    """Get approved recommendations for a user.
    
    Args:
        user_id: User ID
    
    Returns:
        List of approved recommendations
    """
    from ingest.schema import Recommendation
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        recommendations = session.query(Recommendation).filter(
            Recommendation.user_id == user_id,
            Recommendation.approved == True
        ).order_by(Recommendation.created_at.desc()).all()
        
        result = []
        for rec in recommendations:
            rec_dict = {
                "id": rec.id,
                "title": rec.title,
                "recommendation_text": rec.description,
                "action_items": rec.action_items if hasattr(rec, 'action_items') and rec.action_items else [],
                "expected_impact": rec.expected_impact if hasattr(rec, 'expected_impact') else None,
                "priority": rec.priority if hasattr(rec, 'priority') else None,
                "content_id": rec.content_id,
                "type": "actionable_recommendation",
                "persona_id": rec.persona_id,
                "created_at": rec.created_at.isoformat() if rec.created_at else None
            }
            result.append(rec_dict)
        
        return {
            "user_id": user_id,
            "recommendations": result,
            "total": len(result)
        }
    finally:
        session.close()


@app.get("/api/recommendations/{user_id}")
def get_recommendations(
    user_id: str,
    window_days: int = Query(180, description="Time window in days for feature computation (default 180)"),
    num_education: int = Query(5, description="Number of education items to recommend (default 5)"),
    num_offers: int = Query(3, description="Number of partner offers to recommend (default 3)"),
    credit_score: Optional[int] = Query(None, description="Optional credit score for eligibility checks"),
    annual_income: Optional[float] = Query(None, description="Optional annual income for eligibility checks")
):
    """Get personalized recommendations for a user.
    
    Args:
        user_id: User ID
        window_days: Time window for feature computation (30 or 180)
        num_education: Number of education items (1-10)
        num_offers: Number of partner offers (1-5)
        credit_score: Optional credit score for eligibility checks
        annual_income: Optional annual income for eligibility checks
    
    Returns:
        Recommendations including education items and partner offers with rationales
    """
    from recommend.generator import RecommendationGenerator
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if window_days not in [30, 180]:
            raise HTTPException(status_code=400, detail="window_days must be 30 or 180")
        
        if num_education < 1 or num_education > 10:
            raise HTTPException(status_code=400, detail="num_education must be between 1 and 10")
        
        if num_offers < 1 or num_offers > 5:
            raise HTTPException(status_code=400, detail="num_offers must be between 1 and 5")
        
        generator = RecommendationGenerator(session)
        recommendations = generator.generate_recommendations(
            user_id,
            window_days,
            num_education,
            num_offers,
            credit_score,
            annual_income
        )
        generator.close()
        
        return recommendations
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    finally:
        session.close()


@app.post("/api/consent")
async def grant_consent(
    request: Dict[str, Any] = Body(...)
):
    """Grant consent for a user.
    
    Args:
        request: Request body with user_id
    
    Returns:
        Consent record
    """
    from guardrails.consent import ConsentManager
    
    user_id = request.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        consent_manager = ConsentManager(session)
        consent = consent_manager.grant_consent(user_id)
        
        consent_data = {
            "user_id": consent.user_id,
            "consented": consent.consented,
            "consented_at": consent.consented_at.isoformat() if consent.consented_at else None,
            "revoked_at": consent.revoked_at.isoformat() if consent.revoked_at else None
        }
        
        # Broadcast real-time update via WebSocket
        await manager.broadcast_consent_update(user_id, consent.consented, consent_data)
        
        return consent_data
    finally:
        session.close()


@app.delete("/api/consent/{user_id}")
async def revoke_consent(user_id: str):
    """Revoke consent for a user.
    
    Args:
        user_id: User ID
    
    Returns:
        Updated consent record
    """
    from guardrails.consent import ConsentManager
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        consent_manager = ConsentManager(session)
        consent = consent_manager.revoke_consent(user_id)
        
        consent_data = {
            "user_id": consent.user_id,
            "consented": consent.consented,
            "consented_at": consent.consented_at.isoformat() if consent.consented_at else None,
            "revoked_at": consent.revoked_at.isoformat() if consent.revoked_at else None
        }
        
        # Broadcast real-time update via WebSocket
        await manager.broadcast_consent_update(user_id, consent.consented, consent_data)
        
        return consent_data
    finally:
        session.close()


@app.get("/api/consent/{user_id}")
def get_consent_status(user_id: str):
    """Get consent status for a user.
    
    Args:
        user_id: User ID
    
    Returns:
        Consent status
    """
    from guardrails.consent import ConsentManager
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        consent_manager = ConsentManager(session)
        consent = consent_manager.get_consent(user_id)
        
        if consent:
            return {
                "user_id": consent.user_id,
                "consented": consent.consented,
                "consented_at": consent.consented_at.isoformat() if consent.consented_at else None,
                "revoked_at": consent.revoked_at.isoformat() if consent.revoked_at else None
            }
        else:
            return {
                "user_id": user_id,
                "consented": False,
                "consented_at": None,
                "revoked_at": None
            }
    finally:
        session.close()


@app.post("/api/insights/{user_id}/net-worth/snapshot")
def create_net_worth_snapshot(
    user_id: str,
    snapshot_date: Optional[str] = Query(None, description="Snapshot date (YYYY-MM-DD, defaults to now)")
):
    """Create a net worth snapshot for a user.
    
    Args:
        user_id: User ID
        snapshot_date: Date for snapshot (YYYY-MM-DD, defaults to now)
    
    Returns:
        Created snapshot data
    """
    from insights.net_worth_tracker import NetWorthTracker
    from datetime import datetime
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        date = None
        if snapshot_date:
            try:
                date = datetime.fromisoformat(snapshot_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid snapshot_date format. Use YYYY-MM-DD")
        
        tracker = NetWorthTracker(session)
        snapshot = tracker.create_snapshot(user_id, date)
        
        return snapshot
    finally:
        session.close()


@app.post("/api/feedback")
def submit_feedback(
    user_id: str = Body(...),
    insight_id: str = Body(...),
    insight_type: str = Body(...),
    feedback_type: str = Body(...),
    metadata: Optional[Dict[str, Any]] = Body(None)
):
    """Submit user feedback on insights or recommendations.
    
    Args:
        user_id: User ID
        insight_id: Identifier for the insight/recommendation
        insight_type: Type of insight (e.g., 'weekly_recap', 'budget_suggestion', 'recommendation')
        feedback_type: Type of feedback ('like' or 'dislike')
        metadata: Additional context (optional)
    
    Returns:
        Confirmation message
    """
    from ingest.schema import UserFeedback
    import uuid
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if feedback_type not in ['like', 'dislike']:
            raise HTTPException(status_code=400, detail="feedback_type must be 'like' or 'dislike'")
        
        feedback = UserFeedback(
            id=str(uuid.uuid4()),
            user_id=user_id,
            insight_id=insight_id,
            insight_type=insight_type,
            feedback_type=feedback_type,
            feedback_metadata=metadata or {}
        )
        
        session.add(feedback)
        session.commit()
        
        return {
            "message": "Feedback submitted successfully",
            "feedback_id": feedback.id
        }
    finally:
        session.close()


# ============================================================================
# Operator Endpoints
# ============================================================================

@app.get("/api/operator/recommendations")
def get_recommendation_queue(
    status: str = Query("pending", description="Filter by status: pending, approved, flagged, all"),
    user_id: Optional[str] = Query(None, description="Filter by user ID (optional)"),
    limit: int = Query(50, description="Maximum number of recommendations to return")
):
    """Get recommendation approval queue for operators.
    
    Args:
        status: Filter by approval status (pending, approved, flagged, all)
        user_id: Optional user ID to filter recommendations by user
        limit: Maximum number of recommendations to return
    
    Returns:
        List of recommendations with user and persona information
    """
    from ingest.schema import Recommendation
    from datetime import datetime
    
    session = get_session()
    try:
        query = session.query(Recommendation).join(User)
        
        # CRITICAL: Always filter by user_id if provided to ensure recommendations are user-specific
        # This ensures that when viewing a user's detail page, only their recommendations are shown
        if user_id:
            query = query.filter(Recommendation.user_id == user_id)
        # If no user_id provided, return empty (should not happen in user-specific views)
        
        if status == "pending":
            query = query.filter(
                Recommendation.approved == False,
                Recommendation.flagged == False,
                Recommendation.rejected == False
            )
        elif status == "approved":
            query = query.filter(Recommendation.approved == True)
        elif status == "flagged":
            query = query.filter(Recommendation.flagged == True)
        elif status == "rejected":
            # Show both admin-rejected and user-rejected recommendations
            query = query.filter(Recommendation.rejected == True)
        elif status == "user_rejected":
            # Show only user-rejected recommendations (rejected_by is set to user_id)
            query = query.filter(
                Recommendation.rejected == True,
                Recommendation.rejected_by.isnot(None)
            )
        # "all" doesn't filter
        
        query = query.order_by(Recommendation.created_at.desc()).limit(limit)
        recommendations = query.all()
        
        result = []
        for rec in recommendations:
            # Get persona info for the user
            persona_data = None
            try:
                from personas.assigner import PersonaAssigner
                assigner = PersonaAssigner(session)
                persona_result = assigner.assign_persona(rec.user_id, window_days=180)
                persona_data = {
                    "primary_persona": persona_result.get("primary_persona"),
                    "risk": persona_result.get("risk"),
                    "risk_level": persona_result.get("risk_level")
                }
            except Exception as e:
                # If persona assignment fails, continue without it
                pass
            
            # Map persona_id to persona name for display
            persona_name = None
            if rec.persona_id:
                try:
                    from personas.definitions import get_persona_by_id
                    persona = get_persona_by_id(rec.persona_id)
                    if persona:
                        persona_name = persona.name
                except Exception:
                    pass
            
            rec_dict = {
                "id": rec.id,
                "user_id": rec.user_id,
                "user_name": rec.user.name,
                "user_email": rec.user.email,
                "title": rec.title,
                "description": rec.description,
                "rationale": rec.rationale,
                "recommendation_type": rec.recommendation_type,
                "persona_id": rec.persona_id,
                "persona_name": persona_name,
                "content_id": rec.content_id,
                "action_items": rec.action_items if hasattr(rec, 'action_items') and rec.action_items else [],
                "expected_impact": rec.expected_impact if hasattr(rec, 'expected_impact') else None,
                "priority": rec.priority if hasattr(rec, 'priority') else None,
                "approved": rec.approved,
                "approved_at": rec.approved_at.isoformat() if rec.approved_at else None,
                "flagged": rec.flagged,
                "rejected": rec.rejected if hasattr(rec, 'rejected') else False,
                "rejected_at": rec.rejected_at.isoformat() if hasattr(rec, 'rejected_at') and rec.rejected_at else None,
                "rejected_by": rec.rejected_by if hasattr(rec, 'rejected_by') else None,
                "created_at": rec.created_at.isoformat() if rec.created_at else None,
                "updated_at": rec.updated_at.isoformat() if rec.updated_at else None,
                "persona_data": persona_data
            }
            
            result.append(rec_dict)
        
        return {
            "recommendations": result,
            "total": len(result),
            "status": status
        }
    finally:
        session.close()


@app.put("/api/operator/recommendations/{recommendation_id}/approve")
async def approve_recommendation(recommendation_id: str):
    """Approve a recommendation.
    
    Args:
        recommendation_id: Recommendation ID
    
    Returns:
        Updated recommendation
    """
    from ingest.schema import Recommendation
    from datetime import datetime
    
    session = get_session()
    try:
        recommendation = session.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
        if not recommendation:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        
        recommendation.approved = True
        recommendation.approved_at = datetime.utcnow()
        recommendation.rejected = False
        recommendation.rejected_by = None  # Clear user rejection if re-approving
        recommendation.rejected_at = None
        recommendation.flagged = False
        recommendation.updated_at = datetime.utcnow()
        
        session.commit()
        
        # Broadcast real-time update via WebSocket
        recommendation_data = {
            "id": recommendation.id,
            "user_id": recommendation.user_id,
            "approved": True,
            "rejected": False,
            "flagged": False,
            "approved_at": recommendation.approved_at.isoformat() if recommendation.approved_at else None,
        }
        await manager.broadcast_recommendation_update(recommendation.id, "approved", recommendation_data)
        
        return {
            "id": recommendation.id,
            "approved": recommendation.approved,
            "approved_at": recommendation.approved_at.isoformat(),
            "message": "Recommendation approved"
        }
    finally:
        session.close()


@app.put("/api/operator/recommendations/{recommendation_id}/flag")
async def flag_recommendation(recommendation_id: str):
    """Flag a recommendation for review.
    
    Args:
        recommendation_id: Recommendation ID
    
    Returns:
        Updated recommendation
    """
    from ingest.schema import Recommendation
    from datetime import datetime
    
    session = get_session()
    try:
        recommendation = session.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
        if not recommendation:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        
        recommendation.flagged = True
        recommendation.approved = False
        recommendation.rejected = False
        recommendation.updated_at = datetime.utcnow()
        
        session.commit()
        
        # Broadcast real-time update via WebSocket
        recommendation_data = {
            "id": recommendation.id,
            "user_id": recommendation.user_id,
            "approved": False,
            "rejected": False,
            "flagged": True,
        }
        await manager.broadcast_recommendation_update(recommendation.id, "flagged", recommendation_data)
        
        return {
            "id": recommendation.id,
            "flagged": recommendation.flagged,
            "message": "Recommendation flagged for review"
        }
    finally:
        session.close()


@app.put("/api/operator/recommendations/{recommendation_id}/reject")
async def reject_recommendation(recommendation_id: str):
    """Reject a recommendation.
    
    Args:
        recommendation_id: Recommendation ID
    
    Returns:
        Updated recommendation
    """
    from ingest.schema import Recommendation
    from datetime import datetime
    
    session = get_session()
    try:
        recommendation = session.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
        if not recommendation:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        
        recommendation.rejected = True
        recommendation.rejected_at = datetime.utcnow()
        recommendation.approved = False
        recommendation.flagged = False
        recommendation.updated_at = datetime.utcnow()
        
        session.commit()
        
        # Broadcast real-time update via WebSocket
        recommendation_data = {
            "id": recommendation.id,
            "user_id": recommendation.user_id,
            "approved": False,
            "rejected": True,
            "flagged": False,
            "rejected_at": recommendation.rejected_at.isoformat() if recommendation.rejected_at else None,
        }
        await manager.broadcast_recommendation_update(recommendation.id, "rejected", recommendation_data)
        
        return {
            "id": recommendation.id,
            "rejected": recommendation.rejected,
            "rejected_at": recommendation.rejected_at.isoformat(),
            "message": "Recommendation rejected"
        }
    finally:
        session.close()


@app.get("/api/operator/signals/{user_id}")
def get_user_signals(
    user_id: str,
    window_days: int = Query(180, description="Time window in days (30 or 180)")
):
    """Get all behavioral signals for a user.
    
    Args:
        user_id: User ID
        window_days: Time window (30 or 180)
    
    Returns:
        All computed signals for the user
    """
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if window_days not in [30, 180]:
            raise HTTPException(status_code=400, detail="window_days must be 30 or 180")
        
        # Get features for the user
        feature_pipeline = FeaturePipeline()
        try:
            features = feature_pipeline.compute_features_for_user(user_id, window_days)
            
            return {
                "user_id": user_id,
                "window_days": window_days,
                "signals": features,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error computing signals: {str(e)}")
        finally:
            feature_pipeline.close()
    finally:
        session.close()


@app.get("/api/operator/traces/{user_id}")
def get_decision_traces(user_id: str):
    """Get decision traces for a user.
    
    Args:
        user_id: User ID
    
    Returns:
        List of decision traces for persona assignment
    """
    from personas.traces import DecisionTraceLogger
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        trace_logger = DecisionTraceLogger()
        traces = trace_logger.get_traces_for_user(user_id)
        
        return {
            "user_id": user_id,
            "traces": [trace.to_dict() for trace in traces],
            "total": len(traces)
        }
    finally:
        session.close()


@app.get("/api/evaluation/metrics")
def get_evaluation_metrics(
    latency_sample_size: Optional[int] = Query(None, description="Number of users to test for latency (default: all users with consent)")
):
    """Get evaluation metrics for the system.
    
    This endpoint runs the Phase 8 evaluation harness and returns metrics including:
    - Coverage: % of users with assigned persona + ≥3 detected behaviors
    - Explainability: % of recommendations with plain-language rationales
    - Relevance: Education-persona fit scoring
    - Latency: Time to generate recommendations per user
    - Fairness: Demographic parity in persona distribution
    
    Args:
        latency_sample_size: Number of users to test for latency (None = all users with consent)
    
    Returns:
        Complete evaluation metrics with all details
    """
    from eval.harness import EvaluationHarness
    
    harness = EvaluationHarness()
    try:
        # Suppress print statements for API call
        import sys
        from io import StringIO
        
        # Capture stdout to suppress print statements
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            metrics = harness.run_evaluation(
                output_dir=None,  # Don't save files for API call
                latency_sample_size=latency_sample_size,
                generate_csv=False,
                generate_json=False,
                generate_report=False
            )
        finally:
            # Restore stdout
            sys.stdout = old_stdout
        
        return metrics
    finally:
        harness.close()


@app.websocket("/ws/consent/{user_id}")
async def websocket_consent_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time consent updates.
    
    Args:
        websocket: WebSocket connection
        user_id: User ID to receive updates for
    """
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()
            # Echo back or handle client messages if needed
            await websocket.send_json({"type": "ack", "message": "Connection active"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        print(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(websocket, user_id)


@app.websocket("/ws/subscriptions/{user_id}")
async def websocket_subscriptions(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for subscription cancellation updates."""
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()
            # Echo back or handle client messages if needed
            await websocket.send_json({"type": "pong", "message": "Connection alive"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        print(f"Error in subscription WebSocket: {e}")
        manager.disconnect(websocket, user_id)


@app.websocket("/ws/operator/recommendations")
async def websocket_operator_recommendations_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time recommendation updates for operators.
    
    Broadcasts updates when recommendations are approved, rejected, or flagged.
    All operators connected to this endpoint will receive updates in real-time.
    """
    await manager.connect_operator(websocket)
    try:
        # Send initial connection confirmation
        await websocket.send_json({"type": "connected", "message": "Operator WebSocket connected"})
        
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()
            # Echo back to keep connection alive
            await websocket.send_json({"type": "ack", "message": "Connection active"})
    except WebSocketDisconnect:
        manager.disconnect_operator(websocket)
    except Exception as e:
        print(f"Operator WebSocket error: {e}")
        manager.disconnect_operator(websocket)


@app.websocket("/ws/user/{user_id}/recommendations/feedback")
async def websocket_recommendation_feedback_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time recommendation feedback updates for users.
    
    Broadcasts updates when user provides feedback (agree/reject) on recommendations.
    """
    await manager.connect(websocket, user_id)
    try:
        # Send initial connection confirmation
        await websocket.send_json({"type": "connected", "message": "Recommendation Feedback WebSocket connected"})
        
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()
            # Echo back to keep connection alive
            await websocket.send_json({"type": "ack", "message": "Connection active"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        print(f"Recommendation Feedback WebSocket error for user {user_id}: {e}")
        manager.disconnect(websocket, user_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

