"""Persona definitions with criteria and focus areas."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class PersonaRisk(Enum):
    """Risk levels for persona assignment (higher = higher risk/urgency)."""
    CRITICAL = 5  # High Utilization (immediate action needed)
    HIGH = 4      # Variable Income Budgeter (financial stress)
    MEDIUM = 3    # Subscription-Heavy (optimization opportunity)
    LOW = 2       # Savings Builder (growth opportunity)
    MINIMAL = 1   # Balanced (maintenance)


@dataclass
class Persona:
    """Persona definition with criteria and metadata."""
    id: str
    name: str
    description: str
    risk: PersonaRisk  # Changed from priority to risk
    focus_area: str
    criteria: Dict[str, Any]  # Criteria for matching
    rationale_template: str  # Template for explaining assignment
    
    def matches(self, features: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Check if user features match this persona.
        
        Args:
            features: Dictionary with user features (from FeaturePipeline)
        
        Returns:
            Tuple of (matches: bool, reasons: List[str])
        """
        reasons = []
        matches = False
        
        # Extract feature sets
        credit = features.get('credit', {})
        income = features.get('income', {})
        subscriptions = features.get('subscriptions', {})
        savings = features.get('savings', {})
        
        # Persona 1: High Utilization
        if self.id == 'high_utilization':
            # Criteria: utilization ≥50% OR interest > 0 OR min-payment-only OR overdue
            # Check card_details for max utilization
            card_details = credit.get('card_details', [])
            max_utilization = 0.0
            has_interest = credit.get('any_interest_charges', False)
            min_payment_only = credit.get('any_minimum_payment_only', False)
            is_overdue = credit.get('any_overdue', False)
            
            # Find max utilization from card details
            for card in card_details:
                util = card.get('utilization', {})
                util_percent = util.get('utilization_percent', 0.0)
                if util_percent > max_utilization:
                    max_utilization = util_percent
            
            if max_utilization >= 50.0:
                matches = True
                reasons.append(f"Credit utilization is {max_utilization:.1f}% (≥50% threshold)")
            if has_interest:
                matches = True
                reasons.append("Interest charges detected on credit card")
            if min_payment_only:
                matches = True
                reasons.append("Making only minimum payments on credit card")
            if is_overdue:
                matches = True
                reasons.append("Credit card payment is overdue")
        
        # Persona 2: Variable Income Budgeter
        elif self.id == 'variable_income_budgeter':
            # Criteria: median pay gap > 45 days AND cash-flow buffer < 1 month
            median_pay_gap = income.get('median_days_between', 0.0)
            cash_flow_buffer = income.get('cash_flow_buffer_months', 0.0)
            
            if median_pay_gap > 45.0 and cash_flow_buffer < 1.0:
                matches = True
                reasons.append(f"Median pay gap is {median_pay_gap:.0f} days (>45 days)")
                reasons.append(f"Cash-flow buffer is {cash_flow_buffer:.1f} months (<1 month)")
        
        # Persona 3: Subscription-Heavy
        elif self.id == 'subscription_heavy':
            # Criteria: ≥3 recurring merchants AND (≥$50/month OR ≥10% of spend)
            num_recurring = subscriptions.get('recurring_merchants', 0)
            monthly_recurring = subscriptions.get('monthly_recurring_spend', 0.0)
            subscription_share = subscriptions.get('subscription_share_of_total', 0.0)
            
            if num_recurring >= 3:
                if monthly_recurring >= 50.0 or subscription_share >= 10.0:
                    matches = True
                    reasons.append(f"{num_recurring} recurring subscriptions detected")
                    if monthly_recurring >= 50.0:
                        reasons.append(f"Monthly subscription spend: ${monthly_recurring:.2f} (≥$50)")
                    if subscription_share >= 10.0:
                        reasons.append(f"Subscriptions are {subscription_share:.1f}% of total spend (≥10%)")
        
        # Persona 4: Savings Builder
        elif self.id == 'savings_builder':
            # Criteria: savings growth ≥2% OR net inflow ≥$200/month AND all utilizations < 30%
            savings_growth = savings.get('growth_rate_percent', 0.0)
            net_inflow = savings.get('monthly_net_inflow', savings.get('net_inflow_per_month', 0.0))
            
            # Find max utilization from card details
            card_details = credit.get('card_details', [])
            max_utilization = 0.0
            for card in card_details:
                util = card.get('utilization', {})
                util_percent = util.get('utilization_percent', 0.0)
                if util_percent > max_utilization:
                    max_utilization = util_percent
            
            growth_match = savings_growth >= 2.0
            inflow_match = net_inflow >= 200.0 and max_utilization < 30.0
            
            if growth_match:
                matches = True
                reasons.append(f"Savings growth rate: {savings_growth:.1f}% (≥2%)")
            
            if inflow_match:
                matches = True
                reasons.append(f"Monthly savings inflow: ${net_inflow:.2f} (≥$200)")
                reasons.append(f"All credit utilizations < 30% (max: {max_utilization:.1f}%)")
        
        # Persona 5: Balanced/Stable
        elif self.id == 'balanced_stable':
            # Default persona: doesn't match other high-priority personas
            # Criteria: Low utilization, stable income, moderate subscriptions, steady savings
            card_details = credit.get('card_details', [])
            max_utilization = 0.0
            for card in card_details:
                util = card.get('utilization', {})
                util_percent = util.get('utilization_percent', 0.0)
                if util_percent > max_utilization:
                    max_utilization = util_percent
            
            has_interest = credit.get('any_interest_charges', False)
            is_overdue = credit.get('any_overdue', False)
            cash_flow_buffer = income.get('cash_flow_buffer_months', 0.0)
            num_recurring = subscriptions.get('recurring_merchants', 0)
            
            if (max_utilization < 50.0 and 
                not has_interest and 
                not is_overdue and
                cash_flow_buffer >= 1.0 and
                num_recurring < 5):
                matches = True
                reasons.append("Stable financial profile with low risk indicators")
        
        return matches, reasons


