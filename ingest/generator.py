"""Synthetic data generator for Plaid-style financial data."""

import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from faker import Faker
import pandas as pd

# Try to import synthetic-data integration
try:
    from ingest.synthetic_data_integration import SyntheticDataIntegration
    SYNTHETIC_DATA_INTEGRATION_AVAILABLE = True
except ImportError:
    SYNTHETIC_DATA_INTEGRATION_AVAILABLE = False

fake = Faker()
random.seed(42)
Faker.seed(42)


class SyntheticDataGenerator:
    """Generate synthetic Plaid-style financial data."""
    
    # Account types and subtypes
    ACCOUNT_TYPES = {
        "depository": ["checking", "savings", "money_market", "hsa"],
        "credit": ["credit_card"],
        "loan": ["mortgage", "student_loan"]
    }
    
    # Merchant categories for realistic transactions
    MERCHANT_CATEGORIES = {
        "Food & Drink": [
            "McDonald's", "Starbucks", "Chipotle", "Whole Foods", "Trader Joe's",
            "Pizza Hut", "Subway", "Dunkin' Donuts", "Panera Bread"
        ],
        "Shops": [
            "Amazon", "Target", "Walmart", "Costco", "Home Depot", "Best Buy",
<<<<<<< HEAD
            "CVS Pharmacy", "Walgreens", "Macy's", "Nike", "Adidas", "Puma",
            "Reebok", "New Balance", "Uniqlo"
=======
            "CVS Pharmacy", "Walgreens", "Macy's", "Nike"
>>>>>>> 8fa267a461e5ea19895459dde8fa79dd393d6af3
        ],
        "Gas Stations": [
            "Shell", "Exxon", "BP", "Chevron", "Mobil"
        ],
        "Transportation": [
            "Uber", "Lyft", "Metro Transit", "Amtrak", "Delta Airlines"
        ],
        "Entertainment": [
            "Netflix", "Spotify", "Disney+", "HBO Max", "AMC Theaters",
            "MoviePass", "Apple Music", "YouTube Premium"
        ],
        "Bills & Utilities": [
            "Electric Company", "Water Utility", "Internet Provider", 
            "Phone Company", "Cable Company"
        ],
        "Healthcare": [
            "CVS Pharmacy", "Walgreens Pharmacy", "Hospital", "Doctor Office",
            "Dental Office", "Vision Center"
        ]
    }
    
    # Amount ranges based on transactions_final.csv analysis
    # Maps our categories to realistic amount ranges (using quartiles for better distribution)
    CATEGORY_AMOUNT_RANGES = {
        "Food & Drink": {  # Maps to restaurant + groceries
            "min": 5.0,
            "q25": 10.0,
            "median": 30.0,
            "q75": 70.0,
            "max": 300.0,
        },
        "Shops": {  # Maps to retail + online_shopping
            "min": 10.0,
            "q25": 10.0,
            "median": 30.0,
            "q75": 70.0,
            "max": 500.0,
        },
        "Gas Stations": {
            "min": 15.0,
            "q25": 20.0,
            "median": 28.0,
            "q75": 65.0,
            "max": 100.0,
        },
        "Transportation": {
            "min": 10.0,
            "q25": 10.0,
            "median": 30.0,
            "q75": 65.0,
            "max": 300.0,
        },
        "Entertainment": {
            "min": 5.0,
            "q25": 11.0,
            "median": 33.0,
            "q75": 72.0,
            "max": 150.0,
        },
        "Bills & Utilities": {
            "min": 10.0,
            "q25": 11.0,
            "median": 31.0,
            "q75": 65.0,
            "max": 400.0,
        },
        "Healthcare": {
            "min": 10.0,
            "q25": 12.0,
            "median": 30.0,
            "q75": 74.0,
            "max": 250.0,
        },
    }
    
    def _get_realistic_amount(self, category: str) -> float:
        """Get a realistic transaction amount for a category based on transactions_final.csv patterns.
        
        Uses quartile-based distribution to match real-world patterns.
        """
        if category not in self.CATEGORY_AMOUNT_RANGES:
            # Default range
            return random.uniform(10.0, 150.0)
        
        ranges = self.CATEGORY_AMOUNT_RANGES[category]
        # Use weighted selection based on quartiles (more realistic distribution)
        rand = random.random()
        if rand < 0.25:
            # 25% in first quartile
            return random.uniform(ranges["min"], ranges["q25"])
        elif rand < 0.5:
            # 25% in second quartile
            return random.uniform(ranges["q25"], ranges["median"])
        elif rand < 0.75:
            # 25% in third quartile
            return random.uniform(ranges["median"], ranges["q75"])
        else:
            # 25% in fourth quartile (with occasional large transactions)
            if random.random() < 0.1:  # 10% chance of very large
                return random.uniform(ranges["q75"], ranges["max"])
            else:
                return random.uniform(ranges["q75"], ranges["q75"] * 1.5)
    
    # Subscription merchants (recurring)
    SUBSCRIPTION_MERCHANTS = [
        "Netflix", "Spotify", "Disney+", "HBO Max", "Apple Music",
        "YouTube Premium", "Amazon Prime", "Microsoft 365", "Adobe Creative Cloud",
        "Gym Membership", "Fitness App", "Newsletter Subscription"
    ]
    
    def __init__(
        self,
        num_users: int = 5,
        use_csv_source: bool = False,
        csv_path: str = "data/transactions_final.csv",
        use_synthetic_data_lib: bool = False,
    ):
        """Initialize generator.
        
        Args:
            num_users: Number of users to generate (default 5)
            use_csv_source: If True, use transactions_final.csv as source for transaction data
            csv_path: Path to transactions_final.csv file
            use_synthetic_data_lib: If True, use synthetic-data library integration (removes lat/lng and fraud)
        """
        self.num_users = num_users
        self.users = []
        self.accounts = []
        self.transactions = []
        self.liabilities = []
        self._merchant_id_map = {}
        self.use_csv_source = use_csv_source
        self.csv_path = csv_path
        self.use_synthetic_data_lib = use_synthetic_data_lib and SYNTHETIC_DATA_INTEGRATION_AVAILABLE
        self._low_risk_two_account_count = 0  # Track low-risk users with exactly 2 accounts
        
        # Initialize synthetic-data integration if requested
        if self.use_synthetic_data_lib:
            self.synthetic_integration = SyntheticDataIntegration(num_users=num_users)
            print("Using synthetic-data library integration (latitude/longitude and fraud removed)")
        else:
            self.synthetic_integration = None
        
    def generate_user(self) -> Dict[str, Any]:
        """Generate a single user with matching name and email."""
        user_id = str(uuid.uuid4())
        # Generate name
        first_name = fake.first_name()
        last_name = fake.last_name()
        full_name = f"{first_name} {last_name}"
        
        # Generate matching email based on name
        email = f"{first_name.lower()}.{last_name.lower()}@{fake.domain_name()}"
        
        return {
            "id": user_id,
            "name": full_name,
            "email": email,
            "created_at": fake.date_time_between(start_date="-2y", end_date="-1m")
        }
    
    def generate_accounts(self, user_id: str, financial_profile: str, persona: str = None) -> List[Dict[str, Any]]:
        """Generate accounts for a user based on financial profile.
        
        Args:
            user_id: User ID
            financial_profile: One of 'high_income', 'middle_income', 'low_income',
                             'high_utilization', 'saver', 'variable_income'
        """
        accounts = []
        
        # Everyone gets at least a checking account
        # Generate 12-digit account ID (ensure first digit is 1-9 to avoid leading zeros)
        checking_account_id = str(random.randint(1, 9)) + ''.join([str(random.randint(0, 9)) for _ in range(11)])
        
        # Persona-specific checking balance (for cash-flow buffer)
        # Strict enforcement to ensure persona matching
        if persona == "variable_income_budgeter":
            # Variable income: low cash buffer (<1 month expenses = ~$200-1000)
            # This ensures cash_flow_buffer_months < 1.0
            checking_balance = random.uniform(200, 800)
        elif persona == "savings_builder":
            # Savings builder: moderate checking, more in savings
            checking_balance = random.uniform(1000, 5000)
        elif persona == "balanced_stable":
            # Balanced: higher checking balance to ensure cash_flow_buffer >= 1 month
            checking_balance = random.uniform(2000, 8000)
        else:
            # Others: normal checking balance
            checking_balance = random.uniform(1000, 5000)
        
        accounts.append({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "account_id": checking_account_id,
            "name": "Primary Checking",
            "type": "depository",
            "subtype": "checking",
            "iso_currency_code": "USD",
            "available": checking_balance,
            "current": checking_balance,
            "limit": None,
            "holder_category": "individual"
        })
        
        # Determine credit cards FIRST (needed for savings account logic)
        # Strict persona enforcement: ensure users only match their assigned persona
        num_credit_cards = 0
        if persona == "high_utilization":
            # High utilization: ALWAYS has cards with high balances (50-95% utilization)
            # This ensures they match high_utilization persona
            num_credit_cards = random.randint(1, 2)
        elif persona == "savings_builder":
            # Savings builder: may have cards but LOW utilization (<30%)
            # Special case: Allow 2 low-risk users (savings_builder) with exactly 2 accounts
            if self._low_risk_two_account_count < 2:
                # This will be one of the 2 low-risk users with 2 accounts (no credit cards)
                num_credit_cards = 0
            else:
                # Savings builders can have cards but with low utilization
                num_credit_cards = random.randint(0, 1) if random.random() < 0.5 else 0
        elif persona == "balanced_stable":
            # Balanced: moderate cards, moderate utilization (10-40%)
            # Special case: 2 users should have only 2 accounts total (checking + savings, no credit cards)
            if self._low_risk_two_account_count < 2:
                # This will be one of the 2 low-risk users with 2 accounts (no credit cards)
                num_credit_cards = 0
            else:
                # Other balanced users get 0-2 credit cards with moderate utilization
                num_credit_cards = random.randint(0, 2) if random.random() < 0.7 else 0
        elif persona == "variable_income_budgeter":
            # Variable income: may have cards, but utilization should be moderate to avoid matching high_utilization
            num_credit_cards = random.randint(0, 1) if random.random() < 0.6 else 0
        elif persona == "subscription_heavy":
            # Subscription-heavy: may have cards, but utilization should be moderate
            num_credit_cards = random.randint(0, 1) if random.random() < 0.6 else 0
        else:
            # Default: no credit cards
            num_credit_cards = 0
        
        # Add savings account - persona-specific logic
        has_savings = False
        if persona == "high_utilization":
            # High utilization: NO savings account to avoid matching savings_builder
            has_savings = False
            savings_balance = 0
        elif persona == "savings_builder":
            # Savings builder: always has savings account with high balance
            # But if it's one of the 2 low-risk users with 2 accounts, track it
            has_savings = True
            if self._low_risk_two_account_count < 2 and num_credit_cards == 0:
                savings_balance = random.uniform(5000, 50000)
                self._low_risk_two_account_count += 1
            else:
                savings_balance = random.uniform(5000, 50000)
        elif persona == "balanced_stable":
            # Balanced: usually has savings
            # Special case: 2 users should have exactly 2 accounts (checking + savings, no credit cards)
            if self._low_risk_two_account_count < 2 and num_credit_cards == 0:
                # This will be one of the 2 low-risk users with 2 accounts
                has_savings = True
                savings_balance = random.uniform(2000, 20000)
                self._low_risk_two_account_count += 1
            else:
                has_savings = random.random() < 0.8
                savings_balance = random.uniform(2000, 20000) if has_savings else 0
        elif persona == "variable_income_budgeter":
            # Variable income: may have savings but lower amounts
            has_savings = random.random() < 0.5
            savings_balance = random.uniform(100, 3000) if has_savings else 0
        else:
            # Others: standard chance
            has_savings = random.random() < 0.7
            savings_balance = random.uniform(1000, 50000) if (has_savings and financial_profile == "saver") else (random.uniform(100, 5000) if has_savings else 0)
        
        if has_savings:
            # Generate 12-digit account ID (ensure first digit is 1-9)
            account_id_12digit = str(random.randint(1, 9)) + ''.join([str(random.randint(0, 9)) for _ in range(11)])
            
            accounts.append({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "account_id": account_id_12digit,
                "name": "Savings Account",
                "type": "depository",
                "subtype": "savings",
                "iso_currency_code": "USD",
                "available": savings_balance,
                "current": savings_balance,
                "limit": None,
                "holder_category": "individual"
            })
        
        for _ in range(num_credit_cards):
            limit = random.choice([5000, 10000, 15000, 20000, 25000])
            
            # Persona-specific balance logic (strict enforcement)
            if persona == "high_utilization":
                # High utilization: MUST be ≥50% to match persona criteria
                balance = limit * random.uniform(0.50, 0.95)  # 50-95% utilization
            elif persona == "savings_builder":
                # Savings builder: MUST be <30% utilization to match persona criteria
                balance = limit * random.uniform(0.05, 0.25)  # 5-25% utilization (low)
            elif persona == "balanced_stable":
                # Balanced: MUST be <50% utilization to avoid matching high_utilization
                balance = limit * random.uniform(0.10, 0.40)  # 10-40% utilization (moderate)
            elif persona == "variable_income_budgeter":
                # Variable income: Moderate utilization, but <50% to avoid matching high_utilization
                balance = limit * random.uniform(0.15, 0.45)  # 15-45% utilization
            elif persona == "subscription_heavy":
                # Subscription-heavy: Moderate utilization, but <50% to avoid matching high_utilization
                balance = limit * random.uniform(0.15, 0.45)  # 15-45% utilization
            elif financial_profile == "high_utilization":
                balance = limit * random.uniform(0.8, 0.95)
            elif financial_profile == "saver":
                balance = limit * random.uniform(0.05, 0.3)
            else:
                balance = limit * random.uniform(0.2, 0.6)
            
            # Generate 12-digit account ID (ensure first digit is 1-9)
            account_id_12digit = str(random.randint(1, 9)) + ''.join([str(random.randint(0, 9)) for _ in range(11)])
            
            # Different card types for multiple cards
            card_types = ['Visa', 'Mastercard', 'American Express', 'Discover']
            card_name = f"{random.choice(card_types)} Credit Card"
            if num_credit_cards > 1:
                card_name = f"{card_name} #{_ + 1}"
            
            # Calculate amount due (current balance)
            amount_due = balance
            # Minimum payment is typically 2% of balance or $25, whichever is higher
            minimum_payment_due = max(balance * 0.02, 25.0)
            
            accounts.append({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "account_id": account_id_12digit,
                "name": card_name,
                "type": "credit",
                "subtype": "credit_card",
                "iso_currency_code": "USD",
                "available": limit - balance,
                "current": balance,
                "limit": limit,
                "amount_due": amount_due,  # Total amount due
                "minimum_payment_due": minimum_payment_due,  # Minimum payment due
                "holder_category": "individual"
            })
            
            # Determine payment behavior for minimum-payment-only detection
            # For high_utilization persona, always minimum-only behavior to ensure they match
            if persona == "high_utilization":
                is_minimum_only = True  # Always minimum-only for high_utilization
            else:
                is_minimum_only = False  # Other personas don't use minimum-only payments
            minimum_payment_amt = max(balance * 0.02, 25.0)
            
            # Set last_payment_amount based on behavior
            if is_minimum_only:
                last_payment_amount = minimum_payment_amt  # Always minimum
            else:
                # Variable: sometimes minimum, sometimes more
                last_payment_amount = minimum_payment_amt if random.random() < 0.4 else random.uniform(minimum_payment_amt * 1.5, balance * 0.5)
            
            # Add liability for credit card
            self.liabilities.append({
                "id": str(uuid.uuid4()),
                "account_id": accounts[-1]["account_id"],
                "apr_type": random.choice(["variable", "fixed"]),
                "apr_percentage": random.uniform(15.0, 29.99),
                "minimum_payment_amount": minimum_payment_amt,
                "last_payment_amount": last_payment_amount,  # Based on behavior pattern
                "last_payment_date": fake.date_time_between(start_date="-30d", end_date="now"),
                "is_overdue": random.random() < 0.4 if persona == "high_utilization" else False,  # Only high_utilization can be overdue
                "next_payment_due_date": fake.date_time_between(start_date="now", end_date="+15d"),
                "last_statement_balance": balance,
                "liability_type": "credit_card"
            })
        
        # Add HSA (20% of users)
        if random.random() < 0.2:
            # Generate 12-digit account ID (ensure first digit is 1-9)
            account_id_12digit = str(random.randint(1, 9)) + ''.join([str(random.randint(0, 9)) for _ in range(11)])
            
            accounts.append({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "account_id": account_id_12digit,
                "name": "Health Savings Account",
                "type": "depository",
                "subtype": "hsa",
                "iso_currency_code": "USD",
                "available": random.uniform(500, 5000),
                "current": random.uniform(500, 5000),
                "limit": None,
                "holder_category": "individual"
            })
        
        # Add mortgage (35% of users)
        # Note: Users can have both mortgage and student loans - each is a separate account
        # with its own interest_rate and next_payment_due_date
        if random.random() < 0.35:
            # Mortgage balance (outstanding principal)
            mortgage_balance = random.uniform(150000, 500000)
            original_balance = mortgage_balance * random.uniform(1.2, 1.5)  # Original was higher
            interest_rate = random.uniform(3.0, 7.5)  # Typical mortgage rates
            next_payment_due_date = fake.date_time_between(start_date="now", end_date="+30d")
            
            # Generate 12-digit account ID (ensure first digit is 1-9)
            account_id_12digit = str(random.randint(1, 9)) + ''.join([str(random.randint(0, 9)) for _ in range(11)])
            
            accounts.append({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "account_id": account_id_12digit,
                "name": "Mortgage",
                "type": "loan",
                "subtype": "mortgage",
                "iso_currency_code": "USD",
                "available": None,
                "current": -mortgage_balance,  # Negative for liability
                "limit": None,
                "holder_category": "individual",
                # Loan-specific fields as part of account structure
                "interest_rate": interest_rate,
                "next_payment_due_date": next_payment_due_date
            })
            
            # Add liability for mortgage
            self.liabilities.append({
                "id": str(uuid.uuid4()),
                "account_id": accounts[-1]["account_id"],
                "apr_type": None,  # Not applicable for mortgages
                "apr_percentage": None,
                "minimum_payment_amount": None,
                "last_payment_amount": None,
                "last_payment_date": None,
                "is_overdue": random.random() < 0.05,  # 5% chance of overdue
                "next_payment_due_date": next_payment_due_date,
                "last_statement_balance": None,
                "interest_rate": interest_rate,
                "liability_type": "mortgage"
            })
        
        # Add student loan (25-35% of users)
        if random.random() < 0.30:
            # Student loan balance
            loan_balance = random.uniform(10000, 80000)
            interest_rate = random.uniform(3.5, 8.5)  # Typical student loan rates
            next_payment_due_date = fake.date_time_between(start_date="now", end_date="+30d")
            
            # Generate 12-digit account ID (ensure first digit is 1-9)
            account_id_12digit = str(random.randint(1, 9)) + ''.join([str(random.randint(0, 9)) for _ in range(11)])
            
            accounts.append({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "account_id": account_id_12digit,
                "name": random.choice(["Federal Student Loan", "Private Student Loan", "Student Loan"]),
                "type": "loan",
                "subtype": "student_loan",
                "iso_currency_code": "USD",
                "available": None,
                "current": -loan_balance,  # Negative for liability
                "limit": None,
                "holder_category": "individual",
                # Loan-specific fields as part of account structure
                "interest_rate": interest_rate,
                "next_payment_due_date": next_payment_due_date
            })
            
            # Add liability for student loan
            self.liabilities.append({
                "id": str(uuid.uuid4()),
                "account_id": accounts[-1]["account_id"],
                "apr_type": None,  # Not applicable for student loans
                "apr_percentage": None,
                "minimum_payment_amount": None,
                "last_payment_amount": None,
                "last_payment_date": None,
                "is_overdue": random.random() < 0.08,  # 8% chance of overdue (slightly higher than mortgage)
                "next_payment_due_date": next_payment_due_date,
                "last_statement_balance": None,
                "interest_rate": interest_rate,
                "liability_type": "student_loan"
            })
        
        return accounts
    
    def generate_transactions(
        self, 
        account: Dict[str, Any], 
        start_date: datetime, 
        end_date: datetime,
        financial_profile: str,
        persona: str = None
    ) -> List[Dict[str, Any]]:
        """Generate transactions for an account."""
        transactions = []
        account_type = account["type"]
        account_subtype = account.get("subtype", "")
        
        if account_type == "depository":
            # Generate subscription transactions first (recurring, periodic)
            if account_subtype == "checking":
                # Persona-specific subscription count (strict enforcement)
                if persona == "subscription_heavy":
                    # Subscription-heavy: MUST have ≥3 subscriptions AND (≥$50/month OR ≥10% of spend)
                    # Generate 4-7 subscriptions to ensure they meet criteria
                    num_subscriptions = random.randint(4, 7)
                elif persona == "balanced_stable":
                    # Balanced: <5 subscriptions to match persona criteria
                    num_subscriptions = random.randint(1, 3)
                elif persona == "high_utilization":
                    # High utilization: Lower subscriptions to avoid matching subscription_heavy
                    num_subscriptions = random.randint(0, 2)
                elif persona == "variable_income_budgeter":
                    # Variable income: Lower subscriptions
                    num_subscriptions = random.randint(1, 3)
                elif persona == "savings_builder":
                    # Savings builder: Lower subscriptions
                    num_subscriptions = random.randint(1, 3)
                else:
                    # Default: 2-3 subscriptions
                    num_subscriptions = random.randint(2, 3)
                
                subscription_merchants = random.sample(self.SUBSCRIPTION_MERCHANTS, min(num_subscriptions, len(self.SUBSCRIPTION_MERCHANTS)))
                
                for merchant in subscription_merchants:
                    # Determine subscription frequency: monthly (30 days), bi-monthly (60 days), or 30-day interval
                    frequency = random.choice(["monthly", "bimonthly", "30day"])
                    if frequency == "monthly":
                        interval_days = 30
                    elif frequency == "bimonthly":
                        interval_days = 60
                    else:  # 30day
                        interval_days = 30
                    
                    # Subscription amount based on merchant type
                    if "Netflix" in merchant or "Spotify" in merchant or "Disney+" in merchant or "HBO Max" in merchant:
                        sub_amount = random.uniform(8, 15)
                    elif "Apple Music" in merchant or "YouTube Premium" in merchant:
                        sub_amount = random.uniform(10, 15)
                    elif "Amazon Prime" in merchant:
                        sub_amount = random.uniform(12, 15)
                    elif "Microsoft 365" in merchant or "Adobe" in merchant:
                        sub_amount = random.uniform(10, 25)
                    elif "Gym" in merchant or "Fitness" in merchant:
                        sub_amount = random.uniform(20, 60)
                    else:
                        sub_amount = random.uniform(5, 20)
                    
                    # Generate periodic subscription transactions
                    tx_date = start_date
                    while tx_date <= end_date:
                        transactions.append({
                            "id": str(uuid.uuid4()),
                            "account_id": account["account_id"],
                            "transaction_id": f"txn_{fake.uuid4()}",
                            "date": tx_date,
                            "amount": -sub_amount,  # Negative - subscription is an expense
                            "merchant_name": merchant,
                            "merchant_entity_id": None,
                            "payment_channel": "online",
                            "primary_category": "General Merchandise",
                            "detailed_category": "Subscription",
                            "pending": False
                        })
                        tx_date += timedelta(days=interval_days)
