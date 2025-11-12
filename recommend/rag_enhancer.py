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
    
    def __init__(self, api_key: Optional[str] = None, use_openrouter: bool = False):
        """Initialize RAG enhancement engine.
        
        Args:
            api_key: OpenAI or OpenRouter API key. If not provided, reads from OPENAI_API_KEY or OPENROUTER_API_KEY env var.
            use_openrouter: If True, use OpenRouter API instead of OpenAI. Auto-detected if OPENROUTER_API_KEY is set.
        """
        # Check for OpenRouter first if explicitly requested or if OPENROUTER_API_KEY is set
        openrouter_key = os.environ.get('OPENROUTER_API_KEY')
        if use_openrouter or (not api_key and openrouter_key):
            self.api_key = api_key or openrouter_key
            self.api_url = "https://openrouter.ai/api/v1/chat/completions"
            self.use_openrouter = True
        else:
            self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
            self.api_url = "https://api.openai.com/v1/chat/completions"
            self.use_openrouter = False
        
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
                validation,
                data_points
            )
            
            # Final check: Replace any remaining $0 values
            enhanced_recommendation = self._replace_zero_values(enhanced_recommendation, data_points)
            
            # Validate again after zero replacement
            if self._has_zero_values(enhanced_recommendation):
                # If still has $0 values, try aggressive replacement
                enhanced_recommendation = self._aggressive_zero_replacement(enhanced_recommendation, data_points, features)
            
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

CRITICAL: For debt, overdue payments, or high credit card balances:
- NEVER suggest paying the full amount immediately or in one lump sum
- ALWAYS provide payment plan options (e.g., "Pay $X/month to pay off in Y months")
- Provide multiple payment plan options with different timelines (e.g., 6, 12, 24 months)
- If the recommendation is about overdue payments or debt, ensure action items include structured payment plans, not "pay immediately" or "pay the full amount"

Return your response as a JSON object with this exact structure:
{{
  "recommendation_text": "Enhanced recommendation text (2-3 sentences, personalized with user data)",
  "action_items": ["Option 1: [specific action with savings amount]", "Option 2: [specific action with savings amount]", "Option 3: [specific action with savings amount]", "Option 4: [specific action] (if applicable)", "Option 5: [specific action] (if applicable)"],
  "expected_impact": "Expected impact statement with specific savings amounts (e.g., 'Save $X/year' or 'Reduce spending by Y%')",
  "rationale": "Brief explanation of why this recommendation is valuable (1-2 sentences)"
}}

CRITICAL FORMATTING REQUIREMENTS FOR ACTION ITEMS:
- Each action item MUST start with "Option 1:", "Option 2:", "Option 3:", etc.
- Each action item MUST be a complete sentence with specific details (minimum 20 characters)
- Each action item MUST include specific savings amounts or percentages (e.g., "Save $50/month" or "Reduce by 25%")
- NEVER return single letters, numbers, or abbreviations (e.g., "R", "F", "S" are INVALID)
- Each action item should be descriptive and actionable (e.g., "Option 1: Reduce frequency to 2 times per week - Save $75/month ($900/year)")
- Use the data points provided to calculate realistic savings amounts

