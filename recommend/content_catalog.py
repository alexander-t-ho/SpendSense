"""Education content catalog mapped to personas and signals."""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class ContentType(Enum):
    """Types of educational content."""
    ARTICLE = "article"
    TEMPLATE = "template"
    CALCULATOR = "calculator"
    CHECKLIST = "checklist"
    VIDEO = "video"
    COURSE = "course"


@dataclass
class EducationContent:
    """Education content item."""
    id: str
    title: str
    description: str
    content_type: ContentType
    url: str  # External URL or internal path
    target_personas: List[str]  # Persona IDs this content targets
    target_signals: List[str]  # Behavioral signals this addresses
    difficulty: str  # "beginner", "intermediate", "advanced"
    estimated_time: str  # e.g., "5 min read", "15 min video"
    tags: List[str]  # Additional tags for categorization


# Education Content Catalog
EDUCATION_CONTENT = [
    # High Utilization Persona Content
    EducationContent(
        id="debt_paydown_strategy",
        title="How to Pay Down Credit Card Debt: The Snowball vs. Avalanche Method",
        description="Learn two proven strategies for paying off credit card debt, with practical examples and calculators to help you choose the right approach.",
        content_type=ContentType.ARTICLE,
        url="/learn/debt-paydown-strategy",
        target_personas=["high_utilization"],
        target_signals=["high_utilization", "interest_charges", "minimum_payment_only"],
        difficulty="beginner",
        estimated_time="10 min read",
        tags=["debt", "credit cards", "payment strategies"]
    ),
    EducationContent(
        id="credit_utilization_explainer",
        title="Understanding Credit Utilization: What It Means and How to Improve It",
        description="A simple guide to credit utilization, why it matters for your credit score, and actionable steps to lower it.",
        content_type=ContentType.ARTICLE,
        url="/learn/credit-utilization",
        target_personas=["high_utilization"],
        target_signals=["high_utilization"],
        difficulty="beginner",
        estimated_time="7 min read",
        tags=["credit score", "utilization", "credit cards"]
    ),
    EducationContent(
        id="debt_consolidation_guide",
        title="Debt Consolidation: When It Makes Sense and When It Doesn't",
        description="Explore whether debt consolidation is right for you, including balance transfer cards, personal loans, and what to watch out for.",
        content_type=ContentType.ARTICLE,
        url="/learn/debt-consolidation",
        target_personas=["high_utilization"],
        target_signals=["high_utilization", "multiple_credit_cards"],
        difficulty="intermediate",
        estimated_time="12 min read",
        tags=["debt consolidation", "balance transfer", "loans"]
    ),
    EducationContent(
        id="payment_planning_template",
        title="Credit Card Payment Planning Template",
        description="A downloadable spreadsheet template to plan your credit card payments and track progress toward debt-free goals.",
        content_type=ContentType.TEMPLATE,
        url="/templates/payment-planning",
        target_personas=["high_utilization"],
        target_signals=["high_utilization", "minimum_payment_only"],
        difficulty="beginner",
        estimated_time="Template download",
        tags=["budgeting", "debt", "planning"]
    ),
    
    # Variable Income Budgeter Content
    EducationContent(
        id="variable_income_budget",
        title="Budgeting with Variable Income: A Percent-Based Approach",
        description="Learn how to create a flexible budget that works when your income changes month-to-month, using percentage-based allocations.",
        content_type=ContentType.ARTICLE,
        url="/learn/variable-income-budget",
        target_personas=["variable_income_budgeter"],
        target_signals=["variable_income", "irregular_pay"],
        difficulty="beginner",
        estimated_time="8 min read",
        tags=["budgeting", "variable income", "flexible budget"]
    ),
    EducationContent(
        id="emergency_fund_builder",
        title="Building Your Emergency Fund: Start Small, Think Big",
        description="A step-by-step guide to building an emergency fund, even when income is irregular. Learn how to start with $500 and build from there.",
        content_type=ContentType.ARTICLE,
        url="/learn/emergency-fund",
        target_personas=["variable_income_budgeter"],
        target_signals=["variable_income", "low_cash_buffer"],
        difficulty="beginner",
        estimated_time="9 min read",
        tags=["emergency fund", "savings", "financial security"]
    ),
    EducationContent(
        id="income_smoothing_strategies",
        title="Income Smoothing: Strategies for Managing Irregular Paychecks",
        description="Practical techniques for managing cash flow when paychecks are unpredictable, including when to use savings and how to smooth expenses.",
        content_type=ContentType.ARTICLE,
        url="/learn/income-smoothing",
        target_personas=["variable_income_budgeter"],
        target_signals=["variable_income"],
        difficulty="intermediate",
        estimated_time="11 min read",
        tags=["cash flow", "variable income", "planning"]
    ),
    EducationContent(
        id="variable_income_calculator",
        title="Variable Income Budget Calculator",
        description="An interactive calculator to help you determine your base expenses, variable expenses, and savings goals based on your income patterns.",
        content_type=ContentType.CALCULATOR,
        url="/calculators/variable-income-budget",
        target_personas=["variable_income_budgeter"],
        target_signals=["variable_income"],
        difficulty="beginner",
        estimated_time="Interactive tool",
        tags=["calculator", "budgeting", "income"]
    ),
    
    # Subscription-Heavy Content
    EducationContent(
        id="subscription_audit_guide",
        title="The Ultimate Subscription Audit: Find and Cancel Unused Services",
        description="A comprehensive guide to identifying all your subscriptions, evaluating which ones you actually use, and canceling the rest.",
        content_type=ContentType.ARTICLE,
        url="/learn/subscription-audit",
        target_personas=["subscription_heavy"],
        target_signals=["subscription_heavy", "recurring_merchants"],
        difficulty="beginner",
        estimated_time="10 min read",
        tags=["subscriptions", "saving money", "audit"]
    ),
    EducationContent(
        id="subscription_checklist",
        title="Subscription Audit Checklist",
        description="A downloadable checklist to help you systematically review and evaluate all your recurring subscriptions and memberships.",
        content_type=ContentType.CHECKLIST,
        url="/checklists/subscription-audit",
        target_personas=["subscription_heavy"],
        target_signals=["subscription_heavy"],
        difficulty="beginner",
        estimated_time="Checklist download",
        tags=["subscriptions", "checklist", "audit"]
    ),
    EducationContent(
        id="subscription_management_tools",
        title="Best Tools for Managing Subscriptions",
        description="Reviews of subscription management apps and services that can help you track, cancel, and optimize your recurring expenses.",
        content_type=ContentType.ARTICLE,
        url="/learn/subscription-tools",
        target_personas=["subscription_heavy"],
        target_signals=["subscription_heavy"],
        difficulty="beginner",
        estimated_time="6 min read",
        tags=["subscriptions", "tools", "apps"]
    ),
    
    # Savings Builder Content
    EducationContent(
        id="savings_goal_setting",
        title="Setting and Achieving Savings Goals: A Step-by-Step Guide",
        description="Learn how to set realistic savings goals, create a plan to achieve them, and track your progress over time.",
        content_type=ContentType.ARTICLE,
        url="/learn/savings-goals",
        target_personas=["savings_builder"],
        target_signals=["savings_growth", "savings_inflow"],
        difficulty="beginner",
        estimated_time="8 min read",
        tags=["savings", "goal setting", "planning"]
    ),
    EducationContent(
        id="automated_savings_setup",
        title="Automate Your Savings: Set It and Forget It",
        description="A guide to setting up automatic transfers to your savings account, with tips on when and how much to save automatically.",
        content_type=ContentType.ARTICLE,
        url="/learn/automated-savings",
        target_personas=["savings_builder"],
        target_signals=["savings_inflow"],
        difficulty="beginner",
        estimated_time="7 min read",
        tags=["automation", "savings", "banking"]
    ),
    EducationContent(
        id="hysa_guide",
        title="High-Yield Savings Accounts: What They Are and How to Choose One",
        description="Everything you need to know about high-yield savings accounts, including how they work, what to look for, and when to switch.",
        content_type=ContentType.ARTICLE,
        url="/learn/high-yield-savings",
        target_personas=["savings_builder"],
        target_signals=["savings_growth", "savings_inflow"],
        difficulty="beginner",
        estimated_time="9 min read",
        tags=["savings", "interest rates", "banking"]
    ),
    EducationContent(
        id="savings_calculator",
        title="Savings Goal Calculator",
        description="Calculate how long it will take to reach your savings goals based on your current savings rate and monthly contributions.",
        content_type=ContentType.CALCULATOR,
        url="/calculators/savings-goal",
        target_personas=["savings_builder"],
        target_signals=["savings_growth"],
        difficulty="beginner",
        estimated_time="Interactive tool",
        tags=["calculator", "savings", "goals"]
    ),
    
    # Balanced & Stable Content
    EducationContent(
        id="financial_health_maintenance",
        title="Maintaining Good Financial Habits: A Long-Term Guide",
        description="Tips and strategies for maintaining your strong financial foundation and continuing to optimize your finances over time.",
        content_type=ContentType.ARTICLE,
        url="/learn/financial-maintenance",
        target_personas=["balanced_stable"],
        target_signals=["low_utilization", "stable_income"],
        difficulty="beginner",
        estimated_time="8 min read",
        tags=["maintenance", "long-term", "optimization"]
    ),
    EducationContent(
        id="investment_basics",
        title="Investment Basics: Getting Started with Long-Term Wealth Building",
        description="An introduction to investing for beginners, covering stocks, bonds, and retirement accounts for those ready to take the next step.",
        content_type=ContentType.ARTICLE,
        url="/learn/investment-basics",
        target_personas=["balanced_stable"],
        target_signals=["stable_income", "low_utilization"],
        difficulty="intermediate",
        estimated_time="12 min read",
        tags=["investing", "retirement", "wealth building"]
    ),
    EducationContent(
        id="retirement_planning",
        title="Retirement Planning: Start Early, Retire Comfortably",
        description="A comprehensive guide to retirement planning, including 401(k)s, IRAs, and how much you should be saving for retirement.",
        content_type=ContentType.ARTICLE,
        url="/learn/retirement-planning",
        target_personas=["balanced_stable"],
        target_signals=["stable_income"],
        difficulty="intermediate",
        estimated_time="15 min read",
        tags=["retirement", "401k", "IRA"]
    ),
]


