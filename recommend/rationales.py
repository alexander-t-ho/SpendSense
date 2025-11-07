"""Plain-language rationale generation for recommendations."""

from typing import Dict, List, Any, Optional
from personas.definitions import Persona


class RationaleBuilder:
    """Builds plain-language rationales for recommendations."""
    
    def __init__(self):
        """Initialize rationale builder."""
        pass
    
    def build_content_rationale(
        self,
        content_title: str,
        user_features: Dict[str, Any],
        persona: Persona,
        signal_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build rationale for education content recommendation.
        
        Args:
            content_title: Title of the content
            user_features: User's behavioral features
            signal_data: Specific signal data that triggered this recommendation
        
        Returns:
            Plain-language rationale
        """
        # Extract relevant data points
        credit_features = user_features.get('credit', {})
        income_features = user_features.get('income', {})
        subscriptions_features = user_features.get('subscriptions', {})
        savings_features = user_features.get('savings', {})
        
        # Build rationale based on persona
        if persona.id == 'high_utilization':
            # High utilization rationales
            card_details = credit_features.get('card_details', [])
            if card_details:
                card = card_details[0]  # Use first card
                util = card.get('utilization', {})
                util_percent = util.get('utilization_percent', 0)
                account_id = card.get('account_id', 'XXXX')
                balance = util.get('balance', 0)
                limit = util.get('limit', 0)
                
                if util_percent >= 50:
                    return (
                        f"We noticed your credit card ending in {account_id[-4:]} is at "
                        f"{util_percent:.0f}% utilization (${balance:,.0f} of ${limit:,.0f} limit). "
                        f"Lowering this below 30% could improve your credit score and reduce interest charges."
                    )
            
            # Check for interest charges
            if credit_features.get('any_interest_charges'):
                return (
                    "We noticed you're paying interest charges on your credit card. "
                    f"{content_title} can help you develop a strategy to pay down your debt and reduce these charges."
                )
            
            # Check for minimum payments
            if credit_features.get('any_minimum_payment_only'):
                return (
                    "We noticed you're making only minimum payments on your credit card. "
                    f"{content_title} explains how paying more than the minimum can help you save money on interest."
                )
        
        elif persona.id == 'variable_income_budgeter':
            # Variable income rationales
            median_pay_gap = income_features.get('median_days_between', 0)
            cash_buffer = income_features.get('cash_flow_buffer_months', 0)
            
            if median_pay_gap > 45:
                return (
                    f"We noticed your income comes in irregularly (about {median_pay_gap:.0f} days between paychecks). "
                    f"{content_title} can help you create a budget that works with variable income."
                )
            
            if cash_buffer < 1.0:
                return (
                    f"We noticed your cash buffer is {cash_buffer:.1f} months, which is below the recommended 1 month. "
                    f"{content_title} provides strategies for building an emergency fund even with irregular income."
                )
        
        elif persona.id == 'subscription_heavy':
            # Subscription-heavy rationales
            num_recurring = subscriptions_features.get('recurring_merchants', 0)
            monthly_spend = subscriptions_features.get('monthly_recurring_spend', 0)
            subscription_share = subscriptions_features.get('subscription_share_of_total', 0)
            
            if num_recurring >= 3:
                return (
                    f"We noticed you have {num_recurring} recurring subscriptions totaling about "
                    f"${monthly_spend:.0f}/month ({subscription_share:.0f}% of your spending). "
                    f"{content_title} can help you audit and optimize these recurring expenses."
                )
        
        elif persona.id == 'savings_builder':
            # Savings builder rationales
            savings_growth = savings_features.get('growth_rate_percent', 0)
            monthly_inflow = savings_features.get('monthly_net_inflow', 0)
            
            if savings_growth >= 2.0:
                return (
                    f"We noticed your savings are growing at {savings_growth:.1f}% per month. "
                    f"{content_title} can help you optimize your savings strategy and maximize your returns."
                )
            
            if monthly_inflow >= 200:
                return (
                    f"We noticed you're saving ${monthly_inflow:.0f} per month on average. "
                    f"{content_title} provides strategies for setting and achieving larger savings goals."
                )
        
        elif persona.id == 'balanced_stable':
            # Balanced/stable rationales
            return (
                f"Based on your stable financial profile, {content_title} can help you "
                "maintain good habits and explore opportunities for optimization."
            )
        
        # Default rationale
        return (
            f"Based on your financial profile, we recommend {content_title} to help you "
            "improve your financial health."
        )
    
    def build_offer_rationale(
        self,
        offer_title: str,
        user_features: Dict[str, Any],
        persona: Persona,
        offer_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build rationale for partner offer recommendation.
        
        Args:
            offer_title: Title of the offer
            user_features: User's behavioral features
            persona: Assigned persona
            offer_data: Additional offer data
        
        Returns:
            Plain-language rationale
        """
        # Extract relevant data points
        credit_features = user_features.get('credit', {})
        savings_features = user_features.get('savings', {})
        subscriptions_features = user_features.get('subscriptions', {})
        
        # Build rationale based on persona and offer type
        if persona.id == 'high_utilization':
            card_details = credit_features.get('card_details', [])
            if card_details:
                card = card_details[0]
                util = card.get('utilization', {})
                util_percent = util.get('utilization_percent', 0)
                account_id = card.get('account_id', 'XXXX')
                
                if "balance transfer" in offer_title.lower() or "debt consolidation" in offer_title.lower():
                    return (
                        f"We noticed your credit card ending in {account_id[-4:]} is at {util_percent:.0f}% utilization. "
                        f"{offer_title} could help you save money on interest while you pay down your balance."
                    )
        
        elif persona.id == 'variable_income_budgeter':
            cash_buffer = user_features.get('income', {}).get('cash_flow_buffer_months', 0)
            
            if "emergency fund" in offer_title.lower() or "savings" in offer_title.lower():
                return (
                    f"We noticed your cash buffer is {cash_buffer:.1f} months. "
                    f"{offer_title} can help you start building a stronger emergency fund."
                )
            
            if "budgeting" in offer_title.lower():
                return (
                    "We noticed you have variable income. "
                    f"{offer_title} is designed specifically for managing finances with irregular paychecks."
                )
        
        elif persona.id == 'subscription_heavy':
            num_recurring = subscriptions_features.get('recurring_merchants', 0)
            
            if "subscription" in offer_title.lower():
                return (
                    f"We noticed you have {num_recurring} recurring subscriptions. "
                    f"{offer_title} can help you track and manage all your subscriptions in one place."
                )
        
        elif persona.id == 'savings_builder':
            total_savings = savings_features.get('total_savings_balance', 0)
            monthly_inflow = savings_features.get('monthly_net_inflow', 0)
            
            if "high-yield" in offer_title.lower() or "savings" in offer_title.lower():
                return (
                    f"We noticed you're actively building savings (${total_savings:,.0f} saved, "
                    f"${monthly_inflow:.0f}/month contributions). "
                    f"{offer_title} offers a higher interest rate to help your savings grow faster."
                )
        
        elif persona.id == 'balanced_stable':
            if "investment" in offer_title.lower():
                return (
                    "Based on your stable financial profile, "
                    f"{offer_title} could be a good next step for long-term wealth building."
                )
        
        # Default rationale
        return (
            f"Based on your financial profile, {offer_title} may be a good fit for your needs."
        )
    
    def cite_specific_data(
        self,
        data_point: str,
        value: Any,
        context: str = ""
    ) -> str:
        """Create a citation for a specific data point.
        
        Args:
            data_point: Name of the data point
            value: Value of the data point
            context: Additional context
        
        Returns:
            Formatted citation string
        """
        if isinstance(value, float):
            if value >= 1000:
                formatted_value = f"${value:,.0f}"
            elif value >= 1:
                formatted_value = f"${value:.2f}"
            else:
                formatted_value = f"{value*100:.1f}%"
        elif isinstance(value, int):
            formatted_value = str(value)
        else:
            formatted_value = str(value)
        
        if context:
            return f"{data_point}: {formatted_value} ({context})"
        return f"{data_point}: {formatted_value}"




