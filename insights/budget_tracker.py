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
            month_start = datetime.strptime(month, "%Y-%m").replace(day=1, hour=0, minute=0, second=0, microsecond=0)
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
        
        # Get ALL accounts for the user (including credit cards and loans)
        # This ensures spending across all accounts is tracked
        user_accounts = self.db.query(Account).filter(
            Account.user_id == user_id
        ).all()
        account_ids = [acc.id for acc in user_accounts]
        
        # Get transactions for the month (only up to today if current month)
        now = datetime.now()
        # If tracking current month, only count transactions up to today
        # If tracking a past month, count all transactions in that month
        if month_start.year == now.year and month_start.month == now.month:
            # Current month - only count up to today
            end_date = now
        else:
            # Past or future month - use month_end
            end_date = month_end
        
        transactions = []
        if account_ids:
            transactions = self.db.query(Transaction).filter(
                and_(
                    Transaction.account_id.in_(account_ids),
                    Transaction.date >= month_start,
                    Transaction.date <= end_date,
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
        
        # Calculate spent by category (map transaction categories to budget categories)
        category_spent = defaultdict(float)
        for tx in transactions:
            # Get account type for debt repayment detection
            account = next((acc for acc in user_accounts if acc.id == tx.account_id), None)
            account_type = account.type if account else None
            
            # Map transaction category to budget category
            budget_category = self._map_transaction_category_to_budget_category(
                tx.primary_category,
                tx.merchant_name,
                account_type
            )
            category_spent[budget_category] += abs(tx.amount)
        
        # Calculate category breakdown
        category_breakdown = {}
        all_categories = set(list(category_budgets.keys()) + list(category_spent.keys()))
        
        # If no category budgets exist and total budget > 0, divide evenly among categories
        if not category_budgets and total_budget > 0 and all_categories:
            categories_list = list(all_categories)
            budget_per_category = total_budget / len(categories_list) if categories_list else 0.0
            for category in categories_list:
                category_budgets[category] = budget_per_category
        
        # Calculate category percentages if total budget exists
        category_percentages = {}
        if total_budget > 0:
            for category, budget_amount in category_budgets.items():
                percentage = (budget_amount / total_budget * 100) if total_budget > 0 else 0.0
                category_percentages[category] = round(percentage, 1)
        
        for category in all_categories:
            budget_amount = category_budgets.get(category, 0.0)
            spent_amount = category_spent.get(category, 0.0)
            remaining = budget_amount - spent_amount
            percentage_used = (spent_amount / budget_amount * 100) if budget_amount > 0 else 0.0
            budget_percentage = category_percentages.get(category, 0.0)
            is_over_budget = spent_amount > budget_amount
            
            category_breakdown[category] = {
                "budget": budget_amount,
                "spent": spent_amount,
                "remaining": remaining,
                "percentage_used": percentage_used,
                "budget_percentage": budget_percentage,
                "is_over_budget": is_over_budget
            }
        
        # Calculate remaining budget
        remaining_budget = total_budget - total_spent
        percentage_used = (total_spent / total_budget * 100) if total_budget > 0 else 0.0
        
        # Calculate total credit card debt
        credit_card_accounts = [acc for acc in user_accounts if acc.type == 'credit']
        total_credit_card_debt = sum(abs(acc.current or 0) for acc in credit_card_accounts)
        
        # Calculate available funds (checking + savings)
        depository_accounts = [acc for acc in user_accounts if acc.type == 'depository']
        available_funds = sum(acc.available or acc.current or 0 for acc in depository_accounts)
        
        # Check if debt exceeds available funds
        debt_exceeds_funds = total_credit_card_debt > available_funds
        
        # Determine status
        days_elapsed = (datetime.now() - month_start).days + 1
        days_in_month = (month_end - month_start).days + 1
        expected_progress = (days_elapsed / days_in_month) * 100
        
        if total_budget == 0:
            status = "no_budget"
        elif percentage_used > 100:
            status = "over_budget"
        elif debt_exceeds_funds:
            # If credit card debt exceeds available funds, this is a critical warning
            status = "debt_concern"
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
            "category_percentages": category_percentages,
            "status": status,
            "days_remaining": days_remaining,
            "days_elapsed": days_elapsed,
            "days_in_month": days_in_month,
            "expected_progress": expected_progress,
            "credit_card_debt": total_credit_card_debt,
            "available_funds": available_funds,
            "debt_exceeds_funds": debt_exceeds_funds
        }
    
    def _map_transaction_category_to_budget_category(
        self,
        tx_category: Optional[str],
        tx_merchant: Optional[str],
        account_type: Optional[str]
    ) -> str:
        """Map transaction category to budget category.
        
        Args:
            tx_category: Transaction primary category
            tx_merchant: Merchant name (optional)
            account_type: Account type (optional)
        
        Returns:
            Budget category name
        """
        if not tx_category:
            tx_category = "Uncategorized"
        
        # Housing: Rent, Mortgage, Bills and Utilities
        if tx_category in ["Rent", "Mortgage", "Bills and Utilities"]:
            return "Housing"
        
        # Food: Food and Drink, Groceries
        if tx_category in ["Food and Drink", "Groceries"]:
            return "Food"
        
        # Transportation: Transportation, Gas Stations
        if tx_category in ["Transportation", "Gas Stations"]:
            return "Transportation"
        
        # Debt Repayment: Check if this is a debt payment transaction
        if self._is_debt_repayment_transaction(tx_category, tx_merchant, account_type):
            return "Debt Repayment"
        
        # Other: All remaining categories
        return "Other"
    
    def _is_debt_repayment_transaction(
        self,
        tx_category: Optional[str],
        tx_merchant: Optional[str],
        account_type: Optional[str]
    ) -> bool:
        """Check if a transaction is a debt repayment.
        
        Args:
            tx_category: Transaction primary category
            tx_merchant: Merchant name
            account_type: Account type
        
        Returns:
            True if this is a debt repayment transaction
        """
        if not tx_merchant:
            tx_merchant = ""
        if not tx_category:
            tx_category = ""
        
        merchant_upper = tx_merchant.upper()
        category_upper = tx_category.upper()
        
        # Check for debt-related keywords in merchant name
        debt_keywords = ["PAYMENT", "LOAN", "CREDIT CARD", "CREDITCARD", "DEBT", "PAYOFF"]
        if any(keyword in merchant_upper for keyword in debt_keywords):
            return True
        
        # Check for debt-related categories
        if "LOAN" in category_upper or "PAYMENT" in category_upper:
            return True
        
        # Note: Debt payments are typically from checking accounts (depository)
        # to credit/loan accounts, so we rely on merchant name and category patterns
        # rather than account type
        
        return False

