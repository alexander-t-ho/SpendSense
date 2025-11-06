"""RAG enhancement engine using OpenAI's o1-mini thinking model."""

import os
import json
import re
from typing import Dict, List, Any, Optional
import requests

from recommend.validator import RecommendationValidator
from recommend.knowledge_base import RecommendationKnowledgeBase


class RAGEnhancementEngine:
    """Enhances recommendations using RAG with OpenAI's o1-mini thinking model."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize RAG enhancement engine.
        
        Args:
            api_key: OpenAI API key. If not provided, reads from OPENAI_API_KEY env var.
        """
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.enabled = self.api_key is not None
        
        self.validator = RecommendationValidator()
        self.knowledge_base = RecommendationKnowledgeBase()
        
        # Tone rules for all recommendations
        self.tone_rules = """
CRITICAL TONE REQUIREMENTS - MUST FOLLOW:
● No shaming language - Never use phrases that make users feel bad about their spending
● Empowering, educational tone - Focus on opportunities and growth
● Avoid judgmental phrases like "you're overspending", "you're spending too much", "you should stop"
● Use neutral, supportive language - Frame recommendations as opportunities
● Examples of GOOD phrasing:
  - "We noticed an opportunity to optimize..."
  - "You could potentially save..."
  - "Consider exploring..."
● Examples of BAD phrasing (NEVER USE):
  - "You're overspending on..."
  - "You should stop spending so much..."
  - "Your spending is too high..."
  - "You need to cut back on..."
"""
        
        if not self.enabled:
            print("⚠️  OpenAI API key not found. RAG enhancement will be disabled.")
            print("   Set OPENAI_API_KEY environment variable to enable RAG enhancement.")
    
    def enhance_recommendation(
        self,
        recommendation: Dict[str, Any],
        data_points: Optional[Dict[str, Any]] = None,
        features: Optional[Dict[str, Any]] = None,
        template_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Enhance a recommendation using RAG.
        
        Args:
            recommendation: Recommendation dictionary to enhance
            data_points: Original data points used in recommendation
            features: User features from feature pipeline
            template_info: Information about the original template (optional)
        
        Returns:
            Enhanced recommendation dictionary
        """
        if not self.enabled:
            return recommendation
        
        try:
            # Validate the recommendation first
            validation = self.validator.validate(recommendation)
            
            # Extract user context
            user_context = self.knowledge_base.extract_user_context_from_data(
                data_points or {}, features
            )
            
            # Extract category from recommendation or data points
            category = None
            if data_points:
                category = data_points.get('category') or data_points.get('merchant_name')
            
            # Retrieve relevant knowledge
            knowledge = self.knowledge_base.retrieve_relevant_knowledge(
                category=category,
                user_context=user_context
            )
            
            # Build enhancement prompt
            prompt = self._build_enhancement_prompt(
                recommendation,
                validation,
                knowledge,
                user_context,
                data_points
            )
            
            # Call OpenAI o1-mini API
            enhanced_data = self._call_o1_mini_api(prompt)
            
            # Merge enhanced data with original recommendation
            enhanced_recommendation = self._merge_enhancement(
                recommendation,
                enhanced_data,
                validation
            )
            
            return enhanced_recommendation
            
        except Exception as e:
            print(f"⚠️  Error enhancing recommendation with RAG: {e}")
            print("   Returning original recommendation")
            return recommendation
    
    def _build_enhancement_prompt(
        self,
        recommendation: Dict[str, Any],
        validation: Dict[str, Any],
        knowledge: Dict[str, Any],
        user_context: Dict[str, Any],
        data_points: Optional[Dict[str, Any]]
    ) -> str:
        """Build the enhancement prompt for o1-mini."""
        
        # Determine what needs to be fixed
        needs_fix = []
        if validation['status'] == 'needs_regeneration':
            needs_fix.append("The recommendation has critical issues and needs to be regenerated")
        elif validation['status'] == 'needs_enrichment':
            needs_fix.append("The recommendation has some issues and needs enrichment")
        
        if validation['issues']:
            needs_fix.extend(validation['issues'])
        
        prompt = f"""You are a financial advisor helping to improve a recommendation for a user. 

{self.tone_rules}

CURRENT RECOMMENDATION:
Title: {recommendation.get('title', 'N/A')}
Text: {recommendation.get('recommendation_text', 'N/A')}
Action Items: {json.dumps(recommendation.get('action_items', []), indent=2)}
Expected Impact: {recommendation.get('expected_impact', 'N/A')}

VALIDATION ISSUES FOUND:
{chr(10).join(f"- {issue}" for issue in validation['issues']) if validation['issues'] else "None - recommendation is good but could be enhanced"}

USER CONTEXT:
{knowledge.get('user_context_summary', 'No additional context available')}

RELEVANT FINANCIAL KNOWLEDGE:
Tips: {chr(10).join(f"- {tip}" for tip in knowledge.get('tips', [])[:3])}
Alternatives: {chr(10).join(f"- {alt}" for alt in knowledge.get('alternatives', [])[:3])}
Savings Strategies: {chr(10).join(f"- {strategy}" for strategy in knowledge.get('savings_strategies', [])[:3])}

DATA POINTS AVAILABLE:
{json.dumps(data_points, indent=2) if data_points else "Limited data available"}

YOUR TASK:
1. Fix any $0 values, missing categories, or placeholder text - replace with realistic estimates based on user data
2. Ensure there are exactly 3-5 actionable options (MANDATORY - if current has fewer, generate more)
3. Make each action item specific and realistic based on the user's actual spending patterns
4. Use the financial knowledge provided to create better alternatives
5. Calculate realistic savings amounts based on the user's spending data (use percentages if exact amounts aren't available)
6. If user data is limited, use general financial best practices from the knowledge base
7. Keep the same format as the original recommendation

