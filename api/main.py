"""FastAPI application for SpendSense."""

import os
from fastapi import FastAPI, HTTPException, Query, Body, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, Dict, Any
from datetime import datetime

from ingest.schema import get_session, User, Account, Transaction, Liability
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


@app.get("/")
def root():
    return {"message": "SpendSense API", "version": "1.0.0"}


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
                "risk_level": persona_assignment_data.get('primary_persona_risk_level', 'MINIMAL'),
                "top_personas": persona_assignment_data.get('top_personas', []),
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
        
        # Calculate income from payroll transactions over 180 days, scaled to yearly
        income_180d = 0.0
        yearly_income = 0.0
        
        # Get all payroll transactions in the last 180 days
        payroll_start_date = datetime.now() - timedelta(days=180)
        payroll_transactions = session.query(Transaction).join(Account).filter(
            and_(
                Account.user_id == user_id,
                Transaction.date >= payroll_start_date,
                Transaction.merchant_name == "PAYROLL DEPOSIT",
                Transaction.amount > 0  # Only positive amounts (deposits)
            )
        ).all()
        
        if payroll_transactions:
            # Sum all payroll amounts
            income_180d = sum(tx.amount for tx in payroll_transactions)
            # Scale to yearly: (180-day income / 180) * 365
            yearly_income = (income_180d / 180.0) * 365.0
        
        # Build persona object with dual persona support
        persona_obj = {
            "id": persona_data.get("primary_persona"),
            "name": persona_data.get("primary_persona_name"),
            "risk": persona_data.get("primary_persona_risk", 0),
            "risk_level": persona_data.get("primary_persona_risk_level", "MINIMAL"),
            "top_personas": persona_data.get("top_personas", []),
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
                "payroll_count_180d": len(payroll_transactions)
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
    limit: int = Query(50, description="Maximum number of recommendations to return")
):
    """Get recommendation approval queue for operators.
    
    Args:
        status: Filter by approval status (pending, approved, flagged, all)
        limit: Maximum number of recommendations to return
    
    Returns:
        List of recommendations with user and persona information
    """
    from ingest.schema import Recommendation
    from datetime import datetime
    
    session = get_session()
    try:
        query = session.query(Recommendation).join(User)
        
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
            query = query.filter(Recommendation.rejected == True)
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


@app.put("/api/operator/recommendations/{recommendation_id}/flag")
def flag_recommendation(recommendation_id: str):
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
        
        return {
            "id": recommendation.id,
            "flagged": recommendation.flagged,
            "message": "Recommendation flagged for review"
        }
    finally:
        session.close()


@app.put("/api/operator/recommendations/{recommendation_id}/reject")
def reject_recommendation(recommendation_id: str):
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

