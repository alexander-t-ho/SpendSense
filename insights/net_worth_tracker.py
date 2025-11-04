"""Net worth tracking and historical snapshots.

This module calculates net worth and maintains historical snapshots for trend analysis.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from ingest.schema import Account, Liability, NetWorthHistory


class NetWorthTracker:
    """Track net worth and generate historical snapshots."""
    
    def __init__(self, db_session: Session):
        """Initialize tracker.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
    
    def calculate_net_worth(
        self,
        user_id: str,
        as_of_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Calculate current net worth for a user.
        
        Args:
            user_id: User ID
            as_of_date: Date to calculate net worth (defaults to now)
        
        Returns:
            Dictionary with net worth data including:
            - date: Calculation date
            - total_assets: Total assets (checking, savings, investments)
            - total_liabilities: Total liabilities (credit cards, loans)
            - net_worth: Net worth (assets - liabilities)
            - asset_breakdown: Breakdown by asset type
            - liability_breakdown: Breakdown by liability type
        """
        if as_of_date is None:
            as_of_date = datetime.now()
        
        # Get all accounts
        accounts = self.db.query(Account).filter(Account.user_id == user_id).all()
        
        # Calculate assets (depository accounts, investments)
        total_assets = 0.0
        asset_breakdown = defaultdict(float)
        
        for account in accounts:
            if account.type == "depository":
                # Use current balance for assets
                balance = account.current or 0.0
                total_assets += balance
                asset_breakdown[account.subtype or "checking"] += balance
            elif account.type == "investment":
                balance = account.current or 0.0
                total_assets += balance
                asset_breakdown["investment"] += balance
        
        # Calculate liabilities (credit cards, loans)
        total_liabilities = 0.0
        liability_breakdown = defaultdict(float)
        
        for account in accounts:
            if account.type == "credit":
                # Credit card balance (negative for liabilities)
                balance = abs(account.current or 0.0)
                total_liabilities += balance
                liability_breakdown["credit_card"] += balance
            
            elif account.type == "loan":
                # Loan balance
                balance = account.current or 0.0
                total_liabilities += balance
                subtype = account.subtype or "loan"
                liability_breakdown[subtype] += balance
        
        # Also check Liability table for credit card details
        liabilities = self.db.query(Liability).join(Account).filter(
            Account.user_id == user_id
        ).all()
        
        for liability in liabilities:
            if liability.liability_type == "credit_card":
                if liability.last_statement_balance:
                    # Use statement balance if available
                    if "credit_card" not in liability_breakdown:
                        liability_breakdown["credit_card"] = 0.0
                    # Don't double count - already counted from account balance
            elif liability.liability_type in ["mortgage", "student_loan"]:
                # Loan balances are typically in account.current
                pass
        
        # Calculate net worth
        net_worth = total_assets - total_liabilities
        
        return {
            "user_id": user_id,
            "date": as_of_date.isoformat(),
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "net_worth": net_worth,
            "asset_breakdown": dict(asset_breakdown),
            "liability_breakdown": dict(liability_breakdown)
        }
    
    def create_snapshot(
        self,
        user_id: str,
        snapshot_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Create and save a net worth snapshot.
        
        Args:
            user_id: User ID
            snapshot_date: Date for snapshot (defaults to now)
        
        Returns:
            Created snapshot data
        """
        if snapshot_date is None:
            snapshot_date = datetime.now()
        
        # Calculate net worth
        net_worth_data = self.calculate_net_worth(user_id, snapshot_date)
        
        # Create snapshot record
        snapshot_id = f"nw_{user_id}_{snapshot_date.strftime('%Y%m%d')}"
        
        snapshot = NetWorthHistory(
            id=snapshot_id,
            user_id=user_id,
            snapshot_date=snapshot_date,
            total_assets=net_worth_data["total_assets"],
            total_liabilities=net_worth_data["total_liabilities"],
            net_worth=net_worth_data["net_worth"]
        )
        
        # Check if snapshot already exists
        existing = self.db.query(NetWorthHistory).filter(
            NetWorthHistory.id == snapshot_id
        ).first()
        
        if existing:
            # Update existing
            existing.snapshot_date = snapshot_date
            existing.total_assets = net_worth_data["total_assets"]
            existing.total_liabilities = net_worth_data["total_liabilities"]
            existing.net_worth = net_worth_data["net_worth"]
            self.db.commit()
        else:
            # Create new
            self.db.add(snapshot)
            self.db.commit()
        
        return {
            **net_worth_data,
            "snapshot_id": snapshot_id,
            "saved": True
        }
    
    def get_net_worth_history(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: str = "month"
    ) -> Dict[str, Any]:
        """Get historical net worth data.
        
        Args:
            user_id: User ID
            start_date: Start date (defaults to 6 months ago)
            end_date: End date (defaults to now)
            period: Aggregation period (week, month)
        
        Returns:
            Dictionary with historical net worth data
        """
        if end_date is None:
            end_date = datetime.now()
        
        if start_date is None:
            if period == "week":
                start_date = end_date - timedelta(days=90)  # 13 weeks
            else:
                start_date = end_date - timedelta(days=180)  # 6 months
        
        # Get snapshots
        snapshots = self.db.query(NetWorthHistory).filter(
            and_(
                NetWorthHistory.user_id == user_id,
                NetWorthHistory.snapshot_date >= start_date,
                NetWorthHistory.snapshot_date <= end_date
            )
        ).order_by(NetWorthHistory.snapshot_date.asc()).all()
        
        # If no snapshots, create current one
        if not snapshots:
            current = self.create_snapshot(user_id, end_date)
            snapshots = [NetWorthHistory(
                id=current["snapshot_id"],
                user_id=user_id,
                snapshot_date=datetime.fromisoformat(current["date"]),
                total_assets=current["total_assets"],
                total_liabilities=current["total_liabilities"],
                net_worth=current["net_worth"]
            )]
        
        # Format snapshots
        history_data = []
        for snapshot in snapshots:
            history_data.append({
                "date": snapshot.snapshot_date.isoformat(),
                "total_assets": snapshot.total_assets,
                "total_liabilities": snapshot.total_liabilities,
                "net_worth": snapshot.net_worth
            })
        
        # Calculate trends
        if len(history_data) > 1:
            first = history_data[0]
            last = history_data[-1]
            net_worth_change = last["net_worth"] - first["net_worth"]
            percentage_change = (net_worth_change / abs(first["net_worth"]) * 100) if first["net_worth"] != 0 else 0.0
        else:
            net_worth_change = 0.0
            percentage_change = 0.0
        
        return {
            "user_id": user_id,
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "snapshots": history_data,
            "net_worth_change": net_worth_change,
            "percentage_change": percentage_change,
            "current_net_worth": history_data[-1]["net_worth"] if history_data else 0.0
        }

