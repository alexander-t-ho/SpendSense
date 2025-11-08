"""Shared utilities for payroll detection and income calculation."""

from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ingest.schema import Account, Transaction


class PayrollDetector:
    """Utility class for detecting payroll transactions across all depository accounts."""
    
    @staticmethod
    def detect_payroll_transactions(
        db_session: Session,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
        min_amount: float = 1000.0
    ) -> List[Transaction]:
        """Detect payroll transactions using flexible pattern matching.
        
        This method searches all depository accounts (checking, savings) for transactions
        that match payroll patterns. This is the standard method used across the codebase.
        
        Args:
            db_session: Database session
            user_id: User ID
            start_date: Analysis start date
            end_date: Analysis end date
            min_amount: Minimum transaction amount to consider (default $1000)
        
        Returns:
            List of Transaction objects matching payroll patterns
        """
        # Get all depository accounts (checking, savings)
        depository_accounts = db_session.query(Account).filter(
            and_(
                Account.user_id == user_id,
                Account.type == 'depository'
            )
        ).all()
        
        if not depository_accounts:
            return []
        
        depository_account_ids = [acc.id for acc in depository_accounts]
        
        # Query for payroll transactions using flexible pattern matching
        # Matches transactions with "PAYROLL" or "DEPOSIT" in merchant name, or "Transfer In" category
        payroll_transactions = db_session.query(Transaction).filter(
            and_(
                Transaction.account_id.in_(depository_account_ids),
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.amount > 0,  # Only positive amounts (deposits)
                or_(
                    Transaction.merchant_name.like("%PAYROLL%"),
                    Transaction.merchant_name.like("%DEPOSIT%"),
                    Transaction.primary_category == "Transfer In"
                ),
                Transaction.amount >= min_amount
            )
        ).all()
        
        return payroll_transactions
    
    @staticmethod
    def calculate_monthly_income_from_payroll(
        payroll_transactions: List[Transaction],
        days_in_period: int = 180
    ) -> float:
        """Calculate monthly average income from payroll transactions.
        
        Uses the formula: (period_total / days_in_period) * 365 / 12
        This matches the calculation used in the Income Analysis card.
        
        Args:
            payroll_transactions: List of payroll Transaction objects
            days_in_period: Number of days in the analysis period (default 180)
        
        Returns:
            Monthly average income, or 0.0 if no transactions
        """
        if not payroll_transactions:
            return 0.0
        
        # Calculate total income over the period
        period_total = sum(tx.amount for tx in payroll_transactions)
        
        # Calculate yearly income: (period_total / days_in_period) * 365
        yearly_income = (period_total / float(days_in_period)) * 365.0
        
        # Calculate monthly average: yearly_income / 12
        monthly_income = yearly_income / 12.0
        
        return monthly_income

