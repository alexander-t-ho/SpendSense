"""Eligibility checking for partner offers."""

from typing import Dict, Any, Tuple, Optional, List
from sqlalchemy.orm import Session

from ingest.schema import Account
from recommend.offers_catalog import PartnerOffer, EligibilityCriteria
from features.pipeline import FeaturePipeline


class EligibilityChecker:
    """Check eligibility for partner offers based on user data."""
    
    def __init__(self, db_session: Session, db_path: str = "data/spendsense.db"):
        """Initialize eligibility checker.
        
        Args:
            db_session: Database session
            db_path: Path to SQLite database
        """
        self.db = db_session
        self.db_path = db_path
        self.feature_pipeline = FeaturePipeline(db_path)
    
    def check_eligibility(
        self,
        offer: PartnerOffer,
        user_id: str,
        user_features: Optional[Dict[str, Any]] = None,
        credit_score: Optional[int] = None,
        annual_income: Optional[float] = None
    ) -> Tuple[bool, List[str]]:
        """Check if a user is eligible for a partner offer.
        
        Args:
            offer: Partner offer to check
            user_id: User ID
            user_features: Pre-computed user features (optional)
            credit_score: User's credit score (optional)
            annual_income: User's annual income (optional)
        
        Returns:
            Tuple of (is_eligible, reasons) where reasons is a list of strings
            explaining why the offer is eligible or not
        """
        criteria = offer.eligibility
        reasons = []
        
        # Get user features if not provided
        if user_features is None:
            user_features = self.feature_pipeline.compute_features_for_user(user_id, 180)
        
        # Get user accounts
        user_accounts = self.db.query(Account).filter(Account.user_id == user_id).all()
        account_types = [acc.type for acc in user_accounts]
        account_subtypes = [acc.subtype for acc in user_accounts if acc.subtype]
        
        # Check harmful products
        if criteria.is_harmful:
            reasons.append("This product is marked as harmful and will not be recommended")
            return (False, reasons)
        
        # Check credit score requirements
        if credit_score is not None:
            if criteria.min_credit_score is not None and credit_score < criteria.min_credit_score:
                reasons.append(
                    f"Credit score ({credit_score}) below minimum requirement ({criteria.min_credit_score})"
                )
                return (False, reasons)
            
            if criteria.max_credit_score is not None and credit_score > criteria.max_credit_score:
                reasons.append(
                    f"Credit score ({credit_score}) above maximum requirement ({criteria.max_credit_score})"
                )
                return (False, reasons)
        
        # Check income requirements
        if annual_income is not None:
            if criteria.min_income is not None and annual_income < criteria.min_income:
                reasons.append(
                    f"Income (${annual_income:,.0f}) below minimum requirement (${criteria.min_income:,.0f})"
                )
                return (False, reasons)
        
        # Check credit utilization
        credit_features = user_features.get('credit', {})
        if criteria.max_utilization is not None:
            card_details = credit_features.get('card_details', [])
            if card_details:
                max_util = 0
                for card in card_details:
                    util = card.get('utilization', {})
                    util_percent = util.get('utilization_percent', 0)
                    max_util = max(max_util, util_percent)
                
                if max_util > criteria.max_utilization:
                    reasons.append(
                        f"Credit utilization ({max_util:.1f}%) exceeds maximum ({criteria.max_utilization:.1f}%)"
                    )
                    return (False, reasons)
        
        # Check existing account types to exclude
        if criteria.exclude_account_types:
            for exclude_type in criteria.exclude_account_types:
                if exclude_type in account_types or exclude_type in account_subtypes:
                    reasons.append(
                        f"User already has {exclude_type} account (excluded from this offer)"
                    )
                    return (False, reasons)
        
        # Check if existing account is required
        if criteria.requires_existing_account:
            # Check if user has the required account type based on offer type
            offer_type_to_account = {
                'credit_card': 'credit',
                'savings_account': 'depository',
                'loan': 'loan'
            }
            required_type = offer_type_to_account.get(offer.offer_type.value)
            if required_type and required_type not in account_types:
                reasons.append(
                    f"Offer requires existing {required_type} account, but user does not have one"
                )
                return (False, reasons)
        
        # Check savings balance requirements
        if criteria.min_savings_balance is not None:
            savings_features = user_features.get('savings', {})
            total_savings = savings_features.get('total_savings_balance', 0)
            if total_savings < criteria.min_savings_balance:
                reasons.append(
                    f"Savings balance (${total_savings:,.0f}) below minimum requirement "
                    f"(${criteria.min_savings_balance:,.0f})"
                )
                return (False, reasons)
        
        # All checks passed
        reasons.append("User meets all eligibility requirements")
        return (True, reasons)
    
    def close(self):
        """Close database connections."""
        self.feature_pipeline.close()


