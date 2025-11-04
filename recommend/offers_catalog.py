"""Partner offers catalog with eligibility criteria."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class OfferType(Enum):
    """Types of partner offers."""
    CREDIT_CARD = "credit_card"
    SAVINGS_ACCOUNT = "savings_account"
    LOAN = "loan"
    APP = "app"
    SERVICE = "service"


@dataclass
class EligibilityCriteria:
    """Eligibility criteria for partner offers."""
    min_credit_score: Optional[int] = None  # Minimum credit score
    max_credit_score: Optional[int] = None  # Maximum credit score
    min_income: Optional[float] = None  # Minimum annual income
    max_utilization: Optional[float] = None  # Maximum credit utilization
    requires_existing_account: bool = False  # If user must have existing account type
    exclude_account_types: List[str] = None  # Account types to exclude
    min_savings_balance: Optional[float] = None  # Minimum savings balance
    is_harmful: bool = False  # Mark harmful products (payday loans, etc.)


@dataclass
class PartnerOffer:
    """Partner offer with eligibility and metadata."""
    id: str
    title: str
    description: str
    offer_type: OfferType
    partner_name: str
    url: str  # Offer URL
    target_personas: List[str]  # Persona IDs this offer targets
    eligibility: EligibilityCriteria
    benefits: List[str]  # Key benefits of the offer
    terms: str  # Important terms and conditions
    tags: List[str]  # Additional tags


# Partner Offers Catalog
PARTNER_OFFERS = [
    # High Utilization Offers
    PartnerOffer(
        id="balance_transfer_card_1",
        title="0% APR Balance Transfer Card - 18 Months",
        description="Transfer your high-interest credit card debt to a card with 0% APR for 18 months. Save on interest while you pay down your balance.",
        offer_type=OfferType.CREDIT_CARD,
        partner_name="Credit Union Plus",
        url="/offers/balance-transfer-card-1",
        target_personas=["high_utilization"],
        eligibility=EligibilityCriteria(
            min_credit_score=640,
            max_utilization=90.0,  # Only for users with high utilization
            exclude_account_types=["balance_transfer_card"]  # Don't offer if they already have one
        ),
        benefits=[
            "0% APR on balance transfers for 18 months",
            "No annual fee",
            "3% balance transfer fee"
        ],
        terms="Subject to credit approval. 0% APR applies to balance transfers only. Regular APR 18.99% after promotional period.",
        tags=["balance transfer", "debt", "credit card"]
    ),
    PartnerOffer(
        id="debt_consolidation_loan",
        title="Debt Consolidation Personal Loan - Rates as low as 6.99% APR",
        description="Consolidate multiple credit card debts into one manageable monthly payment with a lower interest rate.",
        offer_type=OfferType.LOAN,
        partner_name="Lending Partner",
        url="/offers/debt-consolidation-loan",
        target_personas=["high_utilization"],
        eligibility=EligibilityCriteria(
            min_credit_score=660,
            min_income=30000.0,
            max_utilization=95.0
        ),
        benefits=[
            "Fixed monthly payments",
            "Lower interest rates than credit cards",
            "No prepayment penalties"
        ],
        terms="APR ranges from 6.99% to 24.99% based on creditworthiness. Loan amounts $5,000-$50,000.",
        tags=["debt consolidation", "loan", "debt"]
    ),
    
    # Variable Income Budgeter Offers
    PartnerOffer(
        id="budgeting_app",
        title="Flexible Budgeting App - Free Premium Trial",
        description="A budgeting app designed for variable income, with features for percentage-based budgets and irregular paychecks.",
        offer_type=OfferType.APP,
        partner_name="BudgetBuddy",
        url="/offers/budgeting-app",
        target_personas=["variable_income_budgeter"],
        eligibility=EligibilityCriteria(),  # No eligibility requirements
        benefits=[
            "Percentage-based budgeting",
            "Variable income planning tools",
            "Expense tracking and alerts"
        ],
        terms="Free 30-day premium trial. After trial, $9.99/month or $79.99/year.",
        tags=["budgeting", "app", "variable income"]
    ),
    PartnerOffer(
        id="emergency_fund_savings",
        title="High-Yield Emergency Fund Savings Account",
        description="Start building your emergency fund with a high-yield savings account offering competitive APY rates.",
        offer_type=OfferType.SAVINGS_ACCOUNT,
        partner_name="Secure Savings Bank",
        url="/offers/emergency-fund-savings",
        target_personas=["variable_income_budgeter"],
        eligibility=EligibilityCriteria(
            min_savings_balance=0.0  # No minimum to open
        ),
        benefits=[
            "4.5% APY (annual percentage yield)",
            "No monthly fees",
            "FDIC insured up to $250,000"
        ],
        terms="Minimum opening deposit $0. APY subject to change. No minimum balance required.",
        tags=["savings", "emergency fund", "high yield"]
    ),
    
    # Subscription-Heavy Offers
    PartnerOffer(
        id="subscription_manager_app",
        title="Subscription Management Tool - Free Premium Plan",
        description="Track, manage, and cancel subscriptions all in one place. Get alerts for price changes and renewals.",
        offer_type=OfferType.APP,
        partner_name="SubTracker Pro",
        url="/offers/subscription-manager",
        target_personas=["subscription_heavy"],
        eligibility=EligibilityCriteria(),  # No eligibility requirements
        benefits=[
            "Track all subscriptions in one place",
            "Automatic cancellation reminders",
            "Savings calculator to find unused subscriptions"
        ],
        terms="Free premium plan for 3 months. After trial, $4.99/month.",
        tags=["subscriptions", "app", "saving money"]
    ),
    
    # Savings Builder Offers
    PartnerOffer(
        id="hysa_premium",
        title="Premium High-Yield Savings Account - 5.0% APY",
        description="Maximize your savings with our premium high-yield savings account, perfect for those actively building wealth.",
        offer_type=OfferType.SAVINGS_ACCOUNT,
        partner_name="Wealth Savings Bank",
        url="/offers/hysa-premium",
        target_personas=["savings_builder"],
        eligibility=EligibilityCriteria(
            min_savings_balance=10000.0  # Higher minimum for premium account
        ),
        benefits=[
            "5.0% APY (annual percentage yield)",
            "No monthly fees or minimum balance after opening",
            "Free ATM access nationwide"
        ],
        terms="Minimum opening deposit $10,000. APY subject to change. FDIC insured.",
        tags=["savings", "high yield", "wealth building"]
    ),
    PartnerOffer(
        id="cd_ladder_strategy",
        title="CD Ladder Strategy Guide + Partner CD Rates",
        description="Learn about CD ladder strategies and access partner CD rates for optimizing your savings returns.",
        offer_type=OfferType.SERVICE,
        partner_name="Investment Partners",
        url="/offers/cd-ladder",
        target_personas=["savings_builder"],
        eligibility=EligibilityCriteria(
            min_savings_balance=5000.0
        ),
        benefits=[
            "CD rates up to 5.5% APY",
            "Educational resources on CD ladders",
            "Flexible terms (6 months to 5 years)"
        ],
        terms="CD terms and rates vary. Minimum deposit $1,000. Early withdrawal penalties apply.",
        tags=["CD", "savings", "investing"]
    ),
    
    # Balanced & Stable Offers
    PartnerOffer(
        id="investment_platform",
        title="Low-Cost Investment Platform - Get Started Investing",
        description="Start investing with a low-cost platform offering commission-free trades and educational resources.",
        offer_type=OfferType.APP,
        partner_name="InvestSimple",
        url="/offers/investment-platform",
        target_personas=["balanced_stable"],
        eligibility=EligibilityCriteria(
            min_income=40000.0  # Higher income threshold
        ),
        benefits=[
            "Commission-free stock and ETF trades",
            "Robo-advisor option available",
            "Educational investment resources"
        ],
        terms="Securities offered through InvestSimple Securities. Account minimum $0. Investment advisory services available.",
        tags=["investing", "stocks", "retirement"]
    ),
]


class OffersCatalog:
    """Manages partner offers catalog."""
    
    def __init__(self):
        """Initialize catalog."""
        self.offers = PARTNER_OFFERS
    
    def get_offers_for_persona(self, persona_id: str) -> List[PartnerOffer]:
        """Get offers targeted to a specific persona.
        
        Args:
            persona_id: Persona ID
        
        Returns:
            List of partner offers
        """
        return [offer for offer in self.offers if persona_id in offer.target_personas]
    
    def get_offer_by_id(self, offer_id: str) -> PartnerOffer:
        """Get specific offer by ID.
        
        Args:
            offer_id: Offer ID
        
        Returns:
            Partner offer
        """
        for offer in self.offers:
            if offer.id == offer_id:
                return offer
        raise ValueError(f"Offer not found: {offer_id}")
    
    def check_eligibility(
        self,
        offer: PartnerOffer,
        user_features: Dict[str, Any],
        credit_score: Optional[int] = None,
        annual_income: Optional[float] = None
    ) -> tuple[bool, List[str]]:
        """Check if user is eligible for an offer.
        
        Args:
            offer: Partner offer to check
            user_features: User's behavioral features
            credit_score: User's credit score (if available)
            annual_income: User's annual income (if available)
        
        Returns:
            Tuple of (is_eligible: bool, reasons: List[str])
        """
        reasons = []
        is_eligible = True
        
        criteria = offer.eligibility
        
        # Check credit score
        if criteria.min_credit_score and credit_score:
            if credit_score < criteria.min_credit_score:
                is_eligible = False
                reasons.append(f"Credit score {credit_score} below minimum {criteria.min_credit_score}")
        
        if criteria.max_credit_score and credit_score:
            if credit_score > criteria.max_credit_score:
                is_eligible = False
                reasons.append(f"Credit score {credit_score} above maximum {criteria.max_credit_score}")
        
        # Check income
        if criteria.min_income and annual_income:
            if annual_income < criteria.min_income:
                is_eligible = False
                reasons.append(f"Income ${annual_income:,.0f} below minimum ${criteria.min_income:,.0f}")
        
        # Check credit utilization
        credit_features = user_features.get('credit', {})
        card_details = credit_features.get('card_details', [])
        if card_details and criteria.max_utilization is not None:
            max_util = max(
                (card.get('utilization', {}).get('utilization_percent', 0) 
                 for card in card_details),
                default=0
            )
            if max_util > criteria.max_utilization:
                is_eligible = False
                reasons.append(f"Credit utilization {max_util:.1f}% above maximum {criteria.max_utilization}%")
        
        # Check savings balance
        if criteria.min_savings_balance is not None:
            savings_features = user_features.get('savings', {})
            total_savings = savings_features.get('total_savings_balance', 0)
            if total_savings < criteria.min_savings_balance:
                is_eligible = False
                reasons.append(f"Savings balance ${total_savings:,.0f} below minimum ${criteria.min_savings_balance:,.0f}")
        
        # Check for harmful products
        if criteria.is_harmful:
            is_eligible = False
            reasons.append("Offer filtered: Harmful product category")
        
        return is_eligible, reasons

