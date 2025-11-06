"""Recommendation validation logic to check for missing data and quality issues."""

from typing import Dict, List, Any, Optional
import re


class RecommendationValidator:
    """Validates recommendations for quality and completeness."""
    
    def __init__(self):
        """Initialize validator."""
        pass
    
    def validate(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a recommendation and return validation results.
        
        Args:
            recommendation: Recommendation dictionary with fields:
                - title: str
                - recommendation_text: str
                - action_items: List[str]
                - expected_impact: str
                - data_points: Optional[Dict[str, Any]] - original data points used
        
        Returns:
            Dictionary with:
                - is_valid: bool
                - status: 'valid' | 'needs_enrichment' | 'needs_regeneration'
                - issues: List[str] - list of issues found
                - quality_score: float (0-1) - quality score
        """
        issues = []
        quality_score = 1.0
        
        # Check for $0 values in financial amounts
        text = recommendation.get('recommendation_text', '')
        action_items = recommendation.get('action_items', [])
        expected_impact = recommendation.get('expected_impact', '')
        
        # Check for $0 patterns
        zero_patterns = [
            r'\$0(?:\.00)?',
            r'\$\s*0(?:\.00)?',
            r'0(?:\.00)?\s*dollars',
            r'0(?:\.0+)?%',
        ]
        
        all_text = f"{text} {' '.join(action_items)} {expected_impact}"
        for pattern in zero_patterns:
            if re.search(pattern, all_text, re.IGNORECASE):
                issues.append(f"Found $0 or 0% value in recommendation")
                quality_score -= 0.3
                break
        
        # Check for missing/empty category names
        if '{category}' in text or 'category' in text.lower():
            if '0' in text or 'category' in text.lower() and not any(cat in text for cat in ['Restaurant', 'Grocery', 'Shopping', 'Gas', 'Entertainment', 'Pharmacy']):
                issues.append("Missing or empty category name")
                quality_score -= 0.2
        
        # Check for empty action items
        if not action_items or len(action_items) == 0:
            issues.append("No action items provided")
            quality_score -= 0.4
        elif len(action_items) < 3:
            issues.append(f"Only {len(action_items)} action items (need 3-5)")
            quality_score -= 0.2
        
        # Check action items for $0 values
        for item in action_items:
            for pattern in zero_patterns:
                if re.search(pattern, item, re.IGNORECASE):
                    issues.append("Action items contain $0 values")
                    quality_score -= 0.2
                    break
        
        # Check for missing expected impact
        if not expected_impact or len(expected_impact.strip()) == 0:
            issues.append("Missing expected impact")
            quality_score -= 0.2
        elif any(re.search(pattern, expected_impact, re.IGNORECASE) for pattern in zero_patterns):
            issues.append("Expected impact contains $0 values")
            quality_score -= 0.2
        
        # Check for placeholder text
        placeholder_patterns = [
            r'\{[^}]+\}',  # {placeholder}
            r'\[data not available\]',
            r'\[missing\]',
            r'undefined',
        ]
        
        for pattern in placeholder_patterns:
            if re.search(pattern, all_text, re.IGNORECASE):
                issues.append("Contains placeholder or missing data markers")
                quality_score -= 0.3
                break
        
        # Check for empty or generic text
        if not text or len(text.strip()) < 20:
            issues.append("Recommendation text is too short or empty")
            quality_score -= 0.3
        
        # Determine status
        if quality_score >= 0.9 and len(issues) == 0:
            status = 'valid'
        elif quality_score >= 0.5:
            status = 'needs_enrichment'
        else:
            status = 'needs_regeneration'
        
        # Ensure quality_score is between 0 and 1
        quality_score = max(0.0, min(1.0, quality_score))
        
        return {
            'is_valid': status == 'valid',
            'status': status,
            'issues': issues,
            'quality_score': quality_score
        }
    
    def validate_batch(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate a batch of recommendations.
        
        Args:
            recommendations: List of recommendation dictionaries
        
        Returns:
            List of validation results (one per recommendation)
        """
        return [self.validate(rec) for rec in recommendations]