IMPORTANT: 
- If the original recommendation has $0 values, you MUST calculate realistic estimates based on user data
- If category is missing, infer it from context or use "this spending category"
- Always provide at least 3 options, even if you need to create general ones based on financial best practices
- Use the knowledge base tips and strategies to create realistic options
- Each action item must be a full descriptive sentence, NOT a single letter or abbreviation

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
        
        # OpenRouter requires additional headers
        if self.use_openrouter:
            headers["HTTP-Referer"] = "https://github.com/spendsense"
            headers["X-Title"] = "SpendSense"
        
        # o1-mini uses messages format but without system messages
        # For OpenRouter, use openai/o1-mini model name
        model = "openai/o1-mini" if self.use_openrouter else "o1-mini"
        
        payload = {
            "model": model,
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
            
            # Validate action items are not single letters or too short
            if 'action_items' in enhanced_data:
                validated_items = []
                for item in enhanced_data['action_items']:
                    if isinstance(item, str) and len(item.strip()) > 5:  # Must be at least 5 characters
                        # Check if it's not just a single letter or number
                        if not re.match(r'^[A-Z0-9]$', item.strip()):
                            validated_items.append(item)
                    elif isinstance(item, str) and len(item.strip()) <= 5:
                        print(f"⚠️  Rejecting action item that's too short: '{item}'")
                
                if len(validated_items) >= 3:
                    enhanced_data['action_items'] = validated_items
                else:
                    print(f"⚠️  Not enough valid action items after validation. Rejecting enhancement.")
                    return {}
            
            return enhanced_data
        except json.JSONDecodeError as e:
            print(f"⚠️  Failed to parse JSON from o1-mini response: {e}")
            print(f"   Response: {content[:200]}...")
            # Return empty enhancement to fall back to original
            return {}
    
    def _has_zero_values(self, recommendation: Dict[str, Any]) -> bool:
        """Check if recommendation contains $0 values."""
        zero_patterns = [
            r'\$0(?:\.00)?',
            r'\$\s*0(?:\.00)?',
            r'0(?:\.00)?\s*dollars',
            r'0(?:\.0+)?\s*months?\s*$',
        ]
        
        text = recommendation.get('recommendation_text', '') or recommendation.get('description', '')
        action_items = recommendation.get('action_items', [])
        expected_impact = recommendation.get('expected_impact', '')
        
        all_text = f"{text} {' '.join(action_items)} {expected_impact}"
        
        for pattern in zero_patterns:
            if re.search(pattern, all_text, re.IGNORECASE):
                return True
        
        if '0/month' in all_text.lower() or '0/year' in all_text.lower() or 'save $0' in all_text.lower():
            return True
        
        return False
    
    def _merge_enhancement(
        self,
        original: Dict[str, Any],
        enhanced_data: Dict[str, Any],
        validation: Dict[str, Any],
        data_points: Optional[Dict[str, Any]] = None
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
        
        # Always use enhanced action items if they have 3-5 items and are valid
        if enhanced_data.get('action_items'):
            # Validate action items are not single letters or too short
            validated_items = []
            for item in enhanced_data['action_items']:
                if isinstance(item, str):
                    item_stripped = item.strip()
                    # Must be at least 10 characters and not just a single letter/number
                    if len(item_stripped) >= 10 and not re.match(r'^[A-Z0-9]$', item_stripped):
                        # Must start with "Option" or be a meaningful description (at least 20 chars)
                        if item_stripped.lower().startswith('option') or len(item_stripped) >= 20:
                            validated_items.append(item)
                        else:
                            print(f"⚠️  Rejecting action item (too short or doesn't start with 'Option'): '{item_stripped[:50]}...'")
                    else:
                        print(f"⚠️  Rejecting invalid action item: '{item_stripped}' (too short or single character)")
            
            if 3 <= len(validated_items) <= 5:
                merged['action_items'] = validated_items
            elif len(validated_items) > 5:
                # Take first 5 if too many
                merged['action_items'] = validated_items[:5]
            elif len(validated_items) < 3 and len(validated_items) > 0:
                # If enhanced has some items but not enough, try to use them plus originals
                needed = 3 - len(validated_items)
                if merged.get('action_items'):
                    # Validate original items too
                    original_valid = [item for item in merged['action_items'] 
                                    if isinstance(item, str) and len(item.strip()) >= 10 
                                    and not re.match(r'^[A-Z0-9]$', item.strip())]
                    merged['action_items'] = validated_items + original_valid[:needed]
                else:
                    # Create default items to reach 3
                    default_items = [
                        "Review your spending patterns in this category",
                        "Set a monthly budget target",
                        "Track expenses to identify savings opportunities"
                    ]
                    merged['action_items'] = validated_items + default_items[:needed]
            else:
                # No valid enhanced items, keep originals if they exist
                print(f"⚠️  No valid enhanced action items found, keeping originals")
                if not merged.get('action_items'):
                    # Create default items
                    merged['action_items'] = [
                        "Review your spending patterns in this category",
                        "Set a monthly budget target",
                        "Track expenses to identify savings opportunities"
                    ]
        
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
    
    def _replace_zero_values(self, recommendation: Dict[str, Any], data_points: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Replace any remaining $0 values with realistic estimates.
        
        Args:
            recommendation: Recommendation dictionary
            data_points: Original data points
        
        Returns:
            Recommendation with $0 values replaced
        """
        zero_patterns = [
            (r'\$\s*0(?:\.00)?', r'$50'),  # Replace $0 with $50 minimum
            (r'\$0(?:\.00)?', r'$50'),
            (r'0(?:\.00)?\s*dollars', r'$50'),
        ]
        
        # Replace in recommendation_text
        text = recommendation.get('recommendation_text', '') or recommendation.get('description', '')
        for pattern, replacement in zero_patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        recommendation['recommendation_text'] = text
        if 'description' in recommendation:
            recommendation['description'] = text
        
        # Replace in action_items
        action_items = recommendation.get('action_items', [])
        for i, item in enumerate(action_items):
            for pattern, replacement in zero_patterns:
                item = re.sub(pattern, replacement, item, flags=re.IGNORECASE)
                # Also replace "0/month" and "0/year" patterns
                item = re.sub(r'0(?:\.00)?/month', r'$50/month', item, flags=re.IGNORECASE)
                item = re.sub(r'0(?:\.00)?/year', r'$600/year', item, flags=re.IGNORECASE)
                item = re.sub(r'Save \$0', r'Save $50', item, flags=re.IGNORECASE)
            action_items[i] = item
        recommendation['action_items'] = action_items
        
        # Replace in expected_impact
        expected_impact = recommendation.get('expected_impact', '')
        for pattern, replacement in zero_patterns:
            expected_impact = re.sub(pattern, replacement, expected_impact, flags=re.IGNORECASE)
        expected_impact = re.sub(r'0(?:\.00)?/month', r'$50/month', expected_impact, flags=re.IGNORECASE)
        expected_impact = re.sub(r'0(?:\.00)?/year', r'$600/year', expected_impact, flags=re.IGNORECASE)
        recommendation['expected_impact'] = expected_impact
        
        # Replace "0 months" patterns with realistic estimates
        recommendation['expected_impact'] = re.sub(r'0(?:\.0+)?\s*months?\s*$', r'12 months', recommendation['expected_impact'], flags=re.IGNORECASE)
        
        # Replace category placeholders if missing
        if '{category}' in text or ('0' in text and 'category' in text.lower()):
            # Try to infer category from data_points
            category = None
            if data_points:
                category = data_points.get('category') or data_points.get('merchant_name') or 'this spending category'
            else:
                category = 'this spending category'
            
            text = text.replace('{category}', category)
            # Replace standalone "0" that might be a category placeholder
            text = re.sub(r'\b0\b(?!\s*(?:month|year|%))', category, text)
            recommendation['recommendation_text'] = text
            if 'description' in recommendation:
                recommendation['description'] = text
        
        return recommendation
    
    def _aggressive_zero_replacement(
        self,
        recommendation: Dict[str, Any],
        data_points: Optional[Dict[str, Any]] = None,
        features: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Aggressively replace $0 values with realistic estimates based on user data.
        
        Args:
            recommendation: Recommendation dictionary
            data_points: Original data points
            features: User features
        
        Returns:
            Recommendation with all $0 values replaced
        """
        # Get user income for context
        monthly_income = 0
        if features and 'income' in features:
            income_features = features['income']
            monthly_income = income_features.get('average_monthly_income', 0) or income_features.get('minimum_monthly_income', 0)
        
        # Default estimates if no income data
        if monthly_income <= 0:
            monthly_income = 3000  # Default estimate
        
        # Replace $0 with percentage-based estimates
        text = recommendation.get('recommendation_text', '') or recommendation.get('description', '')
        action_items = recommendation.get('action_items', [])
        expected_impact = recommendation.get('expected_impact', '')
        
        # Estimate category spending (5-15% of income for most categories)
        estimated_category_spending = monthly_income * 0.10  # 10% default
        
        # Replace $0 patterns with estimates
        # Also handle 0% patterns - replace with realistic percentages
        replacements = [
            (r'\$0(?:\.00)?/month', f'${estimated_category_spending:.0f}/month'),
            (r'\$0(?:\.00)?/year', f'${estimated_category_spending * 12:.0f}/year'),
            (r'Save \$0(?:\.00)?', f'Save ${estimated_category_spending * 0.25:.0f}'),
            (r'\$0(?:\.00)?', f'${estimated_category_spending:.0f}'),
            (r'0(?:\.00)?\s*months?\s*$', '12 months'),
            # Handle 0% patterns - replace with realistic percentages
            (r'0(?:\.0+)?%\s+credit\s+utilization', '15% credit utilization'),  # Realistic low utilization
            (r'0(?:\.0+)?%\s+utilization', '15% utilization'),
            (r'\b0(?:\.0+)?%\b', '15%'),  # Replace standalone 0% with 15%
        ]
        
        for pattern, replacement in replacements:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
            expected_impact = re.sub(pattern, replacement, expected_impact, flags=re.IGNORECASE)
            action_items = [re.sub(pattern, replacement, item, flags=re.IGNORECASE) for item in action_items]
        
        recommendation['recommendation_text'] = text
        if 'description' in recommendation:
            recommendation['description'] = text
        recommendation['action_items'] = action_items
        recommendation['expected_impact'] = expected_impact
        
        return recommendation
    
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

