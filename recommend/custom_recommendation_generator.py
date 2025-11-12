"""Custom recommendation generator that uses RAG to create recommendations from admin prompts."""

import os
import json
from typing import Dict, List, Any, Optional
import requests
import uuid
from datetime import datetime

from recommend.rag_enhancer import RAGEnhancementEngine
from recommend.knowledge_base import RecommendationKnowledgeBase
from features.pipeline import FeaturePipeline


class CustomRecommendationGenerator:
    """Generates custom recommendations from admin prompts using RAG."""
    
    def __init__(self, api_key: Optional[str] = None, db_path: str = "data/spendsense.db", use_openrouter: bool = False):
        """Initialize custom recommendation generator.
        
        Args:
            api_key: OpenAI or OpenRouter API key. If not provided, reads from OPENAI_API_KEY or OPENROUTER_API_KEY env var.
            db_path: Path to SQLite database
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
        self.db_path = db_path
        self.rag_enhancer = RAGEnhancementEngine(api_key, use_openrouter=self.use_openrouter)
        self.knowledge_base = RecommendationKnowledgeBase()
        
    def generate_from_prompt(
        self,
        user_id: str,
        admin_prompt: str,
        context_data: Optional[Dict[str, Any]] = None,
        window_days: int = 180,
        recommendation_type: str = 'actionable_recommendation'
    ) -> Dict[str, Any]:
        """Generate a recommendation from an admin prompt.
        
        Args:
            user_id: User ID
            admin_prompt: Admin's prompt describing what recommendation to create
            context_data: Optional context data (e.g., "2+ subscriptions in same category: streaming")
            window_days: Time window for feature computation
        
        Returns:
            Dictionary with generated recommendation
        """
        if not self.enabled:
            raise ValueError("OpenAI API key not found. RAG enhancement is required for custom recommendations.")
        
        # Get user features for context
        feature_pipeline = FeaturePipeline(self.db_path)
        features = feature_pipeline.compute_features_for_user(user_id, window_days)
        
        # Extract user context
        user_context = self.knowledge_base.extract_user_context_from_data(
            context_data or {},
            features
        )
        
        # Retrieve relevant knowledge
        category = context_data.get('category') if context_data else None
        knowledge = self.knowledge_base.retrieve_relevant_knowledge(
            category=category,
            user_context=user_context
        )
        
        # Build prompt for recommendation generation
        prompt = self._build_custom_prompt(
            admin_prompt,
            context_data,
            user_context,
            knowledge,
            features,
            recommendation_type
        )
        
        # Call OpenAI API
        recommendation_data = self._call_api(prompt)
        
        # Enhance with RAG
        recommendation = {
            'title': recommendation_data.get('title', 'Custom Recommendation'),
            'recommendation_text': recommendation_data.get('recommendation_text', ''),
            'action_items': recommendation_data.get('action_items', []),
            'expected_impact': recommendation_data.get('expected_impact', ''),
            'rationale': recommendation_data.get('rationale', ''),
            'priority': recommendation_data.get('priority', 'medium'),
            'context': context_data,
            'admin_prompt': admin_prompt
        }
        
        # Enhance with RAG engine
        enhanced = self.rag_enhancer.enhance_recommendation(
            recommendation,
            data_points=context_data,
            features=features
        )
        
        return enhanced
    
    def _build_custom_prompt(
        self,
        admin_prompt: str,
        context_data: Optional[Dict[str, Any]],
        user_context: Dict[str, Any],
        knowledge: Dict[str, Any],
        features: Dict[str, Any],
        recommendation_type: str = 'actionable_recommendation'
    ) -> str:
        """Build prompt for custom recommendation generation."""
        
        if recommendation_type == 'readings':
            task_description = """Create educational content or reading material based on the admin's observation. This should be informative, educational content that helps the user understand financial concepts, best practices, or strategies related to their situation."""
            output_format = """Return your response as a JSON object with this exact structure:
{{
  "title": "Clear, concise title for the educational content",
  "recommendation_text": "Educational content (3-5 paragraphs) that explains concepts, provides insights, and educates the user about the topic",
  "action_items": [],  // Empty array for readings
  "expected_impact": "How this knowledge can help the user (1-2 sentences)",
  "rationale": "Brief explanation of why this educational content is valuable (1-2 sentences)",
  "priority": "medium"
}}"""
        else:
            task_description = """Create a personalized, actionable financial recommendation based on the admin's observation. The recommendation should provide specific actions the user can take."""
            output_format = """Return your response as a JSON object with this exact structure:
{{
  "title": "Clear, concise title for the recommendation",
  "recommendation_text": "Personalized recommendation text (2-3 sentences) that references the specific observation and uses empowering language",
  "action_items": [
    "Option 1: [specific action with savings amount - e.g., 'Cancel one streaming service to save $15/month']",
    "Option 2: [specific action with savings amount]",
    "Option 3: [specific action with savings amount]",
    "Option 4: [specific action] (if applicable)",
    "Option 5: [specific action] (if applicable)"
  ],
  "expected_impact": "Expected impact statement with specific savings amounts (e.g., 'Save $180/year by canceling one subscription' or 'Reduce spending by 25%')",
  "rationale": "Brief explanation of why this recommendation is valuable (1-2 sentences)",
  "priority": "high|medium|low"
}}"""
        
        prompt = f"""You are a financial advisor creating personalized content based on an admin's observation.

ADMIN'S OBSERVATION:
{admin_prompt}

CONTEXT DATA:
{json.dumps(context_data, indent=2) if context_data else "No specific context data provided"}

USER CONTEXT:
{user_context.get('user_context_summary', 'No additional context available')}

RELEVANT FINANCIAL KNOWLEDGE:
Tips: {chr(10).join(f"- {tip}" for tip in knowledge.get('tips', [])[:5])}
Alternatives: {chr(10).join(f"- {alt}" for alt in knowledge.get('alternatives', [])[:5])}
Savings Strategies: {chr(10).join(f"- {strategy}" for strategy in knowledge.get('savings_strategies', [])[:5])}

CRITICAL TONE REQUIREMENTS - MUST FOLLOW:
● No shaming language - Never use phrases that make users feel bad about their spending
● Empowering, educational tone - Focus on opportunities and growth
● Avoid judgmental phrases like "you're overspending", "you're spending too much"
● Use neutral, supportive language - Frame recommendations as opportunities
● Examples of GOOD phrasing:
  - "We noticed an opportunity to optimize..."
  - "You could potentially save..."
  - "Consider exploring..."

CRITICAL: For debt, overdue payments, or high credit card balances:
● NEVER suggest paying the full amount immediately or in one lump sum
● ALWAYS provide payment plan options (e.g., "Pay $X/month to pay off in Y months")
● Provide multiple payment plan options with different timelines (e.g., 6, 12, 24 months)
● If the observation mentions overdue payments or debt, ensure action items include structured payment plans, not "pay immediately" or "pay the full amount"

YOUR TASK:
{task_description}

The content should:
1. Have a clear, concise title
2. Be personalized and reference the specific observation
3. Use empowering, supportive language (no shaming)
4. Be specific and realistic based on the context data provided
5. Provide value to the user

{output_format}

IMPORTANT:
- For actionable recommendations: Must have EXACTLY 3-5 action items (minimum 3, maximum 5)
- For readings: action_items should be an empty array []
- All financial amounts must be realistic and specific (if applicable)
- Use the context data to provide specific examples (e.g., if context mentions "YouTube Premium, HBO Max, Spotify", reference these in the content)
- No $0 values or generic placeholders allowed
- Use empowering, supportive language throughout
"""
        
        return prompt
    
    def _call_api(self, prompt: str) -> Dict[str, Any]:
        """Call OpenAI API to generate recommendation."""
        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a financial advisor creating personalized, actionable recommendations. Always respond with valid JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1500
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Parse JSON response
                try:
                    # Try to extract JSON if wrapped in markdown
                    import re
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        content = json_match.group(0)
                    
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Failed to parse API response as JSON: {e}")
            else:
                raise ValueError(f"API request failed with status {response.status_code}: {response.text}")
        except Exception as e:
            raise ValueError(f"Failed to generate recommendation: {str(e)}")

