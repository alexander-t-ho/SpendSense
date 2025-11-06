"""Knowledge base for RAG recommendation enhancement."""

from typing import Dict, List, Any, Optional
from collections import defaultdict


class RecommendationKnowledgeBase:
    """Knowledge base containing financial best practices and user context."""
    
    # Hardcoded financial best practices by category
    FINANCIAL_BEST_PRACTICES = {
        'Restaurant': {
            'tips': [
                "Average restaurant meal costs 3-5x more than home cooking",
                "Meal prepping can save $200-400/month for frequent diners",
                "Using coupons and happy hour specials can reduce dining costs by 20-30%",
                "Consider cooking at home 2-3 times per week to maintain variety while saving",
                "Local restaurants often have better value than chain restaurants"
            ],
            'alternatives': [
                "Meal prep services (costs 40-60% less than dining out)",
                "Local grocery stores with prepared meals section",
                "Cooking classes to improve home cooking skills",
                "Group cooking sessions with friends to share costs"
            ],
            'savings_strategies': [
                "Reduce dining frequency by 25% - saves roughly $150-300/month",
                "Switch to lunch specials instead of dinner - saves 30-40%",
                "Share meals or order appetizers as main course",
                "Use cashback credit cards for restaurants (3-5% back)"
            ]
        },
        'Grocery': {
            'tips': [
                "Buy generic/store brands for 20-30% savings",
                "Plan meals around weekly sales and seasonal produce",
                "Bulk buying non-perishables saves 15-25%",
                "Avoid shopping when hungry - reduces impulse purchases by 20%",
                "Use grocery store apps for digital coupons"
            ],
            'alternatives': [
                "Discount grocery stores (Aldi, Lidl) - 20-30% cheaper",
                "Warehouse clubs (Costco, Sam's) for bulk items",
                "Farmer's markets for fresh produce (often 10-15% cheaper)",
                "Online grocery delivery services with coupon stacking"
            ],
            'savings_strategies': [
                "Create shopping list and stick to it - reduces overspending by 15-20%",
                "Buy in-season produce - saves 30-50% vs out-of-season",
                "Use cashback apps (Ibotta, Rakuten) for additional 5-10% savings",
                "Meal plan to reduce food waste (saves 10-15% of grocery budget)"
            ]
        },
        'Coffee': {
            'tips': [
                "Coffee shop drinks cost $4-6 vs $0.50-1.00 at home",
                "Making coffee at home saves $80-120/month for daily drinkers",
                "Investing in quality coffee maker pays for itself in 2-3 months",
                "Bulk coffee beans from Costco or online retailers save 30-40%"
            ],
            'alternatives': [
                "Local coffee shops (often 20-30% cheaper than chains)",
                "Office coffee maker or workplace coffee",
                "Instant coffee or cold brew concentrate for convenience",
                "Coffee subscription services for home brewing"
            ],
            'savings_strategies': [
                "Reduce coffee shop visits by 50% - saves $40-60/month",
                "Make coffee at home 3-4 days per week",
                "Use reusable coffee cups for discounts (often 10% off)",
                "Bulk buy coffee beans and make at home - saves 70-80%"
            ]
        },
        'Shopping': {
            'tips': [
                "Wait 24-48 hours before making non-essential purchases",
                "Compare prices across multiple retailers before buying",
                "Use price tracking tools to buy at lowest price",
                "Buy during sales seasons (Black Friday, end-of-season clearance)",
                "Consider secondhand or refurbished items (30-50% savings)"
            ],
            'alternatives': [
                "Thrift stores and consignment shops",
                "Online marketplaces (Facebook Marketplace, Craigslist)",
                "Buy-nothing groups in your community",
                "Rental services for items used infrequently"
            ],
            'savings_strategies': [
                "Set monthly shopping budget and track spending",
                "Use cashback credit cards (1-5% back on purchases)",
                "Wait for sales or use browser extensions to find deals",
                "Buy quality items that last longer (reduces replacement costs)"
            ]
        },
        'Gas Station': {
            'tips': [
                "Use gas price tracking apps to find cheapest stations",
                "Fill up on weekdays (prices often 5-10% higher on weekends)",
                "Join gas station loyalty programs for discounts",
                "Consider fuel-efficient driving habits (saves 10-20% on gas)",
                "Use grocery store gas rewards programs"
            ],
            'alternatives': [
                "Gas stations away from highways (often 10-20% cheaper)",
                "Membership warehouses (Costco gas) - typically 10-15% cheaper",
                "Electric vehicle or public transportation for short trips",
                "Carpooling or ride-sharing to reduce frequency"
            ],
            'savings_strategies': [
                "Combine errands to reduce trips - saves 15-20% on gas",
                "Use credit cards with gas rewards (3-5% cashback)",
                "Maintain proper tire pressure (improves fuel economy by 3%)",
                "Drive at consistent speeds (saves 10-15% on gas)"
            ]
        },
        'Entertainment': {
            'tips': [
                "Look for free community events and activities",
                "Use library for books, movies, and digital content",
                "Share streaming service accounts with family",
                "Buy annual passes instead of daily tickets (saves 20-30%)",
                "Look for student, senior, or group discounts"
            ],
            'alternatives': [
                "Free streaming services (Tubi, Pluto TV, library apps)",
                "Library events and programs",
                "Community centers and local meetups",
                "Outdoor activities and parks (free or low-cost)"
            ],
            'savings_strategies': [
                "Cancel unused streaming subscriptions - saves $10-50/month",
                "Share subscriptions with family or friends",
                "Use free trial periods before committing",
                "Look for bundle deals (combine services for discount)"
            ]
        },
        'Pharmacy': {
            'tips': [
                "Use generic medications (often 80-90% cheaper)",
                "Compare prices at different pharmacies",
                "Use prescription discount cards (GoodRx, etc.)",
                "Ask about 90-day supplies (often cheaper per dose)",
                "Check if insurance covers mail-order pharmacy"
            ],
            'alternatives': [
                "Mail-order pharmacies (often 20-30% cheaper)",
                "Discount pharmacy chains",
                "Prescription discount programs",
                "Manufacturer assistance programs"
            ],
            'savings_strategies': [
                "Switch to generic medications - saves 70-90%",
                "Use prescription discount cards - saves 20-60%",
                "Buy in bulk (90-day supply) - saves 10-15%",
                "Compare pharmacy prices before filling prescriptions"
            ]
        },
        'General': {
            'tips': [
                "Track all expenses for 30 days to identify patterns",
                "Set specific savings goals to stay motivated",
                "Automate savings transfers to build emergency fund",
                "Review subscriptions monthly and cancel unused ones",
                "Use budgeting apps to monitor spending in real-time"
            ],
            'alternatives': [
                "Compare prices across multiple vendors",
                "Consider secondhand or refurbished items",
                "Look for free alternatives to paid services",
                "Join community groups for shared resources"
            ],
            'savings_strategies': [
                "Reduce frequency by 25% - saves 25% of category spending",
                "Find cheaper alternatives - saves 20-40% typically",
                "Set strict budget limits - prevents overspending",
                "Use cashback and rewards programs - 1-5% back"
            ]
        }
    }
    
    def __init__(self):
        """Initialize knowledge base."""
        pass
    
    def retrieve_relevant_knowledge(
        self,
        category: Optional[str] = None,
        recommendation_type: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Retrieve relevant knowledge for a recommendation.
        
        Args:
            category: Spending category (e.g., 'Restaurant', 'Coffee', 'Shopping')
            recommendation_type: Type of recommendation (e.g., 'reduce_spending', 'budget_optimization')
            user_context: User's financial context (spending patterns, income, etc.)
        
        Returns:
            Dictionary with relevant knowledge:
                - tips: List[str] - financial tips
                - alternatives: List[str] - alternative options
                - savings_strategies: List[str] - strategies to save money
                - user_context_summary: str - summary of user's situation
        """
        # Get category-specific knowledge
        category_key = category if category and category in self.FINANCIAL_BEST_PRACTICES else 'General'
        knowledge = self.FINANCIAL_BEST_PRACTICES.get(category_key, self.FINANCIAL_BEST_PRACTICES['General']).copy()
        
        # Add user context if available
        user_context_summary = ""
        if user_context:
            context_parts = []
            
            if user_context.get('monthly_spending'):
                context_parts.append(f"Monthly spending: ${user_context['monthly_spending']:,.0f}")
            
            if user_context.get('visits_per_week'):
                context_parts.append(f"Frequency: {user_context['visits_per_week']:.1f} times per week")
            
            if user_context.get('avg_spending_per_visit'):
                context_parts.append(f"Average per visit: ${user_context['avg_spending_per_visit']:,.2f}")
            
            if user_context.get('monthly_income'):
                income_ratio = (user_context.get('monthly_spending', 0) / user_context['monthly_income'] * 100) if user_context['monthly_income'] > 0 else 0
                context_parts.append(f"This represents {income_ratio:.1f}% of monthly income")
            
            if context_parts:
                user_context_summary = "User context: " + ", ".join(context_parts)
        
        knowledge['user_context_summary'] = user_context_summary
        
        return knowledge
    
    def extract_user_context_from_data(
        self,
        data_points: Dict[str, Any],
        features: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Extract user context from data points and features.
        
        Args:
            data_points: Data points used in recommendation
            features: User features from feature pipeline
        
        Returns:
            User context dictionary
        """
        context = {}
        
        # Extract spending information
        if 'monthly_spending' in data_points:
            context['monthly_spending'] = data_points['monthly_spending']
        elif 'category_monthly_spending' in data_points:
            context['monthly_spending'] = data_points['category_monthly_spending']
        
        if 'visits_per_week' in data_points:
            context['visits_per_week'] = data_points['visits_per_week']
        
        if 'avg_spending_per_visit' in data_points:
            context['avg_spending_per_visit'] = data_points['avg_spending_per_visit']
        
        # Extract income information
        if features and 'income' in features:
            income_features = features['income']
            context['monthly_income'] = income_features.get('average_monthly_income', 0)
            if context['monthly_income'] == 0:
                context['monthly_income'] = income_features.get('minimum_monthly_income', 0)
        
        # Extract category
        if 'category' in data_points:
            context['category'] = data_points['category']
        elif 'merchant_name' in data_points:
            # Try to infer category from merchant name
            merchant = data_points['merchant_name'].lower()
            if any(word in merchant for word in ['coffee', 'starbucks', 'dunkin']):
                context['category'] = 'Coffee'
            elif any(word in merchant for word in ['restaurant', 'cafe', 'dining']):
                context['category'] = 'Restaurant'
            elif any(word in merchant for word in ['grocery', 'supermarket', 'food']):
                context['category'] = 'Grocery'
            elif any(word in merchant for word in ['gas', 'fuel', 'shell', 'chevron']):
                context['category'] = 'Gas Station'
        
        return context

