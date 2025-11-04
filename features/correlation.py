"""Correlation analysis module for behavioral features."""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ingest.schema import User, Account, Transaction, Liability


class CorrelationAnalyzer:
    """Analyze correlations among all financial variables."""
    
    def __init__(self, db_session: Session):
        """Initialize analyzer.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
    
    def extract_all_variables(self, user_id: Optional[str] = None) -> pd.DataFrame:
        """Extract all available variables for correlation analysis.
        
        Args:
            user_id: Optional user ID to filter (if None, all users)
        
        Returns:
            DataFrame with all variables
        """
        variables = []
        
        # Get users (all or specific)
        if user_id:
            users = self.db.query(User).filter(User.id == user_id).all()
        else:
            users = self.db.query(User).all()
        
        for user in users:
            user_vars = self._extract_user_variables(user.id)
            if user_vars:
                variables.append(user_vars)
        
        if not variables:
            return pd.DataFrame()
        
        return pd.DataFrame(variables)
    
    def _extract_user_variables(self, user_id: str) -> Dict[str, Any]:
        """Extract all variables for a single user.
        
        Args:
            user_id: User ID
        
        Returns:
            Dictionary with all variables
        """
        end_date = datetime.now()
        start_date_30d = end_date - timedelta(days=30)
        start_date_180d = end_date - timedelta(days=180)
        
        var_dict = {"user_id": user_id}
        
        # Get all accounts
        accounts = self.db.query(Account).filter(Account.user_id == user_id).all()
        
        # Account-level variables
        checking_accounts = [a for a in accounts if a.subtype == "checking"]
        savings_accounts = [a for a in accounts if a.subtype in ["savings", "money_market", "hsa"]]
        credit_accounts = [a for a in accounts if a.type == "credit"]
        loan_accounts = [a for a in accounts if a.type == "loan"]
        
        # Checking account balances
        if checking_accounts:
            var_dict["checking_balance"] = sum(a.current or 0 for a in checking_accounts)
            var_dict["checking_available"] = sum(a.available or 0 for a in checking_accounts)
            var_dict["num_checking_accounts"] = len(checking_accounts)
        else:
            var_dict["checking_balance"] = 0
            var_dict["checking_available"] = 0
            var_dict["num_checking_accounts"] = 0
        
        # Savings account balances
        if savings_accounts:
            var_dict["savings_balance"] = sum(a.current or 0 for a in savings_accounts)
            var_dict["savings_available"] = sum(a.available or 0 for a in savings_accounts)
            var_dict["num_savings_accounts"] = len(savings_accounts)
        else:
            var_dict["savings_balance"] = 0
            var_dict["savings_available"] = 0
            var_dict["num_savings_accounts"] = 0
        
        # Credit card variables
        if credit_accounts:
            total_credit_limit = sum(a.limit or 0 for a in credit_accounts)
            total_credit_balance = sum(abs(a.current or 0) for a in credit_accounts)
            total_available_credit = sum(a.available or 0 for a in credit_accounts)
            
            var_dict["total_credit_limit"] = total_credit_limit
            var_dict["total_credit_balance"] = total_credit_balance
            var_dict["total_available_credit"] = total_available_credit
            var_dict["overall_utilization"] = (total_credit_balance / total_credit_limit * 100) if total_credit_limit > 0 else 0
            var_dict["num_credit_cards"] = len(credit_accounts)
            
            # Credit card liability variables
            credit_liabilities = []
            for account in credit_accounts:
                liability = self.db.query(Liability).filter(
                    and_(
                        Liability.account_id == account.id,
                        Liability.liability_type == "credit_card"
                    )
                ).first()
                
                if liability:
                    credit_liabilities.append({
                        "apr_percentage": liability.apr_percentage,
                        "minimum_payment": liability.minimum_payment_amount,
                        "last_payment": liability.last_payment_amount,
                        "is_overdue": 1 if liability.is_overdue else 0,
                        "statement_balance": liability.last_statement_balance
                    })
            
            if credit_liabilities:
                var_dict["avg_apr"] = np.mean([l["apr_percentage"] for l in credit_liabilities if l["apr_percentage"]])
                var_dict["avg_minimum_payment"] = np.mean([l["minimum_payment"] for l in credit_liabilities if l["minimum_payment"]])
                var_dict["avg_last_payment"] = np.mean([l["last_payment"] for l in credit_liabilities if l["last_payment"]])
                var_dict["has_overdue"] = 1 if any(l["is_overdue"] for l in credit_liabilities) else 0
                var_dict["total_statement_balance"] = sum(l["statement_balance"] for l in credit_liabilities if l["statement_balance"])
            else:
                var_dict["avg_apr"] = 0
                var_dict["avg_minimum_payment"] = 0
                var_dict["avg_last_payment"] = 0
                var_dict["has_overdue"] = 0
                var_dict["total_statement_balance"] = 0
        else:
            var_dict["total_credit_limit"] = 0
            var_dict["total_credit_balance"] = 0
            var_dict["total_available_credit"] = 0
            var_dict["overall_utilization"] = 0
            var_dict["num_credit_cards"] = 0
            var_dict["avg_apr"] = 0
            var_dict["avg_minimum_payment"] = 0
            var_dict["avg_last_payment"] = 0
            var_dict["has_overdue"] = 0
            var_dict["total_statement_balance"] = 0
        
        # Loan variables
        if loan_accounts:
            var_dict["num_loans"] = len(loan_accounts)
            var_dict["total_loan_balance"] = sum(abs(a.current or 0) for a in loan_accounts)
            var_dict["avg_loan_interest_rate"] = np.mean([a.interest_rate for a in loan_accounts if a.interest_rate])
        else:
            var_dict["num_loans"] = 0
            var_dict["total_loan_balance"] = 0
            var_dict["avg_loan_interest_rate"] = 0
        
        # Transaction variables (30-day window)
        transactions_30d = self.db.query(Transaction).join(Account).filter(
            and_(
                Account.user_id == user_id,
                Transaction.date >= start_date_30d,
                Transaction.date <= end_date
            )
        ).all()
        
        if transactions_30d:
            expenses_30d = [t.amount for t in transactions_30d if t.amount < 0]
            income_30d = [t.amount for t in transactions_30d if t.amount > 0]
            
            var_dict["total_expenses_30d"] = abs(sum(expenses_30d)) if expenses_30d else 0
            var_dict["total_income_30d"] = sum(income_30d) if income_30d else 0
            var_dict["net_flow_30d"] = var_dict["total_income_30d"] - var_dict["total_expenses_30d"]
            var_dict["num_transactions_30d"] = len(transactions_30d)
            var_dict["avg_transaction_amount_30d"] = np.mean([abs(t.amount) for t in transactions_30d]) if transactions_30d else 0
            var_dict["num_pending_30d"] = sum(1 for t in transactions_30d if t.pending)
        else:
            var_dict["total_expenses_30d"] = 0
            var_dict["total_income_30d"] = 0
            var_dict["net_flow_30d"] = 0
            var_dict["num_transactions_30d"] = 0
            var_dict["avg_transaction_amount_30d"] = 0
            var_dict["num_pending_30d"] = 0
        
        # Transaction variables (180-day window)
        transactions_180d = self.db.query(Transaction).join(Account).filter(
            and_(
                Account.user_id == user_id,
                Transaction.date >= start_date_180d,
                Transaction.date <= end_date
            )
        ).all()
        
        if transactions_180d:
            expenses_180d = [t.amount for t in transactions_180d if t.amount < 0]
            income_180d = [t.amount for t in transactions_180d if t.amount > 0]
            
            var_dict["total_expenses_180d"] = abs(sum(expenses_180d)) if expenses_180d else 0
            var_dict["total_income_180d"] = sum(income_180d) if income_180d else 0
            var_dict["net_flow_180d"] = var_dict["total_income_180d"] - var_dict["total_expenses_180d"]
            var_dict["num_transactions_180d"] = len(transactions_180d)
            var_dict["avg_transaction_amount_180d"] = np.mean([abs(t.amount) for t in transactions_180d]) if transactions_180d else 0
            var_dict["monthly_avg_expenses"] = var_dict["total_expenses_180d"] / 6  # 6 months
            var_dict["monthly_avg_income"] = var_dict["total_income_180d"] / 6
        else:
            var_dict["total_expenses_180d"] = 0
            var_dict["total_income_180d"] = 0
            var_dict["net_flow_180d"] = 0
            var_dict["num_transactions_180d"] = 0
            var_dict["avg_transaction_amount_180d"] = 0
            var_dict["monthly_avg_expenses"] = 0
            var_dict["monthly_avg_income"] = 0
        
        # Subscription-related variables (from merchant names)
        subscription_keywords = ["netflix", "spotify", "disney", "hbo", "amazon prime", "microsoft", "adobe", "gym"]
        subscription_txns = [
            t for t in transactions_180d 
            if t.merchant_name and any(kw in t.merchant_name.lower() for kw in subscription_keywords)
        ]
        var_dict["subscription_spend_180d"] = abs(sum(t.amount for t in subscription_txns if t.amount < 0))
        var_dict["num_subscription_merchants"] = len(set(t.merchant_name for t in subscription_txns if t.merchant_name))
        
        # Interest charges
        interest_txns = [t for t in transactions_180d if "INTEREST" in (t.merchant_name or "").upper()]
        var_dict["total_interest_charges_180d"] = abs(sum(t.amount for t in interest_txns if t.amount < 0))
        
        # Payment patterns
        payment_txns = [t for t in transactions_180d if "PAYMENT" in (t.merchant_name or "").upper()]
        var_dict["total_payments_180d"] = sum(t.amount for t in payment_txns if t.amount > 0)
        var_dict["num_payments_180d"] = len(payment_txns)
        
        return var_dict
    
    def compute_correlation_matrix(
        self, 
        user_id: Optional[str] = None,
        method: str = "pearson",
        min_correlation: float = 0.3
    ) -> Dict[str, Any]:
        """Compute correlation matrix for all variables.
        
        Args:
            user_id: Optional user ID to filter (if None, all users)
            method: Correlation method ('pearson', 'spearman', 'kendall')
            min_correlation: Minimum correlation to include in results
        
        Returns:
            Dictionary with correlation matrix and insights
        """
        # Extract all variables
        df = self.extract_all_variables(user_id)
        
        if df.empty or len(df) < 2:
            return {
                "error": "Insufficient data for correlation analysis",
                "num_users": len(df) if not df.empty else 0
            }
        
        # Select only numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Remove user_id if present
        if "user_id" in numeric_cols:
            numeric_cols.remove("user_id")
        
        if not numeric_cols:
            return {"error": "No numeric variables found"}
        
        # Compute correlation matrix
        corr_matrix = df[numeric_cols].corr(method=method)
        
        # Find strong correlations
        strong_correlations = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) >= min_correlation and not np.isnan(corr_value):
                    strong_correlations.append({
                        "variable1": corr_matrix.columns[i],
                        "variable2": corr_matrix.columns[j],
                        "correlation": float(corr_value),
                        "strength": self._classify_correlation(abs(corr_value))
                    })
        
        # Sort by absolute correlation
        strong_correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        
        return {
            "method": method,
            "num_users": len(df),
            "num_variables": len(numeric_cols),
            "variables": numeric_cols,
            "correlation_matrix": corr_matrix.to_dict(),
            "strong_correlations": strong_correlations,
            "summary": {
                "total_correlations": len(strong_correlations),
                "positive_correlations": len([c for c in strong_correlations if c["correlation"] > 0]),
                "negative_correlations": len([c for c in strong_correlations if c["correlation"] < 0]),
                "strongest_positive": strong_correlations[0] if strong_correlations and strong_correlations[0]["correlation"] > 0 else None,
                "strongest_negative": strong_correlations[0] if strong_correlations and strong_correlations[0]["correlation"] < 0 else None,
            }
        }
    
    def _classify_correlation(self, abs_corr: float) -> str:
        """Classify correlation strength.
        
        Args:
            abs_corr: Absolute correlation value
        
        Returns:
            Strength classification
        """
        if abs_corr >= 0.7:
            return "very_strong"
        elif abs_corr >= 0.5:
            return "strong"
        elif abs_corr >= 0.3:
            return "moderate"
        else:
            return "weak"
    
    def analyze_feature_relationships(
        self,
        variable_groups: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """Analyze relationships between specific variable groups.
        
        Args:
            variable_groups: Dictionary mapping group names to variable lists
        
        Returns:
            Analysis results for each group
        """
        if variable_groups is None:
            # Default groups
            variable_groups = {
                "credit": [
                    "overall_utilization", "avg_apr", "total_credit_balance",
                    "has_overdue", "total_interest_charges_180d"
                ],
                "savings": [
                    "savings_balance", "savings_available", "net_flow_30d",
                    "net_flow_180d", "monthly_avg_expenses"
                ],
                "spending": [
                    "total_expenses_30d", "total_expenses_180d",
                    "monthly_avg_expenses", "avg_transaction_amount_30d",
                    "num_transactions_30d"
                ],
                "income": [
                    "total_income_30d", "total_income_180d",
                    "monthly_avg_income", "checking_balance"
                ]
            }
        
        df = self.extract_all_variables()
        
        if df.empty:
            return {"error": "No data available"}
        
        results = {}
        
        for group_name, variables in variable_groups.items():
            # Filter to variables that exist in DataFrame
            available_vars = [v for v in variables if v in df.columns]
            
            if len(available_vars) < 2:
                results[group_name] = {
                    "error": f"Insufficient variables available: {available_vars}"
                }
                continue
            
            # Compute correlation within group
            group_corr = df[available_vars].corr()
            
            results[group_name] = {
                "variables": available_vars,
                "correlation_matrix": group_corr.to_dict(),
                "insights": self._extract_group_insights(group_name, group_corr, available_vars)
            }
        
        return results
    
    def _extract_group_insights(
        self,
        group_name: str,
        corr_matrix: pd.DataFrame,
        variables: List[str]
    ) -> List[str]:
        """Extract insights from correlation matrix.
        
        Args:
            group_name: Name of variable group
            corr_matrix: Correlation matrix
            variables: List of variables
        
        Returns:
            List of insight strings
        """
        insights = []
        
        for i in range(len(variables)):
            for j in range(i + 1, len(variables)):
                corr = corr_matrix.iloc[i, j]
                if not np.isnan(corr) and abs(corr) > 0.3:
                    direction = "positively" if corr > 0 else "negatively"
                    strength = self._classify_correlation(abs(corr))
                    insights.append(
                        f"{variables[i]} and {variables[j]} are {strength}ly {direction} correlated (r={corr:.3f})"
                    )
        
        return insights

