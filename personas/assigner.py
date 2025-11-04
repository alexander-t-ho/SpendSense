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
        """Assign persona(s) to a user.
        
        Args:
            user_id: User ID
            window_days: Time window for feature computation (default 180 days)
            include_balanced: Whether to include balanced_stable persona if no others match
        
        Returns:
            Dictionary with assignment results including:
            - assigned_personas: List of matching persona IDs
            - primary_persona: Highest priority persona
            - rationale: Plain-language explanation
            - decision_trace: DecisionTrace object
        """
        # Compute features
        features = self.feature_pipeline.compute_features_for_user(user_id, window_days)
        
        # Test each persona
        matching_results = {}
        matched_personas = []
        
        for persona in PERSONA_DEFINITIONS:
            # Skip balanced_stable if not including
            if not include_balanced and persona.id == 'balanced_stable':
                continue
            
            matches, reasons = persona.matches(features)
            matching_results[persona.id] = {
                'matched': matches,
                'reasons': reasons,
                'risk': persona.risk.value,
                'risk_level': persona.risk.name
            }
            
            if matches:
                matched_personas.append(persona)
        
        # If no personas matched and include_balanced is True, assign balanced_stable
        if not matched_personas and include_balanced:
            balanced_persona = next((p for p in PERSONA_DEFINITIONS if p.id == 'balanced_stable'), None)
            if balanced_persona:
                matches, reasons = balanced_persona.matches(features)
                if matches:
                    matched_personas.append(balanced_persona)
                    matching_results['balanced_stable'] = {
                        'matched': True,
                        'reasons': reasons,
                        'priority': balanced_persona.priority.value
                    }
        
        # If still no match, default to balanced_stable
        if not matched_personas:
            balanced_persona = next((p for p in PERSONA_DEFINITIONS if p.id == 'balanced_stable'), None)
            if balanced_persona:
                matched_personas.append(balanced_persona)
                matching_results['balanced_stable'] = {
                    'matched': True,
                    'reasons': ['No other personas matched - default assignment'],
                    'risk': balanced_persona.risk.value,
                    'risk_level': balanced_persona.risk.name
                }
        
        # When multiple personas match, select highest risk persona as primary
        matched_personas.sort(key=lambda p: p.risk.value, reverse=True)
        primary_persona = matched_personas[0]
        
        # Generate rationale
        rationale = self._generate_rationale(primary_persona, matching_results)
        
        # Create decision trace
        trace = DecisionTrace(
            user_id=user_id,
            timestamp=datetime.now(),
            assigned_personas=[p.id for p in matched_personas],
            primary_persona=primary_persona.id,
            matching_results=matching_results,
            features_snapshot=features,
            rationale=rationale
        )
        
        # Log trace
        self.trace_logger.log_trace(trace)
        
        return {
            'user_id': user_id,
            'assigned_personas': [p.id for p in matched_personas],
            'primary_persona': primary_persona.id,
            'primary_persona_name': primary_persona.name,
            'primary_persona_description': primary_persona.description,
            'primary_persona_focus': primary_persona.focus_area,
            'primary_persona_risk': primary_persona.risk.value,
            'primary_persona_risk_level': primary_persona.risk.name,
            'rationale': rationale,
            'matching_results': matching_results,
            'decision_trace': trace.to_dict()
        }
    
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

