"""Persona-based recommendation generator that creates preset recommendations filled with user data."""

from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import re

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
        
        # Add debt payoff timeline recommendation if user has credit card debt
        # Generate this FIRST so it's always included and prioritized
        try:
            debt_rec = self._generate_debt_payoff_recommendation(user_id, features)
            if debt_rec:
                # Insert at the beginning to prioritize debt payoff recommendation
                stored_recommendations.insert(0, debt_rec)
                print(f"✓ Successfully generated debt payoff recommendation for user {user_id}")
            else:
                print(f"⚠️  Debt payoff recommendation returned None for user {user_id}")
        except Exception as e:
            print(f"⚠️  Error generating debt payoff recommendation for user {user_id}: {e}")
            import traceback
            traceback.print_exc()
        
        # Store in database (approved=False by default, awaiting admin approval)
        stored_recommendations_with_ids = []
        for rec_data in stored_recommendations:
            rec_id = str(uuid.uuid4())
            # Use recommendation_type from rec_data if available, otherwise default to "education"
            recommendation_type = rec_data.get('recommendation_type', 'education')
            rec = Recommendation(
                id=rec_id,
                user_id=user_id,
                recommendation_type=recommendation_type,
                title=rec_data['title'],
                description=rec_data.get('recommendation_text', ''),
                rationale=rec_data.get('rationale', ''),
                content_id=rec_data.get('id', rec_data.get('content_id')),
                persona_id=rec_data.get('persona_id'),
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
                    # Validate formatted action is not just a single letter or too short
                    if isinstance(formatted_action, str) and len(formatted_action.strip()) >= 10:
                        # Check it's not just a single character
                        if not re.match(r'^[A-Z0-9]$', formatted_action.strip()):
                            action_items.append(formatted_action)
                        else:
                            print(f"⚠️  Rejecting single-character action item: '{formatted_action}'")
                            # Fallback to template if formatted version is invalid
                            action_items.append(action_template)
                    else:
                        # If formatted is too short, use template
                        action_items.append(action_template)
                except (KeyError, ValueError) as e:
                    # If formatting fails, use template as-is
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
                
                # Post-enhancement validation: Reject recommendations with $0 values
                final_validation = self.rag_enhancer.validator.validate(enhanced_rec)
                if final_validation['is_valid'] or final_validation['status'] != 'needs_regeneration':
                    # Check one more time for $0 values even if validation passed
                    if not self._has_zero_values(enhanced_rec):
                        recommendations.append(enhanced_rec)
                    else:
                        print(f"⚠️  Rejecting recommendation {rec_template.id}: Still contains $0 values after enhancement")
                else:
                    print(f"⚠️  Rejecting recommendation {rec_template.id}: Failed validation after enhancement")
            except Exception as e:
                print(f"⚠️  RAG enhancement failed for recommendation {rec_template.id}: {e}")
                # Only add original if it doesn't have $0 values
                if not self._has_zero_values(rec):
                    recommendations.append(rec)
                else:
                    print(f"⚠️  Rejecting recommendation {rec_template.id}: Contains $0 values and RAG enhancement failed")
        
        return recommendations
    
    def _has_zero_values(self, recommendation: Dict[str, Any]) -> bool:
        """Check if recommendation contains $0 values.
        
        Args:
            recommendation: Recommendation dictionary
        
        Returns:
            True if recommendation contains $0 values, False otherwise
        """
        import re
        
        zero_patterns = [
            r'\$0(?:\.00)?',
            r'\$\s*0(?:\.00)?',
            r'0(?:\.00)?\s*dollars',
            r'0(?:\.0+)?\s*months?\s*$',  # "0 months" at end of string
        ]
        
        text = recommendation.get('recommendation_text', '') or recommendation.get('description', '')
        action_items = recommendation.get('action_items', [])
        expected_impact = recommendation.get('expected_impact', '')
        
        all_text = f"{text} {' '.join(action_items)} {expected_impact}"
        
        for pattern in zero_patterns:
            if re.search(pattern, all_text, re.IGNORECASE):
                return True
        
        # Also check for numeric 0 values that might indicate missing data
        if '0/month' in all_text.lower() or '0/year' in all_text.lower():
            return True
        
        return False
    
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
                    # For overdue recommendations, prioritize overdue cards
                    # Otherwise use the card with highest utilization
                    overdue_cards = [c for c in credit_cards if c.get('is_overdue', False)]
                    if overdue_cards:
                        # Use the overdue card with highest amount due
                        selected_card = max(overdue_cards, key=lambda c: c.get('amount_due', 0))
                    else:
                        # Use the card with highest utilization
                        selected_card = max(credit_cards, key=lambda c: c.get('utilization_percent', 0))
                    data_points.update(selected_card)
            
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
                    
                    # Post-enhancement validation: Reject recommendations with $0 values
                    if not self._has_zero_values(enhanced_rec):
                        recommendations.append(enhanced_rec)
                    else:
                        print(f"⚠️  Rejecting merchant recommendation: Still contains $0 values after enhancement")
                except Exception as e:
                    print(f"⚠️  RAG enhancement failed for merchant recommendation: {e}")
                    # Only add if no $0 values
                    if not self._has_zero_values(rec):
                        recommendations.append(rec)
                    else:
                        print(f"⚠️  Rejecting merchant recommendation: Contains $0 values and RAG failed")
        
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
                        
                        # Post-enhancement validation: Reject recommendations with $0 values
                        if not self._has_zero_values(enhanced_rec):
                            recommendations.append(enhanced_rec)
                        else:
                            print(f"⚠️  Rejecting category recommendation: Still contains $0 values after enhancement")
                    except Exception as e:
                        print(f"⚠️  RAG enhancement failed for category recommendation: {e}")
                        # Only add if no $0 values
                        if not self._has_zero_values(rec):
                            recommendations.append(rec)
                        else:
                            print(f"⚠️  Rejecting category recommendation: Contains $0 values and RAG failed")
        
        return recommendations
    
    def _generate_debt_payoff_recommendation(
        self,
        user_id: str,
        features: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generate debt payoff timeline recommendation for users with credit card debt.
        
        Args:
            user_id: User ID
            features: User features
        
        Returns:
            Debt payoff recommendation dictionary or None if user has no debt
        """
        from ingest.schema import Account
        from insights.budget_calculator import BudgetCalculator
        from datetime import datetime
        
        # Check if user has credit card debt
        from sqlalchemy import and_
        credit_card_accounts = self.db.query(Account).filter(
            and_(
                Account.user_id == user_id,
                Account.type == 'credit'
            )
        ).all()
        
        total_debt = sum(abs(acc.current or 0) for acc in credit_card_accounts)
        
        if total_debt <= 0:
            print(f"⚠️  No credit card debt found for user {user_id}")
            return None
        
        print(f"✓ Found ${total_debt:,.2f} in credit card debt for user {user_id}")
        
        # Get monthly debt repayment from budget
        try:
            budget_calculator = BudgetCalculator(self.db)
            suggested_budget = budget_calculator.suggest_budget(user_id, datetime.now().replace(day=1), lookback_months=6)
            category_budgets = suggested_budget.get('category_budgets', {})
            monthly_payment = category_budgets.get('Debt Repayment', 0)
            
            # Get monthly income from budget calculation (has better fallback logic)
            monthly_income = suggested_budget.get('average_monthly_income', 0.0)
            if monthly_income == 0.0:
                # Try income features as fallback
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
            
            if monthly_payment <= 0:
                # Fallback: use 32.5% of monthly income
                if monthly_income > 0:
                    monthly_payment = monthly_income * 0.325  # 32.5% for debt repayment
                    print(f"✓ Using fallback monthly payment: ${monthly_payment:,.2f} (32.5% of ${monthly_income:,.2f} income)")
                else:
                    print(f"⚠️  Cannot calculate monthly payment: monthly_income is 0")
            else:
                print(f"✓ Using budget monthly payment: ${monthly_payment:,.2f}")
        except Exception as e:
            print(f"⚠️  Error getting budget for debt recommendation: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: use 32.5% of monthly income from features
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
            monthly_payment = monthly_income * 0.325 if monthly_income > 0 else 0  # 32.5% for debt repayment
        
        if monthly_payment <= 0:
            print(f"⚠️  Monthly payment is 0 or negative for user {user_id}, cannot generate debt payoff recommendation")
            return None
        
        # Calculate debt payoff timeline
        try:
            timeline = budget_calculator.calculate_debt_payoff_timeline(
                user_id, monthly_payment, estimated_apr=0.20
            )
            
            if timeline['months_to_payoff'] is None or timeline['months_to_payoff'] <= 0:
                print(f"⚠️  Invalid timeline calculation for user {user_id}: months_to_payoff={timeline.get('months_to_payoff')}")
                return None
            
            print(f"✓ Calculated debt payoff timeline: {timeline['months_to_payoff']} months")
        except Exception as e:
            print(f"⚠️  Error calculating debt payoff timeline: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        # Build recommendation
        months = timeline['months_to_payoff']
        years = months / 12.0
        
        if months < 12:
            timeline_text = f"{months} months"
        elif months < 24:
            timeline_text = f"{years:.1f} years ({months} months)"
        else:
            timeline_text = f"{years:.1f} years"
        
        title = f"Debt Payoff Timeline: Pay Off ${total_debt:,.0f} in {timeline_text}"
        
        description = (
            f"Based on your current budget allocation of ${monthly_payment:,.2f}/month for debt repayment, "
            f"you can pay off your ${total_debt:,.2f} in credit card debt in approximately {timeline_text}. "
            f"This assumes a 20% APR and aggressive repayment strategy."
        )
        
        rationale = (
            f"At ${monthly_payment:,.2f}/month, you'll pay off ${total_debt:,.2f} in debt in {timeline_text}. "
            f"Total interest paid will be approximately ${timeline['total_interest']:,.2f}. "
            f"By following the recommended strategies, you can accelerate your debt payoff and save on interest."
        )
        
        action_items = timeline['strategy_recommendations']
        
        expected_impact = (
            f"Paying off ${total_debt:,.2f} in credit card debt will free up ${monthly_payment:,.2f}/month "
            f"for savings and investments, improve your credit score, and reduce financial stress."
        )
        
        return {
            'id': f'debt_payoff_timeline_{user_id}',
            'title': title,
            'recommendation_text': description,
            'rationale': rationale,
            'action_items': action_items,
            'expected_impact': expected_impact,
            'persona_id': 'debt_management',
            'priority': 'high',
            'category': 'debt_management',
            'recommendation_type': 'actionable_recommendation',  # Ensure type is set
            'timeline_months': months,
            'total_debt': total_debt,
            'monthly_payment': monthly_payment,
            'total_interest': timeline['total_interest'],
            'payoff_date': timeline['payoff_date']
        }
    
    def close(self):
        """Close database connections."""
        self.feature_pipeline.close()
        self.persona_assigner.close()
        self.data_extractor.feature_pipeline.close()

