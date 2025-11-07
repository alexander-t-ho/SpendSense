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
from recommend.actionable_recommendations import ACTIONABLE_RECOMMENDATIONS, ActionableRecommendation
from recommend.data_extractor import RecommendationDataExtractor
from recommend.chatgpt_personalizer import ChatGPTPersonalizer
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
        self.data_extractor = RecommendationDataExtractor(db_session, db_path)
        self.chatgpt_personalizer = ChatGPTPersonalizer()  # Optional: requires OPENAI_API_KEY
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
                higher_risk_education_count,
                user_id
            )
            education_items.extend(higher_risk_education)
        
        # Generate from lower risk persona if it exists and we need more items
        if lower_risk_persona and lower_risk_education_count > 0:
            lower_risk_education = self._generate_education_recommendations(
                lower_risk_persona,
                features,
                lower_risk_education_count,
                user_id
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
        num_items: int,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations with specific data points.
        
        Args:
            persona: Assigned persona
            features: User features
            num_items: Number of items to recommend
            user_id: User ID (required for data extraction)
        
        Returns:
            List of actionable recommendations with personalized text
        """
        # Get actionable recommendations for this persona
        persona_recommendations = [
            rec for rec in ACTIONABLE_RECOMMENDATIONS
            if rec.persona_id == persona.id
        ]
        
        # Sort by priority (HIGH first)
        priority_order = {
            'high': 0,
            'medium': 1,
            'low': 2
        }
        persona_recommendations.sort(key=lambda x: priority_order.get(x.priority.value, 3))
        
        # Extract user data for personalization
        data_points = {}
        if user_id:
            try:
                # Extract credit card data
                if persona.id == 'high_utilization':
                    credit_cards = self.data_extractor.extract_credit_card_data(user_id)
                    if credit_cards:
                        # Use the card with highest utilization
                        highest_util_card = max(credit_cards, key=lambda c: c.get('utilization_percent', 0))
                        data_points.update(highest_util_card)
                
                # Extract subscription data
                if persona.id == 'subscription_heavy':
                    sub_data = self.data_extractor.extract_subscription_data(user_id)
                    data_points.update(sub_data)
                
                # Extract income data
                if persona.id == 'variable_income_budgeter':
                    income_data = self.data_extractor.extract_income_data(user_id)
                    data_points.update(income_data)
                
                # Extract savings data
                if persona.id == 'savings_builder':
                    savings_data = self.data_extractor.extract_savings_data(user_id)
                    data_points.update(savings_data)
                
                # Extract balanced/stable data
                if persona.id == 'balanced_stable':
                    credit_features = features.get('credit', {})
                    savings_features = features.get('savings', {})
                    utilization = credit_features.get('max_utilization_percent', 0)
                    monthly_savings = savings_features.get('monthly_net_inflow', 0)
                    data_points.update({
                        'utilization_below_30': utilization if utilization < 30 else 30,
                        'monthly_savings': monthly_savings
                    })
                    
            except Exception as e:
                print(f"Warning: Error extracting data for recommendations: {e}")
        
        # Filter recommendations based on available data points
        applicable_recommendations = []
        for rec_template in persona_recommendations:
            # Check if we have the required data points
            required_data = set(rec_template.data_points_needed)
            available_data = set(data_points.keys())
            
            # If we have at least 50% of required data points, include it
            if len(required_data.intersection(available_data)) >= len(required_data) * 0.5:
                applicable_recommendations.append(rec_template)
        
        # Select top recommendations
        selected_recommendations = applicable_recommendations[:num_items]
        
        # If we don't have enough, fill with remaining (even if data is incomplete)
        if len(selected_recommendations) < num_items:
            remaining = [r for r in persona_recommendations if r not in selected_recommendations]
            selected_recommendations.extend(remaining[:num_items - len(selected_recommendations)])
        
        # Build personalized recommendations
        recommendations = []
        for rec_template in selected_recommendations:
            # Prepare data points for template
            template_data = {}
            for key in rec_template.data_points_needed:
                if key in data_points:
                    template_data[key] = data_points[key]
                else:
                    # Use placeholder if data not available
                    template_data[key] = self._get_default_value(key)
            
            # Generate personalized text
            try:
                # Try ChatGPT personalization first (if enabled)
                personalized_text = self.chatgpt_personalizer.personalize_recommendation(
                    rec_template.template,
                    template_data,
                    user_context={'persona': persona.name, 'user_features': features}
                )
            except Exception as e:
                # Fallback to template formatting
                print(f"Warning: ChatGPT personalization failed, using template: {e}")
                personalized_text = rec_template.template.format(**template_data)
            
            # Format action items with data
            action_items = []
            for action_template in rec_template.action_items:
                try:
                    formatted_action = action_template.format(**template_data)
                    action_items.append(formatted_action)
                except KeyError:
                    # If data point missing, use template as-is
                    action_items.append(action_template)
            
            # Enhance action items with ChatGPT if enabled
            if self.chatgpt_personalizer.enabled:
                try:
                    action_items = self.chatgpt_personalizer.enhance_action_items(
                        action_items,
                        user_context={'persona': persona.name, 'data_points': template_data}
                    )
                except Exception:
                    pass  # Keep original action items if enhancement fails
            
            # Format expected impact
            try:
                expected_impact = rec_template.expected_impact.format(**template_data)
            except KeyError:
                expected_impact = rec_template.expected_impact
            
            # Validate tone
            is_valid, tone_issues = self.tone_validator.check_rationale(personalized_text)
            if not is_valid:
                personalized_text = self.tone_validator.sanitize(personalized_text)
            
            rec = {
                'id': rec_template.id,
                'title': rec_template.title,
                'recommendation_text': personalized_text,  # The personalized recommendation text
                'type': 'actionable_recommendation',
                'action_items': action_items,
                'expected_impact': expected_impact,
                'priority': rec_template.priority.value,
                'target_personas': [persona.id],
                'persona_names': [persona.name],
                'tags': rec_template.target_signals
            }
            
            # Add disclosure
            rec = self.disclosure_manager.add_disclosure_to_education(rec)
            
            recommendations.append(rec)
        
        return recommendations
    
    def _get_default_value(self, key: str) -> Any:
        """Get default value for missing data point.
        
        Args:
            key: Data point key
        
        Returns:
            Default value
        """
        defaults = {
            'card_type': 'Credit Card',
            'card_last_4': 'XXXX',
            'balance': 0,
            'limit': 0,
            'utilization_percent': 0,
            'monthly_interest': 0,
            'annual_interest': 0,
            'minimum_payment': 0,
            'recommended_payment': 0,
            'target_payment': 0,
            'months_to_30pct': 0,
            'months_to_payoff_min': 0,
            'months_to_payoff_recommended': 0,
            'total_interest_min': 0,
            'total_interest_recommended': 0,
            'interest_savings': 0,
            'months_faster': 0,
            'extra_payment': 0,
            'num_recurring': 0,
            'monthly_recurring_spend': 0,
            'subscription_share_of_total': 0,
            'annual_spend': 0,
            'potential_savings': 0,
            'monthly_savings': 0,
            'annual_savings': 0,
            'median_pay_gap': 0,
            'cash_buffer_months': 0,
            'avg_monthly_income': 0,
            'target_months': 3,
            'monthly_savings_target': 0,
            'months_to_target': 0,
            'one_month_expenses': 0,
            'total_savings_balance': 0,
            'monthly_net_inflow': 0,
            'current_apy': 0.5,
            'high_apy': 4.5,
            'additional_annual_earnings': 0,
            'goal_amount': 0,
            'months_to_goal': 0,
            'overdue_payment_6mo': 0,
            'overdue_months_6mo': 6,
            'overdue_payment_12mo': 0,
            'overdue_months_12mo': 12,
            'overdue_payment_24mo': 0,
            'overdue_months_24mo': 24
        }
        return defaults.get(key, 0)
    
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

