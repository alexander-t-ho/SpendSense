"""Tone validation for recommendations and rationales."""

from typing import List, Tuple
import re


class ToneValidator:
    """Validate tone of recommendations and rationales."""
    
    # Shaming language patterns
    SHAMING_PATTERNS = [
        r'\byou\'re\s+(?:overspending|spending\s+too\s+much|wasting\s+money)',
        r'\byou\s+should\s+be\s+ashamed',
        r'\byou\'re\s+bad\s+with\s+money',
        r'\byou\s+can\'t\s+afford',
        r'\byou\'re\s+irresponsible',
        r'\byou\s+need\s+to\s+stop',
        r'\b(?:terrible|awful|horrible)\s+(?:spending|financial)\s+habits',
        r'\byou\s+should\s+know\s+better',
        r'\bwhat\s+were\s+you\s+thinking',
        r'\byou\'ve\s+made\s+(?:a\s+)?mistake',
    ]
    
    # Judgmental phrases
    JUDGMENTAL_PATTERNS = [
        r'\byou\s+should\s+have',
        r'\byou\s+ought\s+to',
        r'\byou\s+must\s+do',
        r'\b(?:always|never)\s+(?:spend|buy)',
        r'\byou\'re\s+doing\s+it\s+wrong',
    ]
    
    # Empowering language patterns (positive)
    EMPOWERING_PATTERNS = [
        r'\byou\s+can',
        r'\byou\s+have\s+the\s+power',
        r'\b(?:opportunity|possibility|potential)',
        r'\b(?:consider|explore|try)',
        r'\b(?:help|support|guide)',
        r'\b(?:suggest|recommend|option)',
    ]
    
    def __init__(self):
        """Initialize tone validator."""
        self.shaming_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.SHAMING_PATTERNS]
        self.judgmental_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.JUDGMENTAL_PATTERNS]
        self.empowering_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.EMPOWERING_PATTERNS]
    
    def validate(self, text: str) -> Tuple[bool, List[str]]:
        """Validate tone of text.
        
        Args:
            text: Text to validate
        
        Returns:
            Tuple of (is_valid, issues) where issues is a list of detected problems
        """
        issues = []
        text_lower = text.lower()
        
        # Check for shaming language
        for pattern in self.shaming_regex:
            if pattern.search(text):
                issues.append(f"Shaming language detected: {pattern.pattern}")
        
        # Check for judgmental language
        for pattern in self.judgmental_regex:
            if pattern.search(text):
                issues.append(f"Judgmental language detected: {pattern.pattern}")
        
        # Check for empowering language (positive indicator)
        has_empowering = any(pattern.search(text) for pattern in self.empowering_regex)
        
        is_valid = len(issues) == 0
        
        if not is_valid:
            return (False, issues)
        
        # If no issues, check if text is neutral/empowering
        if not has_empowering and len(text) > 50:
            # For longer texts, suggest adding more empowering language
            issues.append("Consider adding more empowering or supportive language")
            return (True, issues)  # Not a failure, just a suggestion
        
        return (True, [])
    
    def sanitize(self, text: str) -> str:
        """Sanitize text to remove problematic language.
        
        Args:
            text: Text to sanitize
        
        Returns:
            Sanitized text
        """
        sanitized = text
        
        # Replace shaming language with neutral alternatives
        replacements = {
            r'\byou\'re\s+overspending': 'your spending patterns suggest',
            r'\byou\'re\s+spending\s+too\s+much': 'your spending is higher than typical',
            r'\byou\s+can\'t\s+afford': 'this may exceed your current budget',
            r'\byou\s+should\s+be\s+ashamed': '',  # Remove entirely
            r'\byou\'re\s+bad\s+with\s+money': 'there are opportunities to improve your financial management',
        }
        
        for pattern, replacement in replacements.items():
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def check_rationale(self, rationale: str) -> Tuple[bool, List[str]]:
        """Check if a rationale meets tone requirements.
        
        Args:
            rationale: Rationale text to check
        
        Returns:
            Tuple of (is_valid, issues)
        """
        return self.validate(rationale)
    
    def check_recommendation(self, title: str, description: str, rationale: str) -> Tuple[bool, List[str]]:
        """Check if a recommendation meets tone requirements.
        
        Args:
            title: Recommendation title
            description: Recommendation description
            rationale: Recommendation rationale
        
        Returns:
            Tuple of (is_valid, issues)
        """
        all_text = f"{title} {description} {rationale}"
        return self.validate(all_text)