CRITICAL REQUIREMENTS:
- Must have EXACTLY 3-5 action items (minimum 3, maximum 5)
- All financial amounts must be realistic - if data shows $0, use industry averages or percentage-based estimates
- No $0 values or placeholders allowed - replace with estimated amounts
- Use empowering, supportive language (no shaming)
- Each action item should be specific and actionable with clear savings amounts
- If category is missing or generic, infer from merchant name or use "this category"

Return your response as a JSON object with this exact structure:
{{
  "recommendation_text": "Enhanced recommendation text (2-3 sentences, personalized with user data)",
  "action_items": ["Option 1: [specific action with savings amount]", "Option 2: [specific action with savings amount]", "Option 3: [specific action with savings amount]", "Option 4: [specific action] (if applicable)", "Option 5: [specific action] (if applicable)"],
  "expected_impact": "Expected impact statement with specific savings amounts (e.g., 'Save $X/year' or 'Reduce spending by Y%')",
  "rationale": "Brief explanation of why this recommendation is valuable (1-2 sentences)"
}}

IMPORTANT: 
- If the original recommendation has $0 values, you MUST calculate realistic estimates
- If category is missing, infer it from context or use "this spending category"
- Always provide at least 3 options, even if you need to create general ones based on financial best practices
- Use the knowledge base tips and strategies to create realistic options

