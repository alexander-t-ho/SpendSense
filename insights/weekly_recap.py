"""Weekly spending recap computation."""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ingest.schema import Account, Transaction
from insights.utils import get_week_start, get_week_end, calculate_percentage_change


class WeeklyRecapAnalyzer:
    """Analyze weekly spending patterns and generate recaps."""
    
    def __init__(self, db_session: Session):
        """Initialize analyzer.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
    
    def compute_weekly_recap(
        self,
        user_id: str,
        week_start_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Compute weekly spending recap for a user.
        
        Args:
            user_id: User ID
            week_start_date: Start date of the week (defaults to current week's Monday)
        
        Returns:
            Dictionary with weekly recap data including:
            - week_start: Start date of the week
            - week_end: End date of the week
            - total_spending: Total spending for the week
            - daily_spending: List of daily spending amounts (7 days)
            - top_category: Category with highest spending
            - category_breakdown: Spending by category
            - previous_week_total: Total spending for previous week
            - week_over_week_change: Percentage change from previous week
            - insights: List of plain-language insights
        """
        # Default to current week
        if week_start_date is None:
            week_start_date = get_week_start(datetime.now())
        
        week_end_date = get_week_end(week_start_date)
        previous_week_start = week_start_date - timedelta(days=7)
        previous_week_end = week_end_date - timedelta(days=7)
        
        # Get all user accounts
        accounts = self.db.query(Account).filter(Account.user_id == user_id).all()
        account_ids = [acc.id for acc in accounts]
        
        if not account_ids:
            return self._empty_recap(week_start_date, week_end_date)
        
        # Get transactions for current week
        current_week_txs = self.db.query(Transaction).filter(
            and_(
                Transaction.account_id.in_(account_ids),
                Transaction.date >= week_start_date,
                Transaction.date <= week_end_date,
                Transaction.amount < 0  # Only expenses (negative amounts)
            )
        ).all()
        
        # Get transactions for previous week
        previous_week_txs = self.db.query(Transaction).filter(
            and_(
                Transaction.account_id.in_(account_ids),
                Transaction.date >= previous_week_start,
                Transaction.date <= previous_week_end,
                Transaction.amount < 0
            )
        ).all()
        
        # Calculate daily spending (7 days)
        daily_spending = self._calculate_daily_spending(current_week_txs, week_start_date)
        
        # Calculate category breakdown
        category_breakdown = self._calculate_category_breakdown(current_week_txs)
        
        # Find top category
        top_category = max(category_breakdown.items(), key=lambda x: x[1]) if category_breakdown else None
        
        # Calculate totals
        total_spending = abs(sum(tx.amount for tx in current_week_txs))
        previous_week_total = abs(sum(tx.amount for tx in previous_week_txs))
        
        # Calculate week-over-week change
        week_over_week_change = calculate_percentage_change(previous_week_total, total_spending)
        
        # Generate insights
        insights = self._generate_insights(
            total_spending,
            previous_week_total,
            week_over_week_change,
            top_category,
            category_breakdown,
            previous_week_txs
        )
        
        return {
            "week_start": week_start_date.isoformat(),
            "week_end": week_end_date.isoformat(),
            "total_spending": total_spending,
            "daily_spending": daily_spending,
            "top_category": top_category[0] if top_category else None,
            "top_category_amount": top_category[1] if top_category else 0,
            "category_breakdown": category_breakdown,
            "previous_week_total": previous_week_total,
            "week_over_week_change": week_over_week_change,
            "insights": insights
        }
    
    def _calculate_daily_spending(
        self,
        transactions: List[Transaction],
        week_start: datetime
    ) -> List[Dict[str, Any]]:
        """Calculate spending for each day of the week.
        
        Args:
            transactions: List of transactions
            week_start: Start date of the week
        
        Returns:
            List of daily spending data with day number and amount
        """
        daily_totals = defaultdict(float)
        
        for tx in transactions:
            # Get day of week (0 = Monday, 6 = Sunday)
            day_offset = (tx.date.date() - week_start.date()).days
            if 0 <= day_offset < 7:
                daily_totals[day_offset] += abs(tx.amount)
        
        # Create list for all 7 days
        daily_spending = []
        for day in range(7):
            daily_spending.append({
                "day": day + 1,  # 1-7
                "date": (week_start + timedelta(days=day)).date().isoformat(),
                "amount": daily_totals.get(day, 0)
            })
        
        return daily_spending
    
    def _calculate_category_breakdown(
        self,
        transactions: List[Transaction]
    ) -> Dict[str, float]:
        """Calculate spending by category.
        
        Args:
            transactions: List of transactions
        
        Returns:
            Dictionary mapping category to total spending
        """
        category_totals = defaultdict(float)
        
        for tx in transactions:
            category = tx.primary_category or "Uncategorized"
            category_totals[category] += abs(tx.amount)
        
        return dict(category_totals)
    
    def _generate_insights(
        self,
        total_spending: float,
        previous_week_total: float,
        week_over_week_change: float,
        top_category: Optional[tuple],
        category_breakdown: Dict[str, float],
        previous_week_txs: List[Transaction]
    ) -> List[str]:
        """Generate plain-language insights.
        
        Args:
            total_spending: Current week total
            previous_week_total: Previous week total
            week_over_week_change: Percentage change
            top_category: (category_name, amount) tuple
            category_breakdown: Current week category breakdown
            previous_week_txs: Previous week transactions
        
        Returns:
            List of insight strings
        """
        insights = []
        
        # Overall spending trend
        if abs(week_over_week_change) < 1:
            insights.append("Spending remained relatively stable this week.")
        elif week_over_week_change > 0:
            insights.append(f"Spending was up {week_over_week_change:.1f}% this week compared to last week.")
        else:
            insights.append(f"Spending was down {abs(week_over_week_change):.1f}% this week compared to last week.")
        
        # Top category
        if top_category:
            category_name, category_amount = top_category
            category_share = (category_amount / total_spending * 100) if total_spending > 0 else 0
            
            # Calculate previous week for this category
            prev_category_total = sum(
                abs(tx.amount)
                for tx in previous_week_txs
                if (tx.primary_category or "Uncategorized") == category_name
            )
            
            if prev_category_total > 0:
                category_change = calculate_percentage_change(prev_category_total, category_amount)
                if category_change > 0:
                    insights.append(
                        f"You spent ${category_amount:,.2f} on {category_name} — "
                        f"a {category_change:.0f}% increase from the week prior — "
                        f"making it your top category ({category_share:.0f}% of total spending)."
                    )
                elif category_change < 0:
                    insights.append(
                        f"You spent ${category_amount:,.2f} on {category_name} — "
                        f"a {abs(category_change):.0f}% decrease from the week prior — "
                        f"making it your top category ({category_share:.0f}% of total spending)."
                    )
                else:
                    insights.append(
                        f"You spent ${category_amount:,.2f} on {category_name}, "
                        f"making it your top category ({category_share:.0f}% of total spending)."
                    )
            else:
                insights.append(
                    f"You spent ${category_amount:,.2f} on {category_name}, "
                    f"making it your top category ({category_share:.0f}% of total spending)."
                )
        
        # Additional category insights
        sorted_categories = sorted(category_breakdown.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_categories) > 1:
            second_category = sorted_categories[1]
            insights.append(
                f"{second_category[0]} came in second at ${second_category[1]:,.2f}."
            )
        
        return insights
    
    def _empty_recap(self, week_start: datetime, week_end: datetime) -> Dict[str, Any]:
        """Return empty recap structure.
        
        Args:
            week_start: Week start date
            week_end: Week end date
        
        Returns:
            Empty recap dictionary
        """
        return {
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "total_spending": 0,
            "daily_spending": [
                {"day": i + 1, "date": (week_start + timedelta(days=i)).date().isoformat(), "amount": 0}
                for i in range(7)
            ],
            "top_category": None,
            "top_category_amount": 0,
            "category_breakdown": {},
            "previous_week_total": 0,
            "week_over_week_change": 0,
            "insights": ["No spending data available for this week."]
        }

