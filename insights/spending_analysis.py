"""6-month spending analysis for financial insights.

This module provides 6-month spending analysis including:
- Monthly spending aggregations
- Income stability analysis
- Spending tightness (spending vs income)
- Cash-flow buffer status
- Key insights in plain language
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ingest.schema import Account, Transaction
from insights.utils import calculate_percentage_change


class SpendingAnalysisAnalyzer:
    """Analyze 6-month spending patterns and generate insights."""
    
    def __init__(self, db_session: Session):
        """Initialize analyzer.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
    
    def compute_spending_analysis(
        self,
        user_id: str,
        months: int = 6
    ) -> Dict[str, Any]:
        """Compute 6-month spending analysis for a user.
        
        Args:
            user_id: User ID
            months: Number of months to analyze (default 6)
        
        Returns:
            Dictionary with spending analysis data including:
            - period_start: Start date of analysis period
            - period_end: End date of analysis period
            - monthly_breakdown: List of monthly spending totals
            - total_spending: Total spending over period
            - average_monthly_spending: Average monthly spending
            - income_stability: Income stability metrics
            - spending_tightness: Spending vs income ratio
            - cash_flow_buffer: Buffer in months
            - insights: List of plain-language insights (3 key insights)
        """
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)  # Approximate months
        
        # Fetch all accounts for the user
        user_accounts = self.db.query(Account).filter(Account.user_id == user_id).all()
        account_ids = [acc.id for acc in user_accounts]
        
        if not account_ids:
            return {
                "user_id": user_id,
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "months": months,
                "monthly_breakdown": [],
                "total_spending": 0.0,
                "average_monthly_spending": 0.0,
                "income_stability": {
                    "status": "unknown",
                    "average_monthly_income": 0.0,
                    "income_volatility": 0.0,
                    "payment_frequency": "unknown"
                },
                "spending_tightness": {
                    "ratio": 0.0,
                    "status": "unknown",
                    "average_income": 0.0,
                    "average_spending": 0.0
                },
                "cash_flow_buffer": {
                    "months": 0.0,
                    "status": "unknown",
                    "checking_balance": 0.0,
                    "average_monthly_expenses": 0.0
                },
                "insights": ["No transaction data found for this period."]
            }
        
        # Get all transactions in the period
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
        
        # Monthly breakdown
        monthly_expenses = defaultdict(float)
        monthly_income = defaultdict(float)
        
        for tx in expenses:
            month_key = tx.date.strftime("%Y-%m")
            monthly_expenses[month_key] += abs(tx.amount)
        
        for tx in income:
            month_key = tx.date.strftime("%Y-%m")
            monthly_income[month_key] += abs(tx.amount)
        
        # Create monthly breakdown list
        monthly_breakdown = []
        current_date = start_date
        while current_date <= end_date:
            month_key = current_date.strftime("%Y-%m")
            monthly_breakdown.append({
                "month": month_key,
                "date": current_date.isoformat(),
                "spending": monthly_expenses[month_key],
                "income": monthly_income[month_key],
                "net": monthly_income[month_key] - monthly_expenses[month_key]
            })
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1, day=1)
        
        # Calculate totals and averages
        total_spending = sum(monthly_expenses.values())
        total_income = sum(monthly_income.values())
        average_monthly_spending = total_spending / months if months > 0 else 0.0
        average_monthly_income = total_income / months if months > 0 else 0.0
        
        # Income stability analysis
        income_amounts = list(monthly_income.values())
        if income_amounts:
            # Calculate volatility (coefficient of variation)
            if average_monthly_income > 0:
                # Calculate standard deviation manually (avoid numpy dependency)
                if len(income_amounts) > 1:
                    mean = sum(income_amounts) / len(income_amounts)
                    variance = sum((x - mean) ** 2 for x in income_amounts) / len(income_amounts)
                    std_dev = variance ** 0.5
                    income_volatility = std_dev / average_monthly_income if average_monthly_income > 0 else 0.0
                else:
                    income_volatility = 0.0
            else:
                income_volatility = 0.0
            
            # Determine payment frequency (simplified)
            if len(income_amounts) >= 4:
                # Look at frequency of income payments
                payment_frequency = "monthly" if income_volatility < 0.2 else "variable"
            else:
                payment_frequency = "unknown"
            
            # Income stability status
            if income_volatility < 0.1:
                income_status = "stable"
            elif income_volatility < 0.3:
                income_status = "moderately_stable"
            else:
                income_status = "variable"
        else:
            income_volatility = 0.0
            payment_frequency = "unknown"
            income_status = "unknown"
        
        # Spending tightness (spending as % of income)
        spending_tightness_ratio = 0.0
        if average_monthly_income > 0:
            spending_tightness_ratio = (average_monthly_spending / average_monthly_income) * 100
        
        if spending_tightness_ratio < 50:
            tightness_status = "comfortable"
        elif spending_tightness_ratio < 80:
            tightness_status = "moderate"
        elif spending_tightness_ratio < 100:
            tightness_status = "tight"
        else:
            tightness_status = "overspending"
        
        # Cash-flow buffer (checking balance / average monthly expenses)
        checking_accounts = [acc for acc in user_accounts if acc.type == "depository" and acc.subtype == "checking"]
        checking_balance = sum(acc.available or 0 for acc in checking_accounts)
        
        cash_flow_buffer_months = 0.0
        if average_monthly_spending > 0:
            cash_flow_buffer_months = checking_balance / average_monthly_spending
        
        if cash_flow_buffer_months >= 6:
            buffer_status = "excellent"
        elif cash_flow_buffer_months >= 3:
            buffer_status = "good"
        elif cash_flow_buffer_months >= 1:
            buffer_status = "adequate"
        else:
            buffer_status = "low"
        
        # Generate 3 key insights
        insights = []
        
        # Insight 1: Spending tightness
        if spending_tightness_ratio > 0:
            if tightness_status == "overspending":
                insights.append(
                    f"Your spending exceeds your income by {spending_tightness_ratio - 100:.1f}% on average. "
                    f"Consider reviewing your expenses to identify areas for reduction."
                )
            elif tightness_status == "tight":
                insights.append(
                    f"You're spending {spending_tightness_ratio:.1f}% of your income on average. "
                    f"Building a buffer could provide more financial flexibility."
                )
            elif tightness_status == "comfortable":
                insights.append(
                    f"Great job! You're spending {spending_tightness_ratio:.1f}% of your income on average, "
                    f"leaving room for savings and investments."
                )
            else:
                insights.append(
                    f"Your spending is {spending_tightness_ratio:.1f}% of your income on average, "
                    f"indicating a moderate spending pattern."
                )
        
        # Insight 2: Income stability
        if income_status != "unknown":
            if income_status == "stable":
                insights.append(
                    f"Your income is stable with low volatility. This consistency helps with budgeting and planning."
                )
            elif income_status == "variable":
                insights.append(
                    f"Your income shows variability. Consider building a larger emergency fund "
                    f"to smooth out income fluctuations."
                )
            else:
                insights.append(
                    f"Your income shows moderate variability. A budget based on your lowest monthly income "
                    f"can help manage uncertainty."
                )
        
        # Insight 3: Cash-flow buffer
        if cash_flow_buffer_months > 0:
            if buffer_status == "low":
                insights.append(
                    f"Your cash-flow buffer is {cash_flow_buffer_months:.1f} months, which is below recommended levels. "
                    f"Aim to build at least 3-6 months of expenses as an emergency fund."
                )
            elif buffer_status == "excellent":
                insights.append(
                    f"Excellent! You have {cash_flow_buffer_months:.1f} months of expenses in your checking account, "
                    f"providing strong financial security."
                )
            else:
                insights.append(
                    f"You have {cash_flow_buffer_months:.1f} months of expenses in your checking account. "
                    f"Consider continuing to build your emergency fund for greater financial resilience."
                )
        
        # Ensure we have exactly 3 insights
        while len(insights) < 3:
            insights.append("Continue monitoring your spending patterns to identify opportunities for improvement.")
        
        return {
            "user_id": user_id,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "months": months,
            "monthly_breakdown": monthly_breakdown[:months],  # Limit to requested months
            "total_spending": total_spending,
            "average_monthly_spending": average_monthly_spending,
            "total_income": total_income,
            "average_monthly_income": average_monthly_income,
            "income_stability": {
                "status": income_status,
                "average_monthly_income": average_monthly_income,
                "income_volatility": float(income_volatility),
                "payment_frequency": payment_frequency
            },
            "spending_tightness": {
                "ratio": spending_tightness_ratio,
                "status": tightness_status,
                "average_income": average_monthly_income,
                "average_spending": average_monthly_spending
            },
            "cash_flow_buffer": {
                "months": cash_flow_buffer_months,
                "status": buffer_status,
                "checking_balance": checking_balance,
                "average_monthly_expenses": average_monthly_spending
            },
            "insights": insights[:3]  # Return exactly 3 insights
        }

