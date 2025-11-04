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
        """
        # Get persona assignment
        persona_assignment = self.persona_assigner.assign_persona(user_id, window_days)
        primary_persona_id = persona_assignment['primary_persona']
        persona = get_persona_by_id(primary_persona_id)
        
        if not persona:
            raise ValueError(f"Persona not found: {primary_persona_id}")
        
        # Get user features
        features = self.feature_pipeline.compute_features_for_user(user_id, window_days)
        
        # Generate education recommendations
        education_items = self._generate_education_recommendations(
            persona,
            features,
            num_education
        )
        
        # Generate partner offers
        partner_offers = self._generate_offer_recommendations(
            persona,
            features,
            num_offers,
            credit_score,
            annual_income
        )
        
        return {
            'user_id': user_id,
            'persona': {
                'id': persona.id,
                'name': persona.name,
                'description': persona.description,
                'risk_level': persona.risk.name,
                'focus_area': persona.focus_area
            },
            'education_items': education_items,
            'partner_offers': partner_offers,
            'total_recommendations': len(education_items) + len(partner_offers)
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
            
            recommendations.append({
                'id': content.id,
                'title': content.title,
                'description': content.description,
                'type': content.content_type.value,
                'url': content.url,
                'difficulty': content.difficulty,
                'estimated_time': content.estimated_time,
                'rationale': rationale,
                'tags': content.tags
            })
        
        return recommendations
    
    def _generate_offer_recommendations(
        self,
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
        
        # Check eligibility and filter
        eligible_offers = []
        for offer in persona_offers:
            is_eligible, reasons = self.offers_catalog.check_eligibility(
                offer,
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
                
                eligible_offers.append({
                    'id': offer.id,
                    'title': offer.title,
                    'description': offer.description,
                    'type': offer.offer_type.value,
                    'partner_name': offer.partner_name,
                    'url': offer.url,
                    'benefits': offer.benefits,
                    'terms': offer.terms,
                    'rationale': rationale,
                    'tags': offer.tags
                })
        
        # Shuffle and select
        random.shuffle(eligible_offers)
        selected_offers = eligible_offers[:num_offers]
        
        return selected_offers
    
    def close(self):
        """Close database connections."""
        self.feature_pipeline.close()
        self.persona_assigner.close()

