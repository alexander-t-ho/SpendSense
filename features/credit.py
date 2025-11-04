"""Credit analysis features."""

from datetime import datetime, timedelta
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ingest.schema import Account, Liability, Transaction


class CreditAnalyzer:
    """Analyze credit card utilization and patterns."""
    
    def __init__(self, db_session: Session):
        """Initialize analyzer.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
    
    def get_credit_cards(self, user_id: str) -> List[Account]:
        """Get all credit card accounts for user.
        
        Args:
            user_id: User ID
        
        Returns:
            List of credit card accounts
        """
        return self.db.query(Account).filter(
            and_(
                Account.user_id == user_id,
                Account.type == "credit",
                Account.subtype == "credit_card"
            )
        ).all()
    
    def calculate_utilization(self, account: Account) -> Dict[str, Any]:
        """Calculate utilization for a credit card.
        
        Args:
            account: Credit card account
        
        Returns:
            Dictionary with utilization metrics
        """
        if not account.limit or account.limit == 0:
            return {
                "account_id": account.account_id,
                "utilization_percent": 0.0,
                "balance": account.current or 0.0,
                "limit": 0.0,
                "available": 0.0,
                "is_high_utilization_30": False,
                "is_high_utilization_50": False,
                "is_high_utilization_80": False
            }
        
        balance = abs(account.current or 0.0)
        limit = account.limit
        utilization = (balance / limit) * 100
        
        return {
            "account_id": account.account_id,
            "utilization_percent": utilization,
            "balance": balance,
            "limit": limit,
            "available": limit - balance,
            "is_high_utilization_30": utilization >= 30.0,
            "is_high_utilization_50": utilization >= 50.0,
            "is_high_utilization_80": utilization >= 80.0
        }
    
    def detect_minimum_payment_only(
        self,
        account: Account,
        start_date: datetime,
        end_date: datetime
    ) -> bool:
        """Detect if user is making minimum payments only.
        
        Args:
            account: Credit card account
            start_date: Analysis start date
            end_date: Analysis end date
        
        Returns:
            True if minimum-payment-only pattern detected
        """
        # Get liability info
        liability = self.db.query(Liability).filter(
            Liability.account_id == account.id
        ).first()
        
        if not liability or not liability.minimum_payment_amount:
            return False
        
        # Get payment transactions
        payments = self.db.query(Transaction).filter(
            and_(
                Transaction.account_id == account.id,
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.amount > 0,  # Payments are positive (credits)
                Transaction.merchant_name.like("%PAYMENT%")
            )
        ).all()
        
        if not payments:
            return False
        
        # Check if payments are close to minimum (within 5% tolerance)
        min_payment = liability.minimum_payment_amount
        tolerance = min_payment * 0.05
        
        for payment in payments:
            payment_amount = abs(payment.amount)
            if abs(payment_amount - min_payment) > tolerance:
                return False  # Found a payment significantly above minimum
        
        return True  # All payments are minimum payments
    
    def detect_interest_charges(
        self,
        account: Account,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Detect interest charges on credit card.
        
        Args:
            account: Credit card account
            start_date: Analysis start date
            end_date: Analysis end date
        
        Returns:
            Dictionary with interest charge information
        """
        # Look for interest/fee transactions
        interest_transactions = self.db.query(Transaction).filter(
            and_(
                Transaction.account_id == account.id,
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.amount < 0,  # Charges are negative
                (
                    Transaction.merchant_name.like("%INTEREST%") |
                    Transaction.merchant_name.like("%FEE%") |
                    Transaction.primary_category.like("%Interest%")
                )
            )
        ).all()
        
        total_interest = sum(abs(tx.amount) for tx in interest_transactions)
        
        return {
            "has_interest_charges": len(interest_transactions) > 0,
            "total_interest_charges": total_interest,
            "monthly_interest_estimate": total_interest / max(1, (end_date - start_date).days / 30.0),
            "interest_transactions": len(interest_transactions)
        }
    
    def check_overdue_status(self, account: Account) -> bool:
        """Check if credit card payment is overdue.
        
        Args:
            account: Credit card account
        
        Returns:
            True if overdue
        """
        liability = self.db.query(Liability).filter(
            Liability.account_id == account.id
        ).first()
        
        if not liability:
            return False
        
        return liability.is_overdue or False
    
    def calculate_credit_metrics(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate all credit-related metrics.
        
        Args:
            user_id: User ID
            start_date: Analysis start date
            end_date: Analysis end date
        
        Returns:
            Dictionary with all credit metrics
        """
        credit_cards = self.get_credit_cards(user_id)
        
        if not credit_cards:
            return {
                "has_credit_cards": False,
                "total_cards": 0,
                "any_high_utilization_50": False,
                "any_high_utilization_80": False,
                "any_interest_charges": False,
                "any_minimum_payment_only": False,
                "any_overdue": False,
                "card_details": []
            }
        
        card_details = []
        any_high_util_50 = False
        any_high_util_80 = False
        any_interest = False
        any_min_payment = False
        any_overdue = False
        
        for card in credit_cards:
            utilization = self.calculate_utilization(card)
            interest_info = self.detect_interest_charges(card, start_date, end_date)
            min_payment_only = self.detect_minimum_payment_only(card, start_date, end_date)
            overdue = self.check_overdue_status(card)
            
            if utilization["is_high_utilization_50"]:
                any_high_util_50 = True
            if utilization["is_high_utilization_80"]:
                any_high_util_80 = True
            if interest_info["has_interest_charges"]:
                any_interest = True
            if min_payment_only:
                any_min_payment = True
            if overdue:
                any_overdue = True
            
            card_details.append({
                "account_id": card.account_id,
                "name": card.name,
                "utilization": utilization,
                "interest_charges": interest_info,
                "minimum_payment_only": min_payment_only,
                "is_overdue": overdue
            })
        
        return {
            "has_credit_cards": True,
            "total_cards": len(credit_cards),
            "any_high_utilization_50": any_high_util_50,
            "any_high_utilization_80": any_high_util_80,
            "any_interest_charges": any_interest,
            "any_minimum_payment_only": any_min_payment,
            "any_overdue": any_overdue,
            "card_details": card_details
        }