# Persona Definitions
PERSONA_DEFINITIONS = [
    Persona(
        id='high_utilization',
        name='High Utilization',
        description='Users with high credit card utilization, interest charges, or payment issues',
        risk=PersonaRisk.CRITICAL,
        focus_area='Reduce utilization, payment planning, debt management',
        criteria={
            'utilization_threshold': 50.0,
            'check_interest': True,
            'check_minimum_payment': True,
            'check_overdue': True
        },
        rationale_template='We identified high credit utilization because {reasons}. Focus on reducing debt and improving payment habits.'
    ),
    Persona(
        id='variable_income_budgeter',
        name='Variable Income Budgeter',
        description='Users with irregular income patterns and limited cash-flow buffer',
        risk=PersonaRisk.HIGH,
        focus_area='Percent-based budgets, emergency fund building, income smoothing',
        criteria={
            'median_pay_gap_days': 45.0,
            'cash_flow_buffer_months': 1.0
        },
        rationale_template='We identified variable income patterns because {reasons}. Focus on building emergency funds and flexible budgeting.'
    ),
    Persona(
        id='subscription_heavy',
        name='Subscription-Heavy',
        description='Users with multiple recurring subscriptions consuming significant portion of spending',
        risk=PersonaRisk.MEDIUM,
        focus_area='Subscription audit, cancellation tips, spending optimization',
        criteria={
            'min_recurring_merchants': 3,
            'min_monthly_spend': 50.0,
            'min_share_of_total': 10.0
        },
        rationale_template='We identified subscription-heavy spending because {reasons}. Focus on auditing and optimizing recurring expenses.'
    ),
    Persona(
        id='savings_builder',
        name='Savings Builder',
        description='Users actively building savings with low credit utilization',
        risk=PersonaRisk.LOW,
        focus_area='Goal setting, automation, high-yield savings accounts',
        criteria={
            'min_growth_rate': 2.0,
            'min_monthly_inflow': 200.0,
            'max_utilization': 30.0
        },
        rationale_template='We identified strong savings behavior because {reasons}. Focus on optimizing savings goals and returns.'
    ),
    Persona(
        id='balanced_stable',
        name='Balanced & Stable',
        description='Users with stable financial patterns, low risk indicators',
        risk=PersonaRisk.MINIMAL,
        focus_area='Maintenance, optimization, long-term planning',
        criteria={
            'max_utilization': 50.0,
            'min_cash_flow_buffer': 1.0,
            'max_subscriptions': 5
        },
        rationale_template='We identified a stable financial profile because {reasons}. Focus on maintaining good habits and optimization.'
    ),
]


def get_persona_by_id(persona_id: str) -> Optional[Persona]:
    """Get persona definition by ID."""
    for persona in PERSONA_DEFINITIONS:
        if persona.id == persona_id:
            return persona
    return None

