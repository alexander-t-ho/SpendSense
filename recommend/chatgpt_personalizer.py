"""ChatGPT API integration for personalized recommendation text generation."""

import os
import json
from typing import Dict, Any, Optional, List
import requests


class ChatGPTPersonalizer:
    """Uses ChatGPT API to generate personalized recommendation text."""
    
    def __init__(self, api_key: Optional[str] = None, use_openrouter: bool = False):
        """Initialize ChatGPT personalizer.
        
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
        
        # Tone rules for all ChatGPT interactions
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
            print("⚠️  ChatGPT API key not found. Personalized text generation will be disabled.")
            print("   Set OPENAI_API_KEY environment variable to enable ChatGPT personalization.")
    
    def personalize_recommendation(
        self,
        recommendation_template: str,
        data_points: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None,
        tone: str = "friendly and supportive"
    ) -> str:
        """Generate personalized recommendation text using ChatGPT.
        
        Args:
            recommendation_template: Template string with placeholders
            data_points: Dictionary of data points to use for personalization
            user_context: Additional user context (optional)
            tone: Desired tone for the text (default: "friendly and supportive")
        
        Returns:
            Personalized recommendation text
        """
        if not self.enabled:
            # Fallback to simple template formatting if ChatGPT is not available
            return self._format_template(recommendation_template, data_points)
        
        try:
            # Build prompt for ChatGPT
            prompt = self._build_personalization_prompt(
                recommendation_template,
                data_points,
                user_context,
                tone
            )
            
            # Call ChatGPT API
            response = self._call_chatgpt_api(prompt)
            
            return response
            
        except Exception as e:
            print(f"⚠️  Error calling ChatGPT API: {e}")
            print("   Falling back to template formatting")
            return self._format_template(recommendation_template, data_points)
    
    def _build_personalization_prompt(
        self,
        template: str,
        data_points: Dict[str, Any],
        user_context: Optional[Dict[str, Any]],
        tone: str
    ) -> str:
        """Build the prompt for ChatGPT."""
        prompt = f"""You are a financial advisor providing personalized recommendations to a user. 

Your task is to transform this recommendation template into natural, personalized text that:
1. Uses the specific data points provided
2. Maintains a {tone} tone
3. Is concise (2-3 sentences maximum)
4. Cites specific numbers and data points
5. Avoids jargon or overly technical language
6. Is empowering and actionable (not judgmental)

Template: {template}

Data points available:
{json.dumps(data_points, indent=2)}

"""
        
        if user_context:
            prompt += f"""
Additional user context:
{json.dumps(user_context, indent=2)}
"""
        
            prompt += f"""
{self.tone_rules}

Generate the personalized recommendation text. Return ONLY the text, no explanations or markdown formatting.
CRITICAL: Follow all tone rules above - use empowering, supportive language with no shaming or judgment.
"""
        
        return prompt
    
    def _call_chatgpt_api(self, prompt: str) -> str:
        """Call ChatGPT API or OpenRouter to generate personalized text."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # OpenRouter requires additional headers
        if self.use_openrouter:
            headers["HTTP-Referer"] = "https://github.com/spendsense"
            headers["X-Title"] = "SpendSense"
        
        # For OpenRouter, use openai/gpt-3.5-turbo model name
        model = "openai/gpt-3.5-turbo" if self.use_openrouter else "gpt-3.5-turbo"
        
        payload = {
            "model": model,  # Use gpt-3.5-turbo for cost efficiency
            "messages": [
                {
                    "role": "system",
                    "content": f"""You are a helpful financial advisor that provides personalized, actionable recommendations with specific data points.

{self.tone_rules}

Your recommendations must be:
- Empowering and educational
- Free of shaming or judgmental language
- Focused on opportunities and growth
- Supportive and neutral in tone"""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,  # Balance between creativity and consistency
            "max_tokens": 200  # Limit response length
        }
        
        response = requests.post(
            self.api_url,
            headers=headers,
            json=payload,
            timeout=10  # 10 second timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"ChatGPT API error: {response.status_code} - {response.text}")
        
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    
    def _format_template(self, template: str, data_points: Dict[str, Any]) -> str:
        """Fallback: Simple template formatting without ChatGPT."""
        try:
            # Format template with data points
            formatted = template.format(**data_points)
            return formatted
        except KeyError as e:
            # If data point is missing, use placeholder
            missing_key = str(e).strip("'")
            formatted = template.replace(f"{{{missing_key}}}", "[data not available]")
            return formatted
    
    def enhance_action_items(
        self,
        action_items: List[str],
        user_context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Enhance action items with ChatGPT for more personalized suggestions.
        
        Args:
            action_items: List of action item templates
            user_context: Additional user context
        
        Returns:
            Enhanced action items
        """
        if not self.enabled:
            return action_items
        
        try:
            prompt = f"""You are a financial advisor. Make these action items more specific and personalized based on the user's context.

Action items:
{chr(10).join(f"- {item}" for item in action_items)}

User context:
{json.dumps(user_context, indent=2) if user_context else "No additional context"}

Return the enhanced action items as a JSON array of strings. Keep them concise and actionable.
"""
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful financial advisor. Return only valid JSON arrays."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.5,
                "max_tokens": 300
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                enhanced = json.loads(result['choices'][0]['message']['content'].strip())
                return enhanced
            else:
                return action_items
                
        except Exception as e:
            print(f"⚠️  Error enhancing action items with ChatGPT: {e}")
            return action_items

