"""Persona assignment logic."""

from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session

from features.pipeline import FeaturePipeline
from personas.definitions import Persona, PERSONA_DEFINITIONS, PersonaRisk
from personas.traces import DecisionTrace, DecisionTraceLogger


class PersonaAssigner:
    """Assign users to personas based on behavioral signals."""
    
    def __init__(self, db_session: Session, db_path: str = "data/spendsense.db"):
        """Initialize assigner.
        
        Args:
            db_session: Database session
            db_path: Path to SQLite database
        """
        self.db = db_session
        self.db_path = db_path
        self.feature_pipeline = FeaturePipeline(db_path)
        self.trace_logger = DecisionTraceLogger()
    
    def assign_persona(
        self,
        user_id: str,
        window_days: int = 180,
        include_balanced: bool = True
    ) -> Dict[str, Any]:
        """Assign up to 2 personas to a user based on criteria match scores.
        
        Args:
            user_id: User ID
            window_days: Time window for feature computation (default 180 days)
            include_balanced: Whether to include balanced_stable persona
        
        Returns:
            Dictionary with assignment results including:
            - top_personas: List of top 2 personas with scores and percentages
            - primary_persona: Persona with highest score
            - secondary_persona: Persona with second highest score (if applicable)
            - rationale: Plain-language explanation
            - decision_trace: DecisionTrace object
        """
        # Compute features
        features = self.feature_pipeline.compute_features_for_user(user_id, window_days)
        
        # Score all personas
        persona_scores = []
        matching_results = {}
        
        for persona in PERSONA_DEFINITIONS:
            # Skip balanced_stable if not including
            if not include_balanced and persona.id == 'balanced_stable':
                continue
            
            # Score this persona (returns: matched_count, total_criteria, reasons)
            matched_count, total_criteria, reasons = persona.score_criteria(features)
            score = matched_count  # Score is the number of criteria matched
            
            matching_results[persona.id] = {
                'matched': matched_count > 0,
                'matched_criteria': matched_count,
                'total_criteria': total_criteria,
                'score': score,
                'reasons': reasons,
                'risk': persona.risk.value,
                'risk_level': persona.risk.name
            }
            
            # Only include personas with at least 1 matched criterion
            if score > 0:
                persona_scores.append({
                    'persona': persona,
                    'score': score,
                    'matched_count': matched_count,
                    'total_criteria': total_criteria
                })
        
        # Sort by score (descending), then by risk (descending) as tiebreaker
        persona_scores.sort(key=lambda x: (x['score'], x['persona'].risk.value), reverse=True)
        
        # Select top 2 personas
        top_personas = persona_scores[:2]
        
        # If no personas scored, default to balanced_stable
        if not top_personas and include_balanced:
            balanced_persona = next((p for p in PERSONA_DEFINITIONS if p.id == 'balanced_stable'), None)
            if balanced_persona:
                matched_count, total_criteria, reasons = balanced_persona.score_criteria(features)
                top_personas = [{
                    'persona': balanced_persona,
                    'score': matched_count,
                    'matched_count': matched_count,
                    'total_criteria': total_criteria
                }]
                matching_results['balanced_stable'] = {
                    'matched': True,
                    'matched_criteria': matched_count,
                    'total_criteria': total_criteria,
                    'score': matched_count,
                    'reasons': reasons,
                    'risk': balanced_persona.risk.value,
                    'risk_level': balanced_persona.risk.name
                }
        
        # Calculate percentages
        if len(top_personas) == 2:
            total_score = top_personas[0]['score'] + top_personas[1]['score']
            persona1_percentage = round((top_personas[0]['score'] / total_score) * 100) if total_score > 0 else 0
            persona2_percentage = round((top_personas[1]['score'] / total_score) * 100) if total_score > 0 else 0
        elif len(top_personas) == 1:
            persona1_percentage = 100
            persona2_percentage = 0
        else:
            persona1_percentage = 0
            persona2_percentage = 0
        
        # Get primary and secondary personas
        primary_persona = top_personas[0]['persona'] if top_personas else None
        secondary_persona = top_personas[1]['persona'] if len(top_personas) > 1 else None
        
        # Generate rationale
        rationale = self._generate_dual_rationale(top_personas, persona1_percentage, persona2_percentage)
        
        # Create decision trace
        assigned_persona_ids = [p['persona'].id for p in top_personas]
        primary_persona_id = primary_persona.id if primary_persona else None
        
        trace = DecisionTrace(
            user_id=user_id,
            timestamp=datetime.now(),
            assigned_personas=assigned_persona_ids,
            primary_persona=primary_persona_id or 'none',
            matching_results=matching_results,
            features_snapshot=features,
            rationale=rationale
        )
        
        # Log trace
        self.trace_logger.log_trace(trace)
        
        # Build response
        result = {
            'user_id': user_id,
            'assigned_personas': assigned_persona_ids,
            'top_personas': [
                {
                    'persona_id': p['persona'].id,
                    'persona_name': p['persona'].name,
                    'matched_criteria': p['matched_count'],
                    'total_criteria': p['total_criteria'],
                    'score': p['score'],
                    'percentage': persona1_percentage if i == 0 else persona2_percentage,
                    'risk': p['persona'].risk.value,
                    'risk_level': p['persona'].risk.name,
                    'matched_reasons': matching_results.get(p['persona'].id, {}).get('reasons', [])
                }
                for i, p in enumerate(top_personas)
            ],
            'primary_persona': primary_persona.id if primary_persona else None,
            'primary_persona_name': primary_persona.name if primary_persona else None,
            'primary_persona_percentage': persona1_percentage,
            'secondary_persona': secondary_persona.id if secondary_persona else None,
            'secondary_persona_name': secondary_persona.name if secondary_persona else None,
            'secondary_persona_percentage': persona2_percentage,
            'rationale': rationale,
            'matching_results': matching_results,
            'decision_trace': trace.to_dict()
        }
        
        # Add legacy fields for backward compatibility
        if primary_persona:
            result['primary_persona_description'] = primary_persona.description
            result['primary_persona_focus'] = primary_persona.focus_area
            result['primary_persona_risk'] = primary_persona.risk.value
            result['primary_persona_risk_level'] = primary_persona.risk.name
        
        return result
    
    def _generate_rationale(
        self,
        primary_persona: Persona,
        matching_results: Dict[str, Dict[str, Any]]
    ) -> str:
        """Generate plain-language rationale for persona assignment.
        
        Args:
            primary_persona: Primary assigned persona
            matching_results: Results of matching all personas
        
        Returns:
            Plain-language rationale
        """
        result = matching_results.get(primary_persona.id, {})
        reasons = result.get('reasons', [])
        
        if reasons:
            reasons_text = ', '.join(reasons)
            # Replace {reasons} placeholder in template
            rationale = primary_persona.rationale_template.replace('{reasons}', reasons_text)
            return rationale
        else:
            return f"Assigned to {primary_persona.name} persona based on financial behavior patterns."
    
    def _generate_dual_rationale(
        self,
        top_personas: List[Dict[str, Any]],
        persona1_percentage: int,
        persona2_percentage: int
    ) -> str:
        """Generate rationale for dual persona assignment.
        
        Args:
            top_personas: List of top 2 personas with scores
            persona1_percentage: Percentage for first persona
            persona2_percentage: Percentage for second persona
        
        Returns:
            Plain-language rationale
        """
        if len(top_personas) == 0:
            return "No personas matched based on current financial behavior."
        
        if len(top_personas) == 1:
            p = top_personas[0]
            persona = p['persona']
            matched = p['matched_count']
            total = p['total_criteria']
            return f"Assigned to {persona.name} persona ({matched}/{total} criteria matched, {persona1_percentage}% match)."
        
        p1 = top_personas[0]
        p2 = top_personas[1]
        persona1 = p1['persona']
        persona2 = p2['persona']
        matched1 = p1['matched_count']
        total1 = p1['total_criteria']
        matched2 = p2['matched_count']
        total2 = p2['total_criteria']
        
        return (
            f"Assigned to {persona1.name} ({matched1}/{total1} criteria, {persona1_percentage}%) "
            f"and {persona2.name} ({matched2}/{total2} criteria, {persona2_percentage}%) personas "
            f"based on financial behavior patterns."
        )
    
    def assign_all_users(
        self,
        window_days: int = 180,
        include_balanced: bool = True
    ) -> List[Dict[str, Any]]:
        """Assign personas to all users.
        
        Args:
            window_days: Time window for feature computation
            include_balanced: Whether to include balanced_stable persona
        
        Returns:
            List of assignment results for all users
        """
        from ingest.schema import User
        
        users = self.db.query(User).all()
        assignments = []
        
        for user in users:
            try:
                assignment = self.assign_persona(user.id, window_days, include_balanced)
                assignments.append(assignment)
            except Exception as e:
                print(f"Error assigning persona to user {user.id}: {e}")
                continue
        
        return assignments
    
    def get_user_persona(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get most recent persona assignment for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Most recent assignment result with persona and risk info, or None
        """
        traces = self.trace_logger.get_traces_for_user(user_id)
        if traces:
            latest_trace = traces[0]
            # Get persona details from definitions
            persona = next((p for p in PERSONA_DEFINITIONS if p.id == latest_trace.primary_persona), None)
            
            return {
                'user_id': user_id,
                'assigned_personas': latest_trace.assigned_personas,
                'primary_persona': latest_trace.primary_persona,
                'primary_persona_name': persona.name if persona else latest_trace.primary_persona,
                'primary_persona_risk': persona.risk.value if persona else 1,
                'primary_persona_risk_level': persona.risk.name if persona else 'MINIMAL',
                'rationale': latest_trace.rationale,
                'timestamp': latest_trace.timestamp.isoformat()
            }
        return None
    
    def close(self):
        """Close database connections."""
        self.feature_pipeline.close()

