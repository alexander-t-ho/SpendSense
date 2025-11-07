"""Budget calculator for AI-suggested monthly budgets.

This module generates personalized budget suggestions based on historical
spending patterns, income stability, and financial goals.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
import math
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ingest.schema import Account, Transaction, Budget
from insights.utils import calculate_percentage_change


class BudgetCalculator:
    """Calculate AI-suggested budgets based on historical data."""
    
    def __init__(self, db_session: Session):
        """Initialize calculator.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
    
    def suggest_budget(
        self,
        user_id: str,
        month: Optional[datetime] = None,
        lookback_months: int = 6
    ) -> Dict[str, Any]:
        """Generate AI-suggested monthly budget for a user.
        
        Args:
            user_id: User ID
            month: Target month (defaults to next month)
            lookback_months: Number of months to analyze for suggestions
        
        Returns:
            Dictionary with suggested budget including:
            - month: Target month
            - total_budget: Total monthly budget
            - category_budgets: Suggested budgets by category
            - rationale: Plain-language explanation
            - income_based: Income-based budget suggestion
            - expense_based: Expense-based budget suggestion
        """
        # Default to next month
        if month is None:
            month = datetime.now().replace(day=1) + timedelta(days=32)
            month = month.replace(day=1)  # First day of next month
        
        # Calculate date range for analysis
        start_date = month - timedelta(days=lookback_months * 30)
        end_date = month - timedelta(days=1)  # Up to the month before target
        
        # Get ALL accounts for the user (including credit cards and loans)
        # This ensures spending across all accounts is included in budget analysis
        user_accounts = self.db.query(Account).filter(
            Account.user_id == user_id
        ).all()
        all_account_ids = [acc.id for acc in user_accounts]
        
        # Get depository accounts separately for income tracking
        # (Income typically only flows into checking/savings accounts)
        depository_accounts = [acc for acc in user_accounts if acc.type == 'depository']
        depository_account_ids = [acc.id for acc in depository_accounts]
        
        if not all_account_ids:
            return {
                "user_id": user_id,
                "month": month.strftime("%Y-%m"),
                "total_budget": 0.0,
                "category_budgets": {},
                "rationale": "No account data available for budget suggestions.",
                "income_based": 0.0,
                "expense_based": 0.0
            }
        
        # Get ALL transactions for spending analysis (from all accounts)
        all_transactions = self.db.query(Transaction).filter(
            and_(
                Transaction.account_id.in_(all_account_ids),
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
        ).all()
        
        # Get income transactions (only from depository accounts)
        income_transactions = []
        if depository_account_ids:
            income_transactions = self.db.query(Transaction).filter(
                and_(
                    Transaction.account_id.in_(depository_account_ids),
                    Transaction.date >= start_date,
                    Transaction.date <= end_date,
                    Transaction.amount > 0  # Income is positive
                )
            ).all()
        
        # Separate expenses (from all accounts) and income (from depository only)
        expenses = [tx for tx in all_transactions if tx.amount < 0]
        income = income_transactions
        
        # Calculate average monthly income
        monthly_income_dict = defaultdict(float)
        for tx in income:
            month_key = tx.date.strftime("%Y-%m")
            monthly_income_dict[month_key] += abs(tx.amount)
        
        avg_monthly_income = sum(monthly_income_dict.values()) / len(monthly_income_dict) if monthly_income_dict else 0.0
        
        # Calculate average monthly expenses by category
        monthly_expenses_by_category = defaultdict(lambda: defaultdict(float))
        for tx in expenses:
            month_key = tx.date.strftime("%Y-%m")
            category = tx.primary_category or "Uncategorized"
            monthly_expenses_by_category[month_key][category] += abs(tx.amount)
        
        # Calculate average spending per category
        category_totals = defaultdict(float)
        category_counts = defaultdict(int)
        
        for month_data in monthly_expenses_by_category.values():
            for category, amount in month_data.items():
                category_totals[category] += amount
                category_counts[category] += 1
        
        avg_category_budgets = {}
        for category in category_totals:
            if category_counts[category] > 0:
                avg_category_budgets[category] = category_totals[category] / category_counts[category]
        
        # Calculate total average monthly expenses (for reference)
        monthly_totals = [sum(cat.values()) for cat in monthly_expenses_by_category.values()]
        avg_monthly_expenses = sum(monthly_totals) / len(monthly_totals) if monthly_totals else 0.0
        
        # CRITICAL: Budget is based on 100% of monthly income from income analysis
        # Use average monthly income calculated from transactions (avg_monthly_income)
        # This represents the average of all monthly income deposits
        # The total budget MUST equal this average monthly income exactly
        monthly_income = avg_monthly_income
        
        # Fallback to FeaturePipeline only if avg_monthly_income is 0 or invalid
        if monthly_income <= 0:
            from features.pipeline import FeaturePipeline
            import os
            db_path = os.environ.get('DATABASE_PATH', 'data/spendsense.db')
            feature_pipeline = FeaturePipeline(db_path)
            features = feature_pipeline.compute_features_for_user(user_id, 90)
            income_features = features.get('income', {})
            # Try average_income_per_pay with frequency multiplier
            avg_income_per_pay = income_features.get('average_income_per_pay', 0.0)
            frequency = income_features.get('payment_frequency', {}).get('frequency', 'monthly')
            if avg_income_per_pay > 0:
                if frequency == 'weekly':
                    monthly_income = avg_income_per_pay * 4.33
                elif frequency == 'biweekly':
                    monthly_income = avg_income_per_pay * 2.17
                elif frequency == 'monthly':
                    monthly_income = avg_income_per_pay
                else:
                    # For irregular, use minimum_monthly_income as last resort
                    monthly_income = income_features.get('minimum_monthly_income', 0.0)
            else:
                # Last resort: use minimum_monthly_income
                monthly_income = income_features.get('minimum_monthly_income', 0.0)
        
        # Calculate total credit card debt
        credit_card_accounts = [acc for acc in user_accounts if acc.type == 'credit']
        total_credit_card_debt = sum(abs(acc.current or 0) for acc in credit_card_accounts)
        has_credit_card_debt = total_credit_card_debt > 0
        
        # Budget is always 100% of monthly income (not capped by available funds)
        # This allows users to save more money and still live their lives
        # CRITICAL: total_budget MUST equal monthly_income (which is avg_monthly_income) exactly
        if monthly_income <= 0:
            total_budget = 0.0
            category_budgets = {}
        else:
            # Budget equals 100% of monthly income (avg_monthly_income from income analysis)
            # This ensures the budget is based on the monthly average for budget tracking
            total_budget = monthly_income
            
            if has_credit_card_debt:
                # Debt-focused allocation: aggressive debt repayment
                # Debt repayment: 30-35% of income (based solely on income, not credit card balances)
                debt_repayment_percentage = 0.325  # 32.5% (middle of 30-35%)
                debt_repayment_budget = total_budget * debt_repayment_percentage
                
                # Essential expenses kept minimal
                housing_budget = total_budget * 0.275  # 27.5% (middle of 25-30%)
                food_budget = total_budget * 0.10      # 10% (middle of 9-11%)
                transportation_budget = total_budget * 0.06  # 6% (middle of 5-7%)
                utilities_budget = total_budget * 0.045  # 4.5% (middle of 4-5%)
                emergency_fund_budget = total_budget * 0.03  # 3% (middle of 2-4%)
                other_necessities_budget = total_budget * 0.045  # 4.5% (middle of 4-5%)
                discretionary_budget = total_budget * 0.03  # 3% (middle of 2-4%)
                
                # Calculate remaining for "Other" category
                allocated = (housing_budget + food_budget + transportation_budget + 
                           utilities_budget + emergency_fund_budget + other_necessities_budget + 
                           discretionary_budget + debt_repayment_budget)
                other_budget = total_budget - allocated
                
                # Build category budgets dictionary
                category_budgets = {
                    "Housing": housing_budget,
                    "Food": food_budget,
                    "Transportation": transportation_budget,
                    "Utilities": utilities_budget,
                    "Emergency Fund": emergency_fund_budget,
                    "Other Necessities": other_necessities_budget,
                    "Discretionary": discretionary_budget,
                    "Debt Repayment": debt_repayment_budget,
                    "Other": other_budget
                }
                
                # Validate: Ensure sum of category budgets equals total_budget exactly
                category_sum = sum(category_budgets.values())
                if abs(category_sum - total_budget) > 0.01:  # Allow small floating point differences
                    # Adjust "Other" category to ensure exact match
                    category_budgets["Other"] = total_budget - (category_sum - other_budget)
            else:
                # No debt: standard allocation with savings
                housing_budget = total_budget * 0.25  # 25%
                food_budget = total_budget * 0.10     # 10%
                transportation_budget = total_budget * 0.15  # 15%
                savings_budget = total_budget * 0.20  # 20% for savings
                emergency_fund_budget = total_budget * 0.03  # 3% (middle of 2-4%)
                
                # Calculate remaining for "Other" category
                allocated = housing_budget + food_budget + transportation_budget + savings_budget + emergency_fund_budget
                other_budget = total_budget - allocated
                
                # Build category budgets dictionary
                category_budgets = {
                    "Housing": housing_budget,
                    "Food": food_budget,
                    "Transportation": transportation_budget,
                    "Savings": savings_budget,
                    "Emergency Fund": emergency_fund_budget,
                    "Other": other_budget
                }
                
                # Validate: Ensure sum of category budgets equals total_budget exactly
                category_sum = sum(category_budgets.values())
                if abs(category_sum - total_budget) > 0.01:  # Allow small floating point differences
                    # Adjust "Other" category to ensure exact match
                    category_budgets["Other"] = total_budget - (category_sum - other_budget)
        
        # Keep income/expense-based values for reference
        income_based_budget = avg_monthly_income * 0.80 if avg_monthly_income > 0 else 0.0
        expense_based_budget = avg_monthly_expenses * 1.10 if avg_monthly_expenses > 0 else 0.0
        
        # Generate rationale
        rationale_parts = []
        if monthly_income > 0:
            rationale_parts.append(
                f"Based on your average monthly income of ${monthly_income:,.2f} (calculated from income analysis), "
                f"we suggest a monthly budget of ${total_budget:,.2f} (100% of your average monthly income)."
            )
            
            if has_credit_card_debt:
                debt_repayment_amount = category_budgets.get("Debt Repayment", 0)
                rationale_parts.append(
                    f"Budget allocation prioritizes aggressive debt repayment: Debt Repayment ({debt_repayment_amount/total_budget*100:.1f}%), "
                    f"Housing (27.5%), Food (10%), Transportation (6%), Utilities (4.5%), Emergency Fund (3%), "
                    f"and minimal discretionary spending (3%)."
                )
                rationale_parts.append(
                    f"Debt Repayment of ${debt_repayment_amount:,.2f}/month is prioritized to help you pay down your ${total_credit_card_debt:,.2f} in credit card debt. "
                    f"See Admin's recommendations for more information on debt payoff timeline and strategies."
                )
                emergency_fund_amount = category_budgets.get("Emergency Fund", 0)
                if emergency_fund_amount > 0:
                    months_to_1000 = 1000 / emergency_fund_amount if emergency_fund_amount > 0 else 0
                    rationale_parts.append(
                        f"Emergency Fund allocation of ${emergency_fund_amount:,.2f}/month will help you build a $1,000 emergency fund in approximately {months_to_1000:.0f} months."
                    )
            else:
                rationale_parts.append(
                    "Budget allocation follows financial best practices: Housing (25%), Food (10%), "
                    "Transportation (15%), Savings (20%), Emergency Fund (3%), and Other expenses."
                )
                emergency_fund_amount = category_budgets.get("Emergency Fund", 0)
                if emergency_fund_amount > 0:
                    months_to_1000 = 1000 / emergency_fund_amount if emergency_fund_amount > 0 else 0
                    rationale_parts.append(
                        f"Emergency Fund allocation of ${emergency_fund_amount:,.2f}/month will help you build a $1,000 emergency fund in approximately {months_to_1000:.0f} months."
                    )
        else:
            rationale_parts.append(
                "No income data available for budget suggestions. Please ensure income transactions are properly categorized."
            )
        
        rationale = " ".join(rationale_parts) if rationale_parts else "Budget suggestions based on historical spending patterns."
        
        # Also get history for charting
        history = []
        for i in range(lookback_months):
            hist_month = month - timedelta(days=30 * (lookback_months - i))
            month_key = hist_month.strftime("%Y-%m")
            
            if month_key in monthly_income_dict and month_key in monthly_expenses_by_category:
                hist_spending = sum(monthly_expenses_by_category[month_key].values())
                hist_income = monthly_income_dict[month_key]
                history.append({
                    "month": month_key,
                    "total_spending": hist_spending,
                    "total_income": hist_income
                })
        
        # Final validation: Ensure total_budget equals avg_monthly_income exactly
        # This is critical for budget tracking - the budget must match the monthly average
        if avg_monthly_income > 0 and abs(total_budget - avg_monthly_income) > 0.01:
            # If there's a discrepancy, use avg_monthly_income as the source of truth
            total_budget = avg_monthly_income
            # Recalculate category budgets to match the corrected total_budget
            if has_credit_card_debt:
                debt_repayment_budget = total_budget * 0.325
                housing_budget = total_budget * 0.275
                food_budget = total_budget * 0.10
                transportation_budget = total_budget * 0.06
                utilities_budget = total_budget * 0.045
                emergency_fund_budget = total_budget * 0.03
                other_necessities_budget = total_budget * 0.045
                discretionary_budget = total_budget * 0.03
                allocated = (housing_budget + food_budget + transportation_budget + 
                           utilities_budget + emergency_fund_budget + other_necessities_budget + 
                           discretionary_budget + debt_repayment_budget)
                other_budget = total_budget - allocated
                category_budgets = {
                    "Housing": housing_budget,
                    "Food": food_budget,
                    "Transportation": transportation_budget,
                    "Utilities": utilities_budget,
                    "Emergency Fund": emergency_fund_budget,
                    "Other Necessities": other_necessities_budget,
                    "Discretionary": discretionary_budget,
                    "Debt Repayment": debt_repayment_budget,
                    "Other": other_budget
                }
            else:
                housing_budget = total_budget * 0.25
                food_budget = total_budget * 0.10
                transportation_budget = total_budget * 0.15
                savings_budget = total_budget * 0.20
                emergency_fund_budget = total_budget * 0.03
                allocated = housing_budget + food_budget + transportation_budget + savings_budget + emergency_fund_budget
                other_budget = total_budget - allocated
                category_budgets = {
                    "Housing": housing_budget,
                    "Food": food_budget,
                    "Transportation": transportation_budget,
                    "Savings": savings_budget,
                    "Emergency Fund": emergency_fund_budget,
                    "Other": other_budget
                }
        
        return {
            "user_id": user_id,
            "month": month.strftime("%Y-%m"),
            "total_budget": total_budget,
            "category_budgets": category_budgets,
            "rationale": rationale,
            "income_based": income_based_budget,
            "expense_based": expense_based_budget,
            "average_monthly_income": avg_monthly_income,
            "average_monthly_expenses": avg_monthly_expenses,
            "lookback_months": lookback_months,
            "history": history
        }
    
    def calculate_debt_payoff_timeline(
        self,
        user_id: str,
        monthly_payment: float,
        estimated_apr: float = 0.20
    ) -> Dict[str, Any]:
        """Calculate debt payoff timeline for user's credit card debt.
        
        Args:
            user_id: User ID
            monthly_payment: Monthly payment amount (from budget)
            estimated_apr: Estimated annual percentage rate (default 20%)
        
        Returns:
            Dictionary with payoff timeline information including:
            - months_to_payoff: Estimated months to pay off debt
            - total_interest: Total interest paid
            - payoff_date: Estimated payoff date
            - strategy_recommendations: List of strategy recommendations
        """
        # Get credit card accounts
        credit_card_accounts = [acc for acc in self.db.query(Account).filter(
            and_(Account.user_id == user_id, Account.type == 'credit')
        ).all()]
        
        total_debt = sum(abs(acc.current or 0) for acc in credit_card_accounts)
        
        if total_debt <= 0 or monthly_payment <= 0:
            return {
                "months_to_payoff": 0,
                "total_interest": 0.0,
                "payoff_date": None,
                "strategy_recommendations": []
            }
        
        # Calculate months to payoff using amortization approximation
        # Using simplified formula: months ≈ -log(1 - (debt * rate/12) / payment) / log(1 + rate/12)
        monthly_rate = estimated_apr / 12.0
        
        if monthly_payment <= total_debt * monthly_rate:
            # Payment is less than or equal to interest - debt will never be paid off
            months_to_payoff = 999  # Indicates debt will grow
        else:
            # Calculate months using amortization formula
            try:
                months_to_payoff = -math.log(1 - (total_debt * monthly_rate) / monthly_payment) / math.log(1 + monthly_rate)
                months_to_payoff = math.ceil(months_to_payoff)
            except (ValueError, ZeroDivisionError):
                # Fallback: simple division if calculation fails
                months_to_payoff = math.ceil(total_debt / monthly_payment)
        
        # Calculate total interest (approximate)
        total_interest = (monthly_payment * months_to_payoff) - total_debt if months_to_payoff < 999 else 0.0
        
        # Calculate payoff date
        from datetime import datetime, timedelta
        payoff_date = datetime.now() + timedelta(days=months_to_payoff * 30) if months_to_payoff < 999 else None
        
        # Generate strategy recommendations
        strategy_recommendations = [
            "Stop using the credit cards - cut them up if necessary",
            f"Pay more than minimum - minimum payments on ${total_debt:,.0f} debt could take 10+ years",
            "Attack highest interest rate first while paying minimums on others",
            "Find extra income if possible (side gig, sell items, overtime)",
            "No new debt - this is crucial"
        ]
        
        return {
            "months_to_payoff": int(months_to_payoff) if months_to_payoff < 999 else None,
            "total_interest": round(total_interest, 2),
            "payoff_date": payoff_date.isoformat() if payoff_date else None,
            "total_debt": total_debt,
            "monthly_payment": monthly_payment,
            "estimated_apr": estimated_apr,
            "strategy_recommendations": strategy_recommendations
        }
    
    def _user_has_debt(self, user_id: str) -> bool:
        """Check if user has any debt (credit cards or loans).
        
        Args:
            user_id: User ID
        
        Returns:
            True if user has debt, False otherwise
        """
        # Check for credit card accounts with balance > 0
        credit_accounts = self.db.query(Account).filter(
            and_(
                Account.user_id == user_id,
                Account.type == 'credit'
            )
        ).all()
        
        for acc in credit_accounts:
            balance = abs(acc.current or 0.0)
            if balance > 0:
                return True
        
        # Check for loan accounts with balance > 0
        loan_accounts = self.db.query(Account).filter(
            and_(
                Account.user_id == user_id,
                Account.type == 'loan'
            )
        ).all()
        
        for acc in loan_accounts:
            balance = acc.current or 0.0
            if balance > 0:
                return True
        
        return False

