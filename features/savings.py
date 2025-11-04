"""Savings pattern detection features."""

from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ingest.schema import Account, Transaction


class SavingsAnalyzer:
    """Analyze savings patterns and emergency fund coverage."""
    
    SAVINGS_ACCOUNT_TYPES = ["savings", "money_market", "hsa", "cash_management"]
    
    def __init__(self, db_session: Session):
        """Initialize analyzer.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
    
    def get_savings_accounts(self, user_id: str) -> List[Account]:
        """Get all savings-like accounts for user.
        
        Args:
            user_id: User ID
        
        Returns:
            List of savings accounts
        """
        return self.db.query(Account).filter(
            and_(
                Account.user_id == user_id,
                Account.subtype.in_(self.SAVINGS_ACCOUNT_TYPES)
            )
        ).all()
    
    def calculate_net_inflow(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """Calculate net inflow to savings accounts.
        
        Args:
            user_id: User ID
            start_date: Analysis start date
            end_date: Analysis end date
        
        Returns:
            Net inflow amount (positive = inflow, negative = outflow)
        """
        savings_accounts = self.get_savings_accounts(user_id)
        
        total_inflow = 0.0
        for account in savings_accounts:
            transactions = self.db.query(Transaction).filter(
                and_(
                    Transaction.account_id == account.id,
                    Transaction.date >= start_date,
                    Transaction.date <= end_date
                )
            ).all()
            
            for tx in transactions:
                total_inflow += tx.amount  # Positive for deposits, negative for withdrawals
        
        return total_inflow
    
    def calculate_growth_rate(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """Calculate savings growth rate over period.
        
        Args:
            user_id: User ID
            start_date: Analysis start date
            end_date: Analysis end date
        
        Returns:
            Growth rate as percentage
        """
        savings_accounts = self.get_savings_accounts(user_id)
        
        if not savings_accounts:
            return 0.0
        
        # Get starting balance (approximate from transactions before start_date)
        start_balance = 0.0
        for account in savings_accounts:
            # Get balance at start_date (current balance - transactions after start)
            transactions_after = self.db.query(Transaction).filter(
                and_(
                    Transaction.account_id == account.id,
                    Transaction.date >= start_date
                )
            ).all()
            
            current_balance = account.current or 0.0
            # Approximate start balance by subtracting net flow
            net_flow = sum(tx.amount for tx in transactions_after)
            approx_start = current_balance - net_flow
            start_balance += max(0, approx_start)
        
        # Get ending balance
        end_balance = sum(account.current or 0.0 for account in savings_accounts)
        
        if start_balance == 0:
            return 0.0 if end_balance == 0 else 100.0  # 100% growth if started at 0
        
        growth_rate = ((end_balance - start_balance) / start_balance) * 100
        return growth_rate
    
    def calculate_emergency_fund_coverage(
        self,
        user_id: str,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate emergency fund coverage (savings / avg monthly expenses).
        
        Args:
            user_id: User ID
            end_date: Analysis end date
        
        Returns:
            Dictionary with emergency fund metrics
        """
        # Get total savings balance
        savings_accounts = self.get_savings_accounts(user_id)
        total_savings = sum(account.current or 0.0 for account in savings_accounts)
        
        # Calculate average monthly expenses (last 6 months)
        six_months_ago = end_date - timedelta(days=180)
        
        # Get all expense transactions (checking account outflows)
        checking_accounts = self.db.query(Account).filter(
            and_(
                Account.user_id == user_id,
                Account.subtype == "checking"
            )
        ).all()
        
        total_expenses = 0.0
        for account in checking_accounts:
            transactions = self.db.query(Transaction).filter(
                and_(
                    Transaction.account_id == account.id,
                    Transaction.date >= six_months_ago,
                    Transaction.date <= end_date,
                    Transaction.amount < 0  # Expenses are negative
                )
            ).all()
            
            total_expenses += abs(sum(tx.amount for tx in transactions))
        
        # Calculate average monthly expenses
        months = 6.0
        avg_monthly_expenses = total_expenses / months if months > 0 else 0.0
        
        # Calculate coverage (months of expenses)
        coverage_months = (total_savings / avg_monthly_expenses) if avg_monthly_expenses > 0 else 0.0
        
        return {
            "total_savings_balance": total_savings,
            "average_monthly_expenses": avg_monthly_expenses,
            "emergency_fund_coverage_months": coverage_months,
            "has_emergency_fund": coverage_months >= 3.0  # 3 months is typical recommendation
        }
    
    def calculate_savings_metrics(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate all savings-related metrics.
        
        Args:
            user_id: User ID
            start_date: Analysis start date
            end_date: Analysis end date
        
        Returns:
            Dictionary with all savings metrics
        """
        net_inflow = self.calculate_net_inflow(user_id, start_date, end_date)
        growth_rate = self.calculate_growth_rate(user_id, start_date, end_date)
        emergency_fund = self.calculate_emergency_fund_coverage(user_id, end_date)
        
        # Calculate monthly net inflow
        days = (end_date - start_date).days
        months = days / 30.0 if days > 0 else 1.0
        monthly_net_inflow = net_inflow / months if months > 0 else 0.0
        
        return {
            "net_inflow": net_inflow,
            "monthly_net_inflow": monthly_net_inflow,
            "growth_rate_percent": growth_rate,
            "emergency_fund_coverage_months": emergency_fund["emergency_fund_coverage_months"],
            "total_savings_balance": emergency_fund["total_savings_balance"],
            "average_monthly_expenses": emergency_fund["average_monthly_expenses"],
            "has_emergency_fund": emergency_fund["has_emergency_fund"]
        }

