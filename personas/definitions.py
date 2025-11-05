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
        """Legacy method for backward compatibility. Use score_criteria instead."""
        matched_count, total_criteria, reasons = self.score_criteria(features)
        return matched_count > 0, reasons
    
    def score_criteria(self, features: Dict[str, Any]) -> tuple[int, int, List[str]]:
        """Score how many criteria this persona matches.
        
        Args:
            features: Dictionary with user features (from FeaturePipeline)
        
        Returns:
            Tuple of (matched_criteria_count: int, total_criteria: int, reasons: List[str])
            Each persona has exactly 5 criteria.
        """
        reasons = []
        matched_count = 0
        total_criteria = 5
        
        # Extract feature sets
        credit = features.get('credit', {})
        income = features.get('income', {})
        subscriptions = features.get('subscriptions', {})
        savings = features.get('savings', {})
        
        # Persona 1: High Utilization - 5 Criteria
        if self.id == 'high_utilization':
            card_details = credit.get('card_details', [])
            max_utilization = 0.0
            for card in card_details:
                util = card.get('utilization', {})
                util_percent = util.get('utilization_percent', 0.0)
                if util_percent > max_utilization:
                    max_utilization = util_percent
            
            # Criterion 1: Utilization ≥50%
            if max_utilization >= 50.0:
                matched_count += 1
                reasons.append(f"Criterion 1: Credit utilization {max_utilization:.1f}% (≥50%)")
            
            # Criterion 2: Utilization ≥80%
            if max_utilization >= 80.0:
                matched_count += 1
                reasons.append(f"Criterion 2: Credit utilization {max_utilization:.1f}% (≥80%)")
            
            # Criterion 3: Interest charges present
            has_interest = credit.get('any_interest_charges', False)
            if has_interest:
                matched_count += 1
                reasons.append("Criterion 3: Interest charges detected")
            
            # Criterion 4: Minimum payment only
            min_payment_only = credit.get('any_minimum_payment_only', False)
            if min_payment_only:
                matched_count += 1
                reasons.append("Criterion 4: Making only minimum payments")
            
            # Criterion 5: Overdue payments
            is_overdue = credit.get('any_overdue', False)
            if is_overdue:
                matched_count += 1
                reasons.append("Criterion 5: Credit card payment overdue")
        
        # Persona 2: Variable Income Budgeter - 5 Criteria
        elif self.id == 'variable_income_budgeter':
            median_pay_gap = income.get('median_pay_gap_days', 0.0)
            cash_flow_buffer = income.get('cash_flow_buffer_months', 0.0)
            income_std = income.get('income_std', 0.0)
            income_mean = income.get('income_mean', 0.0)
            income_cv = (income_std / income_mean * 100) if income_mean > 0 else 0.0
            minimum_monthly_income = income.get('minimum_monthly_income', 0.0)
            average_monthly_expenses = income.get('average_monthly_expenses', 0.0)
            distinct_income_sources = income.get('distinct_income_sources_90d', 0)
            
            # Criterion 1: Median pay gap > 45 days
            if median_pay_gap > 45.0:
                matched_count += 1
                reasons.append(f"Criterion 1: Median pay gap {median_pay_gap:.0f} days (>45)")
            
            # Criterion 2: Cash-flow buffer < 1 month
            if cash_flow_buffer < 1.0:
                matched_count += 1
                reasons.append(f"Criterion 2: Cash-flow buffer {cash_flow_buffer:.1f} months (<1)")
            
            # Criterion 3: High income variability (CV > 30%)
            if income_cv > 30.0:
                matched_count += 1
                reasons.append(f"Criterion 3: Income variability {income_cv:.1f}% (CV >30%)")
            
            # Criterion 4: Spending >70% of minimum monthly income
            if minimum_monthly_income > 0 and average_monthly_expenses > (minimum_monthly_income * 0.70):
                matched_count += 1
                spending_ratio = (average_monthly_expenses / minimum_monthly_income) * 100
                reasons.append(f"Criterion 4: Spending ${average_monthly_expenses:.2f}/month ({spending_ratio:.1f}% of minimum income ${minimum_monthly_income:.2f})")
            
            # Criterion 5: 3+ different income sources in last 90 days
            if distinct_income_sources >= 3:
                matched_count += 1
                reasons.append(f"Criterion 5: {distinct_income_sources} different income sources (≥3)")
        
        # Persona 3: Subscription-Heavy - 5 Criteria
        elif self.id == 'subscription_heavy':
            num_recurring = subscriptions.get('recurring_merchants', 0)
            monthly_recurring = subscriptions.get('monthly_recurring_spend', 0.0)
            subscription_share = subscriptions.get('subscription_share_of_total', 0.0)
            has_category_duplicates = subscriptions.get('has_category_duplicates', False)
            category_duplicates = subscriptions.get('category_duplicates', {})
            subscription_to_income_ratio = subscriptions.get('subscription_to_income_ratio', 0.0)
            
            # Criterion 1: Has at least 2 subscriptions from the same category
            if has_category_duplicates:
                # Build list of duplicate categories and their merchants
                duplicate_categories = []
                for category, merchants in category_duplicates.items():
                    duplicate_categories.append(f"{category} ({', '.join(merchants[:3])}{'...' if len(merchants) > 3 else ''})")
                matched_count += 1
                reasons.append(f"Criterion 1: Has 2+ subscriptions in same category: {', '.join(duplicate_categories[:2])}")
            
            # Criterion 2: ≥5 recurring merchants
            if num_recurring >= 5:
                matched_count += 1
                reasons.append(f"Criterion 2: {num_recurring} recurring subscriptions (≥5)")
            
            # Criterion 3: Subscription spend ≥10% of monthly income
            if subscription_to_income_ratio >= 10.0:
                matched_count += 1
                reasons.append(f"Criterion 3: Subscription spend {subscription_to_income_ratio:.1f}% of monthly income (≥10%)")
            
            # Criterion 4: Subscription share ≥10% of total spend
            if subscription_share >= 10.0:
                matched_count += 1
                reasons.append(f"Criterion 4: Subscriptions {subscription_share:.1f}% of total (≥10%)")
            
            # Criterion 5: Monthly subscription spend ≥$100
            if monthly_recurring >= 100.0:
                matched_count += 1
                reasons.append(f"Criterion 5: Monthly subscription spend ${monthly_recurring:.2f} (≥$100)")
        
        # Persona 4: Savings Builder - 5 Criteria
        elif self.id == 'savings_builder':
            savings_growth = savings.get('growth_rate_percent', 0.0)
            net_inflow = savings.get('monthly_net_inflow', savings.get('net_inflow_per_month', 0.0))
            savings_balance = savings.get('total_savings_balance', 0.0)
            
            card_details = credit.get('card_details', [])
            max_utilization = 0.0
            for card in card_details:
                util = card.get('utilization', {})
                util_percent = util.get('utilization_percent', 0.0)
                if util_percent > max_utilization:
                    max_utilization = util_percent
            
            # Criterion 1: Savings growth rate ≥2%
            if savings_growth >= 2.0:
                matched_count += 1
                reasons.append(f"Criterion 1: Savings growth {savings_growth:.1f}% (≥2%)")
            
            # Criterion 2: Monthly net inflow ≥$200
            if net_inflow >= 200.0:
                matched_count += 1
                reasons.append(f"Criterion 2: Monthly savings inflow ${net_inflow:.2f} (≥$200)")
            
            # Criterion 3: All credit utilizations < 30%
            if max_utilization < 30.0:
                matched_count += 1
                reasons.append(f"Criterion 3: Max credit utilization {max_utilization:.1f}% (<30%)")
            
            # Criterion 4: Monthly net inflow ≥$500
            if net_inflow >= 500.0:
                matched_count += 1
                reasons.append(f"Criterion 4: Monthly savings inflow ${net_inflow:.2f} (≥$500)")
            
            # Criterion 5: Savings balance > $5,000
            if savings_balance >= 5000.0:
                matched_count += 1
                reasons.append(f"Criterion 5: Savings balance ${savings_balance:.2f} (≥$5,000)")
        
        # Persona 5: Fee Accumulator - 5 Criteria
        elif self.id == 'fee_accumulator':
            fees = features.get('fees', {})
            
            overdraft_nsf_fees = fees.get('overdraft_nsf_fees_90d', 0)
            total_fees_last_month = fees.get('total_fees_last_month', 0.0)
            atm_fees_90d = fees.get('atm_fees_90d', 0)
            accounts_with_late_fees = fees.get('accounts_with_late_fees', 0)
            has_maintenance_fees = fees.get('has_maintenance_fees', False)
            
            # Criterion 1: ≥3 overdraft/NSF fees in last 90 days
            if overdraft_nsf_fees >= 3:
                matched_count += 1
                reasons.append(f"Criterion 1: {overdraft_nsf_fees} overdraft/NSF fees in last 90 days (≥3)")
            
            # Criterion 2: Total fees ≥$50 in last month
            if total_fees_last_month >= 50.0:
                matched_count += 1
                reasons.append(f"Criterion 2: Total fees ${total_fees_last_month:.2f} in last month (≥$50)")
            
            # Criterion 3: ≥5 out-of-network ATM fees in last 90 days
            if atm_fees_90d >= 5:
                matched_count += 1
                reasons.append(f"Criterion 3: {atm_fees_90d} ATM fees in last 90 days (≥5)")
            
            # Criterion 4: Late payment fees on ≥2 accounts
            if accounts_with_late_fees >= 2:
                matched_count += 1
                reasons.append(f"Criterion 4: Late payment fees on {accounts_with_late_fees} accounts (≥2)")
            
            # Criterion 5: Monthly maintenance fees on checking/savings
            if has_maintenance_fees:
                matched_count += 1
                reasons.append("Criterion 5: Monthly maintenance fees on checking/savings accounts")
        
        return matched_count, total_criteria, reasons


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
        id='fee_accumulator',
        name='Fee Accumulator',
        description='Users frequently incurring avoidable banking fees (overdraft, NSF, late fees, out-of-network ATM)',
        risk=PersonaRisk.MEDIUM,
        focus_area='Fee avoidance strategies, account optimization, alert setup, better account selection',
        criteria={
            'min_overdraft_nsf_fees': 3,
            'min_total_fees_monthly': 50.0,
            'min_atm_fees': 5,
            'min_late_fee_accounts': 2
        },
        rationale_template='We identified frequent fee accumulation because {reasons}. Focus on fee avoidance strategies and account optimization.'
    ),
]


def get_persona_by_id(persona_id: str) -> Optional[Persona]:
    """Get persona definition by ID."""
    for persona in PERSONA_DEFINITIONS:
        if persona.id == persona_id:
            return persona
    return None

