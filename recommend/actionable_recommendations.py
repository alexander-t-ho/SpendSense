"""Library of actionable recommendations per persona with improvement templates."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class RecommendationPriority(Enum):
    """Priority levels for recommendations."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ActionableRecommendation:
    """An actionable recommendation that can be personalized with user data."""
    id: str
    persona_id: str  # Persona this recommendation targets
    priority: RecommendationPriority
    title: str  # Short title/headline
    template: str  # Template with placeholders for personalization
    action_items: List[str]  # Specific action steps
    expected_impact: str  # Expected outcome/benefit
    target_signals: List[str]  # Signals that trigger this recommendation
    data_points_needed: List[str]  # Data points needed for personalization (e.g., "card_last_4", "utilization_percent", "balance", "limit", "interest_charges")


# Actionable Recommendations Library
# These are templates that get personalized with specific user data

ACTIONABLE_RECOMMENDATIONS = [
    # High Utilization Persona Recommendations
    ActionableRecommendation(
        id="reduce_utilization_specific_card",
        persona_id="high_utilization",
        priority=RecommendationPriority.HIGH,
        title="Reduce Credit Card Utilization",
        template="We noticed your {card_type} ending in {card_last_4} is at {utilization_percent:.1f}% utilization (${balance:,.0f} of ${limit:,.0f} limit). Bringing this below 30% over 6 months could improve your credit score and reduce interest charges of ${monthly_interest:,.2f}/month.",
        action_items=[
            "Month 1-2: Pay ${monthly_payment_months_1_2:,.0f}/month to bring utilization below {utilization_after_2mo:.0f}% (current: {utilization_percent:.0f}%)",
            "Month 3-4: Increase payment to ${monthly_payment_months_3_4:,.0f}/month to reach below 50% utilization",
            "Month 5-6: Maintain ${monthly_payment_months_5_6:,.0f}/month to get below 30% utilization and improve credit score",
            "Set up automatic payments of ${automatic_payment_amount:,.0f}/month to stay on track",
            "Stop using this card for new purchases until utilization is below 30%",
            "Consider a balance transfer to a card with 0% APR if eligible (could save ${potential_balance_transfer_savings:,.0f} in interest)"
        ],
        expected_impact="Improve credit score by 15-30 points over 6 months, save ${total_interest_savings_6mo:,.0f} in interest charges by following the plan",
        target_signals=["high_utilization", "credit_card_utilization_above_50"],
        data_points_needed=["card_type", "card_last_4", "utilization_percent", "balance", "limit", "monthly_interest", "annual_interest", "monthly_payment_months_1_2", "monthly_payment_months_3_4", "monthly_payment_months_5_6", "utilization_after_2mo", "automatic_payment_amount", "potential_balance_transfer_savings", "total_interest_savings_6mo"]
    ),
    ActionableRecommendation(
        id="reduce_interest_charges",
        persona_id="high_utilization",
        priority=RecommendationPriority.HIGH,
        title="Reduce Monthly Interest Charges",
        template="We noticed you're paying ${monthly_interest:,.2f} per month in interest charges on your {card_type} ending in {card_last_4}. Paying ${extra_payment:,.0f} more per month could save you ${annual_savings:,.0f} in interest over the next year.",
        action_items=[
            "Increase your monthly payment by ${extra_payment:,.0f}",
            "Pay more than the minimum payment of ${minimum_payment:,.0f}",
            "Consider consolidating debt to a lower interest rate",
            "Use the debt avalanche method: pay extra toward the highest interest card first"
        ],
        expected_impact="Save ${annual_savings:,.0f} in interest charges, pay off debt {months_faster} months faster",
        target_signals=["interest_charges", "minimum_payment_only"],
        data_points_needed=["card_type", "card_last_4", "monthly_interest", "extra_payment", "annual_savings", "minimum_payment", "months_faster"]
    ),
    ActionableRecommendation(
        id="stop_minimum_payments",
        persona_id="high_utilization",
        priority=RecommendationPriority.HIGH,
        title="Stop Making Only Minimum Payments",
        template="We noticed you're only making minimum payments of ${minimum_payment:,.0f} on your {card_type} ending in {card_last_4} (balance: ${balance:,.0f}). At this rate, it will take {months_to_payoff_min} months to pay off and cost ${total_interest_min:,.0f} in interest. Increasing your payment to ${payment_12mo:,.0f}/month would pay it off in 12 months and save ${interest_savings_12mo:,.0f} in interest.",
        action_items=[
            "Increase monthly payment from ${minimum_payment:,.0f} to ${payment_12mo:,.0f} to pay off in 12 months",
            "Set up automatic payments for the higher amount",
            "Use any extra income (tax refunds, bonuses) to make extra payments",
            "Track your progress monthly to stay motivated",
            "If ${payment_12mo:,.0f}/month isn't feasible, start with ${minimum_payment:,.0f} and increase by $50/month each month"
        ],
        expected_impact="Pay off debt {months_faster_12mo} months faster (in 12 months instead of {months_to_payoff_min}), save ${interest_savings_12mo:,.0f} in interest",
        target_signals=["minimum_payment_only", "high_utilization"],
        data_points_needed=["card_type", "card_last_4", "minimum_payment", "balance", "months_to_payoff_min", "total_interest_min", "payment_12mo", "interest_savings_12mo", "months_faster_12mo"]
    ),
    ActionableRecommendation(
        id="address_overdue_status",
        persona_id="high_utilization",
        priority=RecommendationPriority.HIGH,
        title="Address Overdue Payment",
        template="We noticed your {card_type} ending in {card_last_4} has an overdue payment of ${amount_due:,.0f}. This is negatively impacting your credit score. Making a payment immediately can prevent further damage.",
        action_items=[
            "Pay the overdue amount of ${amount_due:,.0f} immediately",
            "Set up automatic payments to prevent future overdue payments",
            "Contact the credit card company to discuss payment options if needed",
            "Consider a payment plan if you're struggling to catch up"
        ],
        expected_impact="Prevent further credit score damage, avoid late fees, maintain good payment history",
        target_signals=["is_overdue", "overdue_payment"],
        data_points_needed=["card_type", "card_last_4", "amount_due"]
    ),
    
    # Variable Income Budgeter Recommendations
    ActionableRecommendation(
        id="build_emergency_fund",
        persona_id="variable_income_budgeter",
        priority=RecommendationPriority.HIGH,
        title="Build Emergency Fund with Variable Income",
        template="We noticed your cash buffer is {cash_buffer_months:.1f} months, which is below the recommended 2-3 months for variable income earners. With {median_pay_gap:.0f} days between paychecks, building a buffer is especially important. Choose a savings plan that fits your budget:",
        action_items=[
            "Option 1 (Fast Track): Save ${plan1_monthly:,.0f}/month to build a {plan1_months}-month buffer in {plan1_timeline} months",
            "Option 2 (Steady Progress): Save ${plan2_monthly:,.0f}/month to build a {plan2_months}-month buffer in {plan2_timeline} months",
            "Option 3 (Recommended): Save ${plan3_monthly:,.0f}/month to build a {plan3_months}-month buffer in {plan3_timeline} months",
            "Option 4 (Slow & Steady): Save ${plan4_monthly:,.0f}/month to build a {plan4_months}-month buffer in {plan4_timeline} months",
            "Use a separate high-yield savings account for your emergency fund",
            "Automate transfers to savings account on payday to build the habit"
        ],
        expected_impact="Build a 1-2 month emergency fund based on your chosen plan, reduce financial stress during income gaps",
        target_signals=["variable_income", "low_cash_buffer", "irregular_pay"],
        data_points_needed=["cash_buffer_months", "median_pay_gap", "one_month_expenses", "plan1_monthly", "plan1_months", "plan1_timeline", "plan2_monthly", "plan2_months", "plan2_timeline", "plan3_monthly", "plan3_months", "plan3_timeline", "plan4_monthly", "plan4_months", "plan4_timeline"]
    ),
    ActionableRecommendation(
        id="create_variable_income_budget",
        persona_id="variable_income_budgeter",
        priority=RecommendationPriority.HIGH,
        title="Create a Percent-Based Budget",
        template="We noticed your income varies significantly (paychecks every {median_pay_gap:.0f} days on average). A percent-based budget can help you manage expenses regardless of income amount. Allocate {needs_percent}% to needs, {wants_percent}% to wants, and {savings_percent}% to savings from each paycheck.",
        action_items=[
            "Calculate your average monthly income: ${avg_monthly_income:,.0f}",
            "Use percentages: {needs_percent}% needs (${needs_amount:,.0f}), {wants_percent}% wants (${wants_amount:,.0f}), {savings_percent}% savings (${savings_amount:,.0f})",
            "Adjust percentages when income is higher or lower than average",
            "Track spending in each category to stay on target"
        ],
        expected_impact="Better manage variable income, reduce overspending, build savings consistently",
        target_signals=["variable_income", "irregular_pay"],
        data_points_needed=["median_pay_gap", "needs_percent", "wants_percent", "savings_percent", "avg_monthly_income", "needs_amount", "wants_amount", "savings_amount"]
    ),
    
    # Subscription-Heavy Recommendations
    ActionableRecommendation(
        id="audit_subscriptions",
        persona_id="subscription_heavy",
        priority=RecommendationPriority.HIGH,
        title="Review and Cancel Unused Subscriptions",
        template="You spend ${monthly_recurring_spend:,.0f} a month on subscriptions ({subscription_share_of_total:.1f}% of your total spending). Click here to check all your subscriptions and decide which to keep or cancel.",
        action_items=[
            "List all {num_recurring} subscriptions and identify which you actually use",
            "Cancel subscriptions you haven't used in the last 90 days",
            "Look for duplicate services (e.g., multiple streaming services)",
            "Consider annual plans instead of monthly to save 10-20%",
            "Set reminders to review subscriptions quarterly"
        ],
        expected_impact="Save ${potential_savings:,.0f}/year by canceling unused subscriptions, reduce monthly expenses by ${monthly_savings:,.0f}",
        target_signals=["subscription_heavy", "multiple_recurring_subscriptions"],
        data_points_needed=["num_recurring", "monthly_recurring_spend", "subscription_share_of_total", "annual_spend", "potential_savings", "monthly_savings"]
    ),
    ActionableRecommendation(
        id="negotiate_subscription_rates",
        persona_id="subscription_heavy",
        priority=RecommendationPriority.MEDIUM,
        title="Negotiate Better Subscription Rates",
        template="You're spending ${monthly_recurring_spend:,.0f}/month on subscriptions. Many services offer discounts for annual plans or student/military rates. You could potentially save ${annual_savings:,.0f}/year by switching to annual plans or negotiating better rates.",
        action_items=[
            "Contact subscription services to ask about annual plan discounts",
            "Check if you qualify for student, military, or family plan discounts",
            "Look for promotional rates or introductory offers",
            "Consider sharing family plans with trusted friends or family members",
            "Use subscription management tools to track and optimize spending"
        ],
        expected_impact="Save ${annual_savings:,.0f}/year, reduce monthly expenses while keeping services you use",
        target_signals=["subscription_heavy", "high_subscription_spend"],
        data_points_needed=["monthly_recurring_spend", "annual_savings"]
    ),
    ActionableRecommendation(
        id="subscription_free_trial_reminder",
        persona_id="subscription_heavy",
        priority=RecommendationPriority.MEDIUM,
        title="Review Free Trials and Auto-Renewals",
        template="You have {num_recurring} active subscriptions. Many free trials convert to paid subscriptions automatically. Review your subscriptions to identify any you forgot to cancel after a free trial period.",
        action_items=[
            "Check all subscriptions for auto-renewal settings",
            "Set calendar reminders before free trial periods end",
            "Cancel subscriptions you only signed up for a trial",
            "Use a subscription tracking app to monitor all renewals",
            "Review bank statements monthly for unexpected subscription charges"
        ],
        expected_impact="Avoid unexpected charges, save money on unused subscriptions",
        target_signals=["subscription_heavy", "multiple_recurring_subscriptions"],
        data_points_needed=["num_recurring"]
    ),
    ActionableRecommendation(
        id="subscription_consolidation",
        persona_id="subscription_heavy",
        priority=RecommendationPriority.LOW,
        title="Consolidate Duplicate Services",
        template="You're spending ${monthly_recurring_spend:,.0f}/month on subscriptions. Look for overlapping services - you might have multiple streaming services, music apps, or cloud storage subscriptions. Pick one service per category to save ${potential_savings:,.0f}/month.",
        action_items=[
            "Group subscriptions by category (streaming, music, cloud storage, etc.)",
            "Choose one service per category and cancel the rest",
            "Share family plans with trusted friends or family members",
            "Use free alternatives where possible (e.g., free cloud storage tiers)",
            "Set a monthly subscription budget limit (e.g., $50/month)"
        ],
        expected_impact="Save ${potential_savings:,.0f}/month by eliminating duplicate services",
        target_signals=["subscription_heavy", "high_subscription_spend"],
        data_points_needed=["monthly_recurring_spend", "potential_savings"]
    ),
    ActionableRecommendation(
        id="subscription_impact_on_goals",
        persona_id="subscription_heavy",
        priority=RecommendationPriority.HIGH,
        title="See How Subscriptions Impact Your Financial Goals",
        template="Your ${monthly_recurring_spend:,.0f}/month in subscriptions adds up to ${annual_spend:,.0f} per year. That's money that could go toward paying off debt, building savings, or other financial goals. Reducing subscriptions by 30% could free up ${annual_savings:,.0f}/year.",
        action_items=[
            "Calculate how much you could save by canceling unused subscriptions",
            "Set a goal: save ${annual_savings:,.0f} this year by reducing subscriptions",
            "Redirect subscription savings to debt payoff or savings goals",
            "Track progress monthly toward your financial goals",
            "Celebrate milestones when you hit savings targets"
        ],
        expected_impact="Free up ${annual_savings:,.0f}/year for debt payoff or savings goals",
        target_signals=["subscription_heavy", "high_subscription_spend"],
        data_points_needed=["monthly_recurring_spend", "annual_spend", "annual_savings"]
    ),
    ActionableRecommendation(
        id="subscription_usage_tracking",
        persona_id="subscription_heavy",
        priority=RecommendationPriority.MEDIUM,
        title="Track Your Actual Subscription Usage",
        template="You have {num_recurring} subscriptions costing ${monthly_recurring_spend:,.0f}/month. Many people pay for subscriptions they rarely use. Track your usage for 30 days to see which subscriptions you actually use regularly.",
        action_items=[
            "List all subscriptions and their monthly costs",
            "Track which ones you use daily, weekly, or monthly",
            "Cancel subscriptions you use less than once per month",
            "Set a usage threshold: if you use it <2x/month, cancel it",
            "Review and adjust subscriptions quarterly"
        ],
        expected_impact="Save ${potential_savings:,.0f}/month by canceling rarely-used subscriptions",
        target_signals=["subscription_heavy", "multiple_recurring_subscriptions"],
        data_points_needed=["num_recurring", "monthly_recurring_spend", "potential_savings"]
    ),
    ActionableRecommendation(
        id="subscription_budget_limit",
        persona_id="subscription_heavy",
        priority=RecommendationPriority.MEDIUM,
        title="Set a Monthly Subscription Budget",
        template="Your subscriptions are {subscription_share_of_total:.1f}% of your total spending (${monthly_recurring_spend:,.0f}/month). Setting a monthly subscription budget (e.g., 5% of income) can help you stay on track and avoid subscription creep.",
        action_items=[
            "Calculate a reasonable subscription budget (e.g., 5% of monthly income)",
            "List all subscriptions and prioritize by value and usage",
            "Cancel subscriptions that push you over budget",
            "Before subscribing to anything new, cancel something else",
            "Review budget monthly and adjust as needed"
        ],
        expected_impact="Control subscription spending, stay within budget, reduce financial stress",
        target_signals=["subscription_heavy", "high_subscription_spend"],
        data_points_needed=["subscription_share_of_total", "monthly_recurring_spend"]
    ),
    ActionableRecommendation(
        id="subscription_annual_vs_monthly",
        persona_id="subscription_heavy",
        priority=RecommendationPriority.LOW,
        title="Switch to Annual Plans to Save Money",
        template="Many of your subscriptions offer annual plans at 10-20% discounts. If you spend ${monthly_recurring_spend:,.0f}/month on subscriptions, switching to annual plans for services you use regularly could save you ${annual_savings:,.0f}/year.",
        action_items=[
            "Identify subscriptions you use regularly and plan to keep",
            "Check if annual plans are available and calculate savings",
            "Switch to annual plans for 3-5 most-used subscriptions",
            "Set aside money monthly to pay annual fees upfront",
            "Track your annual savings from the switch"
        ],
        expected_impact="Save ${annual_savings:,.0f}/year by switching to annual plans",
        target_signals=["subscription_heavy", "high_subscription_spend"],
        data_points_needed=["monthly_recurring_spend", "annual_savings"]
    ),
    
    # Savings Builder Recommendations
    ActionableRecommendation(
        id="optimize_savings_apy",
        persona_id="savings_builder",
        priority=RecommendationPriority.LOW,
        title="Maximize Your Savings with Higher APY",
        template="We noticed you're actively building savings (${total_savings_balance:,.0f} saved, ${monthly_net_inflow:,.0f}/month contributions). Your current savings account is earning {current_apy:.2f}% APY. Moving to a high-yield savings account with {high_apy:.2f}% APY could earn you an additional ${additional_annual_earnings:,.0f} per year.",
        action_items=[
            "Research high-yield savings accounts (HYSA) with APY above {high_apy:.2f}%",
            "Open a new HYSA and transfer your ${total_savings_balance:,.0f} savings",
            "Set up automatic transfers of ${monthly_net_inflow:,.0f}/month to the new account",
            "Keep your emergency fund in the HYSA for easy access",
            "Consider certificates of deposit (CDs) for longer-term savings goals"
        ],
        expected_impact="Earn an additional ${additional_annual_earnings:,.0f}/year in interest, accelerate savings growth",
        target_signals=["savings_builder", "active_savings", "low_apy"],
        data_points_needed=["total_savings_balance", "monthly_net_inflow", "current_apy", "high_apy", "additional_annual_earnings"]
    ),
    ActionableRecommendation(
        id="set_savings_goals",
        persona_id="savings_builder",
        priority=RecommendationPriority.LOW,
        title="Set Specific Savings Goals",
        template="We noticed you're saving ${monthly_net_inflow:,.0f}/month consistently. Setting specific savings goals can help you save even more. With your current savings rate, you could reach a ${goal_amount:,.0f} goal in {months_to_goal:.0f} months.",
        action_items=[
            "Define specific savings goals (emergency fund, vacation, down payment, etc.)",
            "Calculate how much you need: ${goal_amount:,.0f}",
            "Set a timeline: {months_to_goal:.0f} months at your current rate",
            "Automate savings transfers to make progress automatic",
            "Track progress monthly and celebrate milestones"
        ],
        expected_impact="Reach ${goal_amount:,.0f} savings goal in {months_to_goal:.0f} months, build financial confidence",
        target_signals=["savings_builder", "consistent_savings"],
        data_points_needed=["monthly_net_inflow", "goal_amount", "months_to_goal"]
    ),
    
    # Balanced/Stable Recommendations
    ActionableRecommendation(
        id="optimize_financial_habits",
        persona_id="balanced_stable",
        priority=RecommendationPriority.LOW,
        title="Optimize Your Financial Habits",
        template="You're maintaining good financial habits with {utilization_below_30}% credit utilization and ${monthly_savings:,.0f}/month in savings. Consider optimizing further by reviewing your investment options, maximizing retirement contributions, or exploring additional income streams.",
        action_items=[
            "Review your investment portfolio and rebalance if needed",
            "Maximize employer 401(k) match if available",
            "Consider opening a Roth IRA for tax-free growth",
            "Explore side income opportunities to increase savings rate",
            "Review insurance coverage to ensure adequate protection"
        ],
        expected_impact="Further optimize financial health, accelerate wealth building, prepare for long-term goals",
        target_signals=["balanced_stable", "good_utilization", "consistent_savings"],
        data_points_needed=["utilization_below_30", "monthly_savings"]
    ),
]


