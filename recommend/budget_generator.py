"""RAG-based budget generator that creates random preset budgets with category allocations."""

import os
import json
import random
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
import requests
import uuid

from ingest.schema import Budget, Transaction, Account
from collections import defaultdict


class RAGBudgetGenerator:
    """Generates random preset budgets using RAG for intelligent allocation."""
    
    def __init__(self, api_key: Optional[str] = None, db_path: str = "data/spendsense.db"):
        """Initialize RAG budget generator.
        
        Args:
            api_key: OpenAI API key. If not provided, reads from OPENAI_API_KEY env var.
            db_path: Path to SQLite database
        """
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.enabled = self.api_key is not None
        self.db_path = db_path
        
    def generate_user_budget(
        self,
        db_session: Session,
        user_id: str,
        month: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate random preset budget for a user with category allocations.
        
        Args:
            db_session: Database session
            user_id: User ID
            month: Month in YYYY-MM format (defaults to current month)
        
        Returns:
            Dictionary with generated budget and category allocations
        """
        # Parse month or use current month
        if month:
            try:
                month_date = datetime.strptime(month, "%Y-%m")
            except ValueError:
                month_date = datetime.now().replace(day=1)
        else:
            month_date = datetime.now().replace(day=1)
        
        # Calculate period
        period_start = month_date.replace(day=1)
        if month_date.month == 12:
            period_end = month_date.replace(year=month_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            period_end = month_date.replace(month=month_date.month + 1, day=1) - timedelta(days=1)
        
        # Get user's spending patterns to inform budget
        # Only include checking and saving accounts (depository accounts)
        user_accounts = db_session.query(Account).filter(
            and_(
                Account.user_id == user_id,
                Account.type == 'depository'
            )
        ).all()
        account_ids = [acc.id for acc in user_accounts]
        
        # Get recent transactions to understand spending patterns
        recent_start = period_start - timedelta(days=90)
        transactions = []
        if account_ids:
            transactions = db_session.query(Transaction).filter(
                and_(
                    Transaction.account_id.in_(account_ids),
                    Transaction.date >= recent_start,
                    Transaction.date < period_start,
                    Transaction.amount < 0  # Only expenses
                )
            ).all()
        
        # Calculate average spending by category
        category_spending = defaultdict(float)
        for tx in transactions:
            category = tx.primary_category or "Uncategorized"
            category_spending[category] += abs(tx.amount)
        
        # Get user's monthly income
        from features.pipeline import FeaturePipeline
        feature_pipeline = FeaturePipeline(self.db_path)
        features = feature_pipeline.compute_features_for_user(user_id, 90)
        income_features = features.get('income', {})
        monthly_income = income_features.get('minimum_monthly_income', 0.0)
        if monthly_income == 0.0:
            avg_income_per_pay = income_features.get('average_income_per_pay', 0.0)
            frequency = income_features.get('payment_frequency', {}).get('frequency', 'monthly')
            if frequency == 'weekly':
                monthly_income = avg_income_per_pay * 4.33
            elif frequency == 'biweekly':
                monthly_income = avg_income_per_pay * 2.17
            elif frequency == 'monthly':
                monthly_income = avg_income_per_pay
        
        # CRITICAL: Budget is based on 100% of take-home income
        # Total budget equals monthly take-home income
        if monthly_income <= 0:
            total_budget = 0.0
            category_budgets = {}
        else:
            total_budget = monthly_income
            
            # Check if user has debt
            has_debt = self._user_has_debt(db_session, user_id)
            
            # Allocate fixed percentages based on financial best practices
            # Using lower end of recommended ranges
            housing_budget = total_budget * 0.25  # 25% (lower end of 25-30%)
            food_budget = total_budget * 0.10     # 10% (lower end of 10-15%)
            transportation_budget = total_budget * 0.15  # 15% (lower end of 15-20%)
            savings_budget = total_budget * 0.10  # 10% (lower end of 10-20%)
            debt_repayment_budget = total_budget * 0.10 if has_debt else 0.0  # 10% if debt exists
            
            # Calculate remaining for "Other" category
            allocated = housing_budget + food_budget + transportation_budget + savings_budget + debt_repayment_budget
            other_budget = total_budget - allocated
            
            # Build category budgets dictionary
            category_budgets = {
                "Housing": housing_budget,
                "Food": food_budget,
                "Transportation": transportation_budget,
                "Savings": savings_budget,
                "Other": other_budget
            }
            
            # Only include debt repayment if user has debt
            if has_debt:
                category_budgets["Debt Repayment"] = debt_repayment_budget
        
        # Store budgets in database
        budget_id = str(uuid.uuid4())
        
        # Store overall budget
        overall_budget = Budget(
            id=budget_id,
            user_id=user_id,
            category=None,
            amount=total_budget,
            period_start=period_start,
            period_end=period_end,
            is_suggested=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db_session.add(overall_budget)
        
        # Store category budgets
        category_budget_ids = []
        for category, amount in category_budgets.items():
            cat_budget_id = str(uuid.uuid4())
            cat_budget = Budget(
                id=cat_budget_id,
                user_id=user_id,
                category=category,
                amount=amount,
                period_start=period_start,
                period_end=period_end,
                is_suggested=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db_session.add(cat_budget)
            category_budget_ids.append(cat_budget_id)
        
        db_session.commit()
        
        # Calculate percentages for each category
        category_percentages = {}
        for category, amount in category_budgets.items():
            percentage = (amount / total_budget * 100) if total_budget > 0 else 0
            category_percentages[category] = round(percentage, 1)
        
        return {
            "user_id": user_id,
            "month": month_date.strftime("%Y-%m"),
            "total_budget": total_budget,
            "category_budgets": category_budgets,
            "category_percentages": category_percentages,
            "budget_id": budget_id,
            "category_budget_ids": category_budget_ids,
            "monthly_income": monthly_income
        }
    
    def _generate_category_allocations_with_rag(
        self,
        categories: List[str],
        total_budget: float,
        historical_spending: Dict[str, float]
    ) -> Dict[str, float]:
        """Generate category allocations using RAG.
        
        Args:
            categories: List of spending categories
            total_budget: Total budget amount
            historical_spending: Historical spending by category
        
        Returns:
            Dictionary of category -> budget allocation
        """
        try:
            # Build prompt for RAG
            prompt = self._build_budget_allocation_prompt(
                categories, total_budget, historical_spending
            )
            
            # Call OpenAI API
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",  # Use o1-mini equivalent for faster responses
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a financial budget allocation expert. Generate realistic budget allocations for spending categories based on historical patterns and best practices."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Parse JSON response
                try:
                    # Try to extract JSON if wrapped in markdown
                    import re
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        content = json_match.group(0)
                    
                    allocations_data = json.loads(content)
                    
                    # Check if we have the new format with percentages
                    if 'percentages' in allocations_data and 'amounts' in allocations_data:
                        percentages = allocations_data['percentages']
                        amounts = allocations_data['amounts']
                        
                        # Validate percentages sum to 100
                        total_percent = sum(percentages.values())
                        if abs(total_percent - 100) < 0.1:  # Allow small floating point errors
                            # Validate amounts sum to total_budget (within 5% tolerance)
                            allocation_sum = sum(amounts.values())
                            if 0.95 * total_budget <= allocation_sum <= 1.05 * total_budget:
                                # Normalize to match total_budget exactly
                                scale_factor = total_budget / allocation_sum
                                return {k: v * scale_factor for k, v in amounts.items()}
                    
                    # Fallback: try old format (direct amounts)
                    if isinstance(allocations_data, dict) and 'percentages' not in allocations_data:
                        allocations = allocations_data
                        allocation_sum = sum(allocations.values())
                        if 0.95 * total_budget <= allocation_sum <= 1.05 * total_budget:
                            scale_factor = total_budget / allocation_sum
                            return {k: v * scale_factor for k, v in allocations.items()}
                    
                    # Fallback if validation fails
                    return self._generate_random_category_allocations(
                        categories, total_budget, historical_spending
                    )
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    print(f"⚠️  Failed to parse RAG response: {e}")
                    # Fallback if parsing fails
                    return self._generate_random_category_allocations(
                        categories, total_budget, historical_spending
                    )
            else:
                # Fallback on API error
                return self._generate_random_category_allocations(
                    categories, total_budget, historical_spending
                )
        except Exception as e:
            print(f"⚠️  RAG budget generation failed: {e}")
            # Fallback to random allocation
            return self._generate_random_category_allocations(
                categories, total_budget, historical_spending
            )
    
    def _build_budget_allocation_prompt(
        self,
        categories: List[str],
        total_budget: float,
        historical_spending: Dict[str, float]
    ) -> str:
        """Build prompt for RAG budget allocation using percentages."""
        prompt = f"""Generate a realistic monthly budget allocation using percentages for the following categories:

Total Budget: ${total_budget:,.2f}

Categories: {', '.join(categories)}

"""
        if historical_spending:
            prompt += "Historical spending (last 90 days):\n"
            for category, amount in sorted(historical_spending.items(), key=lambda x: x[1], reverse=True)[:10]:
                prompt += f"  - {category}: ${amount:,.2f}\n"
            prompt += "\n"
        
        prompt += """Allocate the total budget across these categories using PERCENTAGES following these principles:
1. Assign a percentage to each category (e.g., 30% for subscriptions, 40% for dining, 10% for miscellaneous)
2. All percentages must sum to 100%
3. Allocate based on historical spending patterns (if available) but vary the percentages to be realistic
4. Use realistic budget percentages (e.g., 20-40% for major categories, 5-15% for smaller ones)
5. Each category should get at least 5% unless there are many categories

Return a JSON object with TWO keys:
- "percentages": An object with category names as keys and percentage values (0-100) as values
- "amounts": An object with category names as keys and calculated dollar amounts (percentage * total_budget)

Example format:
{
  "percentages": {
    "Food and Drink": 30,
    "Transportation": 20,
    "Entertainment": 15,
    "Bills and Utilities": 25,
    "Miscellaneous": 10
  },
  "amounts": {
    "Food and Drink": 600.00,
    "Transportation": 400.00,
    "Entertainment": 300.00,
    "Bills and Utilities": 500.00,
    "Miscellaneous": 200.00
  }
}

IMPORTANT: The percentages must sum to exactly 100, and the amounts must sum to exactly the total budget.

Return ONLY the JSON object, no additional text."""
        
        return prompt
    
    def _generate_random_category_allocations(
        self,
        categories: List[str],
        total_budget: float,
        historical_spending: Dict[str, float]
    ) -> Dict[str, float]:
        """Generate random category allocations using percentages (fallback method).
        
        Args:
            categories: List of spending categories
            total_budget: Total budget amount
            historical_spending: Historical spending by category (for weighting)
        
        Returns:
            Dictionary of category -> budget allocation
        """
        # Generate random percentages that sum to 100%
        num_categories = len(categories)
        percentages = []
        remaining_percent = 100.0
        
        if historical_spending and len(historical_spending) > 0:
            # Weight percentages based on historical spending
            total_historical = sum(historical_spending.values())
            sorted_categories = sorted(historical_spending.items(), key=lambda x: x[1], reverse=True)
            
            # Generate percentages weighted by historical spending
            for i, (category, historical_amount) in enumerate(sorted_categories):
                if i == len(sorted_categories) - 1:
                    # Last category gets the remainder
                    percentages.append((category, remaining_percent))
                else:
                    # Base percentage from historical spending
                    base_percent = (historical_amount / total_historical * 100) if total_historical > 0 else (100 / num_categories)
                    # Add randomness (±20%)
                    random_percent = base_percent * random.uniform(0.8, 1.2)
                    # Ensure minimum 5% and leave room for others
                    random_percent = max(5.0, min(random_percent, remaining_percent - (num_categories - i - 1) * 5))
                    percentages.append((category, random_percent))
                    remaining_percent -= random_percent
        else:
            # Generate random percentages if no historical data
            for i, category in enumerate(categories):
                if i == len(categories) - 1:
                    # Last category gets the remainder
                    percentages.append((category, remaining_percent))
                else:
                    # Random percentage between 10-40% for first few, 5-15% for others
                    if i < min(3, num_categories - 1):
                        random_percent = random.uniform(10, 40)
                    else:
                        random_percent = random.uniform(5, 15)
                    # Ensure we don't exceed remaining
                    random_percent = min(random_percent, remaining_percent - (num_categories - i - 1) * 5)
                    percentages.append((category, random_percent))
                    remaining_percent -= random_percent
        
        # Convert percentages to dollar amounts
        allocations = {}
        for category, percentage in percentages:
            allocations[category] = (total_budget * percentage / 100.0)
        
        # Normalize to ensure exact total (fix any rounding errors)
        total_allocated = sum(allocations.values())
        if total_allocated > 0 and abs(total_allocated - total_budget) > 0.01:
            scale_factor = total_budget / total_allocated
            allocations = {k: v * scale_factor for k, v in allocations.items()}
        
        return allocations
    
    def _user_has_debt(self, db_session: Session, user_id: str) -> bool:
        """Check if user has any debt (credit cards or loans).
        
        Args:
            db_session: Database session
            user_id: User ID
        
        Returns:
            True if user has debt, False otherwise
        """
        # Check for credit card accounts with balance > 0
        credit_accounts = db_session.query(Account).filter(
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
        loan_accounts = db_session.query(Account).filter(
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
    
    def _map_transaction_category_to_budget_category(
        self,
        tx_category: str,
        tx_merchant: Optional[str],
        account_type: Optional[str]
    ) -> str:
        """Map transaction category to budget category.
        
        Args:
            tx_category: Transaction primary category
            tx_merchant: Merchant name (optional)
            account_type: Account type (optional)
        
        Returns:
            Budget category name
        """
        if not tx_category:
            tx_category = "Uncategorized"
        
        # Housing: Rent, Mortgage, Bills and Utilities
        if tx_category in ["Rent", "Mortgage", "Bills and Utilities"]:
            return "Housing"
        
        # Food: Food and Drink, Groceries
        if tx_category in ["Food and Drink", "Groceries"]:
            return "Food"
        
        # Transportation: Transportation, Gas Stations
        if tx_category in ["Transportation", "Gas Stations"]:
            return "Transportation"
        
        # Debt Repayment: Check if this is a debt payment transaction
        if self._is_debt_repayment_transaction(tx_category, tx_merchant, account_type):
            return "Debt Repayment"
        
        # Other: All remaining categories
        return "Other"
    
    def _is_debt_repayment_transaction(
        self,
        tx_category: Optional[str],
        tx_merchant: Optional[str],
        account_type: Optional[str]
    ) -> bool:
        """Check if a transaction is a debt repayment.
        
        Args:
            tx_category: Transaction primary category
            tx_merchant: Merchant name
            account_type: Account type
        
        Returns:
            True if this is a debt repayment transaction
        """
        if not tx_merchant:
            tx_merchant = ""
        if not tx_category:
            tx_category = ""
        
        merchant_upper = tx_merchant.upper()
        category_upper = tx_category.upper()
        
        # Check for debt-related keywords in merchant name
        debt_keywords = ["PAYMENT", "LOAN", "CREDIT CARD", "CREDITCARD", "DEBT", "PAYOFF"]
        if any(keyword in merchant_upper for keyword in debt_keywords):
            return True
        
        # Check for debt-related categories
        if "LOAN" in category_upper or "PAYMENT" in category_upper:
            return True
        
        # Note: Debt payments are typically from checking accounts (depository)
        # to credit/loan accounts, so we rely on merchant name and category patterns
        # rather than account type
        
        return False

