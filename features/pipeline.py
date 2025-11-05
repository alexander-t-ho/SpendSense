"""Feature pipeline orchestrator."""

from datetime import datetime, timedelta
from typing import Dict, List, Any
import polars as pl
from pathlib import Path

from ingest.schema import get_session, User
from features.subscriptions import SubscriptionDetector
from features.savings import SavingsAnalyzer
from features.credit import CreditAnalyzer
from features.income import IncomeAnalyzer
from features.fees import FeeAnalyzer
from features.correlation import CorrelationAnalyzer


class FeaturePipeline:
    """Orchestrates feature computation and storage."""
    
    def __init__(self, db_path: str = "data/spendsense.db"):
        """Initialize pipeline.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.session = get_session(db_path)
        
        # Initialize detectors
        self.subscription_detector = SubscriptionDetector(self.session)
        self.savings_analyzer = SavingsAnalyzer(self.session)
        self.credit_analyzer = CreditAnalyzer(self.session)
        self.income_analyzer = IncomeAnalyzer(self.session)
        self.fee_analyzer = FeeAnalyzer(self.session)
        self.correlation_analyzer = CorrelationAnalyzer(self.session)
    
    def compute_features_for_user(
        self,
        user_id: str,
        window_days: int = 30
    ) -> Dict[str, Any]:
        """Compute all features for a user.
        
        Args:
            user_id: User ID
            window_days: Time window in days (30 or 180)
        
        Returns:
            Dictionary with all computed features
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=window_days)
        
        # Compute income features first (needed for subscription calculations)
        income_features = self.income_analyzer.calculate_income_metrics(
            user_id, start_date, end_date
        )
        
        # Calculate monthly income for subscription-to-income ratio
        # Use average income per pay * frequency multiplier, or minimum monthly income
        monthly_income = income_features.get('minimum_monthly_income', 0.0)
        if monthly_income == 0.0:
            # Fallback: use average income per pay * frequency
            avg_income_per_pay = income_features.get('average_income_per_pay', 0.0)
            frequency = income_features.get('payment_frequency', {}).get('frequency', 'monthly')
            if frequency == 'weekly':
                monthly_income = avg_income_per_pay * 4.33
            elif frequency == 'biweekly':
                monthly_income = avg_income_per_pay * 2.17
            elif frequency == 'monthly':
                monthly_income = avg_income_per_pay
            else:
                # For irregular, estimate from median days
                median_days = income_features.get('payment_frequency', {}).get('median_days_between', 30.0)
                if median_days > 0:
                    monthly_income = avg_income_per_pay * (30.0 / median_days)
        
        # Compute subscription features with monthly income
        subscription_features = self.subscription_detector.calculate_subscription_metrics(
            user_id, start_date, end_date, monthly_income=monthly_income
        )
        
        savings_features = self.savings_analyzer.calculate_savings_metrics(
            user_id, start_date, end_date
        )
        
        credit_features = self.credit_analyzer.calculate_credit_metrics(
            user_id, start_date, end_date
        )
        
        fee_features = self.fee_analyzer.get_fee_metrics(
            user_id, start_date, end_date
        )
        
        return {
            "user_id": user_id,
            "window_days": window_days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "subscriptions": subscription_features,
            "savings": savings_features,
            "credit": credit_features,
            "income": income_features,
            "fees": fee_features
        }
    
    def compute_features_for_all_users(
        self,
        window_days: int = 30,
        output_dir: str = "data/features"
    ) -> List[Dict[str, Any]]:
        """Compute features for all users.
        
        Args:
            window_days: Time window in days (30 or 180)
            output_dir: Directory to save Parquet files
        
        Returns:
            List of feature dictionaries for all users
        """
        # Get all users
        users = self.session.query(User).all()
        
        all_features = []
        
        for user in users:
            try:
                features = self.compute_features_for_user(user.id, window_days)
                all_features.append(features)
            except Exception as e:
                print(f"Error computing features for user {user.id}: {e}")
                continue
        
        # Save to Parquet
        self.save_to_parquet(all_features, window_days, output_dir)
        
        return all_features
    
    def save_to_parquet(
        self,
        features: List[Dict[str, Any]],
        window_days: int,
        output_dir: str
    ):
        """Save features to Parquet file.
        
        Args:
            features: List of feature dictionaries
            window_days: Time window (for filename)
            output_dir: Output directory
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Flatten nested structures for Parquet storage
        flattened_features = []
        
        for feature_set in features:
            flattened = {
                "user_id": feature_set["user_id"],
                "window_days": feature_set["window_days"],
                "start_date": feature_set["start_date"],
                "end_date": feature_set["end_date"],
                
                # Subscriptions
                "recurring_merchants": feature_set["subscriptions"]["recurring_merchants"],
                "monthly_recurring_spend": feature_set["subscriptions"]["monthly_recurring_spend"],
                "subscription_share_of_total": feature_set["subscriptions"]["subscription_share_of_total"],
                "total_subscription_spend": feature_set["subscriptions"]["total_subscription_spend"],
                
                # Savings
                "savings_net_inflow": feature_set["savings"]["net_inflow"],
                "savings_monthly_net_inflow": feature_set["savings"]["monthly_net_inflow"],
                "savings_growth_rate": feature_set["savings"]["growth_rate_percent"],
                "emergency_fund_coverage_months": feature_set["savings"]["emergency_fund_coverage_months"],
                "total_savings_balance": feature_set["savings"]["total_savings_balance"],
                "has_emergency_fund": feature_set["savings"]["has_emergency_fund"],
                
                # Credit
                "has_credit_cards": feature_set["credit"]["has_credit_cards"],
                "any_high_utilization_50": feature_set["credit"]["any_high_utilization_50"],
                "any_high_utilization_80": feature_set["credit"]["any_high_utilization_80"],
                "any_interest_charges": feature_set["credit"]["any_interest_charges"],
                "any_minimum_payment_only": feature_set["credit"]["any_minimum_payment_only"],
                "any_overdue": feature_set["credit"]["any_overdue"],
                
                # Income
                "has_payroll_detected": feature_set["income"]["has_payroll_detected"],
                "median_pay_gap_days": feature_set["income"]["median_pay_gap_days"],
                "cash_flow_buffer_months": feature_set["income"]["cash_flow_buffer_months"],
                "is_variable_income": feature_set["income"]["is_variable_income"],
                "payment_frequency": feature_set["income"]["payment_frequency"]["frequency"],
                "is_regular_income": feature_set["income"]["payment_frequency"]["is_regular"],
            }
            flattened_features.append(flattened)
        
        # Create Polars DataFrame and save
        df = pl.DataFrame(flattened_features)
        output_path = Path(output_dir) / f"features_{window_days}d.parquet"
        df.write_parquet(output_path)
        
        print(f"Saved {len(flattened_features)} feature records to {output_path}")
    
    def compute_all_windows(
        self,
        output_dir: str = "data/features"
    ):
        """Compute features for both 30-day and 180-day windows.
        
        Args:
            output_dir: Output directory
        """
        print("Computing 30-day features...")
        self.compute_features_for_all_users(30, output_dir)
        
        print("\nComputing 180-day features...")
        self.compute_features_for_all_users(180, output_dir)
        
        print("\nFeature computation complete!")
    
    def close(self):
        """Close database session."""
        self.session.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Compute behavioral features")
    parser.add_argument("--window-days", type=int, choices=[30, 180], help="Time window in days")
    parser.add_argument("--user-id", type=str, help="Compute for specific user only")
    parser.add_argument("--output-dir", type=str, default="data/features", help="Output directory")
    parser.add_argument("--db-path", type=str, default="data/spendsense.db", help="Database path")
    
    args = parser.parse_args()
    
    pipeline = FeaturePipeline(db_path=args.db_path)
    
    if args.user_id:
        # Compute for single user
        features = pipeline.compute_features_for_user(args.user_id, args.window_days or 30)
        print(f"Features for user {args.user_id}:")
        import json
        print(json.dumps(features, indent=2, default=str))
    elif args.window_days:
        # Compute for all users, specific window
        pipeline.compute_features_for_all_users(args.window_days, args.output_dir)
    else:
        # Compute for all users, both windows
        pipeline.compute_all_windows(args.output_dir)
    
    pipeline.close()

