"""Persona-based recommendation generator that creates preset recommendations filled with user data."""

from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from personas.assigner import PersonaAssigner
from recommend.actionable_recommendations import ACTIONABLE_RECOMMENDATIONS, ActionableRecommendation
from recommend.data_extractor import RecommendationDataExtractor
from recommend.rag_enhancer import RAGEnhancementEngine
from features.pipeline import FeaturePipeline
from ingest.schema import Recommendation, User


class PersonaRecommendationGenerator:
    """Generates persona-based preset recommendations filled with user-specific data."""
    
    def __init__(self, db_session: Session, db_path: str = "data/spendsense.db"):
        """Initialize generator.
        
        Args:
            db_session: Database session
            db_path: Path to SQLite database
        """
        self.db = db_session
        self.db_path = db_path
        self.feature_pipeline = FeaturePipeline(db_path)
        self.persona_assigner = PersonaAssigner(db_session, db_path)
        self.data_extractor = RecommendationDataExtractor(db_session, db_path)
        self.rag_enhancer = RAGEnhancementEngine()  # Optional: requires OPENAI_API_KEY
    
    def generate_and_store_recommendations(
        self,
        user_id: str,
        window_days: int = 180,
        num_recommendations: int = 8
    ) -> List[Dict[str, Any]]:
        """Generate persona-based recommendations and store them in the database.
        
        Args:
            user_id: User ID
            window_days: Time window for feature computation (default 180)
            num_recommendations: Number of recommendations to generate (default 8)
        
        Returns:
            List of recommendation dictionaries that were stored
        """
        # Get persona assignment
        persona_assignment = self.persona_assigner.assign_persona(user_id, window_days)
        primary_persona_id = persona_assignment['primary_persona']
        secondary_persona_id = persona_assignment.get('secondary_persona')
        primary_percentage = persona_assignment.get('primary_persona_percentage', 100)
        secondary_percentage = persona_assignment.get('secondary_persona_percentage', 0)
        
        # Get matched criteria for each persona
        all_matching_personas = persona_assignment.get('all_matching_personas', [])
        persona_matched_criteria = {}
        for persona_data in all_matching_personas:
            persona_id = persona_data.get('persona_id')
            matched_reasons = persona_data.get('matched_reasons', [])
            persona_matched_criteria[persona_id] = matched_reasons
        
        # Get user features
        features = self.feature_pipeline.compute_features_for_user(user_id, window_days)
        
        # Determine number of recommendations per persona based on risk-weighted percentages
        # Higher risk personas get more recommendations to mitigate bad habits
        if secondary_persona_id and secondary_percentage > 0:
            from personas.definitions import get_persona_by_id
            primary_persona = get_persona_by_id(primary_persona_id)
            secondary_persona = get_persona_by_id(secondary_persona_id)
            
            if primary_persona and secondary_persona:
                # Calculate risk-weighted scores
                primary_risk_weight = (primary_percentage / 100) * primary_persona.risk.value
                secondary_risk_weight = (secondary_percentage / 100) * secondary_persona.risk.value
                total_risk_weight = primary_risk_weight + secondary_risk_weight
                
                if total_risk_weight > 0:
                    primary_ratio = primary_risk_weight / total_risk_weight
                    secondary_ratio = secondary_risk_weight / total_risk_weight
                    
                    primary_count = max(1, round(num_recommendations * primary_ratio))
                    secondary_count = max(1, num_recommendations - primary_count)
                else:
                    # Fallback to percentage-based
                    primary_count = max(1, round(num_recommendations * (primary_percentage / 100)))
                    secondary_count = max(1, num_recommendations - primary_count)
            else:
                primary_count = num_recommendations
                secondary_count = 0
        else:
            primary_count = num_recommendations
            secondary_count = 0
        
        # Generate recommendations for each persona
        stored_recommendations = []
        
        # Primary persona recommendations
        if primary_count > 0:
            matched_criteria = persona_matched_criteria.get(primary_persona_id, [])
            primary_recs = self._generate_persona_recommendations(
                user_id, primary_persona_id, features, primary_count, window_days, matched_criteria
            )
            stored_recommendations.extend(primary_recs)
        
        # Secondary persona recommendations
        if secondary_count > 0 and secondary_persona_id:
            matched_criteria = persona_matched_criteria.get(secondary_persona_id, [])
            secondary_recs = self._generate_persona_recommendations(
                user_id, secondary_persona_id, features, secondary_count, window_days, matched_criteria
            )
            stored_recommendations.extend(secondary_recs)
        
        # Add universal spending pattern recommendations (apply to all users)
        # Add 1-2 spending pattern recommendations if available
        spending_recs = self._generate_spending_pattern_recommendations(
            user_id, features, window_days, primary_persona_id, max_recommendations=2
        )
        stored_recommendations.extend(spending_recs)
        
        # Store in database (approved=False by default, awaiting admin approval)
        stored_recommendations_with_ids = []
        for rec_data in stored_recommendations:
            rec_id = str(uuid.uuid4())
            rec = Recommendation(
                id=rec_id,
                user_id=user_id,
                recommendation_type="education",
                title=rec_data['title'],
                description=rec_data.get('recommendation_text', ''),
                rationale=rec_data.get('rationale', ''),
                content_id=rec_data['id'],
                persona_id=rec_data['persona_id'],
                action_items=rec_data.get('action_items', []),
                expected_impact=rec_data.get('expected_impact', ''),
                priority=rec_data.get('priority', 'medium'),
                approved=False,  # Requires admin approval
                flagged=False,
                rejected=False,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            self.db.add(rec)
            # Add the database ID to the returned data
            rec_data_with_id = {
                **rec_data,
                'id': rec_id,  # Database ID for API operations
                'approved': False,
                'rejected': False,
                'flagged': False,
                'status': 'pending'
            }
            stored_recommendations_with_ids.append(rec_data_with_id)
        
        self.db.commit()
        
        return stored_recommendations_with_ids
    
    def _generate_persona_recommendations(
        self,
        user_id: str,
        persona_id: str,
        features: Dict[str, Any],
        num_recommendations: int,
        window_days: int,
        matched_criteria: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate recommendations for a specific persona.
        
        Args:
            user_id: User ID
            persona_id: Persona ID
            features: User features
            num_recommendations: Number of recommendations to generate
            window_days: Time window for data extraction
        
        Returns:
            List of recommendation dictionaries
        """
        # Get actionable recommendations for this persona (including universal)
        persona_recommendations = [
            rec for rec in ACTIONABLE_RECOMMENDATIONS
            if rec.persona_id == persona_id or rec.persona_id == "universal"
        ]
        
        # Extract user data for personalization
        data_points = self._extract_data_for_persona(user_id, persona_id, features, window_days)
        
        # Filter recommendations based on matched criteria and available data
        applicable_recommendations = []
        matched_criteria_set = set(matched_criteria or [])
        
        for rec_template in persona_recommendations:
            # Check if recommendation matches any of the matched criteria
            # Match by checking if target_signals or recommendation keywords appear in matched criteria
            matches_criteria = False
            if matched_criteria:
                # Check if any target signal or keyword from recommendation matches criteria
                for criteria_text in matched_criteria:
                    criteria_lower = criteria_text.lower()
                    # Check target signals
                    for signal in rec_template.target_signals:
                        if signal.lower() in criteria_lower:
                            matches_criteria = True
                            break
                    # Check if recommendation title/keywords match criteria
                    if not matches_criteria:
                        title_lower = rec_template.title.lower()
                        if any(keyword in criteria_lower for keyword in title_lower.split() if len(keyword) > 3):
                            matches_criteria = True
                            break
            else:
                # If no matched criteria, accept all recommendations for the persona
                matches_criteria = True
            
            # Also check data availability
            required_data = set(rec_template.data_points_needed)
            available_data = set(data_points.keys())
            has_data = len(required_data.intersection(available_data)) >= len(required_data) * 0.5
            
            # Include if it matches criteria OR if we have good data coverage
            if matches_criteria or (has_data and not matched_criteria):
                applicable_recommendations.append(rec_template)
        
        # Sort by priority (HIGH first), then by criteria match
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        applicable_recommendations.sort(key=lambda x: (
            priority_order.get(x.priority.value, 3),
            # Prefer recommendations that match criteria
            not any(signal.lower() in ' '.join(matched_criteria or []).lower() 
                   for signal in x.target_signals)
        ))
        
        # Select top recommendations (prioritize by priority and data availability)
        selected_recommendations = applicable_recommendations[:num_recommendations]
        
        # If we don't have enough, fill with remaining
        if len(selected_recommendations) < num_recommendations:
            remaining = [r for r in persona_recommendations if r not in selected_recommendations]
            selected_recommendations.extend(remaining[:num_recommendations - len(selected_recommendations)])
        
        # Build personalized recommendations
        recommendations = []
        for rec_template in selected_recommendations:
            # Prepare data points for template
            template_data = {}
            for key in rec_template.data_points_needed:
                if key in data_points:
                    template_data[key] = data_points[key]
                else:
                    template_data[key] = self._get_default_value(key)
            
            # Generate personalized text
            try:
                personalized_text = rec_template.template.format(**template_data)
            except (KeyError, ValueError) as e:
                # Fallback to template without formatting if data is missing
                personalized_text = rec_template.template
            
            # Format action items
            action_items = []
            for action_template in rec_template.action_items:
                try:
                    formatted_action = action_template.format(**template_data)
                    action_items.append(formatted_action)
                except (KeyError, ValueError):
                    action_items.append(action_template)
            
            # Format expected impact
            try:
                expected_impact = rec_template.expected_impact.format(**template_data)
            except (KeyError, ValueError):
                expected_impact = rec_template.expected_impact
            
            # Ensure action_items is always present (even if empty template)
            if not action_items:
                action_items = ["Review this recommendation and consider taking action"]
            
            # Build rationale
            rationale_parts = [personalized_text]
            if action_items:
                rationale_parts.append(f"Action steps: {', '.join(action_items[:3])}")  # First 3 actions
            if expected_impact:
                rationale_parts.append(f"Expected impact: {expected_impact}")
            rationale = " ".join(rationale_parts)
            
            rec = {
                'id': rec_template.id,
                'persona_id': persona_id if rec_template.persona_id != "universal" else persona_id,  # Use actual persona for universal recommendations
                'title': rec_template.title,
                'recommendation_text': personalized_text,
                'action_items': action_items,
                'expected_impact': expected_impact,
                'priority': rec_template.priority.value,
                'rationale': rationale
            }
            
            # Option B: Always enhance with RAG (validate and enrich all recommendations)
            try:
                enhanced_rec = self.rag_enhancer.enhance_recommendation(
                    rec,
                    data_points=template_data,
                    features=features,
                    template_info={'template_id': rec_template.id, 'persona_id': persona_id}
                )
                recommendations.append(enhanced_rec)
            except Exception as e:
                print(f"⚠️  RAG enhancement failed for recommendation {rec_template.id}: {e}")
                # Fallback to original recommendation if RAG fails
                recommendations.append(rec)
        
        return recommendations
    
    def _extract_data_for_persona(
        self,
        user_id: str,
        persona_id: str,
        features: Dict[str, Any],
        window_days: int
    ) -> Dict[str, Any]:
        """Extract data points needed for persona recommendations.
        
        Args:
            user_id: User ID
            persona_id: Persona ID
            features: User features
            window_days: Time window for extraction
        
        Returns:
            Dictionary of data points
        """
        data_points = {}
        
        try:
            if persona_id == 'high_utilization':
                credit_cards = self.data_extractor.extract_credit_card_data(user_id)
                if credit_cards:
                    # Use the card with highest utilization
                    highest_util_card = max(credit_cards, key=lambda c: c.get('utilization_percent', 0))
                    data_points.update(highest_util_card)
            
            elif persona_id == 'subscription_heavy':
                sub_data = self.data_extractor.extract_subscription_data(user_id, window_days)
                data_points.update(sub_data)
            
            elif persona_id == 'variable_income_budgeter':
                income_data = self.data_extractor.extract_income_data(user_id, window_days)
                data_points.update(income_data)
                
                # Map savings plan options to individual fields for template
                if 'savings_plan_options' in income_data and income_data['savings_plan_options']:
                    plans = income_data['savings_plan_options']
                    if len(plans) >= 4:
                        # Option 1: Fast Track
                        data_points['plan1_monthly'] = plans[0]['monthly_savings']
                        data_points['plan1_months'] = plans[0]['target_months']
                        data_points['plan1_timeline'] = plans[0]['months_to_target']
                        # Option 2: Steady Progress
                        data_points['plan2_monthly'] = plans[1]['monthly_savings']
                        data_points['plan2_months'] = plans[1]['target_months']
                        data_points['plan2_timeline'] = plans[1]['months_to_target']
                        # Option 3: Recommended
                        data_points['plan3_monthly'] = plans[2]['monthly_savings']
                        data_points['plan3_months'] = plans[2]['target_months']
                        data_points['plan3_timeline'] = plans[2]['months_to_target']
                        # Option 4: Slow & Steady
                        data_points['plan4_monthly'] = plans[3]['monthly_savings']
                        data_points['plan4_months'] = plans[3]['target_months']
                        data_points['plan4_timeline'] = plans[3]['months_to_target']
            
            elif persona_id == 'savings_builder':
                savings_data = self.data_extractor.extract_savings_data(user_id, window_days)
                data_points.update(savings_data)
            
            elif persona_id == 'balanced_stable':
                credit_features = features.get('credit', {})
                savings_features = features.get('savings', {})
                utilization = credit_features.get('max_utilization_percent', 0)
                monthly_savings = savings_features.get('monthly_net_inflow', 0)
                data_points.update({
                    'utilization_below_30': utilization if utilization < 30 else 30,
                    'monthly_savings': monthly_savings
                })
                
        except Exception as e:
            print(f"Warning: Error extracting data for persona {persona_id}: {e}")
        
        return data_points
    
    def _get_default_value(self, key: str) -> Any:
        """Get default value for missing data point."""
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
            'months_to_goal': 0
        }
        return defaults.get(key, 0)
    
    def _generate_spending_pattern_recommendations(
        self,
        user_id: str,
        features: Dict[str, Any],
        window_days: int,
        persona_id: str,
        max_recommendations: int = 2
    ) -> List[Dict[str, Any]]:
        """Generate spending pattern recommendations (universal).
        
        Args:
            user_id: User ID
            features: User features
            window_days: Time window for analysis
            max_recommendations: Maximum number of spending pattern recommendations
        
        Returns:
            List of spending pattern recommendation dictionaries
        """
        recommendations = []
        
        # Get spending pattern data
        try:
            spending_patterns = self.data_extractor.extract_spending_pattern_data(user_id, window_days)
            category_spending = self.data_extractor.extract_category_spending_data(user_id, window_days)
        except Exception as e:
            print(f"Error extracting spending pattern data: {e}")
            return recommendations
        
        # Get universal recommendations
        universal_recs = [
            rec for rec in ACTIONABLE_RECOMMENDATIONS
            if rec.persona_id == "universal"
        ]
        
        # Generate merchant-specific recommendations
        merchant_rec_template = next((r for r in universal_recs if r.id == "reduce_frequent_merchant_spending"), None)
        if merchant_rec_template and spending_patterns:
            for merchant_data in spending_patterns[:max_recommendations]:
                # Prepare template data
                template_data = merchant_data.copy()
                
                # Generate personalized text
                try:
                    personalized_text = merchant_rec_template.template.format(**template_data)
                except (KeyError, ValueError):
                    personalized_text = merchant_rec_template.template
                
                # Format action items
                action_items = []
                for action_template in merchant_rec_template.action_items:
                    try:
                        formatted_action = action_template.format(**template_data)
                        action_items.append(formatted_action)
                    except (KeyError, ValueError):
                        action_items.append(action_template)
                
                # Format expected impact
                try:
                    expected_impact = merchant_rec_template.expected_impact.format(**template_data)
                except (KeyError, ValueError):
                    expected_impact = merchant_rec_template.expected_impact
                
                # Build rationale
                rationale_parts = [personalized_text]
                if action_items:
                    rationale_parts.append(f"Action steps: {', '.join(action_items[:3])}")
                if expected_impact:
                    rationale_parts.append(f"Expected impact: {expected_impact}")
                rationale = " ".join(rationale_parts)
                
                # Use provided persona_id
                
                rec = {
                    'id': f"{merchant_rec_template.id}_{merchant_data['merchant_name'].replace(' ', '_').lower()}",
                    'persona_id': persona_id,
                    'title': merchant_rec_template.title.format(**{'merchant_name': merchant_data['merchant_name']}),
                    'recommendation_text': personalized_text,
                    'action_items': action_items,
                    'expected_impact': expected_impact,
                    'priority': merchant_rec_template.priority.value,
                    'rationale': rationale
                }
                
                # Option B: Always enhance with RAG
                try:
                    enhanced_rec = self.rag_enhancer.enhance_recommendation(
                        rec,
                        data_points=template_data,
                        features=features,
                        template_info={'template_id': merchant_rec_template.id, 'merchant_name': merchant_data['merchant_name']}
                    )
                    recommendations.append(enhanced_rec)
                except Exception as e:
                    print(f"⚠️  RAG enhancement failed for merchant recommendation: {e}")
                    recommendations.append(rec)
        
        # Generate category-specific recommendations (if we haven't reached max)
        if len(recommendations) < max_recommendations:
            category_rec_template = next((r for r in universal_recs if r.id == "reduce_category_spending"), None)
            if category_rec_template and category_spending:
                for category_data in category_spending[:max_recommendations - len(recommendations)]:
                    # Prepare template data
                    template_data = category_data.copy()
                    
                    # Generate personalized text
                    try:
                        personalized_text = category_rec_template.template.format(**template_data)
                    except (KeyError, ValueError):
                        personalized_text = category_rec_template.template
                    
                    # Format action items
                    action_items = []
                    for action_template in category_rec_template.action_items:
                        try:
                            formatted_action = action_template.format(**template_data)
                            action_items.append(formatted_action)
                        except (KeyError, ValueError):
                            action_items.append(action_template)
                    
                    # Format expected impact
                    try:
                        expected_impact = category_rec_template.expected_impact.format(**template_data)
                    except (KeyError, ValueError):
                        expected_impact = category_rec_template.expected_impact
                    
                    # Build rationale
                    rationale_parts = [personalized_text]
                    if action_items:
                        rationale_parts.append(f"Action steps: {', '.join(action_items[:3])}")
                    if expected_impact:
                        rationale_parts.append(f"Expected impact: {expected_impact}")
                    rationale = " ".join(rationale_parts)
                    
                    # Use provided persona_id (already set in function scope)
                    
                    rec = {
                        'id': f"{category_rec_template.id}_{category_data['category'].replace(' ', '_').lower()}",
                        'persona_id': persona_id,
                        'title': category_rec_template.title.format(**{'category': category_data['category']}),
                        'recommendation_text': personalized_text,
                        'action_items': action_items,
                        'expected_impact': expected_impact,
                        'priority': category_rec_template.priority.value,
                        'rationale': rationale
                    }
                    
                    # Option B: Always enhance with RAG
                    try:
                        enhanced_rec = self.rag_enhancer.enhance_recommendation(
                            rec,
                            data_points=template_data,
                            features=features,
                            template_info={'template_id': category_rec_template.id, 'category': category_data['category']}
                        )
                        recommendations.append(enhanced_rec)
                    except Exception as e:
                        print(f"⚠️  RAG enhancement failed for category recommendation: {e}")
                        recommendations.append(rec)
        
        return recommendations
    
    def close(self):
        """Close database connections."""
        self.feature_pipeline.close()
        self.persona_assigner.close()
        self.data_extractor.feature_pipeline.close()