class ContentCatalog:
    """Manages education content catalog."""
    
    def __init__(self):
        """Initialize catalog."""
        self.content = EDUCATION_CONTENT
    
    def get_content_for_persona(self, persona_id: str) -> List[EducationContent]:
        """Get content targeted to a specific persona.
        
        Args:
            persona_id: Persona ID
        
        Returns:
            List of education content items
        """
        return [item for item in self.content if persona_id in item.target_personas]
    
    def get_content_for_signal(self, signal: str) -> List[EducationContent]:
        """Get content that addresses a specific behavioral signal.
        
        Args:
            signal: Behavioral signal name
        
        Returns:
            List of education content items
        """
        return [item for item in self.content if signal in item.target_signals]
    
    def get_content_by_id(self, content_id: str) -> EducationContent:
        """Get specific content item by ID.
        
        Args:
            content_id: Content ID
        
        Returns:
            Education content item
        """
        for item in self.content:
            if item.id == content_id:
                return item
        raise ValueError(f"Content not found: {content_id}")
    
    def search_content(self, query: str) -> List[EducationContent]:
        """Search content by title, description, or tags.
        
        Args:
            query: Search query
        
        Returns:
            List of matching content items
        """
        query_lower = query.lower()
        results = []
        for item in self.content:
            if (query_lower in item.title.lower() or
                query_lower in item.description.lower() or
                any(query_lower in tag.lower() for tag in item.tags)):
                results.append(item)
        return results