<<<<<<< HEAD
                
                # Recurring transaction patterns for all users
                # Starbucks: 2-4 transactions per week
                starbucks_per_week = random.randint(2, 4)
                days_between_starbucks = 7.0 / starbucks_per_week  # Distribute evenly across week
                starbucks_date = start_date
                while starbucks_date <= end_date:
                    # Randomize time of day (typical coffee shop hours: 6 AM - 10 PM)
                    hour = random.randint(6, 22)
                    minute = random.randint(0, 59)
                    starbucks_datetime = starbucks_date.replace(hour=hour, minute=minute)
                    if starbucks_datetime <= end_date:
                        transactions.append({
                            "id": str(uuid.uuid4()),
                            "account_id": account["account_id"],
                            "transaction_id": f"txn_{fake.uuid4()}",
                            "date": starbucks_datetime,
                            "amount": -random.uniform(5.0, 8.0),  # Typical coffee price
                            "merchant_name": "Starbucks",
                            "merchant_entity_id": None,
                            "payment_channel": random.choice(["in store", "online"]),
                            "primary_category": "Food & Drink",
                            "detailed_category": "Coffee Shop",
                            "pending": False
                        })
                    starbucks_date += timedelta(days=days_between_starbucks)
                
                # Athletic retailers: 1 transaction per month per retailer
                # Each user gets 2-4 different athletic retailers
                athletic_retailers = ["Nike", "Adidas", "Puma", "Reebok", "New Balance"]
                num_athletic_retailers = random.randint(2, 4)
                selected_retailers = random.sample(athletic_retailers, num_athletic_retailers)
                
                for retailer in selected_retailers:
                    # Determine amount range based on retailer
                    if retailer == "Nike":
                        amount_range = (50.0, 200.0)
                    elif retailer == "Adidas":
                        amount_range = (50.0, 200.0)
                    elif retailer == "Puma":
                        amount_range = (40.0, 150.0)
                    elif retailer == "Reebok":
                        amount_range = (40.0, 150.0)
                    elif retailer == "New Balance":
                        amount_range = (50.0, 180.0)
                    else:
                        amount_range = (50.0, 200.0)
                    
                    # Generate monthly transactions
                    retailer_date = start_date.replace(day=1)  # Start from first of month
                    while retailer_date <= end_date:
                        # Randomize date within the month (1-28 to avoid month-end issues)
                        day_of_month = random.randint(1, 28)
                        try:
                            retailer_datetime = retailer_date.replace(day=day_of_month)
                        except ValueError:
                            # Handle months with fewer days
                            retailer_datetime = retailer_date.replace(day=28)
                        
                        if retailer_datetime >= start_date and retailer_datetime <= end_date:
                            transactions.append({
                                "id": str(uuid.uuid4()),
                                "account_id": account["account_id"],
                                "transaction_id": f"txn_{fake.uuid4()}",
                                "date": retailer_datetime,
                                "amount": -random.uniform(amount_range[0], amount_range[1]),
                                "merchant_name": retailer,
                                "merchant_entity_id": None,
                                "payment_channel": random.choice(["in store", "online"]),
                                "primary_category": "Shops",
                                "detailed_category": "Athletic Wear",
                                "pending": False
                            })
                        # Move to next month
                        if retailer_date.month == 12:
                            retailer_date = retailer_date.replace(year=retailer_date.year + 1, month=1, day=1)
                        else:
                            retailer_date = retailer_date.replace(month=retailer_date.month + 1, day=1)
                
                # Uniqlo: 1-2 transactions per month
                uniqlo_frequency = random.randint(1, 2)  # 1 or 2 times per month
                uniqlo_date = start_date.replace(day=1)  # Start from first of month
                while uniqlo_date <= end_date:
                    for _ in range(uniqlo_frequency):
                        # Randomize date within the month
                        day_of_month = random.randint(1, 28)
                        try:
                            uniqlo_datetime = uniqlo_date.replace(day=day_of_month)
                        except ValueError:
                            # Handle months with fewer days
                            uniqlo_datetime = uniqlo_date.replace(day=28)
                        
                        if uniqlo_datetime >= start_date and uniqlo_datetime <= end_date:
                            transactions.append({
                                "id": str(uuid.uuid4()),
                                "account_id": account["account_id"],
                                "transaction_id": f"txn_{fake.uuid4()}",
                                "date": uniqlo_datetime,
                                "amount": -random.uniform(30.0, 120.0),
                                "merchant_name": "Uniqlo",
                                "merchant_entity_id": None,
                                "payment_channel": random.choice(["in store", "online"]),
                                "primary_category": "Shops",
                                "detailed_category": "Clothing",
                                "pending": False
                            })
                    # Move to next month
                    if uniqlo_date.month == 12:
                        uniqlo_date = uniqlo_date.replace(year=uniqlo_date.year + 1, month=1, day=1)
                    else:
                        uniqlo_date = uniqlo_date.replace(month=uniqlo_date.month + 1, day=1)
