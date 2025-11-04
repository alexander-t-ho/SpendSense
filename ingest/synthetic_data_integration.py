#!/usr/bin/env python
"""
Integration with the synthetic-data library for generating transaction data.

This module adapts the synthetic-data library's transaction generation
to match SpendSense's Plaid-style structure while:
- Removing latitude/longitude fields
- Removing fraud indicators
- Adding persona-specific markers
- Ensuring data aligns with our 5 personas
"""

import sys
from pathlib import Path

# Add synthetic-data library to path if available
SYNTHETIC_DATA_PATH = Path("/Users/alexho/synthetic-data")
if SYNTHETIC_DATA_PATH.exists():
    sys.path.insert(0, str(SYNTHETIC_DATA_PATH))

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import random
import uuid

try:
    from synthetic_data.synthetic_data import make_tabular_data
    SYNTHETIC_DATA_AVAILABLE = True
except ImportError:
    SYNTHETIC_DATA_AVAILABLE = False
    print("Warning: synthetic-data library not found. Using fallback generation.")


class SyntheticDataIntegration:
    """
    Integrates synthetic-data library with SpendSense data generation.
    """
    
    def __init__(self, num_users: int = 50, seed: int = 42):
        """
        Initialize the integration.
        
        Args:
            num_users: Number of users to generate
            seed: Random seed for reproducibility
        """
        self.num_users = num_users
        self.seed = seed
        np.random.seed(seed)
        random.seed(seed)
        
        # Persona distribution (even: 10 users each)
        self.persona_distribution = [
            ("high_utilization", 10),
            ("variable_income_budgeter", 10),
            ("subscription_heavy", 10),
            ("savings_builder", 10),
            ("balanced_stable", 10),
        ]
        
        # Merchant categories matching our system
        self.merchant_categories = [
            'groceries', 'restaurant', 'gas_station', 'retail', 'online_shopping',
            'entertainment', 'utilities', 'transportation', 'healthcare', 'other'
        ]
        
        # Transaction types matching our system
        self.transaction_types = ['purchase', 'refund', 'transfer', 'withdrawal', 'deposit', 'fee']
        
        # Payment methods matching our system
        self.payment_methods = ['credit_card', 'debit_card', 'cash', 'digital_wallet', 'bank_transfer']
    
    def generate_transactions_for_user(
        self,
        user_id: str,
        customer_id: str,
        persona: str,
        accounts: List[Dict],
        start_date: datetime,
        end_date: datetime,
        transactions_per_account: int = 50
    ) -> List[Dict]:
        """
        Generate transactions for a single user using synthetic-data approach.
        
        Args:
            user_id: User identifier
            customer_id: Customer identifier (CUST000001)
            persona: Persona type (high_utilization, etc.)
            accounts: List of account dictionaries
            start_date: Start date for transactions
            end_date: End date for transactions
            transactions_per_account: Number of transactions per account
            
        Returns:
            List of transaction dictionaries
        """
        transactions = []
        date_range = (end_date - start_date).days
        
        for account in accounts:
            account_id = account["account_id"]
            account_type = account.get("type", "depository")
            
            # Persona-specific transaction characteristics
            num_txns = self._get_persona_transaction_count(persona, transactions_per_account)
            
            for i in range(num_txns):
                # Generate timestamp (randomly distributed)
                days_offset = random.uniform(0, date_range)
                hours_offset = random.uniform(0, 24)
                minutes_offset = random.uniform(0, 60)
                tx_date = start_date + timedelta(
                    days=days_offset,
                    hours=hours_offset,
                    minutes=minutes_offset
                )
                
                # Persona-specific transaction type and amount
                tx_type, amount = self._get_persona_transaction(persona, account_type, account)
                
                # Merchant category based on persona
                merchant_category = self._get_persona_merchant_category(persona)
                
                # Payment method based on account type
                payment_method = self._get_payment_method(account_type)
                
                # Generate merchant ID
                merchant_id = f"MERCH{random.randint(1, 200):06d}"
                
                # Transaction status
                status = "pending" if (end_date - tx_date).days <= 2 else "approved"
                
                # Amount category
                amount_category = self._get_amount_category(amount)
                
                transaction = {
                    "transaction_id": f"TXN{random.randint(10000000, 99999999)}",
                    "timestamp": tx_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "date": tx_date.strftime("%Y-%m-%d"),
                    "time": tx_date.strftime("%H:%M:%S"),
                    "customer_id": customer_id,
                    "merchant_id": merchant_id,
                    "merchant_category": merchant_category,
                    "transaction_type": tx_type,
                    "payment_method": payment_method,
                    "amount": abs(amount),  # Positive for transactions_final.csv
                    "amount_category": amount_category,
                    "status": status,
                    "account_id": account_id,
                    "account_balance": account.get("current", 0),  # Simplified
                    "hour": tx_date.hour,
                    "day_of_week": tx_date.strftime("%A"),
                    "month": tx_date.month,
                    "month_name": tx_date.strftime("%B"),
                    "quarter": (tx_date.month - 1) // 3 + 1,
                    "year": tx_date.year,
                }
                
                transactions.append(transaction)
        
        # Sort by timestamp
        transactions.sort(key=lambda x: x["timestamp"])
        return transactions
    
    def _get_persona_transaction_count(self, persona: str, base_count: int) -> int:
        """Get transaction count based on persona."""
        if persona == "high_utilization":
            # High utilization: more transactions (spending)
            return int(base_count * random.uniform(1.2, 1.5))
        elif persona == "subscription_heavy":
            # Subscription-heavy: moderate transactions + subscriptions
            return int(base_count * random.uniform(1.0, 1.3))
        elif persona == "variable_income_budgeter":
            # Variable income: fewer transactions (irregular income)
            return int(base_count * random.uniform(0.7, 1.0))
        elif persona == "savings_builder":
            # Savings builder: fewer transactions (saving money)
            return int(base_count * random.uniform(0.8, 1.0))
        else:  # balanced_stable
            return base_count
    
    def _get_persona_transaction(self, persona: str, account_type: str, account: Dict) -> tuple:
        """
        Get transaction type and amount based on persona.
        
        Returns:
            (transaction_type, amount) tuple
        """
        if account_type == "credit":
            # Credit card transactions
            if persona == "high_utilization":
                # High utilization: purchases, fees, minimum payments
                tx_type = random.choice(["purchase", "fee", "purchase"])
                amount = random.uniform(50, 500) if tx_type == "purchase" else random.uniform(5, 50)
            elif persona == "subscription_heavy":
                # Subscription-heavy: many recurring purchases
                tx_type = random.choice(["purchase", "purchase", "purchase", "refund"])
                amount = random.uniform(10, 150)
            else:
                # Other personas: moderate spending
                tx_type = random.choice(["purchase", "purchase", "refund"])
                amount = random.uniform(20, 200)
        else:
            # Depository account transactions
            if persona == "variable_income_budgeter":
                # Variable income: irregular deposits, careful spending
                tx_type = random.choice(["deposit", "purchase", "withdrawal"])
                if tx_type == "deposit":
                    amount = random.uniform(1000, 5000)  # Larger, irregular deposits
                else:
                    amount = random.uniform(20, 150)  # Smaller purchases
            elif persona == "savings_builder":
                # Savings builder: regular deposits, controlled spending
                tx_type = random.choice(["deposit", "transfer", "purchase"])
                if tx_type in ["deposit", "transfer"]:
                    amount = random.uniform(200, 1000)  # Regular savings deposits
                else:
                    amount = random.uniform(15, 100)  # Controlled spending
            elif persona == "subscription_heavy":
                # Subscription payments from checking
                tx_type = random.choice(["purchase", "transfer", "purchase"])
                amount = random.uniform(10, 150)
            else:
                # Balanced or high utilization
                tx_type = random.choice(["purchase", "deposit", "transfer", "withdrawal"])
                if tx_type == "deposit":
                    amount = random.uniform(500, 3000)
                else:
                    amount = random.uniform(20, 300)
        
        # Handle refunds (negative amounts become positive refunds)
        if tx_type == "refund":
            amount = abs(amount)
        
        return tx_type, amount
    
    def _get_persona_merchant_category(self, persona: str) -> str:
        """Get merchant category based on persona."""
        if persona == "subscription_heavy":
            # More online/entertainment subscriptions
            categories = ['online_shopping', 'entertainment', 'retail', 'utilities']
        elif persona == "high_utilization":
            # More varied spending
            categories = ['retail', 'restaurant', 'gas_station', 'online_shopping']
        elif persona == "savings_builder":
            # More essential spending
            categories = ['groceries', 'utilities', 'gas_station', 'healthcare']
        elif persona == "variable_income_budgeter":
            # Essential spending
            categories = ['groceries', 'utilities', 'gas_station', 'transportation']
        else:  # balanced_stable
            categories = self.merchant_categories
        
        return random.choice(categories)
    
    def _get_payment_method(self, account_type: str) -> str:
        """Get payment method based on account type."""
        if account_type == "credit":
            return "credit_card"
        elif account_type == "depository":
            methods = ["debit_card", "digital_wallet", "bank_transfer", "cash"]
            return random.choice(methods)
        else:
            return "bank_transfer"
    
    def _get_amount_category(self, amount: float) -> str:
        """Categorize amount."""
        abs_amount = abs(amount)
        if abs_amount < 10:
            return "small"
        elif abs_amount < 50:
            return "medium"
        elif abs_amount < 100:
            return "large"
        elif abs_amount < 500:
            return "very_large"
        else:
            return "extra_large"
    
    def generate_users_with_personas(self) -> List[Dict]:
        """Generate user assignments with persona distribution."""
        users = []
        persona_assignments = []
        
        for persona, count in self.persona_distribution:
            persona_assignments.extend([persona] * count)
        
        # Shuffle for randomness
        random.shuffle(persona_assignments)
        
        for i, persona in enumerate(persona_assignments):
            user_id = str(uuid.uuid4())
            customer_id = f"CUST{i+1:06d}"
            
            users.append({
                "id": user_id,
                "customer_id": customer_id,
                "persona": persona,
                "name": f"User {i+1}",
                "email": f"user{i+1}@example.com"
            })
        
        return users
    
    def adapt_to_spendsense_format(
        self,
        transactions_df: pd.DataFrame,
        users: List[Dict],
        accounts: List[Dict]
    ) -> pd.DataFrame:
        """
        Adapt synthetic-data transaction DataFrame to SpendSense format.
        
        This removes latitude, longitude, is_fraud and ensures proper format.
        """
        # Create account lookup
        account_lookup = {acc["account_id"]: acc for acc in accounts}
        user_lookup = {user["id"]: user for user in users}
        
        # Filter out unwanted columns if they exist
        columns_to_remove = ['latitude', 'longitude', 'is_fraud']
        for col in columns_to_remove:
            if col in transactions_df.columns:
                transactions_df = transactions_df.drop(columns=[col])
        
        # Ensure all required columns exist
        required_columns = [
            'transaction_id', 'timestamp', 'date', 'time',
            'customer_id', 'merchant_id', 'merchant_category',
            'transaction_type', 'payment_method', 'amount',
            'amount_category', 'status', 'account_balance',
            'account_id', 'hour', 'day_of_week', 'month',
            'month_name', 'quarter', 'year'
        ]
        
        # Add missing columns with defaults
        for col in required_columns:
            if col not in transactions_df.columns:
                if col == 'account_id':
                    transactions_df[col] = transactions_df.get('account_id', '')
                elif col in ['hour', 'month', 'quarter', 'year']:
                    transactions_df[col] = 0
                elif col in ['amount_category', 'status']:
                    transactions_df[col] = 'unknown'
                else:
                    transactions_df[col] = ''
        
        # Ensure proper data types
        if 'timestamp' in transactions_df.columns:
            transactions_df['timestamp'] = pd.to_datetime(transactions_df['timestamp'])
            transactions_df['date'] = transactions_df['timestamp'].dt.date.astype(str)
            transactions_df['time'] = transactions_df['timestamp'].dt.time.astype(str)
            transactions_df['hour'] = transactions_df['timestamp'].dt.hour
            transactions_df['day_of_week'] = transactions_df['timestamp'].dt.strftime('%A')
            transactions_df['month'] = transactions_df['timestamp'].dt.month
            transactions_df['month_name'] = transactions_df['timestamp'].dt.strftime('%B')
            transactions_df['quarter'] = ((transactions_df['timestamp'].dt.month - 1) // 3) + 1
            transactions_df['year'] = transactions_df['timestamp'].dt.year
        
        # Round amounts to 2 decimals
        if 'amount' in transactions_df.columns:
            transactions_df['amount'] = transactions_df['amount'].round(2)
        
        # Round account_balance to 2 decimals
        if 'account_balance' in transactions_df.columns:
            transactions_df['account_balance'] = transactions_df['account_balance'].round(2)
        
        # Select and order columns
        transactions_df = transactions_df[required_columns]
        
        # Sort by timestamp
        transactions_df = transactions_df.sort_values('timestamp').reset_index(drop=True)
        
        return transactions_df


if __name__ == "__main__":
    # Example usage
    integration = SyntheticDataIntegration(num_users=50)
    
    print("Synthetic Data Integration initialized")
    print(f"Synthetic-data library available: {SYNTHETIC_DATA_AVAILABLE}")
    
    users = integration.generate_users_with_personas()
    print(f"Generated {len(users)} users with personas")

