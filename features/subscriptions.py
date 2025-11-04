"""Subscription detection features."""

from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ingest.schema import Transaction, Account


class SubscriptionDetector:
    """Detect subscription patterns from transactions."""
    
    def __init__(self, db_session: Session):
        """Initialize detector.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
    
    def detect_recurring_merchants(
        self, 
        user_id: str, 
        start_date: datetime, 
        end_date: datetime,
        min_occurrences: int = 3,
        window_days: int = 90
    ) -> List[Dict[str, Any]]:
        """Detect recurring merchants (subscriptions).
        
        Args:
            user_id: User ID
            start_date: Analysis start date
            end_date: Analysis end date
            min_occurrences: Minimum occurrences to consider recurring
            window_days: Time window for recurrence detection (default 90 days)
        
        Returns:
            List of recurring merchant patterns
        """
        # Get all transactions for user in date range
        transactions = self.db.query(Transaction).join(Account).filter(
            and_(
                Account.user_id == user_id,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
        ).all()
        
        # Group by merchant name
        merchant_transactions = defaultdict(list)
        for tx in transactions:
            if tx.merchant_name and tx.amount < 0:  # Only expenses
                merchant_transactions[tx.merchant_name].append(tx)
        
        recurring_merchants = []
        
        for merchant_name, txs in merchant_transactions.items():
            if len(txs) < min_occurrences:
                continue
            
            # Sort by date
            txs_sorted = sorted(txs, key=lambda x: x.date)
            
            # Check if transactions occur at regular intervals (monthly or weekly)
            intervals = []
            for i in range(1, len(txs_sorted)):
                days_between = (txs_sorted[i].date - txs_sorted[i-1].date).days
                intervals.append(days_between)
            
            # Check for monthly pattern (25-35 days) or weekly (6-8 days)
            avg_interval = sum(intervals) / len(intervals) if intervals else 0
            is_monthly = 25 <= avg_interval <= 35
            is_weekly = 6 <= avg_interval <= 8
            
            if is_monthly or is_weekly:
                total_amount = sum(abs(tx.amount) for tx in txs)
                avg_amount = total_amount / len(txs)
                
                recurring_merchants.append({
                    "merchant_name": merchant_name,
                    "occurrences": len(txs),
                    "cadence": "monthly" if is_monthly else "weekly",
                    "average_interval_days": avg_interval,
                    "total_amount": total_amount,
                    "average_amount": avg_amount,
                    "first_transaction": txs_sorted[0].date,
                    "last_transaction": txs_sorted[-1].date
                })
        
        return recurring_merchants
    
    def calculate_subscription_metrics(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate subscription-related metrics.
        
        Args:
            user_id: User ID
            start_date: Analysis start date
            end_date: Analysis end date
        
        Returns:
            Dictionary with subscription metrics
        """
        recurring = self.detect_recurring_merchants(user_id, start_date, end_date)
        
        # Get all transactions in period
        all_transactions = self.db.query(Transaction).join(Account).filter(
            and_(
                Account.user_id == user_id,
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.amount < 0  # Only expenses
            )
        ).all()
        
        total_spend = sum(abs(tx.amount) for tx in all_transactions)
        subscription_spend = sum(merchant["total_amount"] for merchant in recurring)
        subscription_share = (subscription_spend / total_spend * 100) if total_spend > 0 else 0
        
        # Monthly recurring spend (for last 30 days)
        thirty_days_ago = end_date - timedelta(days=30)
        monthly_recurring = sum(
            merchant["average_amount"] for merchant in recurring
            if merchant["cadence"] == "monthly"
        )
        
        return {
            "recurring_merchants": len(recurring),
            "recurring_merchant_details": recurring,
            "monthly_recurring_spend": monthly_recurring,
            "total_subscription_spend": subscription_spend,
            "subscription_share_of_total": subscription_share,
            "total_spend": total_spend
        }

