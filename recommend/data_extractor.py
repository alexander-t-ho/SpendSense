"""Extract specific user data points for personalized recommendations."""

from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ingest.schema import get_session, User, Account, Transaction, Liability
from sqlalchemy.orm import sessionmaker
from features.pipeline import FeaturePipeline


class RecommendationDataExtractor:
    """Extracts specific data points from user accounts and transactions for recommendations."""
    
    def __init__(self, db_session: Session, db_path: str = "data/spendsense.db"):
        """Initialize data extractor.
        
        Args:
            db_session: Database session
            db_path: Path to SQLite database
        """
        self.db = db_session
        self.db_path = db_path
        self.feature_pipeline = FeaturePipeline(db_path)
    
    def extract_credit_card_data(self, user_id: str) -> List[Dict[str, Any]]:
        """Extract detailed credit card data for recommendations.
        
        Args:
            user_id: User ID
        
        Returns:
            List of credit card data dictionaries with:
            - card_type: Credit card type/name
            - card_last_4: Last 4 digits of account
            - balance: Current balance
            - limit: Credit limit
            - utilization_percent: Utilization percentage
            - monthly_interest: Estimated monthly interest charges
            - annual_interest: Estimated annual interest charges
            - minimum_payment: Minimum payment amount
            - is_overdue: Whether payment is overdue
            - amount_due: Amount currently due
            - apr: APR percentage
        """
        cards = []
        from sqlalchemy import create_engine
        from ingest.schema import Base
        engine = create_engine(f'sqlite:///{self.db_path}')
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Get all credit card accounts
            credit_accounts = session.query(Account).filter(
                Account.user_id == user_id,
                Account.type == "credit"
            ).all()
            
            for account in credit_accounts:
                balance = account.current or 0
                limit = account.limit or 0
                utilization_percent = (balance / limit * 100) if limit > 0 else 0
                
                # Get liability details
                liability = session.query(Liability).filter(
                    Liability.account_id == account.id,
                    Liability.liability_type == "credit_card"
                ).first()
                
                # Calculate interest charges
                apr = liability.apr_percentage if liability else 15.0  # Default 15% APR
                monthly_apr = apr / 12 / 100
                monthly_interest = balance * monthly_apr
                annual_interest = balance * (apr / 100)
                
                # Get minimum payment (use liability or account minimum_payment_due)
                minimum_payment = None
                if liability and liability.minimum_payment_amount:
                    minimum_payment = liability.minimum_payment_amount
                elif account.minimum_payment_due:
                    minimum_payment = account.minimum_payment_due
                else:
                    # Calculate typical minimum payment (usually 1-3% of balance + interest)
                    minimum_payment = max(25.0, balance * 0.02 + monthly_interest)
                
                # Calculate recommended payment (to get to 30% utilization)
                target_balance = limit * 0.30
                recommended_payment = max(minimum_payment, balance - target_balance)
                
                # Calculate payoff scenarios
                months_to_payoff_min = self._calculate_payoff_months(
                    balance, minimum_payment, monthly_interest
                )
                months_to_payoff_recommended = self._calculate_payoff_months(
                    balance, recommended_payment, monthly_interest
                )
                
                # Calculate interest savings
                total_interest_min = self._calculate_total_interest(
                    balance, minimum_payment, monthly_interest, months_to_payoff_min
                )
                total_interest_recommended = self._calculate_total_interest(
                    balance, recommended_payment, monthly_interest, months_to_payoff_recommended
                )
                interest_savings = total_interest_min - total_interest_recommended
                
                # Calculate months to 30% utilization
                months_to_30pct = self._calculate_months_to_target_utilization(
                    balance, limit, recommended_payment, monthly_interest, 0.30
                )
                
                card_data = {
                    'card_type': account.name or "Credit Card",
                    'card_last_4': account.account_id[-4:] if len(account.account_id) >= 4 else account.account_id,
                    'account_id': account.account_id,
                    'balance': balance,
                    'limit': limit,
                    'utilization_percent': utilization_percent,
                    'monthly_interest': monthly_interest,
                    'annual_interest': annual_interest,
                    'minimum_payment': minimum_payment,
                    'recommended_payment': recommended_payment,
                    'is_overdue': liability.is_overdue if liability else False,
                    'amount_due': account.amount_due or balance,
                    'apr': apr,
                    'target_payment': recommended_payment,  # Payment needed to get to 30%
                    'months_to_30pct': months_to_30pct,
                    'months_to_payoff_min': months_to_payoff_min,
                    'months_to_payoff_recommended': months_to_payoff_recommended,
                    'total_interest_min': total_interest_min,
                    'total_interest_recommended': total_interest_recommended,
                    'interest_savings': interest_savings,
                    'months_faster': months_to_payoff_min - months_to_payoff_recommended,
                    'extra_payment': recommended_payment - minimum_payment
                }
                
                cards.append(card_data)
            
            return cards
            
        finally:
            session.close()
    
    def extract_subscription_data(self, user_id: str, window_days: int = 180) -> Dict[str, Any]:
        """Extract subscription-related data.
        
        Args:
            user_id: User ID
            window_days: Time window for analysis
        
        Returns:
            Dictionary with subscription data
        """
        features = self.feature_pipeline.compute_features_for_user(user_id, window_days)
        sub_features = features.get('subscriptions', {})
        
        monthly_recurring = sub_features.get('monthly_recurring_spend', 0)
        annual_spend = monthly_recurring * 12
        num_recurring = sub_features.get('recurring_merchants', 0)
        subscription_share = sub_features.get('subscription_share_of_total', 0)
        
        # Estimate potential savings (assume 20% can be canceled/optimized)
        potential_savings = monthly_recurring * 0.20
        monthly_savings = potential_savings
        annual_savings = potential_savings * 12
        
        return {
            'num_recurring': num_recurring,
            'monthly_recurring_spend': monthly_recurring,
            'subscription_share_of_total': subscription_share,
            'annual_spend': annual_spend,
            'potential_savings': potential_savings,
            'monthly_savings': monthly_savings,
            'annual_savings': annual_savings
        }
    
    def extract_income_data(self, user_id: str, window_days: int = 180) -> Dict[str, Any]:
        """Extract income-related data.
        
        Args:
            user_id: User ID
            window_days: Time window for analysis
        
        Returns:
            Dictionary with income data
        """
        features = self.feature_pipeline.compute_features_for_user(user_id, window_days)
        income_features = features.get('income', {})
        
        median_pay_gap = income_features.get('median_days_between', 0)
        cash_buffer = income_features.get('cash_flow_buffer_months', 0)
        avg_monthly_income = income_features.get('average_monthly_income', 0)
        
        # Calculate average monthly expenses
        avg_monthly_expenses = avg_monthly_income * 0.7  # Rough estimate
        
        # Calculate savings targets
        target_months = 3  # 3-month emergency fund goal
        target_amount = avg_monthly_expenses * target_months
        monthly_savings_target = avg_monthly_expenses * 0.20  # 20% savings rate
        months_to_target = (target_amount - (cash_buffer * avg_monthly_expenses)) / monthly_savings_target if monthly_savings_target > 0 else 0
        
        # Budget percentages
        needs_percent = 50
        wants_percent = 30
        savings_percent = 20
        
        return {
            'median_pay_gap': median_pay_gap,
            'cash_buffer_months': cash_buffer,
            'avg_monthly_income': avg_monthly_income,
            'avg_monthly_expenses': avg_monthly_expenses,
            'target_months': target_months,
            'target_amount': target_amount,
            'monthly_savings_target': monthly_savings_target,
            'months_to_target': max(0, months_to_target),
            'one_month_expenses': avg_monthly_expenses,
            'needs_percent': needs_percent,
            'wants_percent': wants_percent,
            'savings_percent': savings_percent,
            'needs_amount': avg_monthly_income * (needs_percent / 100),
            'wants_amount': avg_monthly_income * (wants_percent / 100),
            'savings_amount': avg_monthly_income * (savings_percent / 100)
        }
    
    def extract_savings_data(self, user_id: str, window_days: int = 180) -> Dict[str, Any]:
        """Extract savings-related data.
        
        Args:
            user_id: User ID
            window_days: Time window for analysis
        
        Returns:
            Dictionary with savings data
        """
        features = self.feature_pipeline.compute_features_for_user(user_id, window_days)
        savings_features = features.get('savings', {})
        
        total_balance = savings_features.get('total_savings_balance', 0)
        monthly_inflow = savings_features.get('monthly_net_inflow', 0)
        growth_rate = savings_features.get('growth_rate_percent', 0)
        
        # Assume current APY is low (e.g., 0.5%)
        current_apy = 0.5
        high_apy = 4.5  # High-yield savings APY
        
        # Calculate additional earnings
        current_annual_earnings = total_balance * (current_apy / 100)
        high_apy_annual_earnings = total_balance * (high_apy / 100)
        additional_annual_earnings = high_apy_annual_earnings - current_annual_earnings
        
        # Calculate goal timeline (e.g., $10,000 goal)
        goal_amount = 10000
        months_to_goal = (goal_amount - total_balance) / monthly_inflow if monthly_inflow > 0 else 0
        
        return {
            'total_savings_balance': total_balance,
            'monthly_net_inflow': monthly_inflow,
            'growth_rate_percent': growth_rate,
            'current_apy': current_apy,
            'high_apy': high_apy,
            'additional_annual_earnings': additional_annual_earnings,
            'goal_amount': goal_amount,
            'months_to_goal': max(0, months_to_goal)
        }
    
    def _calculate_payoff_months(
        self,
        balance: float,
        monthly_payment: float,
        monthly_interest: float
    ) -> int:
        """Calculate months to pay off balance with given payment.
        
        Args:
            balance: Starting balance
            monthly_payment: Monthly payment amount
            monthly_interest: Monthly interest charge
        
        Returns:
            Number of months to pay off
        """
        if monthly_payment <= monthly_interest:
            return 999  # Never pay off with this payment
        
        months = 0
        remaining = balance
        
        while remaining > 0.01 and months < 600:  # Max 50 years
            interest_charge = remaining * (monthly_interest / balance) if balance > 0 else 0
            principal_payment = monthly_payment - interest_charge
            remaining -= principal_payment
            months += 1
            
            if remaining < 0:
                remaining = 0
        
        return months
    
    def _calculate_total_interest(
        self,
        balance: float,
        monthly_payment: float,
        monthly_interest: float,
        months: int
    ) -> float:
        """Calculate total interest paid over payoff period.
        
        Args:
            balance: Starting balance
            monthly_payment: Monthly payment amount
            monthly_interest: Monthly interest charge
            months: Number of months to pay off
        
        Returns:
            Total interest paid
        """
        if months >= 999:
            return balance * 10  # Very high interest if never pays off
        
        total_interest = 0
        remaining = balance
        
        for _ in range(min(months, 600)):
            if remaining <= 0:
                break
            interest_charge = remaining * (monthly_interest / balance) if balance > 0 else 0
            total_interest += interest_charge
            principal_payment = monthly_payment - interest_charge
            remaining -= principal_payment
        
        return total_interest
    
    def _calculate_months_to_target_utilization(
        self,
        balance: float,
        limit: float,
        monthly_payment: float,
        monthly_interest: float,
        target_utilization: float
    ) -> int:
        """Calculate months to reach target utilization percentage.
        
        Args:
            balance: Current balance
            limit: Credit limit
            monthly_payment: Monthly payment amount
            monthly_interest: Monthly interest charge
            target_utilization: Target utilization (e.g., 0.30 for 30%)
        
        Returns:
            Number of months to reach target
        """
        target_balance = limit * target_utilization
        
        if balance <= target_balance:
            return 0
        
        months = 0
        remaining = balance
        
        while remaining > target_balance and months < 600:
            interest_charge = remaining * (monthly_interest / balance) if balance > 0 else 0
            principal_payment = monthly_payment - interest_charge
            remaining -= principal_payment
            months += 1
        
        return months

