"""FastAPI application for SpendSense."""

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, Dict, Any

from ingest.schema import get_session, User, Account, Transaction, Liability
from features.pipeline import FeaturePipeline

app = FastAPI(title="SpendSense API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
            
            # Get persona assignment
            persona_assignment = assigner.get_user_persona(user.id)
            if not persona_assignment:
                # Assign persona if not already assigned
                persona_assignment_data = assigner.assign_persona(user.id)
                persona_assignment = {
                    'primary_persona': persona_assignment_data['primary_persona'],
                    'primary_persona_name': persona_assignment_data['primary_persona_name'],
                    'primary_persona_risk': persona_assignment_data.get('primary_persona_risk', 0),
                    'primary_persona_risk_level': persona_assignment_data.get('primary_persona_risk_level', 'MINIMAL')
                }
            
            result.append({
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "account_count": account_count or 0,
                "persona": {
                    "id": persona_assignment.get('primary_persona'),
                    "name": persona_assignment.get('primary_persona_name'),
                    "risk": persona_assignment.get('primary_persona_risk', 0),
                    "risk_level": persona_assignment.get('primary_persona_risk_level', 'MINIMAL')
                }
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
        persona_data = assigner.assign_persona(user_id)
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
        
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "accounts": accounts_data,
            "transactions": transactions_data,
            "features_30d": features_30d,
            "features_180d": features_180d,
            "persona": {
                "id": persona_data.get("primary_persona"),
                "name": persona_data.get("primary_persona_name"),
                "risk": persona_data.get("primary_persona_risk", 0),
                "risk_level": persona_data.get("primary_persona_risk_level", "MINIMAL"),
                "all_matched_personas": persona_data.get("matched_personas", []),
                "decision_trace": persona_data.get("decision_trace", {})
            },
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

