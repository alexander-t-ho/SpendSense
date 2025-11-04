"""Budget tracking and progress monitoring.

This module tracks budget vs actual spending and provides progress updates.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ingest.schema import Account, Transaction, Budget


class BudgetTracker:
    """Track budget vs actual spending."""
    
    def __init__(self, db_session: Session):
        """Initialize tracker.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
    
    def track_budget(
        self,
        user_id: str,
        month: Optional[str] = None
    ) -> Dict[str, Any]:
        """Track budget vs actual spending for a month.
        
        Args:
            user_id: User ID
            month: Month in YYYY-MM format (defaults to current month)
        
        Returns:
            Dictionary with budget tracking data including:
            - month: Month being tracked
            - total_budget: Total budget for the month
            - total_spent: Total amount spent
            - remaining: Remaining budget
            - percentage_used: Percentage of budget used
            - category_breakdown: Budget vs actual by category
            - status: Budget status (on_track, warning, over_budget)
            - days_remaining: Days left in the month
        """
        # Default to current month
        if month is None:
            month = datetime.now().strftime("%Y-%m")
        
        # Parse month
        try:
            month_start = datetime.strptime(month, "%Y-%m")
        except ValueError:
            raise ValueError(f"Invalid month format. Use YYYY-MM, got: {month}")
        
        # Calculate month end
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)
        
        # Get budgets for this month
        budgets = self.db.query(Budget).filter(
            and_(
                Budget.user_id == user_id,
                Budget.period_start <= month_end,
                Budget.period_end >= month_start
            )
        ).all()
        
        # Get all accounts
        user_accounts = self.db.query(Account).filter(Account.user_id == user_id).all()
        account_ids = [acc.id for acc in user_accounts]
        
        # Get transactions for the month
        transactions = []
        if account_ids:
            transactions = self.db.query(Transaction).filter(
                and_(
                    Transaction.account_id.in_(account_ids),
                    Transaction.date >= month_start,
                    Transaction.date <= month_end,
                    Transaction.amount < 0  # Only expenses
                )
            ).all()
        
        # Calculate total budget
        total_budget = sum(budget.amount for budget in budgets if budget.category is None)
        
        # Calculate category budgets
        category_budgets = {}
        for budget in budgets:
            if budget.category:
                category_budgets[budget.category] = budget.amount
        
        # Calculate total spent
        total_spent = sum(abs(tx.amount) for tx in transactions)
        
        # Calculate spent by category
        category_spent = defaultdict(float)
        for tx in transactions:
            category = tx.primary_category or "Uncategorized"
            category_spent[category] += abs(tx.amount)
        
        # Calculate category breakdown
        category_breakdown = {}
        all_categories = set(list(category_budgets.keys()) + list(category_spent.keys()))
        
        for category in all_categories:
            budget_amount = category_budgets.get(category, 0.0)
            spent_amount = category_spent.get(category, 0.0)
            remaining = budget_amount - spent_amount
            percentage_used = (spent_amount / budget_amount * 100) if budget_amount > 0 else 0.0
            
            category_breakdown[category] = {
                "budget": budget_amount,
                "spent": spent_amount,
                "remaining": remaining,
                "percentage_used": percentage_used
            }
        
        # Calculate remaining budget
        remaining_budget = total_budget - total_spent
        percentage_used = (total_spent / total_budget * 100) if total_budget > 0 else 0.0
        
        # Determine status
        days_elapsed = (datetime.now() - month_start).days + 1
        days_in_month = (month_end - month_start).days + 1
        expected_progress = (days_elapsed / days_in_month) * 100
        
        if total_budget == 0:
            status = "no_budget"
        elif percentage_used > 100:
            status = "over_budget"
        elif percentage_used > expected_progress * 1.2:  # 20% ahead of pace
            status = "warning"
        else:
            status = "on_track"
        
        days_remaining = max(0, days_in_month - days_elapsed)
        
        return {
            "user_id": user_id,
            "month": month,
            "total_budget": total_budget,
            "total_spent": total_spent,
            "remaining": remaining_budget,
            "percentage_used": percentage_used,
            "category_breakdown": category_breakdown,
            "status": status,
            "days_remaining": days_remaining,
            "days_elapsed": days_elapsed,
            "days_in_month": days_in_month,
            "expected_progress": expected_progress
        }