=======
>>>>>>> 8fa267a461e5ea19895459dde8fa79dd393d6af3
            
            # Income transactions (payroll)
            if account_subtype == "checking":
                # Persona-specific income patterns (strict enforcement)
                if persona == "variable_income_budgeter":
                    # Variable income: irregular pay gaps (>45 days median) AND low cash buffer
                    # Generate only 2-3 payroll transactions with 45-60 day gaps over 180 days
                    # This ensures median_pay_gap > 45 days
                    # For variable income, still target around $60-70K yearly but with larger variance
                    # With 2-3 paychecks over 180 days, each should be larger to maintain similar yearly income
                    # 3 paychecks: $60K/3 = $20K per paycheck, $70K/3 = $23.3K per paycheck
                    # 2 paychecks: $60K/2 = $30K per paycheck, $70K/2 = $35K per paycheck
                    current_date = start_date
                    num_payrolls = random.randint(2, 3)  # Fewer payrolls = larger gaps
                    for i in range(num_payrolls):
                        if num_payrolls == 2:
                            # 2 paychecks over 180 days: larger amounts to maintain yearly income
                            # But can also be lower for variable income with low income profile
                            if financial_profile == "low_income":
                                amount = random.uniform(14000, 18000)  # Targets $28-35K yearly
                            else:
                                amount = random.uniform(28000, 35000)  # Targets $60-70K yearly
                        else:
                            # 3 paychecks over 180 days: medium amounts
                            if financial_profile == "low_income":
                                amount = random.uniform(9000, 14000)  # Targets $28-35K yearly
                            else:
                                amount = random.uniform(18000, 24000)  # Targets $60-70K yearly
                        transactions.append({
                            "id": str(uuid.uuid4()),
                            "account_id": account["account_id"],
                            "transaction_id": f"txn_{fake.uuid4()}",
                            "date": current_date,
                            "amount": amount,
                            "merchant_name": "PAYROLL DEPOSIT",
                            "merchant_entity_id": None,
                            "payment_channel": "other",
                            "primary_category": "Transfer In",
                            "detailed_category": "Payroll",
                            "pending": False
                        })
                        # Next payroll in 45-60 days (ensures median > 45)
                        if i < num_payrolls - 1:  # Don't add days after last payroll
                            current_date += timedelta(days=random.randint(45, 60))
                else:
                    # Regular income: bi-weekly or monthly (for all other personas)
                    # Target median yearly income: $60-70K, minimum: ~$28K
                    # Bi-weekly (26 paychecks/year): $28K/26=$1,077, $60K/26=$2,308, $70K/26=$2,692 → median ~$2,500
                    # Monthly (12 paychecks/year): $28K/12=$2,333, $60K/12=$5,000, $70K/12=$5,833 → median ~$5,417
                    pay_frequency = random.choice(["biweekly", "monthly"])
                    if pay_frequency == "biweekly":
                        days_between = 14
                        # Bi-weekly: range from $28K to $72K+ yearly
                        # This gives $28,000-$72,800 yearly, median ~$65,000
                        if financial_profile == "high_income":
                            amount = random.uniform(2800, 3800)  # $72,800-$98,800 yearly
                        elif financial_profile == "middle_income":
                            amount = random.uniform(2200, 2800)  # $57,200-$72,800 yearly (median ~$65K)
                        elif financial_profile == "variable_income":
                            # Variable income: high variability but still around median
                            amount = random.uniform(2000, 3000) * random.uniform(0.8, 1.2)
                        elif financial_profile == "low_income":
                            # Low income: target minimum ~$28K yearly
                            amount = random.uniform(1150, 1900)  # $29,900-$49,400 yearly (min ~$28K)
                        else:
                            # Default: mix of low to middle income
                            amount = random.uniform(1150, 2700)  # $29,900-$70,200 yearly
                    else:
                        days_between = 30
                        # Monthly: range from $28K to $72K+ yearly
                        # This gives $28,000-$72,000 yearly, median ~$65,000
                        if financial_profile == "high_income":
                            amount = random.uniform(6000, 8000)  # $72,000-$96,000 yearly
                        elif financial_profile == "middle_income":
                            amount = random.uniform(5000, 5800)  # $60,000-$69,600 yearly (median ~$65K)
                        elif financial_profile == "variable_income":
                            # Variable income: high variability but still around median
                            amount = random.uniform(4500, 6000) * random.uniform(0.8, 1.2)
                        elif financial_profile == "low_income":
                            # Low income: target minimum ~$28K yearly
                            amount = random.uniform(2400, 3600)  # $28,800-$43,200 yearly (min ~$28K)
                        else:
                            # Default: mix of low to middle income
                            amount = random.uniform(2400, 5700)  # $28,800-$68,400 yearly
                    
                    current_date = start_date
                    while current_date <= end_date:
                        transactions.append({
                            "id": str(uuid.uuid4()),
                            "account_id": account["account_id"],
                            "transaction_id": f"txn_{fake.uuid4()}",
                            "date": current_date,
                            "amount": amount,
                            "merchant_name": "PAYROLL DEPOSIT",
                            "merchant_entity_id": None,
                            "payment_channel": "other",
                            "primary_category": "Transfer In",
                            "detailed_category": "Payroll",
                            "pending": False
                        })
                        current_date += timedelta(days=days_between)
                
                # Expense transactions
                num_expenses = random.randint(30, 120)  # 30-120 transactions over period
                expense_txs = []  # Store expense transactions for returns
                current_balance = account.get("current", 0) or 0
                
                for _ in range(num_expenses):
                    category = random.choice(list(self.MERCHANT_CATEGORIES.keys()))
                    merchant = random.choice(self.MERCHANT_CATEGORIES[category])
                    
                    # Get realistic amount based on category (from transactions_final.csv patterns)
                    amount = self._get_realistic_amount(category)
                    
                    # Ensure transaction doesn't exceed available balance (for checking accounts)
                    # Leave at least $100 buffer
                    available_balance = account.get("available", current_balance) or current_balance
                    if available_balance > 0:
                        max_amount = max(0, available_balance - 100)
                        if amount > max_amount:
                            amount = random.uniform(10, max_amount * 0.8) if max_amount > 10 else max_amount
                    
                    # Skip subscription merchants here - they'll be handled separately
                    if merchant in self.SUBSCRIPTION_MERCHANTS:
                        continue
                    
                    tx_date = fake.date_time_between(start_date=start_date, end_date=end_date)
                    
                    # Pending transactions should only be in last 24-48 hours
                    is_pending = False
                    now = datetime.now()
                    hours_ago = (now - tx_date).total_seconds() / 3600
                    if hours_ago <= 48 and random.random() < 0.15:  # 15% chance if recent
                        is_pending = True
                    
                    tx_data = {
                        "id": str(uuid.uuid4()),
                        "account_id": account["account_id"],
                        "transaction_id": f"txn_{fake.uuid4()}",
                        "date": tx_date,
                        "amount": -amount,  # Negative for expenses
                        "merchant_name": merchant,
                        "merchant_entity_id": None,
                        "payment_channel": random.choice(["in store", "online", "other"]),
                        "primary_category": category,
                        "detailed_category": category,
                        "pending": is_pending
                    }
                    transactions.append(tx_data)
                    expense_txs.append(tx_data)  # Store for potential returns
                
                # Add returns/partial returns (3-8% of purchases)
                num_returns = max(1, int(len(expense_txs) * random.uniform(0.03, 0.08)))
                return_txs = random.sample(expense_txs, min(num_returns, len(expense_txs)))
                
                for original_tx in return_txs:
                    # Return happens 3-30 days after purchase
                    return_date = original_tx["date"] + timedelta(days=random.randint(3, 30))
                    
                    # Skip if return date is beyond end_date
                    if return_date > end_date:
                        continue
                    
                    # Full return (60% chance) or partial return (40% chance)
                    if random.random() < 0.6:
                        # Full return
                        return_amount = abs(original_tx["amount"])
                    else:
                        # Partial return (40-90% of original)
                        return_amount = abs(original_tx["amount"]) * random.uniform(0.4, 0.9)
                    
                    transactions.append({
                        "id": str(uuid.uuid4()),
                        "account_id": account["account_id"],
                        "transaction_id": f"txn_{fake.uuid4()}",
                        "date": return_date,
                        "amount": return_amount,  # Positive - money back
                        "merchant_name": f"{original_tx['merchant_name']} - RETURN",
                        "merchant_entity_id": None,
                        "payment_channel": original_tx["payment_channel"],
                        "primary_category": original_tx["primary_category"],
                        "detailed_category": "Return",
                        "pending": False  # Returns are not pending
                    })
            
            # Savings transactions (deposits/withdrawals)
            elif account_subtype == "savings":
                # Persona-specific savings behavior (strict enforcement)
                if persona == "savings_builder":
                    # Savings builder: MUST have regular deposits ≥$200/month to match persona
                    # Generate monthly deposits of $200-1000
                    current_date = start_date
                    while current_date <= end_date:
                        # Savings builders: $200-1000 monthly deposits (ensures ≥$200/month)
                        deposit_amount = random.uniform(200, 1000)
                        transactions.append({
                            "id": str(uuid.uuid4()),
                            "account_id": account["account_id"],
                            "transaction_id": f"txn_{fake.uuid4()}",
                            "date": current_date,
                            "amount": deposit_amount,
                            "merchant_name": "TRANSFER FROM CHECKING",
                            "merchant_entity_id": None,
                            "payment_channel": "other",
                            "primary_category": "Transfer In",
                            "detailed_category": "Savings",
                            "pending": False
                        })
                        current_date += timedelta(days=random.randint(25, 35))  # Monthly deposits
                elif persona == "balanced_stable":
                    # Balanced: moderate savings deposits (but <$200/month to avoid matching savings_builder)
                    current_date = start_date
                    while current_date <= end_date:
                        transactions.append({
                            "id": str(uuid.uuid4()),
                            "account_id": account["account_id"],
                            "transaction_id": f"txn_{fake.uuid4()}",
                            "date": current_date,
                            "amount": random.uniform(50, 150),  # <$200/month
                            "merchant_name": "TRANSFER FROM CHECKING",
                            "merchant_entity_id": None,
                            "payment_channel": "other",
                            "primary_category": "Transfer In",
                            "detailed_category": "Savings",
                            "pending": False
                        })
                        current_date += timedelta(days=random.randint(14, 30))
                elif persona == "variable_income_budgeter":
                    # Variable income: minimal savings deposits (irregular income)
                    current_date = start_date
                    while current_date <= end_date:
                        if random.random() < 0.3:  # Only 30% chance of deposits
                            transactions.append({
                                "id": str(uuid.uuid4()),
                                "account_id": account["account_id"],
                                "transaction_id": f"txn_{fake.uuid4()}",
                                "date": current_date,
                                "amount": random.uniform(50, 200),
                                "merchant_name": "TRANSFER FROM CHECKING",
                                "merchant_entity_id": None,
                                "payment_channel": "other",
                                "primary_category": "Transfer In",
                                "detailed_category": "Savings",
                                "pending": False
                            })
                        current_date += timedelta(days=random.randint(30, 60))
                elif financial_profile == "saver":
                    # Legacy saver profile: moderate deposits
                    current_date = start_date
                    while current_date <= end_date:
                        transactions.append({
                            "id": str(uuid.uuid4()),
                            "account_id": account["account_id"],
                            "transaction_id": f"txn_{fake.uuid4()}",
                            "date": current_date,
                            "amount": random.uniform(100, 500),
                            "merchant_name": "TRANSFER FROM CHECKING",
                            "merchant_entity_id": None,
                            "payment_channel": "other",
                            "primary_category": "Transfer In",
                            "detailed_category": "Savings",
                            "pending": False
                        })
                        current_date += timedelta(days=random.randint(14, 30))
        
        elif account_type == "credit":
            # Credit card transactions
            num_transactions = random.randint(20, 80)
            expense_txs = []  # Store for returns
            credit_limit = account.get("limit", 5000)
            current_balance = abs(account.get("current", 0) or 0)
            available_credit = credit_limit - current_balance
            
            for _ in range(num_transactions):
                category = random.choice(list(self.MERCHANT_CATEGORIES.keys()))
                merchant = random.choice(self.MERCHANT_CATEGORIES[category])
                
                # Get realistic amount based on category
                amount = self._get_realistic_amount(category)
                
                # Ensure transaction doesn't exceed credit limit
                # Leave at least $100 of available credit
                max_amount = max(0, available_credit - 100)
                if amount > max_amount:
                    # Scale down to fit within limit
                    if max_amount > 10:
                        amount = random.uniform(10, max_amount * 0.8)
                    else:
                        continue  # Skip if not enough credit available
                tx_date = fake.date_time_between(start_date=start_date, end_date=end_date)
                
                # Pending transactions should only be in last 24-48 hours
                is_pending = False
                now = datetime.now()
                hours_ago = (now - tx_date).total_seconds() / 3600
                if hours_ago <= 48 and random.random() < 0.15:  # 15% chance if recent
                    is_pending = True
                
                tx_data = {
                    "id": str(uuid.uuid4()),
                    "account_id": account["account_id"],
                    "transaction_id": f"txn_{fake.uuid4()}",
                    "date": tx_date,
                    "amount": -amount,  # Negative for credit card charges
                    "merchant_name": merchant,
                    "merchant_entity_id": None,
                    "payment_channel": random.choice(["in store", "online", "other"]),
                    "primary_category": category,
                    "detailed_category": category,
                    "pending": is_pending
                }
                transactions.append(tx_data)
                expense_txs.append(tx_data)
            
            # Add returns for credit cards (3-8% of purchases)
            num_returns = max(1, int(len(expense_txs) * random.uniform(0.03, 0.08)))
            return_txs = random.sample(expense_txs, min(num_returns, len(expense_txs)))
            
            for original_tx in return_txs:
                return_date = original_tx["date"] + timedelta(days=random.randint(3, 30))
                if return_date > end_date:
                    continue
                
                if random.random() < 0.6:
                    return_amount = abs(original_tx["amount"])
                else:
                    return_amount = abs(original_tx["amount"]) * random.uniform(0.4, 0.9)
                
                transactions.append({
                    "id": str(uuid.uuid4()),
                    "account_id": account["account_id"],
                    "transaction_id": f"txn_{fake.uuid4()}",
                    "date": return_date,
                    "amount": return_amount,  # Positive - credit back
                    "merchant_name": f"{original_tx['merchant_name']} - RETURN",
                    "merchant_entity_id": None,
                    "payment_channel": original_tx["payment_channel"],
                    "primary_category": original_tx["primary_category"],
                    "detailed_category": "Return",
                    "pending": False
                })
            
            # Get liability for this account to determine payment behavior
            liability = next((l for l in self.liabilities if l.get("account_id") == account["account_id"]), None)
            minimum_payment = liability["minimum_payment_amount"] if liability else account.get("minimum_payment_due", 25.0)
            balance = account.get("current", 1000)
            
            # Determine payment behavior based on liability's last_payment_amount
            # If last_payment_amount equals minimum_payment_amount, user is minimum-only payer
            if liability and liability.get("last_payment_amount"):
                payment_behavior = "minimum_only" if abs(liability["last_payment_amount"] - liability["minimum_payment_amount"]) < 0.01 else "variable"
            else:
                # Fallback: use profile-based logic
                payment_behavior = "minimum_only" if financial_profile == "high_utilization" and random.random() < 0.7 else "variable"
            
            # Generate monthly payment (align with next_payment_due_date if available)
            if liability and liability.get("next_payment_due_date"):
                payment_date = liability["next_payment_due_date"]
                # Adjust to be within our date window
                while payment_date < start_date:
                    payment_date -= timedelta(days=30)
                while payment_date > end_date:
                    payment_date -= timedelta(days=30)
            else:
                payment_date = start_date + timedelta(days=random.randint(1, 15))  # Random date in first half of month
            
            while payment_date <= end_date:
                if payment_behavior == "minimum_only":
                    # Always pay exactly minimum (for detection)
                    payment_amount = minimum_payment
                else:
                    # Variable payments: sometimes minimum, sometimes more
                    if random.random() < 0.4:  # 40% chance of minimum payment
                        payment_amount = minimum_payment
                    else:
                        # Pay between minimum and balance
                        payment_amount = random.uniform(minimum_payment * 1.2, min(balance * 0.8, minimum_payment * 10))
                
                transactions.append({
                    "id": str(uuid.uuid4()),
                    "account_id": account["account_id"],
                    "transaction_id": f"txn_{fake.uuid4()}",
                    "date": payment_date,
                    "amount": payment_amount,  # Positive - payment reduces balance
                    "merchant_name": "CREDIT CARD PAYMENT",
                    "merchant_entity_id": None,
                    "payment_channel": "online",
                    "primary_category": "Transfer Out",
                    "detailed_category": "Payment",
                    "pending": False
                })
                payment_date += timedelta(days=30)
            
            # Add interest charges (monthly, if balance > 0)
            # Only high_utilization persona should have interest charges to ensure they match
            if balance > 0 and persona == "high_utilization":
                apr = liability["apr_percentage"] if liability else 25.0
                monthly_interest_rate = apr / 12.0 / 100.0
                
                interest_date = start_date
                while interest_date <= end_date:
                    # Interest charge = balance * monthly rate
                    interest_amount = balance * monthly_interest_rate
                    
                    transactions.append({
                        "id": str(uuid.uuid4()),
                        "account_id": account["account_id"],
                        "transaction_id": f"txn_{fake.uuid4()}",
                        "date": interest_date,
                        "amount": -interest_amount,  # Negative - interest charge
                        "merchant_name": "INTEREST CHARGE",
                        "merchant_entity_id": None,
                        "payment_channel": "other",
                        "primary_category": "Interest",
                        "detailed_category": "Interest Charge",
                        "pending": False
                    })
                    interest_date += timedelta(days=30)
        
        elif account_type == "loan":
            # Loan payment transactions (monthly payments)
            if account_subtype == "mortgage":
                # Monthly mortgage payments - NEGATIVE (money going out)
                current_date = start_date
                while current_date <= end_date:
                    # Typical mortgage payment: $800-$2000
                    payment_amount = random.uniform(800, 2000)
                    transactions.append({
                        "id": str(uuid.uuid4()),
                        "account_id": account["account_id"],
                        "transaction_id": f"txn_{fake.uuid4()}",
                        "date": current_date,
                        "amount": -payment_amount,  # Negative - money going out (expense)
                        "merchant_name": "MORTGAGE PAYMENT",
                        "merchant_entity_id": None,
                        "payment_channel": "online",
                        "primary_category": "Transfer Out",
                        "detailed_category": "Loan Payment",
                        "pending": False
                    })
                    current_date += timedelta(days=30)  # Monthly payments
            
            elif account_subtype == "student_loan":
                # Monthly student loan payments - NEGATIVE (money going out)
                current_date = start_date
                while current_date <= end_date:
                    # Typical student loan payment: $100-$600
                    payment_amount = random.uniform(100, 600)
                    transactions.append({
                        "id": str(uuid.uuid4()),
                        "account_id": account["account_id"],
                        "transaction_id": f"txn_{fake.uuid4()}",
                        "date": current_date,
                        "amount": -payment_amount,  # Negative - money going out (expense)
                        "merchant_name": "STUDENT LOAN PAYMENT",
                        "merchant_entity_id": None,
                        "payment_channel": "online",
                        "primary_category": "Transfer Out",
                        "detailed_category": "Loan Payment",
                        "pending": False
                    })
                    current_date += timedelta(days=30)  # Monthly payments
        
        return transactions
    
    def generate_all(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generate all synthetic data with persona-based distribution.
        
<<<<<<< HEAD
        Persona distribution for 100 users:
        - High Utilization: ~15-20 users
        - Variable Income Budgeter: ~15-20 users
        - Subscription-Heavy: ~15-20 users
        - Savings Builder: ~15-20 users
        - Balanced & Stable: ~20-25 users
        """
        # Persona distribution for diverse 100 users
        persona_distribution = [
            ("high_utilization", 18),         # 18 users
            ("variable_income_budgeter", 18),  # 18 users
            ("subscription_heavy", 18),       # 18 users
            ("savings_builder", 18),         # 18 users
            ("balanced_stable", 23),         # 23 users
=======
        Persona distribution:
        - High Utilization: 10% (least common)
        - Variable Income Budgeter: 20%
        - Subscription-Heavy: 20%
        - Savings Builder: 20%
        - Balanced & Stable: 30% (most common)
        """
        # Persona distribution (even distribution: 10 users each for 50 users)
        persona_distribution = [
            ("high_utilization", 10),         # 10 users (20%)
            ("variable_income_budgeter", 10),  # 10 users (20%)
            ("subscription_heavy", 10),       # 10 users (20%)
            ("savings_builder", 10),         # 10 users (20%)
            ("balanced_stable", 10),         # 10 users (20%)
>>>>>>> 8fa267a461e5ea19895459dde8fa79dd393d6af3
        ]
        
        # Assign personas to users
        persona_assignments = []
        for persona, count in persona_distribution:
            persona_assignments.extend([persona] * count)
        
        # Fill remaining slots (due to rounding) with balanced_stable
        while len(persona_assignments) < self.num_users:
            persona_assignments.append("balanced_stable")
        
        # Shuffle to randomize order
        random.shuffle(persona_assignments)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)  # Last 180 days of data for proper persona detection
        
        for i in range(self.num_users):
            # Assign persona-based profile
            persona = persona_assignments[i]
            profile = self._map_persona_to_profile(persona)
            
            # Generate user
            user = self.generate_user()
            self.users.append(user)
            
            # Generate accounts with persona-specific settings
            accounts = self.generate_accounts(user["id"], profile, persona)
            self.accounts.extend(accounts)
            
            # Generate transactions for each account
            for account in accounts:
                transactions = self.generate_transactions(
                    account, start_date, end_date, profile, persona
                )
                self.transactions.extend(transactions)
        
        return {
            "users": self.users,
            "accounts": self.accounts,
            "transactions": self.transactions,
            "liabilities": self.liabilities
        }
    
    def _map_persona_to_profile(self, persona: str) -> str:
        """Map persona to financial profile for backward compatibility."""
        # Map personas to income profiles with weighted distribution:
        # - ~10-15% low_income (to hit minimum ~$28K)
        # - ~60-70% middle_income (to maintain median ~$60-70K)
        # - ~15-20% high_income (for range)
        
        # Use a counter to ensure we get roughly the right distribution across all users
        if not hasattr(self, '_profile_counter'):
            self._profile_counter = {"low": 0, "middle": 0, "high": 0}
        
        rand = random.random()
        
        # First 10-15% of users should be low_income to hit minimum
        if self._profile_counter["low"] < (self.num_users * 0.15):
            if rand < 0.5:  # 50% chance if we haven't hit quota yet
                self._profile_counter["low"] += 1
                return "low_income"
        
        # Next 60-70% should be middle_income
        if self._profile_counter["middle"] < (self.num_users * 0.70):
            if rand < 0.7:  # 70% chance if we haven't hit quota yet
                self._profile_counter["middle"] += 1
                if persona == "variable_income_budgeter":
                    return "variable_income"
                elif persona == "savings_builder":
                    return "saver"
                else:
                    return "middle_income"
        
        # Rest should be high_income
        self._profile_counter["high"] += 1
        if persona == "high_utilization":
            return "high_utilization"
        else:
            return "high_income"
    
    def _generate_from_csv(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generate data using transactions_final.csv as source for transaction values."""
        import os
        
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"CSV source file not found: {self.csv_path}")
        
        print(f"Reading transaction data from {self.csv_path}...")
        df = pd.read_csv(self.csv_path)
        
        # Sample transactions from CSV (use up to 1000 transactions)
        max_transactions = min(1000, len(df))
        sampled_df = df.sample(n=max_transactions, random_state=42).reset_index(drop=True)
        
        # Generate users and accounts first
        financial_profiles = [
            "high_income", "middle_income", "low_income",
            "high_utilization", "saver", "variable_income"
        ]
        
        # Use same persona distribution as generate_all (even distribution)
        persona_distribution = [
            ("high_utilization", 10),
            ("variable_income_budgeter", 10),
            ("subscription_heavy", 10),
            ("savings_builder", 10),
            ("balanced_stable", 10),
        ]
        
        persona_assignments = []
        for persona, count in persona_distribution:
            persona_assignments.extend([persona] * count)
        
        while len(persona_assignments) < self.num_users:
            persona_assignments.append("balanced_stable")
        
        random.shuffle(persona_assignments)
        
        for i in range(self.num_users):
            persona = persona_assignments[i]
            profile = self._map_persona_to_profile(persona)
            user = self.generate_user()
            self.users.append(user)
            
            accounts = self.generate_accounts(user["id"], profile, persona)
            self.accounts.extend(accounts)
        
        # Map CSV transactions to our accounts
        # Group transactions by customer_id from CSV to distribute across our users
        user_accounts = {}  # user_id -> list of accounts
        
        for user in self.users:
            user_accounts[user["id"]] = [
                acc for acc in self.accounts if acc["user_id"] == user["id"]
            ]
        
        # Distribute CSV transactions across our users
        transactions_per_user = len(sampled_df) // self.num_users
        user_idx = 0
        
        for idx, row in sampled_df.iterrows():
            # Assign to user in round-robin fashion
            if user_idx >= self.num_users:
                user_idx = 0
            
            user = self.users[user_idx]
            user_accounts_list = user_accounts[user["id"]]
            
            if not user_accounts_list:
                user_idx += 1
                continue
            
            # Select an account (prefer checking/credit for transactions)
            account = random.choice(user_accounts_list)
            
            # Parse date from CSV
            try:
                tx_date = pd.to_datetime(row['timestamp'])
            except:
                tx_date = pd.to_datetime(row['date'])
            
            # Map CSV columns to our transaction format
            # Determine amount sign based on transaction_type
            amount = float(row['amount'])
            if row['transaction_type'] in ['purchase', 'fee', 'withdrawal']:
                amount = -abs(amount)  # Negative for expenses
            elif row['transaction_type'] in ['deposit', 'refund']:
                amount = abs(amount)  # Positive for income/returns
            elif row['transaction_type'] == 'transfer':
                # For transfers, check if it's outgoing (negative) or incoming (positive)
                # Assume outgoing for now (can be refined)
                amount = -abs(amount)
            
            # Map merchant_category to our category format
            merchant_category = str(row['merchant_category']).replace('_', ' ').title()
            primary_category = merchant_category
            
            # Determine pending status
            pending = row['status'] == 'pending'
            
            # Map payment_method to payment_channel
            payment_method = str(row['payment_method']).lower()
            if 'credit' in payment_method:
                payment_channel = 'online'
            elif 'debit' in payment_method:
                payment_channel = 'in store'
            elif 'digital' in payment_method or 'wallet' in payment_method:
                payment_channel = 'online'
            else:
                payment_channel = 'other'
            
            # Generate merchant name if not present
            merchant_name = f"Merchant {row['merchant_id']}" if pd.isna(row.get('merchant_name')) else str(row.get('merchant_name', 'Unknown'))
            
            transaction = {
                "id": str(uuid.uuid4()),
                "account_id": account["account_id"],
                "transaction_id": f"txn_{idx:08d}",
                "date": tx_date,
                "amount": amount,
                "merchant_name": merchant_name,
                "merchant_entity_id": str(row.get('merchant_id', '')),
                "payment_channel": payment_channel,
                "primary_category": primary_category,
                "detailed_category": primary_category,
                "pending": pending
            }
            
            self.transactions.append(transaction)
            
            # Move to next user after transactions_per_user transactions
            if (idx + 1) % transactions_per_user == 0:
                user_idx += 1
        
        print(f"Generated {len(self.users)} users, {len(self.accounts)} accounts, {len(self.transactions)} transactions from CSV")
        
        return {
            "users": self.users,
            "accounts": self.accounts,
            "transactions": self.transactions,
            "liabilities": self.liabilities
        }
    
    def _get_amount_category(self, amount: float) -> str:
        """Get amount category based on absolute value."""
        abs_amount = abs(amount)
        if abs_amount < 15:
            return "small"
        elif abs_amount < 50:
            return "medium"
        elif abs_amount < 100:
            return "large"
        elif abs_amount < 200:
            return "very_large"
        else:
            return "extra_large"
    
    def _get_transaction_type(self, merchant_name: str, detailed_category: str, amount: float) -> str:
        """Determine transaction type from transaction details."""
        if "RETURN" in merchant_name or detailed_category == "Return":
            return "refund"
        elif "PAYROLL" in merchant_name or detailed_category == "Payroll":
            return "deposit"
        elif "PAYMENT" in merchant_name or detailed_category == "Payment":
            return "transfer"
        elif "INTEREST CHARGE" in merchant_name or "FEE" in merchant_name:
            return "fee"
        elif "TRANSFER" in merchant_name:
            return "transfer"
        elif amount < 0:
            return "purchase"
        elif amount > 0 and "WITHDRAWAL" not in merchant_name:
            return "deposit"
        else:
            return "withdrawal"
    
    def _map_payment_channel_to_method(self, payment_channel: str, account_type: str) -> str:
        """Map payment_channel to payment_method format."""
        if account_type == "credit":
            return "credit_card"
        elif payment_channel == "online":
            return "digital_wallet"
        elif payment_channel == "in store":
            return "debit_card"
        elif payment_channel == "other":
            return "bank_transfer"
        else:
            return "debit_card"  # default
    
    def _generate_merchant_id(self, merchant_name: str) -> str:
        """Generate a merchant ID from merchant name."""
        # Create consistent merchant IDs based on name
        merchant_id_map = getattr(self, '_merchant_id_map', {})
        if merchant_name not in merchant_id_map:
            merchant_id_map[merchant_name] = f"MERCH{len(merchant_id_map):06d}"
        self._merchant_id_map = merchant_id_map
        return merchant_id_map[merchant_name]
    
    def save_to_csv(self, output_dir: str = "data/synthetic"):
        """Save generated data to CSV files matching transactions_final.csv format."""
        import os
        from collections import defaultdict
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Save users, accounts, liabilities as before
        pd.DataFrame(self.users).to_csv(f"{output_dir}/users.csv", index=False)
        pd.DataFrame(self.accounts).to_csv(f"{output_dir}/accounts.csv", index=False)
        pd.DataFrame(self.liabilities).to_csv(f"{output_dir}/liabilities.csv", index=False)
        
        # Create account lookup for account_id -> account details
        account_lookup = {acc["account_id"]: acc for acc in self.accounts}
        user_lookup = {acc["user_id"]: acc for acc in self.accounts}
        
        # Create user_id -> customer_id mapping (for dashboard consistency)
        user_id_to_customer = {}
        for idx, user in enumerate(self.users, 1):
            user_id_to_customer[user["id"]] = f"CUST{idx:06d}"
        
        # Build transactions CSV matching transactions_final.csv format
        transactions_final_rows = []
        
        # Track running balances per account (start with initial balances)
        account_balances = defaultdict(float)
        for acc in self.accounts:
            # Start with initial balance (for depository: current, for credit: -current)
            initial_balance = acc.get("current", 0) or 0
            if acc.get("type") == "credit":
                # Credit cards: balance is negative (what you owe)
                account_balances[acc["account_id"]] = initial_balance
            else:
                # Depository: balance is positive (what you have)
                account_balances[acc["account_id"]] = initial_balance
        
        # Sort transactions by date for proper balance tracking
        sorted_transactions = sorted(self.transactions, key=lambda x: x["date"])
        
        for tx in sorted_transactions:
            account = account_lookup.get(tx["account_id"])
            if not account:
                continue
            
            user_id = account["user_id"]
            customer_id = user_id_to_customer.get(user_id, f"CUST{hash(user_id) % 1000000:06d}")
            
            # Parse date
            if isinstance(tx["date"], str):
                tx_date = datetime.fromisoformat(tx["date"].replace('Z', '+00:00'))
            else:
                tx_date = tx["date"]
            
            # Update running balance (transaction amounts are already in correct sign)
            # For credit cards: negative amounts increase balance owed, positive decrease
            # For depository: negative amounts decrease balance, positive increase
            account_balances[tx["account_id"]] += tx["amount"]
            
            # Generate merchant ID
            merchant_id = self._generate_merchant_id(tx.get("merchant_name", "Unknown"))
            
            # Map merchant category
            merchant_category = tx.get("primary_category", "other").lower().replace(" & ", "_").replace(" ", "_")
            
            # Determine transaction type
            transaction_type = self._get_transaction_type(
                tx.get("merchant_name", ""),
                tx.get("detailed_category", ""),
                tx["amount"]
            )
            
            # Map payment method
            payment_method = self._map_payment_channel_to_method(
                tx.get("payment_channel", "other"),
                account.get("type", "depository")
            )
            
            # Get amount category
            amount_category = self._get_amount_category(tx["amount"])
            
            # Determine status
            status = "pending" if tx.get("pending", False) else "approved"
            
            # Extract time components
            hour = tx_date.hour
            day_of_week = tx_date.strftime("%A")
            month = tx_date.month
            month_name = tx_date.strftime("%B")
            quarter = (month - 1) // 3 + 1
            year = tx_date.year
            time = tx_date.strftime("%H:%M:%S")
            timestamp = tx_date.strftime("%Y-%m-%d %H:%M:%S")
            date = tx_date.strftime("%Y-%m-%d")
            
            transactions_final_rows.append({
                "transaction_id": tx.get("transaction_id", tx["id"]),
                "timestamp": timestamp,
                "date": date,
                "time": time,
                "customer_id": customer_id,  # Dashboard identifier (user)
                "merchant_id": merchant_id,
                "merchant_category": merchant_category,
                "transaction_type": transaction_type,
                "payment_method": payment_method,
                "amount": abs(tx["amount"]),  # transactions_final.csv shows positive amounts (sign in transaction_type)
                "amount_category": amount_category,
                "status": status,
                "account_balance": account_balances[tx["account_id"]],
                "account_id": tx["account_id"],  # Dashboard identifier (account, last 4 digits shown)
                "hour": hour,
                "day_of_week": day_of_week,
                "month": month,
                "month_name": month_name,
                "quarter": quarter,
                "year": year,
            })
        
        # Save transactions in transactions_final.csv format
        transactions_df = pd.DataFrame(transactions_final_rows)
        transactions_df.to_csv(f"{output_dir}/transactions_final.csv", index=False)
        
        # Also save in original format for compatibility
        pd.DataFrame(self.transactions).to_csv(f"{output_dir}/transactions.csv", index=False)
        
        print(f"Generated data saved to {output_dir}/")
        print(f"  - {len(self.users)} users")
        print(f"  - {len(self.accounts)} accounts")
        print(f"  - {len(self.transactions)} transactions")
        print(f"  - {len(self.liabilities)} liabilities")
        print(f"  - transactions_final.csv created with {len(transactions_final_rows)} rows")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate synthetic Plaid-style data")
    parser.add_argument("--num-users", type=int, default=75, help="Number of users to generate (50-100)")
    parser.add_argument("--output-dir", type=str, default="data/synthetic", help="Output directory")
    
    args = parser.parse_args()
    
    generator = SyntheticDataGenerator(num_users=args.num_users)
    generator.generate_all()
    generator.save_to_csv(args.output_dir)


