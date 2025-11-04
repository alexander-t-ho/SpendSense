"""Budget calculator for AI-suggested monthly budgets.

This module generates personalized budget suggestions based on historical
spending patterns, income stability, and financial goals.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ingest.schema import Account, Transaction, Budget
from insights.utils import calculate_percentage_change


class BudgetCalculator:
    """Calculate AI-suggested budgets based on historical data."""
    
    def __init__(self, db_session: Session):
        """Initialize calculator.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
    
    def suggest_budget(
        self,
        user_id: str,
        month: Optional[datetime] = None,
        lookback_months: int = 6
    ) -> Dict[str, Any]:
        """Generate AI-suggested monthly budget for a user.
        
        Args:
            user_id: User ID
            month: Target month (defaults to next month)
            lookback_months: Number of months to analyze for suggestions
        
        Returns:
            Dictionary with suggested budget including:
            - month: Target month
            - total_budget: Total monthly budget
            - category_budgets: Suggested budgets by category
            - rationale: Plain-language explanation
            - income_based: Income-based budget suggestion
            - expense_based: Expense-based budget suggestion
        """
        # Default to next month
        if month is None:
            month = datetime.now().replace(day=1) + timedelta(days=32)
            month = month.replace(day=1)  # First day of next month
        
        # Calculate date range for analysis
        start_date = month - timedelta(days=lookback_months * 30)
        end_date = month - timedelta(days=1)  # Up to the month before target
        
        # Get all accounts
        user_accounts = self.db.query(Account).filter(Account.user_id == user_id).all()
        account_ids = [acc.id for acc in user_accounts]
        
        if not account_ids:
            return {
                "user_id": user_id,
                "month": month.strftime("%Y-%m"),
                "total_budget": 0.0,
                "category_budgets": {},
                "rationale": "No account data available for budget suggestions.",
                "income_based": 0.0,
                "expense_based": 0.0
            }
        
        # Get transactions for analysis period
        transactions = self.db.query(Transaction).filter(
            and_(
                Transaction.account_id.in_(account_ids),
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
        ).all()
        
        # Separate income and expenses
        expenses = [tx for tx in transactions if tx.amount < 0]
        income = [tx for tx in transactions if tx.amount > 0]
        
        # Calculate average monthly income
        monthly_income = defaultdict(float)
        for tx in income:
            month_key = tx.date.strftime("%Y-%m")
            monthly_income[month_key] += abs(tx.amount)
        
        avg_monthly_income = sum(monthly_income.values()) / len(monthly_income) if monthly_income else 0.0
        
        # Calculate average monthly expenses by category
        monthly_expenses_by_category = defaultdict(lambda: defaultdict(float))
        for tx in expenses:
            month_key = tx.date.strftime("%Y-%m")
            category = tx.primary_category or "Uncategorized"
            monthly_expenses_by_category[month_key][category] += abs(tx.amount)
        
        # Calculate average spending per category
        category_totals = defaultdict(float)
        category_counts = defaultdict(int)
        
        for month_data in monthly_expenses_by_category.values():
            for category, amount in month_data.items():
                category_totals[category] += amount
                category_counts[category] += 1
        
        avg_category_budgets = {}
        for category in category_totals:
            if category_counts[category] > 0:
                avg_category_budgets[category] = category_totals[category] / category_counts[category]
        
        # Calculate total average monthly expenses
        monthly_totals = [sum(cat.values()) for cat in monthly_expenses_by_category.values()]
        avg_monthly_expenses = sum(monthly_totals) / len(monthly_totals) if monthly_totals else 0.0
        
        # Generate budget suggestions
        # Strategy: Use 80% of average income or 110% of average expenses (whichever is lower)
        # This provides a buffer while encouraging savings
        income_based_budget = avg_monthly_income * 0.80 if avg_monthly_income > 0 else 0.0
        expense_based_budget = avg_monthly_expenses * 1.10 if avg_monthly_expenses > 0 else 0.0
        
        # Use the more conservative approach
        if income_based_budget > 0 and expense_based_budget > 0:
            total_budget = min(income_based_budget, expense_based_budget)
        elif income_based_budget > 0:
            total_budget = income_based_budget
        elif expense_based_budget > 0:
            total_budget = expense_based_budget
        else:
            total_budget = 0.0
        
        # Allocate budget to categories proportionally
        category_budgets = {}
        if total_budget > 0 and avg_monthly_expenses > 0:
            for category, avg_amount in avg_category_budgets.items():
                # Allocate proportionally based on average spending
                proportion = avg_amount / avg_monthly_expenses
                category_budgets[category] = total_budget * proportion
        
        # Generate rationale
        rationale_parts = []
        if avg_monthly_income > 0:
            rationale_parts.append(
                f"Based on your average monthly income of ${avg_monthly_income:,.2f} over the last {lookback_months} months, "
                f"we suggest a monthly budget of ${total_budget:,.2f}."
            )
        else:
            rationale_parts.append(
                f"Based on your average monthly expenses of ${avg_monthly_expenses:,.2f} over the last {lookback_months} months, "
                f"we suggest a monthly budget of ${total_budget:,.2f}."
            )
        
        if category_budgets:
            top_category = max(category_budgets.items(), key=lambda x: x[1])
            rationale_parts.append(
                f"Your largest budget category is {top_category[0]} with ${top_category[1]:,.2f} allocated."
            )
        
        rationale = " ".join(rationale_parts) if rationale_parts else "Budget suggestions based on historical spending patterns."
        
        # Also get history for charting
        history = []
        for i in range(lookback_months):
            hist_month = month - timedelta(days=30 * (lookback_months - i))
            month_key = hist_month.strftime("%Y-%m")
            
            if month_key in monthly_income and month_key in monthly_expenses_by_category:
                hist_spending = sum(monthly_expenses_by_category[month_key].values())
                hist_income = monthly_income[month_key]
                history.append({
                    "month": month_key,
                    "total_spending": hist_spending,
                    "total_income": hist_income
                })
        
        return {
            "user_id": user_id,
            "month": month.strftime("%Y-%m"),
            "total_budget": total_budget,
            "category_budgets": category_budgets,
            "rationale": rationale,
            "income_based": income_based_budget,
            "expense_based": expense_based_budget,
            "average_monthly_income": avg_monthly_income,
            "average_monthly_expenses": avg_monthly_expenses,
            "lookback_months": lookback_months,
            "history": history
        }