Return ONLY the JSON object, no other text or markdown formatting."""
        
        return prompt
    
    def _call_o1_mini_api(self, prompt: str) -> Dict[str, Any]:
        """Call OpenAI o1-mini API.
        
        Note: o1-mini uses a different format than regular chat models.
        It doesn't support system messages or temperature.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # o1-mini uses messages format but without system messages
        payload = {
            "model": "o1-mini",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 1,  # o1-mini accepts temperature but may ignore it
            "max_tokens": 1000  # Higher limit for structured output
        }
        
        response = requests.post(
            self.api_url,
            headers=headers,
            json=payload,
            timeout=30  # Longer timeout for thinking model
        )
        
        if response.status_code != 200:
            raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
        
        result = response.json()
        content = result['choices'][0]['message']['content'].strip()
        
        # Parse JSON response
        try:
            # Try to extract JSON if wrapped in markdown
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
            
            enhanced_data = json.loads(content)
            return enhanced_data
        except json.JSONDecodeError as e:
            print(f"⚠️  Failed to parse JSON from o1-mini response: {e}")
            print(f"   Response: {content[:200]}...")
            # Return empty enhancement to fall back to original
            return {}
    
    def _merge_enhancement(
        self,
        original: Dict[str, Any],
        enhanced_data: Dict[str, Any],
        validation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge enhanced data with original recommendation.
        
        Args:
            original: Original recommendation
            enhanced_data: Enhanced data from LLM
            validation: Validation results
        
        Returns:
            Merged recommendation
        """
        merged = original.copy()
        
        # Only update fields that were enhanced
        if enhanced_data.get('recommendation_text'):
            merged['recommendation_text'] = enhanced_data['recommendation_text']
        
        # Always use enhanced action items if they have 3-5 items
        if enhanced_data.get('action_items'):
            if 3 <= len(enhanced_data['action_items']) <= 5:
                merged['action_items'] = enhanced_data['action_items']
            elif len(enhanced_data['action_items']) > 5:
                # Take first 5 if too many
                merged['action_items'] = enhanced_data['action_items'][:5]
            elif len(enhanced_data['action_items']) < 3 and len(enhanced_data['action_items']) > 0:
                # If enhanced has some items but not enough, try to use them plus originals
                enhanced_items = enhanced_data['action_items']
                needed = 3 - len(enhanced_items)
                if merged.get('action_items'):
                    # Add original items if available
                    merged['action_items'] = enhanced_items + merged['action_items'][:needed]
                else:
                    # Create default items to reach 3
                    default_items = [
                        "Review your spending patterns in this category",
                        "Set a monthly budget target",
                        "Track expenses to identify savings opportunities"
                    ]
                    merged['action_items'] = enhanced_items + default_items[:needed]
        
        if enhanced_data.get('expected_impact'):
            merged['expected_impact'] = enhanced_data['expected_impact']
        
        if enhanced_data.get('rationale'):
            # Update rationale if provided
            merged['rationale'] = enhanced_data['rationale']
        
        # Ensure action_items is always present and has at least 3 items
        if not merged.get('action_items') or len(merged['action_items']) < 3:
            # Fallback: create default options based on recommendation type
            title = merged.get('title', '').lower()
            if 'category' in title or 'spending' in title:
                merged['action_items'] = [
                    "Option 1: Reduce frequency by 25% - Save approximately 25% of current spending",
                    "Option 2: Find cheaper alternatives - Save 20-30% by switching vendors",
                    "Option 3: Set a monthly budget limit - Control spending and track progress"
                ]
            elif 'subscription' in title or 'recurring' in title:
                merged['action_items'] = [
                    "Option 1: Cancel unused subscriptions - Save $X/month",
                    "Option 2: Switch to annual plans - Save 10-15% vs monthly",
                    "Option 3: Review and consolidate similar services"
                ]
            else:
                merged['action_items'] = [
                    "Option 1: Review and optimize this spending category",
                    "Option 2: Set specific savings goals for this area",
                    "Option 3: Track expenses and identify opportunities"
                ]
        
        # Ensure we don't exceed 5 items
        if len(merged.get('action_items', [])) > 5:
            merged['action_items'] = merged['action_items'][:5]
        
        return merged
    
    def enhance_batch(
        self,
        recommendations: List[Dict[str, Any]],
        data_points_map: Optional[Dict[int, Dict[str, Any]]] = None,
        features: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Enhance a batch of recommendations.
        
        Args:
            recommendations: List of recommendations to enhance
            data_points_map: Optional mapping of index to data points for each recommendation
            features: User features
        
        Returns:
            List of enhanced recommendations
        """
        enhanced = []
        for i, rec in enumerate(recommendations):
            data_points = data_points_map.get(i) if data_points_map else None
            enhanced_rec = self.enhance_recommendation(rec, data_points, features)
            enhanced.append(enhanced_rec)
        return enhanced

