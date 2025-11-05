"""Metrics calculation for SpendSense evaluation."""

import time
import importlib.util
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session

from ingest.schema import User, Consent
from features.pipeline import FeaturePipeline
from personas.assigner import PersonaAssigner


class MetricsCalculator:
    """Calculate evaluation metrics for SpendSense."""
    
    def __init__(self, db_session: Session, db_path: str = "data/spendsense.db"):
        """Initialize metrics calculator.
        
        Args:
            db_session: Database session
            db_path: Path to SQLite database
        """
        self.db = db_session
        self.db_path = db_path
        self.feature_pipeline = FeaturePipeline(db_path)
        self.persona_assigner = PersonaAssigner(db_session, db_path)
    
    def calculate_coverage(self) -> Dict[str, Any]:
        """Calculate coverage metric: % users with persona + ≥3 behaviors.
        
        Returns:
            Dictionary with coverage metrics
        """
        users = self.db.query(User).all()
        total_users = len(users)
        
        if total_users == 0:
            return {
                'total_users': 0,
                'users_with_persona': 0,
                'users_with_3plus_behaviors': 0,
                'users_with_persona_and_3plus_behaviors': 0,
                'coverage_percentage': 0.0
            }
        
        users_with_persona = 0
        users_with_3plus_behaviors = 0
        users_with_both = 0
        user_details = []
        
        for user in users:
            # Check if user has persona assignment
            try:
                persona_assignment = self.persona_assigner.assign_persona(user.id, 180)
                has_persona = persona_assignment.get('primary_persona') is not None
                if has_persona:
                    users_with_persona += 1
            except Exception:
                has_persona = False
            
            # Count behavioral signals (features)
            try:
                features = self.feature_pipeline.compute_features_for_user(user.id, 180)
                behavior_count = self._count_behaviors(features)
                has_3plus = behavior_count >= 3
                if has_3plus:
                    users_with_3plus_behaviors += 1
            except Exception:
                behavior_count = 0
                has_3plus = False
            
            # Check if user has both
            if has_persona and has_3plus:
                users_with_both += 1
            
            user_details.append({
                'user_id': user.id,
                'has_persona': has_persona,
                'behavior_count': behavior_count,
                'meets_coverage': has_persona and has_3plus
            })
        
        coverage_percentage = (users_with_both / total_users * 100) if total_users > 0 else 0.0
        
        return {
            'total_users': total_users,
            'users_with_persona': users_with_persona,
            'users_with_3plus_behaviors': users_with_3plus_behaviors,
            'users_with_persona_and_3plus_behaviors': users_with_both,
            'coverage_percentage': round(coverage_percentage, 2),
            'user_details': user_details
        }
    
    def _count_behaviors(self, features: Dict[str, Any]) -> int:
        """Count distinct behavioral signals detected.
        
        Args:
            features: User features dictionary
            
        Returns:
            Count of distinct behaviors
        """
        count = 0
        
        # Subscription behavior
        if features.get('subscriptions', {}).get('num_recurring_merchants', 0) > 0:
            count += 1
        
        # Savings behavior
        if features.get('savings', {}).get('net_inflow_180d', 0) > 0:
            count += 1
        
        # Credit behavior
        if features.get('credit', {}).get('has_credit_cards', False):
            count += 1
        if features.get('credit', {}).get('any_high_utilization_50', False):
            count += 1
        if features.get('credit', {}).get('any_interest_charges', False):
            count += 1
        
        # Income behavior
        if features.get('income', {}).get('payroll_detected', False):
            count += 1
        if features.get('income', {}).get('variable_income', False):
            count += 1
        
        return count
    
    def _get_consent_manager(self):
        """Get ConsentManager without circular import issues."""
        # Direct file import to avoid circular dependency
        consent_path = Path(__file__).parent.parent / "guardrails" / "consent.py"
        spec = importlib.util.spec_from_file_location("consent", consent_path)
        consent_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(consent_module)
        return consent_module.ConsentManager(self.db)
    
    def calculate_explainability(self) -> Dict[str, Any]:
        """Calculate explainability metric: % recommendations with rationales.
        
        Returns:
            Dictionary with explainability metrics
        """
        users = self.db.query(User).all()
        consent_manager = self._get_consent_manager()
        
        total_recommendations = 0
        recommendations_with_rationales = 0
        user_details = []
        
        for user in users:
            # Only check users with consent
            if not consent_manager.has_consent(user.id):
                continue
            
            try:
                from recommend.generator import RecommendationGenerator
                generator = RecommendationGenerator(self.db, self.db_path)
                recommendations = generator.generate_recommendations(
                    user.id,
                    window_days=180,
                    num_education=5,
                    num_offers=3
                )
                generator.close()
                
                education_items = recommendations.get('education_items', [])
                partner_offers = recommendations.get('partner_offers', [])
                all_recommendations = education_items + partner_offers
                
                for rec in all_recommendations:
                    total_recommendations += 1
                    if rec.get('rationale') and len(rec.get('rationale', '').strip()) > 0:
                        recommendations_with_rationales += 1
                
                user_details.append({
                    'user_id': user.id,
                    'total_recommendations': len(all_recommendations),
                    'with_rationales': sum(1 for r in all_recommendations if r.get('rationale')),
                    'all_have_rationales': all(r.get('rationale') for r in all_recommendations)
                })
            except Exception as e:
                # Skip users without consent or with errors
                continue
        
        explainability_percentage = (
            (recommendations_with_rationales / total_recommendations * 100)
            if total_recommendations > 0 else 0.0
        )
        
        return {
            'total_recommendations': total_recommendations,
            'recommendations_with_rationales': recommendations_with_rationales,
            'explainability_percentage': round(explainability_percentage, 2),
            'user_details': user_details
        }
    
    def calculate_relevance(self) -> Dict[str, Any]:
        """Calculate relevance metric: Education-persona fit scoring.
        
        Returns:
            Dictionary with relevance metrics
        """
        users = self.db.query(User).all()
        consent_manager = self._get_consent_manager()
        
        total_recommendations = 0
        relevant_recommendations = 0
        user_details = []
        
        for user in users:
            if not consent_manager.has_consent(user.id):
                continue
            
            try:
                # Get persona assignment
                persona_assignment = self.persona_assigner.assign_persona(user.id, 180)
                primary_persona_id = persona_assignment.get('primary_persona')
                secondary_persona_id = persona_assignment.get('secondary_persona')
                
                if not primary_persona_id:
                    continue
                
                # Get recommendations
                from recommend.generator import RecommendationGenerator
                generator = RecommendationGenerator(self.db, self.db_path)
                recommendations = generator.generate_recommendations(
                    user.id,
                    window_days=180,
                    num_education=5,
                    num_offers=3
                )
                generator.close()
                
                education_items = recommendations.get('education_items', [])
                
                user_relevant = 0
                user_total = len(education_items)
                
                for item in education_items:
                    total_recommendations += 1
                    target_personas = item.get('target_personas', [])
                    
                    # Check if recommendation targets user's persona
                    is_relevant = (
                        primary_persona_id in target_personas or
                        (secondary_persona_id and secondary_persona_id in target_personas)
                    )
                    
                    if is_relevant:
                        relevant_recommendations += 1
                        user_relevant += 1
                
                user_details.append({
                    'user_id': user.id,
                    'primary_persona': primary_persona_id,
                    'secondary_persona': secondary_persona_id,
                    'total_recommendations': user_total,
                    'relevant_recommendations': user_relevant,
                    'relevance_percentage': round((user_relevant / user_total * 100) if user_total > 0 else 0, 2)
                })
            except Exception as e:
                continue
        
        relevance_percentage = (
            (relevant_recommendations / total_recommendations * 100)
            if total_recommendations > 0 else 0.0
        )
        
        return {
            'total_recommendations': total_recommendations,
            'relevant_recommendations': relevant_recommendations,
            'relevance_percentage': round(relevance_percentage, 2),
            'user_details': user_details
        }
    
    def calculate_latency(self, sample_size: Optional[int] = None) -> Dict[str, Any]:
        """Calculate latency metric: Time to generate recommendations.
        
        Args:
            sample_size: Number of users to test (None = all users with consent)
        
        Returns:
            Dictionary with latency metrics
        """
        users = self.db.query(User).all()
        consent_manager = self._get_consent_manager()
        
        # Filter to users with consent
        users_with_consent = [u for u in users if consent_manager.has_consent(u.id)]
        
        if sample_size:
            users_with_consent = users_with_consent[:sample_size]
        
        if not users_with_consent:
            return {
                'total_users_tested': 0,
                'average_latency_seconds': 0.0,
                'min_latency_seconds': 0.0,
                'max_latency_seconds': 0.0,
                'p95_latency_seconds': 0.0,
                'p99_latency_seconds': 0.0,
                'user_details': []
            }
        
        latencies = []
        user_details = []
        
        for user in users_with_consent:
            try:
                from recommend.generator import RecommendationGenerator
                generator = RecommendationGenerator(self.db, self.db_path)
                
                start_time = time.time()
                recommendations = generator.generate_recommendations(
                    user.id,
                    window_days=180,
                    num_education=5,
                    num_offers=3
                )
                end_time = time.time()
                generator.close()
                
                latency = end_time - start_time
                latencies.append(latency)
                
                user_details.append({
                    'user_id': user.id,
                    'latency_seconds': round(latency, 3),
                    'recommendations_generated': len(recommendations.get('education_items', [])) + len(recommendations.get('partner_offers', []))
                })
            except Exception as e:
                continue
        
        if not latencies:
            return {
                'total_users_tested': 0,
                'average_latency_seconds': 0.0,
                'min_latency_seconds': 0.0,
                'max_latency_seconds': 0.0,
                'p95_latency_seconds': 0.0,
                'p99_latency_seconds': 0.0,
                'user_details': []
            }
        
        latencies_sorted = sorted(latencies)
        n = len(latencies_sorted)
        
        return {
            'total_users_tested': len(latencies),
            'average_latency_seconds': round(sum(latencies) / len(latencies), 3),
            'min_latency_seconds': round(min(latencies), 3),
            'max_latency_seconds': round(max(latencies), 3),
            'p95_latency_seconds': round(latencies_sorted[int(n * 0.95)] if n > 0 else 0, 3),
            'p99_latency_seconds': round(latencies_sorted[int(n * 0.99)] if n > 0 else 0, 3),
            'user_details': user_details
        }
    
    def calculate_fairness(self) -> Dict[str, Any]:
        """Calculate fairness metric: Basic demographic parity check.
        
        Note: Since we don't have explicit demographics in our synthetic data,
        we'll check for parity in persona assignment and recommendation distribution.
        
        Returns:
            Dictionary with fairness metrics
        """
        users = self.db.query(User).all()
        
        if not users:
            return {
                'total_users': 0,
                'persona_distribution': {},
                'recommendation_distribution': {},
                'fairness_score': 0.0
            }
        
        # Count persona distribution
        persona_counts = {}
        persona_percentages = {}
        
        for user in users:
            try:
                persona_assignment = self.persona_assigner.assign_persona(user.id, 180)
                primary_persona = persona_assignment.get('primary_persona', 'unknown')
                persona_counts[primary_persona] = persona_counts.get(primary_persona, 0) + 1
            except Exception:
                persona_counts['unknown'] = persona_counts.get('unknown', 0) + 1
        
        total = sum(persona_counts.values())
        for persona, count in persona_counts.items():
            persona_percentages[persona] = round((count / total * 100) if total > 0 else 0, 2)
        
        # Calculate fairness score (lower variance = more fair distribution)
        percentages = list(persona_percentages.values())
        if percentages:
            mean_pct = sum(percentages) / len(percentages)
            variance = sum((p - mean_pct) ** 2 for p in percentages) / len(percentages)
            # Fairness score: 1 - normalized variance (0 = perfectly fair, 1 = completely unfair)
            max_variance = 10000  # Maximum possible variance for 100% in one category
            fairness_score = 1 - (variance / max_variance)
            fairness_score = max(0, min(1, fairness_score))  # Clamp to [0, 1]
        else:
            fairness_score = 0.0
        
        return {
            'total_users': len(users),
            'persona_distribution': persona_counts,
            'persona_percentages': persona_percentages,
            'fairness_score': round(fairness_score, 3),
            'fairness_interpretation': self._interpret_fairness_score(fairness_score)
        }
    
    def _interpret_fairness_score(self, score: float) -> str:
        """Interpret fairness score.
        
        Args:
            score: Fairness score (0-1)
        
        Returns:
            Interpretation string
        """
        if score >= 0.9:
            return "Excellent - Very balanced distribution"
        elif score >= 0.7:
            return "Good - Reasonably balanced distribution"
        elif score >= 0.5:
            return "Fair - Some imbalance in distribution"
        else:
            return "Poor - Significant imbalance in distribution"
    
    def calculate_all_metrics(self, latency_sample_size: Optional[int] = None) -> Dict[str, Any]:
        """Calculate all metrics.
        
        Args:
            latency_sample_size: Number of users to test for latency (None = all)
        
        Returns:
            Dictionary with all metrics
        """
        print("Calculating coverage metric...")
        coverage = self.calculate_coverage()
        
        print("Calculating explainability metric...")
        explainability = self.calculate_explainability()
        
        print("Calculating relevance metric...")
        relevance = self.calculate_relevance()
        
        print("Calculating latency metric...")
        latency = self.calculate_latency(sample_size=latency_sample_size)
        
        print("Calculating fairness metric...")
        fairness = self.calculate_fairness()
        
        # Calculate overall score
        overall_score = (
            (coverage['coverage_percentage'] / 100) * 0.25 +
            (explainability['explainability_percentage'] / 100) * 0.25 +
            (relevance['relevance_percentage'] / 100) * 0.20 +
            (1.0 if latency['average_latency_seconds'] < 5.0 else 0.5) * 0.15 +
            fairness['fairness_score'] * 0.15
        )
        
        return {
            'timestamp': datetime.now().isoformat(),
            'coverage': coverage,
            'explainability': explainability,
            'relevance': relevance,
            'latency': latency,
            'fairness': fairness,
            'overall_score': round(overall_score, 3),
            'targets_met': {
                'coverage_100pct': coverage['coverage_percentage'] >= 100.0,
                'explainability_100pct': explainability['explainability_percentage'] >= 100.0,
                'latency_under_5s': latency['average_latency_seconds'] < 5.0,
                'relevance_high': relevance['relevance_percentage'] >= 80.0,
                'fairness_good': fairness['fairness_score'] >= 0.7
            }
        }
    
    def close(self):
        """Close database connections."""
        self.feature_pipeline.close()
        self.persona_assigner.close()

