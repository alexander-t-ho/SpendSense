"""Subscription category mapping for merchant categorization."""

from typing import Optional, Dict, List, Set


class SubscriptionCategoryMapper:
    """Map merchant names to subscription categories."""
    
    # Known merchant lists by category
    STREAMING_SERVICES = {
        'netflix', 'disney+', 'disney plus', 'hulu', 'spotify', 'apple music', 
        'youtube premium', 'youtube music', 'amazon prime video', 'paramount+', 
        'paramount plus', 'peacock', 'nbc peacock', 'hbo max', 'max', 'hbo',
        'showtime', 'starz', 'crunchyroll', 'funimation', 'vudu', 'amc+',
        'apple tv+', 'apple tv plus', 'cbs all access', 'philo', 'sling tv',
        'fubo', 'fubotv', 'directv', 'direct tv', 'dish network'
    }
    
    FITNESS_APPS = {
        'peloton', 'classpass', 'nike training', 'nike run club', 'strava',
        'myfitnesspal', 'fitbit', 'garmin', 'zwift', 'trainingpeaks',
        'planet fitness', '24 hour fitness', 'la fitness', 'equinox',
        'orange theory', 'crossfit', 'barry\'s bootcamp', 'soulcycle',
        'pure barre', 'pilates', 'yoga', 'yoga studio', 'yoga class'
    }
    
    CLOUD_STORAGE = {
        'dropbox', 'google drive', 'google one', 'icloud', 'onedrive',
        'microsoft 365', 'office 365', 'box', 'pcloud', 'mega',
        'amazon drive', 'backblaze', 'carbonite', 'idrive'
    }
    
    SOFTWARE_TOOLS = {
        'adobe', 'adobe creative cloud', 'adobe acrobat', 'photoshop',
        'illustrator', 'microsoft office', 'microsoft 365', 'office 365',
        'autodesk', 'autocad', 'sketch', 'figma', 'notion', 'evernote',
        'lastpass', '1password', 'dashlane', 'norton', 'mcafee',
        'kaspersky', 'avast', 'nordvpn', 'expressvpn', 'surfshark'
    }
    
    FOOD_DELIVERY = {
        'doordash', 'ubereats', 'uber eats', 'grubhub', 'postmates',
        'instacart', 'shipt', 'caviar', 'seamless', 'deliveroo'
    }
    
    NEWS_MEDIA = {
        'new york times', 'nytimes', 'wall street journal', 'wsj',
        'washington post', 'the economist', 'atlantic', 'new yorker',
        'bloomberg', 'financial times', 'ft.com', 'substack',
        'medium', 'patreon', 'podcast', 'spotify premium'
    }
    
    GAMING = {
        'xbox game pass', 'xbox live', 'playstation plus', 'ps plus',
        'nintendo switch online', 'steam', 'epic games', 'ubisoft',
        'ea play', 'origin access', 'blizzard', 'world of warcraft'
    }
    
    EDUCATION = {
        'coursera', 'udemy', 'linkedin learning', 'skillshare',
        'masterclass', 'khan academy', 'duolingo', 'babbel',
        'rosetta stone', 'grammarly', 'chegg', 'course hero'
    }
    
    # Category keyword patterns (for fuzzy matching)
    CATEGORY_KEYWORDS: Dict[str, List[str]] = {
        'streaming': ['streaming', 'tv', 'video', 'movie', 'series', 'channel'],
        'fitness': ['fitness', 'gym', 'workout', 'exercise', 'training', 'health', 'yoga', 'pilates'],
        'cloud_storage': ['cloud', 'storage', 'backup', 'drive', 'sync'],
        'software': ['software', 'app', 'tool', 'suite', 'subscription', 'license'],
        'food_delivery': ['delivery', 'food', 'restaurant', 'order', 'meal'],
        'news_media': ['news', 'magazine', 'journal', 'newspaper', 'media', 'publication'],
        'gaming': ['game', 'gaming', 'play', 'console', 'xbox', 'playstation'],
        'education': ['learning', 'course', 'education', 'training', 'tutorial', 'class']
    }
    
    @classmethod
    def categorize_subscription(cls, merchant_name: str) -> Optional[str]:
        """Categorize a subscription merchant by name.
        
        Args:
            merchant_name: Merchant name from transaction
            
        Returns:
            Category name (e.g., 'streaming', 'fitness', 'cloud_storage') or None
        """
        if not merchant_name:
            return None
        
        merchant_lower = merchant_name.lower().strip()
        
        # First, check exact matches in known merchant lists
        if merchant_lower in cls.STREAMING_SERVICES:
            return 'streaming'
        elif merchant_lower in cls.FITNESS_APPS:
            return 'fitness'
        elif merchant_lower in cls.CLOUD_STORAGE:
            return 'cloud_storage'
        elif merchant_lower in cls.SOFTWARE_TOOLS:
            return 'software'
        elif merchant_lower in cls.FOOD_DELIVERY:
            return 'food_delivery'
        elif merchant_lower in cls.NEWS_MEDIA:
            return 'news_media'
        elif merchant_lower in cls.GAMING:
            return 'gaming'
        elif merchant_lower in cls.EDUCATION:
            return 'education'
        
        # If no exact match, try keyword pattern matching
        for category, keywords in cls.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in merchant_lower:
                    return category
        
        # Check for partial matches (e.g., "Netflix" in "NETFLIX SUBSCRIPTION")
        for category, merchant_set in [
            ('streaming', cls.STREAMING_SERVICES),
            ('fitness', cls.FITNESS_APPS),
            ('cloud_storage', cls.CLOUD_STORAGE),
            ('software', cls.SOFTWARE_TOOLS),
            ('food_delivery', cls.FOOD_DELIVERY),
            ('news_media', cls.NEWS_MEDIA),
            ('gaming', cls.GAMING),
            ('education', cls.EDUCATION)
        ]:
            for known_merchant in merchant_set:
                if known_merchant in merchant_lower or merchant_lower in known_merchant:
                    return category
        
        return None
    
    @classmethod
    def get_category_duplicates(cls, merchant_list: List[str]) -> Dict[str, List[str]]:
        """Find merchants in the same category (potential duplicates).
        
        Args:
            merchant_list: List of merchant names
            
        Returns:
            Dictionary mapping category to list of merchants in that category
        """
        category_merchants: Dict[str, List[str]] = {}
        
        for merchant in merchant_list:
            category = cls.categorize_subscription(merchant)
            if category:
                if category not in category_merchants:
                    category_merchants[category] = []
                category_merchants[category].append(merchant)
        
        # Only return categories with 2+ merchants (duplicates)
        return {
            cat: merchants 
            for cat, merchants in category_merchants.items() 
            if len(merchants) >= 2
        }

