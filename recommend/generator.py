"""Recommendation generator that creates personalized recommendations with rationales."""

from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
import random

from features.pipeline import FeaturePipeline
from personas.assigner import PersonaAssigner
from personas.definitions import Persona, get_persona_by_id
from recommend.content_catalog import ContentCatalog, EducationContent
from recommend.offers_catalog import OffersCatalog, PartnerOffer
from recommend.rationales import RationaleBuilder
from guardrails.consent import ConsentManager
from guardrails.eligibility import EligibilityChecker
from guardrails.tone import ToneValidator
from guardrails.disclosure import DisclosureManager


class RecommendationGenerator:
    """Generates personalized recommendations for users."""
    
    def __init__(self, db_session: Session, db_path: str = "data/spendsense.db"):
        """Initialize recommendation generator.
        
        Args:
            db_session: Database session
            db_path: Path to SQLite database
        """
        self.db = db_session
        self.db_path = db_path
        self.feature_pipeline = FeaturePipeline(db_path)
        self.persona_assigner = PersonaAssigner(db_session, db_path)
        self.content_catalog = ContentCatalog()
        self.offers_catalog = OffersCatalog()
        self.rationale_builder = RationaleBuilder()
        self.consent_manager = ConsentManager(db_session)
        self.eligibility_checker = EligibilityChecker(db_session, db_path)
        self.tone_validator = ToneValidator()
        self.disclosure_manager = DisclosureManager()
    
    def generate_recommendations(
        self,
        user_id: str,
        window_days: int = 180,
        num_education: int = 5,
        num_offers: int = 3,
        credit_score: Optional[int] = None,
        annual_income: Optional[float] = None
    ) -> Dict[str, Any]:
        """Generate personalized recommendations for a user.
        
        Args:
            user_id: User ID
            window_days: Time window for feature computation (30 or 180)
            num_education: Number of education items to generate (default 5)
            num_offers: Number of partner offers to generate (default 3)
            credit_score: User's credit score (optional, for eligibility checks)
            annual_income: User's annual income (optional, for eligibility checks)
        
        Returns:
            Dictionary with recommendations including:
            - education_items: List of education recommendations
            - partner_offers: List of partner offer recommendations
            - persona: Assigned persona information
        
        Raises:
            PermissionError: If user has not consented to data processing
        """
        # Check consent first
        self.consent_manager.require_consent(user_id)
        
        # Get persona assignment with percentages
        persona_assignment = self.persona_assigner.assign_persona(user_id, window_days)
        primary_persona_id = persona_assignment['primary_persona']
        secondary_persona_id = persona_assignment.get('secondary_persona')
        primary_percentage = persona_assignment.get('primary_persona_percentage', 100)
        secondary_percentage = persona_assignment.get('secondary_persona_percentage', 0)
        
        primary_persona = get_persona_by_id(primary_persona_id)
        if not primary_persona:
            raise ValueError(f"Persona not found: {primary_persona_id}")
        
        secondary_persona = None
        if secondary_persona_id:
            secondary_persona = get_persona_by_id(secondary_persona_id)
        
        # Get user features
        features = self.feature_pipeline.compute_features_for_user(user_id, window_days)
        
        # Calculate number of recommendations per persona based on RISK-WEIGHTED scores
        # Higher risk personas get more recommendations to mitigate risk, even if they have lower percentage
        # Example: 60% Balanced (MINIMAL risk=1) + 40% Subscription-Heavy (MEDIUM risk=3)
        #   Risk-weighted: Balanced = 0.6, Subscription-Heavy = 1.2
        #   Subscription-Heavy gets more recommendations despite lower percentage
        if secondary_persona and secondary_percentage > 0:
            # Calculate risk-weighted scores: percentage * risk_value
            primary_risk_weight = (primary_percentage / 100) * primary_persona.risk.value
            secondary_risk_weight = (secondary_percentage / 100) * secondary_persona.risk.value
            total_risk_weight = primary_risk_weight + secondary_risk_weight
            
            if total_risk_weight > 0:
                # Distribute based on risk-weighted proportions
                # Higher risk persona gets more recommendations to mitigate risk
                primary_risk_ratio = primary_risk_weight / total_risk_weight
                secondary_risk_ratio = secondary_risk_weight / total_risk_weight
                
                primary_education_count = max(1, round(num_education * primary_risk_ratio))
                secondary_education_count = max(0, num_education - primary_education_count)
                
                primary_offers_count = max(1, round(num_offers * primary_risk_ratio))
                secondary_offers_count = max(0, num_offers - primary_offers_count)
            else:
                # Fallback to percentage-based if no risk weights
                primary_education_count = max(1, round(num_education * (primary_percentage / 100)))
                secondary_education_count = max(0, num_education - primary_education_count)
                
                primary_offers_count = max(1, round(num_offers * (primary_percentage / 100)))
                secondary_offers_count = max(0, num_offers - primary_offers_count)
        else:
            # Only primary persona or secondary is 0%, use all for primary
            primary_education_count = num_education
            secondary_education_count = 0
            
            primary_offers_count = num_offers
            secondary_offers_count = 0
        
        # Determine which persona has higher risk (for ordering)
        # Higher risk persona should come first in recommendations to prioritize risk mitigation
        if secondary_persona:
            primary_is_higher_risk = primary_persona.risk.value >= secondary_persona.risk.value
            higher_risk_persona = primary_persona if primary_is_higher_risk else secondary_persona
            lower_risk_persona = secondary_persona if primary_is_higher_risk else primary_persona
            
            # Assign counts based on risk-weighted calculation
            # Higher risk persona already gets more via risk-weighted calculation
            if primary_is_higher_risk:
                higher_risk_education_count = primary_education_count
                lower_risk_education_count = secondary_education_count
                higher_risk_offers_count = primary_offers_count
                lower_risk_offers_count = secondary_offers_count
            else:
                # Secondary has higher risk, so it gets more recommendations
                higher_risk_education_count = secondary_education_count
                lower_risk_education_count = primary_education_count
                higher_risk_offers_count = secondary_offers_count
                lower_risk_offers_count = primary_offers_count
        else:
            # Only one persona
            higher_risk_persona = primary_persona
            lower_risk_persona = None
            higher_risk_education_count = primary_education_count
            lower_risk_education_count = 0
            higher_risk_offers_count = primary_offers_count
            lower_risk_offers_count = 0
        
        # Generate education recommendations weighted by risk levels
        # Higher risk personas get more recommendations to mitigate risk
        # Higher risk recommendations appear first
        education_items = []
        
        # Generate from higher risk persona first (prioritize risk mitigation)
        if higher_risk_education_count > 0:
            higher_risk_education = self._generate_education_recommendations(
                higher_risk_persona,
                features,
                higher_risk_education_count
            )
            education_items.extend(higher_risk_education)
        
        # Generate from lower risk persona if it exists and we need more items
        if lower_risk_persona and lower_risk_education_count > 0:
            lower_risk_education = self._generate_education_recommendations(
                lower_risk_persona,
                features,
                lower_risk_education_count
            )
            education_items.extend(lower_risk_education)
        
        # Generate partner offers weighted by risk levels
        # Higher risk personas get more offers to mitigate risk
        # Higher risk offers appear first
        partner_offers = []
        
        # Generate from higher risk persona first (prioritize risk mitigation)
        if higher_risk_offers_count > 0:
            higher_risk_offers = self._generate_offer_recommendations(
                user_id,
                higher_risk_persona,
                features,
                higher_risk_offers_count,
                credit_score,
                annual_income
            )
            partner_offers.extend(higher_risk_offers)
        
        # Generate from lower risk persona if it exists and we need more offers
        if lower_risk_persona and lower_risk_offers_count > 0:
            lower_risk_offers = self._generate_offer_recommendations(
                user_id,
                lower_risk_persona,
                features,
                lower_risk_offers_count,
                credit_score,
                annual_income
            )
            partner_offers.extend(lower_risk_offers)
        
        return {
            'user_id': user_id,
            'persona': {
                'id': primary_persona.id,
                'name': primary_persona.name,
                'description': primary_persona.description,
                'risk_level': primary_persona.risk.name,
                'focus_area': primary_persona.focus_area,
                'primary_persona_percentage': primary_percentage,
                'secondary_persona': secondary_persona.name if secondary_persona else None,
                'secondary_persona_percentage': secondary_percentage
            },
            'education_items': education_items,
            'partner_offers': partner_offers,
            'total_recommendations': len(education_items) + len(partner_offers),
            'recommendation_distribution': {
                'primary_education_count': primary_education_count,
                'secondary_education_count': secondary_education_count,
                'primary_offers_count': primary_offers_count,
                'secondary_offers_count': secondary_offers_count
            }
        }
    
    def _generate_education_recommendations(
        self,
        persona: Persona,
        features: Dict[str, Any],
        num_items: int
    ) -> List[Dict[str, Any]]:
        """Generate education content recommendations.
        
        Args:
            persona: Assigned persona
            features: User features
            num_items: Number of items to recommend
        
        Returns:
            List of education recommendations with rationales
        """
        # Get content for this persona
        persona_content = self.content_catalog.get_content_for_persona(persona.id)
        
        # Also get content for specific signals
        signal_content = []
        if persona.id == 'high_utilization':
            if features.get('credit', {}).get('any_interest_charges'):
                signal_content.extend(self.content_catalog.get_content_for_signal('interest_charges'))
            if features.get('credit', {}).get('any_minimum_payment_only'):
                signal_content.extend(self.content_catalog.get_content_for_signal('minimum_payment_only'))
        elif persona.id == 'variable_income_budgeter':
            signal_content.extend(self.content_catalog.get_content_for_signal('variable_income'))
        elif persona.id == 'subscription_heavy':
            signal_content.extend(self.content_catalog.get_content_for_signal('subscription_heavy'))
        elif persona.id == 'savings_builder':
            signal_content.extend(self.content_catalog.get_content_for_signal('savings_growth'))
        
        # Combine and deduplicate
        all_content = list({item.id: item for item in persona_content + signal_content}.values())
        
        # Shuffle and select
        random.shuffle(all_content)
        selected_content = all_content[:num_items]
        
        # Build recommendations with rationales
        recommendations = []
        for content in selected_content:
            rationale = self.rationale_builder.build_content_rationale(
                content.title,
                features,
                persona
            )
            
            # Validate tone
            is_valid, tone_issues = self.tone_validator.check_rationale(rationale)
            if not is_valid:
                # Sanitize if tone issues found
                rationale = self.tone_validator.sanitize(rationale)
            
            rec = {
                'id': content.id,
                'title': content.title,
                'description': content.description,
                'type': content.content_type.value,
                'url': content.url,
                'difficulty': content.difficulty,
                'estimated_time': content.estimated_time,
                'rationale': rationale,
                'tags': content.tags,
                'target_personas': content.target_personas,  # Persona IDs this content targets
                'persona_names': []  # Will be populated with persona names
            }
            
            # Map persona IDs to persona names for display
            for persona_id in content.target_personas:
                target_persona = get_persona_by_id(persona_id)
                if target_persona:
                    rec['persona_names'].append(target_persona.name)
            
            # Add disclosure
            rec = self.disclosure_manager.add_disclosure_to_education(rec)
            
            recommendations.append(rec)
        
        return recommendations
    
    def _generate_offer_recommendations(
        self,
        user_id: str,
        persona: Persona,
        features: Dict[str, Any],
        num_offers: int,
        credit_score: Optional[int] = None,
        annual_income: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Generate partner offer recommendations.
        
        Args:
            persona: Assigned persona
            features: User features
            num_offers: Number of offers to recommend
            credit_score: User's credit score (optional)
            annual_income: User's annual income (optional)
        
        Returns:
            List of eligible partner offers with rationales
        """
        # Get offers for this persona
        persona_offers = self.offers_catalog.get_offers_for_persona(persona.id)
        
        # Check eligibility and filter using EligibilityChecker
        eligible_offers = []
        for offer in persona_offers:
            is_eligible, reasons = self.eligibility_checker.check_eligibility(
                offer,
                user_id,
                features,
                credit_score,
                annual_income
            )
            
            if is_eligible:
                rationale = self.rationale_builder.build_offer_rationale(
                    offer.title,
                    features,
                    persona
                )
                
                # Validate tone
                is_valid, tone_issues = self.tone_validator.check_rationale(rationale)
                if not is_valid:
                    # Sanitize if tone issues found
                    rationale = self.tone_validator.sanitize(rationale)
                
                rec = {
                    'id': offer.id,
                    'title': offer.title,
                    'description': offer.description,
                    'type': offer.offer_type.value,
                    'partner_name': offer.partner_name,
                    'url': offer.url,
                    'benefits': offer.benefits,
                    'terms': offer.terms,
                    'rationale': rationale,
                    'tags': offer.tags,
                    'target_personas': offer.target_personas,  # Persona IDs this offer targets
                    'persona_names': []  # Will be populated with persona names
                }
                
                # Map persona IDs to persona names for display
                for persona_id in offer.target_personas:
                    target_persona = get_persona_by_id(persona_id)
                    if target_persona:
                        rec['persona_names'].append(target_persona.name)
                
                # Add disclosure
                rec = self.disclosure_manager.add_disclosure_to_offer(rec)
                
                eligible_offers.append(rec)
        
        # Shuffle and select
        random.shuffle(eligible_offers)
        selected_offers = eligible_offers[:num_offers]
        
        return selected_offers
    
    def close(self):
        """Close database connections."""
        self.feature_pipeline.close()
        self.persona_assigner.close()
        self.eligibility_checker.close()

