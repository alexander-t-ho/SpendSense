"""Income stability analysis features."""

from datetime import datetime, timedelta
from typing import Dict, List, Any
from statistics import median
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ingest.schema import Account, Transaction


class IncomeAnalyzer:
    """Analyze income patterns and stability."""
    
    def __init__(self, db_session: Session):
        """Initialize analyzer.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
    
    def detect_payroll_ach(self, user_id: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Detect payroll ACH deposits.
        
        Args:
            user_id: User ID
            start_date: Analysis start date
            end_date: Analysis end date
        
        Returns:
            List of payroll transactions
        """
        # Get checking accounts
        checking_accounts = self.db.query(Account).filter(
            and_(
                Account.user_id == user_id,
                Account.subtype == "checking"
            )
        ).all()
        
        payroll_transactions = []
        
        for account in checking_accounts:
            transactions = self.db.query(Transaction).filter(
                and_(
                    Transaction.account_id == account.id,
                    Transaction.date >= start_date,
                    Transaction.date <= end_date,
                    Transaction.amount > 0,  # Deposits are positive
                    (
                        Transaction.merchant_name.like("%PAYROLL%") |
                        Transaction.merchant_name.like("%DEPOSIT%") |
                        Transaction.primary_category == "Transfer In"
                    )
                )
            ).order_by(Transaction.date).all()
            
            for tx in transactions:
                # Filter for likely payroll (substantial amounts)
                if tx.amount >= 1000:  # Reasonable minimum for payroll
                    payroll_transactions.append({
                        "date": tx.date,
                        "amount": tx.amount,
                        "account_id": account.account_id,
                        "transaction_id": tx.transaction_id
                    })
        
        return sorted(payroll_transactions, key=lambda x: x["date"])
    
    def calculate_payment_frequency(
        self,
        payroll_transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate payment frequency and variability.
        
        Args:
            payroll_transactions: List of payroll transactions
        
        Returns:
            Dictionary with frequency metrics
        """
        if len(payroll_transactions) < 2:
            return {
                "frequency": "unknown",
                "average_days_between": 0.0,
                "median_days_between": 0.0,
                "frequency_variability": 0.0,
                "is_regular": False
            }
        
        # Calculate days between payments
        intervals = []
        for i in range(1, len(payroll_transactions)):
            days = (payroll_transactions[i]["date"] - payroll_transactions[i-1]["date"]).days
            intervals.append(days)
        
        avg_interval = sum(intervals) / len(intervals) if intervals else 0.0
        median_interval = median(intervals) if intervals else 0.0
        
        # Calculate variability (standard deviation)
        if len(intervals) > 1:
            variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
            std_dev = variance ** 0.5
        else:
            std_dev = 0.0
        
        # Determine frequency
        if 13 <= median_interval <= 15:
            frequency = "biweekly"
        elif 28 <= median_interval <= 31:
            frequency = "monthly"
        elif 6 <= median_interval <= 8:
            frequency = "weekly"
        else:
            frequency = "irregular"
        
        # Consider regular if std dev is less than 20% of median
        is_regular = std_dev < (median_interval * 0.2) if median_interval > 0 else False
        
        return {
            "frequency": frequency,
            "average_days_between": avg_interval,
            "median_days_between": median_interval,
            "frequency_variability": std_dev,
            "is_regular": is_regular,
            "total_payments": len(payroll_transactions)
        }
    
    def calculate_cash_flow_buffer(
        self,
        user_id: str,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate cash-flow buffer in months.
        
        Args:
            user_id: User ID
            end_date: Analysis end date
        
        Returns:
            Dictionary with cash-flow buffer metrics
        """
        # Get checking account balance
        checking_accounts = self.db.query(Account).filter(
            and_(
                Account.user_id == user_id,
                Account.subtype == "checking"
            )
        ).all()
        
        total_checking_balance = sum(account.current or 0.0 for account in checking_accounts)
        
        # Calculate average monthly expenses (last 3 months)
        three_months_ago = end_date - timedelta(days=90)
        
        total_expenses = 0.0
        for account in checking_accounts:
            transactions = self.db.query(Transaction).filter(
                and_(
                    Transaction.account_id == account.id,
                    Transaction.date >= three_months_ago,
                    Transaction.date <= end_date,
                    Transaction.amount < 0  # Expenses
                )
            ).all()
            
            total_expenses += abs(sum(tx.amount for tx in transactions))
        
        months = 3.0
        avg_monthly_expenses = total_expenses / months if months > 0 else 0.0
        
        # Calculate buffer
        buffer_months = (total_checking_balance / avg_monthly_expenses) if avg_monthly_expenses > 0 else 0.0
        
        return {
            "checking_balance": total_checking_balance,
            "average_monthly_expenses": avg_monthly_expenses,
            "cash_flow_buffer_months": buffer_months,
            "has_sufficient_buffer": buffer_months >= 1.0
        }
    
    def calculate_income_metrics(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate all income-related metrics.
        
        Args:
            user_id: User ID
            start_date: Analysis start date
            end_date: Analysis end date
        
        Returns:
            Dictionary with all income metrics
        """
        payroll_transactions = self.detect_payroll_ach(user_id, start_date, end_date)
        frequency_info = self.calculate_payment_frequency(payroll_transactions)
        cash_flow_buffer = self.calculate_cash_flow_buffer(user_id, end_date)
        
        # Calculate median pay gap (for variable income detection)
        if len(payroll_transactions) >= 2:
            intervals = []
            for i in range(1, len(payroll_transactions)):
                days = (payroll_transactions[i]["date"] - payroll_transactions[i-1]["date"]).days
                intervals.append(days)
            median_pay_gap = median(intervals) if intervals else 0.0
        else:
            median_pay_gap = 0.0
        
        # Calculate average income
        if payroll_transactions:
            avg_income = sum(tx["amount"] for tx in payroll_transactions) / len(payroll_transactions)
        else:
            avg_income = 0.0
        
        return {
            "has_payroll_detected": len(payroll_transactions) > 0,
            "total_payroll_transactions": len(payroll_transactions),
            "average_income_per_pay": avg_income,
            "payment_frequency": frequency_info,
            "median_pay_gap_days": median_pay_gap,
            "cash_flow_buffer_months": cash_flow_buffer["cash_flow_buffer_months"],
            "checking_balance": cash_flow_buffer["checking_balance"],
            "average_monthly_expenses": cash_flow_buffer["average_monthly_expenses"],
            "has_sufficient_buffer": cash_flow_buffer["has_sufficient_buffer"],
            "is_variable_income": median_pay_gap > 45 and cash_flow_buffer["cash_flow_buffer_months"] < 1.0
        }

