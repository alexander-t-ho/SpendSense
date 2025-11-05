"""Fee detection and analysis features."""

from datetime import datetime, timedelta
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ingest.schema import Account, Transaction


class FeeAnalyzer:
    """Analyze banking fees and charges."""
    
    def __init__(self, db_session: Session):
        """Initialize analyzer.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
    
    def detect_fees_90d(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Detect various fee types in the last 90 days.
        
        Args:
            user_id: User ID
            start_date: Analysis start date
            end_date: Analysis end date
            
        Returns:
            Dictionary with fee counts by type
        """
        # Get all accounts for user
        accounts = self.db.query(Account).filter(Account.user_id == user_id).all()
        
        fee_counts = {
            "overdraft_fees": 0,
            "nsf_fees": 0,
            "atm_fees": 0,
            "late_payment_fees": 0,
            "maintenance_fees": 0,
            "total_fees": 0
        }
        
        fee_transactions = []
        
        for account in accounts:
            transactions = self.db.query(Transaction).filter(
                and_(
                    Transaction.account_id == account.id,
                    Transaction.date >= start_date,
                    Transaction.date <= end_date,
                    Transaction.amount < 0  # Fees are negative
                )
            ).all()
            
            for tx in transactions:
                merchant_upper = (tx.merchant_name or "").upper()
                category_upper = (tx.primary_category or "").upper()
                detailed_upper = (tx.detailed_category or "").upper()
                
                # Check for overdraft fees
                if any(term in merchant_upper for term in ["OVERDRAFT", "OD FEE", "OD CHARGE"]):
                    fee_counts["overdraft_fees"] += 1
                    fee_transactions.append({"type": "overdraft", "amount": abs(tx.amount), "date": tx.date})
                
                # Check for NSF fees
                elif any(term in merchant_upper for term in ["NSF", "INSUFFICIENT FUNDS", "INSUFF FUNDS", "NON-SUFFICIENT"]):
                    fee_counts["nsf_fees"] += 1
                    fee_transactions.append({"type": "nsf", "amount": abs(tx.amount), "date": tx.date})
                
                # Check for ATM fees
                elif any(term in merchant_upper for term in ["ATM FEE", "ATM SURCHARGE", "OUT OF NETWORK ATM", "OON ATM"]):
                    fee_counts["atm_fees"] += 1
                    fee_transactions.append({"type": "atm", "amount": abs(tx.amount), "date": tx.date})
                
                # Check for late payment fees
                elif any(term in merchant_upper for term in ["LATE", "PAST DUE", "LATE PAYMENT", "LATE FEE"]):
                    fee_counts["late_payment_fees"] += 1
                    fee_transactions.append({"type": "late_payment", "amount": abs(tx.amount), "date": tx.date})
                
                # Check for maintenance fees
                elif any(term in merchant_upper for term in ["MAINTENANCE", "MONTHLY FEE", "SERVICE CHARGE", "ACCOUNT FEE"]):
                    fee_counts["maintenance_fees"] += 1
                    fee_transactions.append({"type": "maintenance", "amount": abs(tx.amount), "date": tx.date})
                
                # Also check categories
                if "FEE" in category_upper or "FEE" in detailed_upper:
                    # Try to categorize based on amount patterns
                    fee_amount = abs(tx.amount)
                    if fee_amount <= 5.0:  # Small fees are often ATM
                        if fee_counts["atm_fees"] == 0 or tx.merchant_name not in [f["merchant"] for f in fee_transactions if f.get("merchant")]:
                            fee_counts["atm_fees"] += 1
                    elif fee_amount >= 25.0:  # Larger fees are often overdraft/NSF
                        if fee_counts["overdraft_fees"] == 0 and fee_counts["nsf_fees"] == 0:
                            fee_counts["overdraft_fees"] += 1
        
        fee_counts["total_fees"] = sum([
            fee_counts["overdraft_fees"],
            fee_counts["nsf_fees"],
            fee_counts["atm_fees"],
            fee_counts["late_payment_fees"],
            fee_counts["maintenance_fees"]
        ])
        
        return {
            **fee_counts,
            "fee_transactions": fee_transactions
        }
    
    def calculate_total_fees(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """Calculate total fees in date range.
        
        Args:
            user_id: User ID
            start_date: Analysis start date
            end_date: Analysis end date
            
        Returns:
            Total fee amount
        """
        accounts = self.db.query(Account).filter(Account.user_id == user_id).all()
        
        total_fees = 0.0
        
        for account in accounts:
            transactions = self.db.query(Transaction).filter(
                and_(
                    Transaction.account_id == account.id,
                    Transaction.date >= start_date,
                    Transaction.date <= end_date,
                    Transaction.amount < 0  # Fees are negative
                )
            ).all()
            
            for tx in transactions:
                merchant_upper = (tx.merchant_name or "").upper()
                category_upper = (tx.primary_category or "").upper()
                
                # Check if transaction is a fee
                if any(term in merchant_upper for term in [
                    "FEE", "OVERDRAFT", "NSF", "ATM", "LATE", "MAINTENANCE",
                    "SERVICE CHARGE", "CHARGE"
                ]) or "FEE" in category_upper:
                    total_fees += abs(tx.amount)
        
        return total_fees
    
    def count_late_payment_accounts(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """Count number of accounts with late payment fees.
        
        Args:
            user_id: User ID
            start_date: Analysis start date
            end_date: Analysis end date
            
        Returns:
            Count of accounts with late payment fees
        """
        accounts = self.db.query(Account).filter(Account.user_id == user_id).all()
        
        accounts_with_late_fees = set()
        
        for account in accounts:
            transactions = self.db.query(Transaction).filter(
                and_(
                    Transaction.account_id == account.id,
                    Transaction.date >= start_date,
                    Transaction.date <= end_date,
                    Transaction.amount < 0
                )
            ).all()
            
            for tx in transactions:
                merchant_upper = (tx.merchant_name or "").upper()
                if any(term in merchant_upper for term in ["LATE", "PAST DUE", "LATE PAYMENT", "LATE FEE"]):
                    accounts_with_late_fees.add(account.id)
                    break  # Only count account once
        
        return len(accounts_with_late_fees)
    
    def get_fee_metrics(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get comprehensive fee metrics.
        
        Args:
            user_id: User ID
            start_date: Analysis start date
            end_date: Analysis end date
            
        Returns:
            Dictionary with all fee metrics
        """
        fees_90d = self.detect_fees_90d(user_id, start_date, end_date)
        
        # Calculate fees for last month (30 days)
        one_month_ago = end_date - timedelta(days=30)
        total_fees_last_month = self.calculate_total_fees(user_id, one_month_ago, end_date)
        
        # Count accounts with late fees
        accounts_with_late_fees = self.count_late_payment_accounts(user_id, start_date, end_date)
        
        # Check for maintenance fees on checking/savings
        maintenance_fees = fees_90d["maintenance_fees"]
        has_maintenance_fees = maintenance_fees > 0
        
        return {
            "overdraft_nsf_fees_90d": fees_90d["overdraft_fees"] + fees_90d["nsf_fees"],
            "total_fees_last_month": total_fees_last_month,
            "atm_fees_90d": fees_90d["atm_fees"],
            "accounts_with_late_fees": accounts_with_late_fees,
            "has_maintenance_fees": has_maintenance_fees,
            "maintenance_fees_90d": maintenance_fees,
            "total_fees_90d": fees_90d["total_fees"],
            **fees_90d
        }

