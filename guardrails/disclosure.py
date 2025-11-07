"""Disclosure and disclaimer management for SpendSense."""

from typing import Dict, Any


class DisclosureManager:
    """Manage regulatory disclosures and disclaimers."""
    
    STANDARD_DISCLAIMER = (
        "This is educational content, not financial advice. "
        "Consult a licensed financial advisor for personalized guidance."
    )
    
    NOT_FINANCIAL_ADVICE = (
        "This information is provided for educational purposes only and does not constitute "
        "financial, investment, or legal advice. Please consult with a qualified financial "
        "advisor before making any financial decisions."
    )
    
    def __init__(self):
        """Initialize disclosure manager."""
        pass
    
    def get_disclaimer(self, context: str = "recommendation") -> str:
        """Get appropriate disclaimer based on context.
        
        Args:
            context: Context for the disclaimer (recommendation, insight, offer)
        
        Returns:
            Disclaimer text
        """
        if context == "recommendation":
            return self.STANDARD_DISCLAIMER
        elif context == "offer":
            return (
                f"{self.NOT_FINANCIAL_ADVICE} "
                "Offers are subject to terms and conditions set by the partner. "
                "We may receive compensation if you sign up through our links."
            )
        elif context == "insight":
            return (
                "These insights are based on your transaction data and are for "
                "educational purposes only. They do not constitute financial advice."
            )
        else:
            return self.STANDARD_DISCLAIMER
    
    def add_disclosure_to_recommendation(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Add disclosure to a recommendation.
        
        Args:
            recommendation: Recommendation dictionary
        
        Returns:
            Recommendation with disclosure added
        """
        context = "offer" if recommendation.get("type") == "partner_offer" else "recommendation"
        recommendation["disclosure"] = self.get_disclaimer(context)
        return recommendation
    
    def add_disclosure_to_education(self, education_item: Dict[str, Any]) -> Dict[str, Any]:
        """Add disclosure to an education item.
        
        Args:
            education_item: Education item dictionary
        
        Returns:
            Education item with disclosure added
        """
        education_item["disclosure"] = self.get_disclaimer("recommendation")
        return education_item
    
    def add_disclosure_to_offer(self, offer: Dict[str, Any]) -> Dict[str, Any]:
        """Add disclosure to a partner offer.
        
        Args:
            offer: Partner offer dictionary
        
        Returns:
            Offer with disclosure added
        """
        offer["disclosure"] = self.get_disclaimer("offer")
        return offer
    
    def add_disclosure_to_insight(self, insight: Dict[str, Any]) -> Dict[str, Any]:
        """Add disclosure to an insight.
        
        Args:
            insight: Insight dictionary
        
        Returns:
            Insight with disclosure added
        """
        insight["disclosure"] = self.get_disclaimer("insight")
        return insight




