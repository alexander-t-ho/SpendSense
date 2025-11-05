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
                
                # Calculate 6-month phased payment plan
                payment_plan = self._calculate_6month_payment_plan(
                    balance, limit, apr, monthly_interest, minimum_payment
                )
                
                # Calculate payment needed to pay off in 12 months
                payment_12mo = self._calculate_payment_for_payoff_months(
                    balance, apr, 12
                )
                months_to_payoff_12mo = self._calculate_payoff_months(
                    balance, payment_12mo, monthly_interest
                )
                total_interest_12mo = self._calculate_total_interest(
                    balance, payment_12mo, monthly_interest, months_to_payoff_12mo
                )
                interest_savings_12mo = total_interest_min - total_interest_12mo
                months_faster_12mo = months_to_payoff_min - months_to_payoff_12mo
                
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
                    'extra_payment': recommended_payment - minimum_payment,
                    # 6-month payment plan data
                    'monthly_payment_months_1_2': payment_plan['monthly_payment_months_1_2'],
                    'monthly_payment_months_3_4': payment_plan['monthly_payment_months_3_4'],
                    'monthly_payment_months_5_6': payment_plan['monthly_payment_months_5_6'],
                    'utilization_after_2mo': payment_plan['utilization_after_2mo'],
                    'automatic_payment_amount': payment_plan['automatic_payment_amount'],
                    'potential_balance_transfer_savings': payment_plan['potential_balance_transfer_savings'],
                    'total_interest_savings_6mo': payment_plan['total_interest_savings_6mo'],
                    # 12-month payoff data for stop_minimum_payments recommendation
                    'payment_12mo': payment_12mo,
                    'months_with_extra': months_to_payoff_12mo,
                    'total_interest_12mo': total_interest_12mo,
                    'interest_savings_12mo': interest_savings_12mo,
                    'months_faster_12mo': months_faster_12mo
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
        
        median_pay_gap = income_features.get('median_pay_gap_days', 0) or income_features.get('median_days_between', 0)
        cash_buffer = income_features.get('cash_flow_buffer_months', 0)
        avg_monthly_income = income_features.get('average_monthly_income', 0)
        avg_monthly_expenses = income_features.get('average_monthly_expenses', 0)
        minimum_monthly_income = income_features.get('minimum_monthly_income', 0)
        
        # Use actual expenses if available, otherwise estimate
        if avg_monthly_expenses <= 0:
            # Estimate expenses as 70% of average income, or use minimum income as fallback
            if avg_monthly_income > 0:
                avg_monthly_expenses = avg_monthly_income * 0.7
            elif minimum_monthly_income > 0:
                avg_monthly_expenses = minimum_monthly_income * 0.8  # Estimate expenses as 80% of minimum income
            else:
                # Fallback: assume $2,000/month expenses if no data
                avg_monthly_expenses = 2000.0
        
        # Calculate emergency fund savings plan options
        # Goal: Provide multiple options for building 1-2 month buffer
        current_buffer_amount = cash_buffer * avg_monthly_expenses
        
        # Calculate multiple savings plan options
        savings_plans = []
        
        # Option 1: Build 1-month buffer in 6 months (aggressive)
        target_1mo = 1
        target_1mo_amount = target_1mo * avg_monthly_expenses
        amount_needed_1mo = max(0, target_1mo_amount - current_buffer_amount)
        months_1mo = 6
        monthly_savings_1mo = amount_needed_1mo / months_1mo if months_1mo > 0 else 0
        monthly_savings_1mo = round(monthly_savings_1mo / 10) * 10
        if monthly_savings_1mo < 50:
            monthly_savings_1mo = 50
            months_1mo = int(amount_needed_1mo / monthly_savings_1mo) if monthly_savings_1mo > 0 else 6
        
        savings_plans.append({
            'target_months': target_1mo,
            'monthly_savings': monthly_savings_1mo,
            'months_to_target': months_1mo,
            'label': 'Fast Track'
        })
        
        # Option 2: Build 1-month buffer in 12 months (moderate)
        months_1mo_moderate = 12
        monthly_savings_1mo_moderate = amount_needed_1mo / months_1mo_moderate if months_1mo_moderate > 0 else 0
        monthly_savings_1mo_moderate = round(monthly_savings_1mo_moderate / 10) * 10
        if monthly_savings_1mo_moderate < 50:
            monthly_savings_1mo_moderate = 50
            months_1mo_moderate = int(amount_needed_1mo / monthly_savings_1mo_moderate) if monthly_savings_1mo_moderate > 0 else 12
        
        savings_plans.append({
            'target_months': target_1mo,
            'monthly_savings': monthly_savings_1mo_moderate,
            'months_to_target': months_1mo_moderate,
            'label': 'Steady Progress'
        })
        
        # Option 3: Build 2-month buffer in 12 months (recommended)
        target_2mo = 2
        target_2mo_amount = target_2mo * avg_monthly_expenses
        amount_needed_2mo = max(0, target_2mo_amount - current_buffer_amount)
        months_2mo = 12
        monthly_savings_2mo = amount_needed_2mo / months_2mo if months_2mo > 0 else 0
        monthly_savings_2mo = round(monthly_savings_2mo / 10) * 10
        if monthly_savings_2mo < 100:
            monthly_savings_2mo = 100
            months_2mo = int(amount_needed_2mo / monthly_savings_2mo) if monthly_savings_2mo > 0 else 12
        
        # Cap at 20% of income if available
        if avg_monthly_income > 0:
            max_affordable = avg_monthly_income * 0.20
            if monthly_savings_2mo > max_affordable:
                monthly_savings_2mo = max_affordable
                months_2mo = int(amount_needed_2mo / monthly_savings_2mo) if monthly_savings_2mo > 0 else 18
        
        savings_plans.append({
            'target_months': target_2mo,
            'monthly_savings': monthly_savings_2mo,
            'months_to_target': months_2mo,
            'label': 'Recommended'
        })
        
        # Option 4: Build 2-month buffer in 18 months (slow but steady)
        months_2mo_slow = 18
        monthly_savings_2mo_slow = amount_needed_2mo / months_2mo_slow if months_2mo_slow > 0 else 0
        monthly_savings_2mo_slow = round(monthly_savings_2mo_slow / 10) * 10
        if monthly_savings_2mo_slow < 50:
            monthly_savings_2mo_slow = 50
            months_2mo_slow = int(amount_needed_2mo / monthly_savings_2mo_slow) if monthly_savings_2mo_slow > 0 else 18
        
        savings_plans.append({
            'target_months': target_2mo,
            'monthly_savings': monthly_savings_2mo_slow,
            'months_to_target': months_2mo_slow,
            'label': 'Slow & Steady'
        })
        
        # Select recommended plan (Option 3: 2 months in 12 months)
        recommended_plan = savings_plans[2]  # Option 3
        monthly_savings_target = recommended_plan['monthly_savings']
        months_to_target = recommended_plan['months_to_target']
        target_months = recommended_plan['target_months']
        
        # Calculate minimum monthly savings (starting point if user can't afford full amount)
        min_monthly_savings = max(50, round(monthly_savings_target * 0.5 / 10) * 10)  # At least $50, or 50% of target
        
        # Ensure we have a reasonable median_pay_gap (at least 1 day)
        if median_pay_gap <= 0:
            median_pay_gap = 30  # Default to monthly if unknown
        
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
            'target_amount': target_2mo_amount,
            'monthly_savings_target': monthly_savings_target,
            'months_to_target': max(6, months_to_target),  # Minimum 6 months
            'one_month_expenses': avg_monthly_expenses,
            'min_monthly_savings': min_monthly_savings,
            'savings_plan_options': savings_plans,  # Multiple options for the user
            'needs_percent': needs_percent,
            'wants_percent': wants_percent,
            'savings_percent': savings_percent,
            'needs_amount': avg_monthly_income * (needs_percent / 100) if avg_monthly_income > 0 else 0,
            'wants_amount': avg_monthly_income * (wants_percent / 100) if avg_monthly_income > 0 else 0,
            'savings_amount': avg_monthly_income * (savings_percent / 100) if avg_monthly_income > 0 else 0
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
        
        # Calculate monthly interest rate from monthly_interest
        # monthly_interest is the interest on the current balance
        monthly_rate = (monthly_interest / balance) if balance > 0 else 0
        
        while remaining > 0.01 and months < 600:  # Max 50 years
            interest_charge = remaining * monthly_rate
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
        
        # Calculate monthly interest rate from monthly_interest
        monthly_rate = (monthly_interest / balance) if balance > 0 else 0
        
        for _ in range(min(months, 600)):
            if remaining <= 0:
                break
            interest_charge = remaining * monthly_rate
            total_interest += interest_charge
            principal_payment = monthly_payment - interest_charge
            remaining -= principal_payment
        
        return total_interest
    
    def _calculate_payment_for_payoff_months(
        self,
        balance: float,
        apr: float,
        target_months: int
    ) -> float:
        """Calculate monthly payment needed to pay off balance in target months.
        
        Uses iterative approach to find the payment amount that pays off the debt
        in exactly target_months, accounting for interest.
        
        Args:
            balance: Starting balance
            apr: Annual percentage rate (as percentage, e.g., 15.0 for 15%)
            target_months: Target number of months to pay off
        
        Returns:
            Monthly payment amount needed
        """
        if target_months <= 0:
            return balance
        
        # Calculate monthly interest rate
        monthly_rate = (apr / 100.0) / 12.0 if apr > 0 else 0.02
        
        # Start with a guess: balance divided by months plus some interest
        # Use formula: payment ≈ balance * (r * (1 + r)^n) / ((1 + r)^n - 1)
        # where r is monthly rate and n is number of months
        if monthly_rate > 0:
            r = monthly_rate
            n = target_months
            payment_guess = balance * (r * (1 + r)**n) / ((1 + r)**n - 1)
        else:
            payment_guess = balance / target_months
        
        # Refine using binary search
        low = balance / target_months  # Minimum payment (no interest)
        high = balance * 2  # High upper bound
        payment = payment_guess
        
        for _ in range(50):  # Max 50 iterations
            # Simulate payoff
            remaining = balance
            for month in range(target_months):
                interest_charge = remaining * monthly_rate
                remaining = max(0, remaining - payment + interest_charge)
                if remaining <= 0:
                    break
            
            if abs(remaining) < 0.01:  # Close enough
                break
            elif remaining > 0:
                # Need higher payment
                low = payment
                payment = (payment + high) / 2
            else:
                # Payment too high
                high = payment
                payment = (low + payment) / 2
        
        # Round up to nearest $10 for practicality
        return round(payment / 10) * 10
    
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
    
    def _calculate_6month_payment_plan(
        self,
        balance: float,
        limit: float,
        apr: float,
        monthly_interest: float,
        minimum_payment: float
    ) -> Dict[str, Any]:
        """Calculate a realistic 6-month phased payment plan.
        
        Plan structure:
        - Months 1-2: Target 70% utilization (aggressive start)
        - Months 3-4: Target 50% utilization (moderate progress)
        - Months 5-6: Target 30% utilization (final goal)
        
        Args:
            balance: Current balance
            limit: Credit limit
            apr: Annual percentage rate (as decimal, e.g., 0.24 for 24%)
            monthly_interest: Current monthly interest charge
            minimum_payment: Minimum monthly payment
        
        Returns:
            Dictionary with payment plan details
        """
        target_70pct = limit * 0.70
        target_50pct = limit * 0.50
        target_30pct = limit * 0.30
        
        # Calculate monthly interest rate from APR (APR is already in percentage form, e.g., 15.0 for 15%)
        # Convert to decimal and divide by 12 for monthly rate
        monthly_rate = (apr / 100.0) / 12.0 if apr > 0 else 0.02  # Default to 2% monthly if no APR
        
        # Calculate payments needed for each phase using iterative approach
        # Phase 1: Months 1-2 - Target 70% utilization
        balance_after_2mo = balance
        payment_months_1_2 = minimum_payment * 1.5  # Start with 1.5x minimum
        
        # Iteratively find payment amount to reach 70% after 2 months
        for _ in range(20):  # Max 20 iterations
            test_balance = balance
            for month in range(2):
                interest_charge = test_balance * monthly_rate
                test_balance = max(0, test_balance - payment_months_1_2 + interest_charge)
            
            if test_balance <= target_70pct:
                break
            else:
                # Increase payment to reach target
                needed_reduction = test_balance - target_70pct
                payment_months_1_2 += needed_reduction / 2
        
        payment_months_1_2 = max(minimum_payment * 1.5, payment_months_1_2)
        
        # Simulate balance after 2 months
        balance_after_2mo = balance
        for month in range(2):
            interest_charge = balance_after_2mo * monthly_rate
            balance_after_2mo = max(0, balance_after_2mo - payment_months_1_2 + interest_charge)
        
        utilization_after_2mo = (balance_after_2mo / limit * 100) if limit > 0 else 0
        
        # Phase 2: Months 3-4 - Target 50% utilization
        balance_at_month_3 = balance_after_2mo
        payment_months_3_4 = payment_months_1_2  # Start with previous payment
        
        # Iteratively find payment amount to reach 50% after months 3-4
        for _ in range(20):
            test_balance = balance_at_month_3
            for month in range(2):
                interest_charge = test_balance * monthly_rate
                test_balance = max(0, test_balance - payment_months_3_4 + interest_charge)
            
            if test_balance <= target_50pct:
                break
            else:
                needed_reduction = test_balance - target_50pct
                payment_months_3_4 += needed_reduction / 2
        
        payment_months_3_4 = max(payment_months_1_2, payment_months_3_4)
        
        # Simulate balance after 4 months
        balance_after_4mo = balance_after_2mo
        for month in range(2):
            interest_charge = balance_after_4mo * monthly_rate
            balance_after_4mo = max(0, balance_after_4mo - payment_months_3_4 + interest_charge)
        
        # Phase 3: Months 5-6 - Target 30% utilization
        balance_at_month_5 = balance_after_4mo
        payment_months_5_6 = payment_months_3_4  # Start with previous payment
        
        # Iteratively find payment amount to reach 30% after months 5-6
        for _ in range(20):
            test_balance = balance_at_month_5
            for month in range(2):
                interest_charge = test_balance * monthly_rate
                test_balance = max(0, test_balance - payment_months_5_6 + interest_charge)
            
            if test_balance <= target_30pct:
                break
            else:
                needed_reduction = test_balance - target_30pct
                payment_months_5_6 += needed_reduction / 2
        
        payment_months_5_6 = max(payment_months_3_4, payment_months_5_6)
        
        # Calculate automatic payment amount (average of all phases, rounded up)
        automatic_payment = ((payment_months_1_2 * 2 + payment_months_3_4 * 2 + payment_months_5_6 * 2) / 6)
        automatic_payment = round(automatic_payment / 10) * 10  # Round to nearest $10
        
        # Calculate interest savings vs. minimum payment over 6 months
        total_interest_min = 0
        total_interest_plan = 0
        remaining_min = balance
        remaining_plan = balance
        
        for month in range(6):
            # Minimum payment scenario
            interest_min = remaining_min * monthly_rate
            total_interest_min += interest_min
            remaining_min = max(0, remaining_min - minimum_payment + interest_min)
            
            # Plan scenario
            if month < 2:
                payment = payment_months_1_2
            elif month < 4:
                payment = payment_months_3_4
            else:
                payment = payment_months_5_6
            
            interest_plan = remaining_plan * monthly_rate
            total_interest_plan += interest_plan
            remaining_plan = max(0, remaining_plan - payment + interest_plan)
        
        total_interest_savings_6mo = total_interest_min - total_interest_plan
        
        # Estimate balance transfer savings (assume 0% APR for 12-18 months)
        # Savings = 6 months of interest that would be paid
        potential_balance_transfer_savings = monthly_interest * 6
        
        return {
            'monthly_payment_months_1_2': round(payment_months_1_2, 2),
            'monthly_payment_months_3_4': round(payment_months_3_4, 2),
            'monthly_payment_months_5_6': round(payment_months_5_6, 2),
            'utilization_after_2mo': round(utilization_after_2mo, 1),
            'automatic_payment_amount': automatic_payment,
            'potential_balance_transfer_savings': round(potential_balance_transfer_savings, 2),
            'total_interest_savings_6mo': round(total_interest_savings_6mo, 2)
        }

