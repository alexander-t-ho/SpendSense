"""Spending pattern detection using correlation analysis for days of week and frequent merchants."""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ingest.schema import User, Account, Transaction


class SpendingPatternAnalyzer:
    """Analyze spending patterns by day of week and frequent merchant locations."""
    
    def __init__(self, db_session: Session):
        """Initialize analyzer.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
    
    def analyze_day_of_week_spending(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        window_days: int = 180
    ) -> Dict[str, Any]:
        """Analyze spending patterns by day of week using correlation analysis.
        
        Args:
            user_id: User ID
            start_date: Analysis start date (optional)
            end_date: Analysis end date (optional)
            window_days: Number of days to analyze if dates not provided
        
        Returns:
            Dictionary with day-of-week spending patterns and insights
        """
        # Set date range
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=window_days)
        
        # Get all transactions
        transactions = self.db.query(Transaction).join(Account).filter(
            and_(
                Account.user_id == user_id,
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.amount < 0  # Only spending (negative amounts)
            )
        ).all()
        
        if not transactions:
            return {
                "error": "No spending transactions found",
                "user_id": user_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        
        # Create DataFrame with day of week and spending amounts
        data = []
        for txn in transactions:
            day_of_week = txn.date.weekday()  # 0=Monday, 6=Sunday
            day_name = txn.date.strftime('%A')
            data.append({
                'date': txn.date,
                'day_of_week': day_of_week,
                'day_name': day_name,
                'amount': abs(txn.amount),
                'transaction_count': 1
            })
        
        df = pd.DataFrame(data)
        
        # Aggregate by day of week
        day_stats = df.groupby(['day_of_week', 'day_name']).agg({
            'amount': ['sum', 'mean', 'count'],
        }).reset_index()
        
        day_stats.columns = ['day_of_week', 'day_name', 'total_spending', 'avg_spending', 'transaction_count']
        day_stats = day_stats.sort_values('day_of_week')
        
        # Calculate correlation with day of week (0-6)
        df['day_of_week_numeric'] = df['day_of_week']
        correlation = df['amount'].corr(df['day_of_week_numeric'])
        
        # Find highest spending days
        highest_spending_day = day_stats.loc[day_stats['total_spending'].idxmax()]
        lowest_spending_day = day_stats.loc[day_stats['total_spending'].idxmin()]
        
        # Calculate percentage of total spending by day
        total_spending = day_stats['total_spending'].sum()
        day_stats['spending_percentage'] = (day_stats['total_spending'] / total_spending * 100).round(2) if total_spending > 0 else 0
        
        # Identify patterns (e.g., weekend vs weekday)
        weekend_days = [5, 6]  # Saturday, Sunday
        weekday_days = [0, 1, 2, 3, 4]  # Monday-Friday
        
        weekend_spending = day_stats[day_stats['day_of_week'].isin(weekend_days)]['total_spending'].sum()
        weekday_spending = day_stats[day_stats['day_of_week'].isin(weekday_days)]['total_spending'].sum()
        
        weekend_share = (weekend_spending / total_spending * 100) if total_spending > 0 else 0
        weekday_share = (weekday_spending / total_spending * 100) if total_spending > 0 else 0
        
        # Convert to dict for safe access
        day_stats_dict = day_stats.to_dict('records')
        
        return {
            "user_id": user_id,
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days_analyzed": (end_date - start_date).days
            },
            "day_of_week_stats": day_stats_dict,
            "insights": {
                "correlation_with_day": round(correlation, 3) if not pd.isna(correlation) else 0,
                "highest_spending_day": {
                    "day": highest_spending_day['day_name'],
                    "total_spending": round(highest_spending_day['total_spending'], 2),
                    "avg_spending": round(highest_spending_day['avg_spending'], 2),
                    "transaction_count": int(highest_spending_day['transaction_count']),
                    "percentage_of_total": round(highest_spending_day.get('spending_percentage', 0), 2)
                },
                "lowest_spending_day": {
                    "day": lowest_spending_day['day_name'],
                    "total_spending": round(lowest_spending_day['total_spending'], 2),
                    "avg_spending": round(lowest_spending_day['avg_spending'], 2),
                    "transaction_count": int(lowest_spending_day['transaction_count']),
                    "percentage_of_total": round(lowest_spending_day.get('spending_percentage', 0), 2)
                },
                "weekend_vs_weekday": {
                    "weekend_spending": round(weekend_spending, 2),
                    "weekday_spending": round(weekday_spending, 2),
                    "weekend_share_percent": round(weekend_share, 2),
                    "weekday_share_percent": round(weekday_share, 2)
                }
            },
            "total_transactions": len(transactions),
            "total_spending": round(total_spending, 2)
        }
    
    def detect_frequent_purchase_locations(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        window_days: int = 180,
        min_occurrences: int = 3,
        min_total_spend: float = 50.0
    ) -> Dict[str, Any]:
        """Detect frequent purchase locations (merchants) beyond subscriptions.
        
        Args:
            user_id: User ID
            start_date: Analysis start date (optional)
            end_date: Analysis end date (optional)
            window_days: Number of days to analyze if dates not provided
            min_occurrences: Minimum number of visits to be considered frequent
            min_total_spend: Minimum total spending at location
        
        Returns:
            Dictionary with frequent merchant patterns and insights
        """
        # Set date range
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=window_days)
        
        # Get all transactions
        transactions = self.db.query(Transaction).join(Account).filter(
            and_(
                Account.user_id == user_id,
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.amount < 0  # Only spending
            )
        ).all()
        
        if not transactions:
            return {
                "error": "No spending transactions found",
                "user_id": user_id
            }
        
        # Group by merchant
        merchant_data = defaultdict(lambda: {
            'transactions': [],
            'total_spending': 0,
            'first_visit': None,
            'last_visit': None,
            'days_of_week': [],
            'amounts': []
        })
        
        for txn in transactions:
            merchant = txn.merchant_name or "Unknown"
            amount = abs(txn.amount)
            
            merchant_data[merchant]['transactions'].append(txn)
            merchant_data[merchant]['total_spending'] += amount
            merchant_data[merchant]['days_of_week'].append(txn.date.weekday())
            merchant_data[merchant]['amounts'].append(amount)
            
            if not merchant_data[merchant]['first_visit'] or txn.date < merchant_data[merchant]['first_visit']:
                merchant_data[merchant]['first_visit'] = txn.date
            if not merchant_data[merchant]['last_visit'] or txn.date > merchant_data[merchant]['last_visit']:
                merchant_data[merchant]['last_visit'] = txn.date
        
        # Filter and analyze frequent merchants
        frequent_merchants = []
        for merchant, data in merchant_data.items():
            occurrences = len(data['transactions'])
            
            if occurrences >= min_occurrences and data['total_spending'] >= min_total_spend:
                # Calculate visit frequency
                days_active = (data['last_visit'] - data['first_visit']).days + 1
                visits_per_week = (occurrences / days_active) * 7 if days_active > 0 else 0
                
                # Calculate average spending per visit
                avg_spending = data['total_spending'] / occurrences
                
                # Find most common day of week
                day_counts = pd.Series(data['days_of_week']).value_counts()
                most_common_day = day_counts.index[0] if len(day_counts) > 0 else None
                day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                most_common_day_name = day_names[most_common_day] if most_common_day is not None else None
                
                # Calculate spending consistency (coefficient of variation)
                amounts_std = np.std(data['amounts'])
                amounts_mean = np.mean(data['amounts'])
                consistency = (1 - (amounts_std / amounts_mean)) * 100 if amounts_mean > 0 else 0
                
                frequent_merchants.append({
                    'merchant_name': merchant,
                    'occurrences': occurrences,
                    'total_spending': round(data['total_spending'], 2),
                    'avg_spending_per_visit': round(avg_spending, 2),
                    'visits_per_week': round(visits_per_week, 2),
                    'first_visit': data['first_visit'].isoformat(),
                    'last_visit': data['last_visit'].isoformat(),
                    'days_active': days_active,
                    'most_common_day': most_common_day_name,
                    'spending_consistency_percent': round(consistency, 2),
                    'category': self._categorize_merchant(merchant)
                })
        
        # Sort by total spending (descending)
        frequent_merchants.sort(key=lambda x: x['total_spending'], reverse=True)
        
        # Calculate correlations
        correlations = self._calculate_merchant_correlations(frequent_merchants, transactions)
        
        return {
            "user_id": user_id,
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days_analyzed": (end_date - start_date).days
            },
            "frequent_merchants": frequent_merchants,
            "summary": {
                "total_frequent_locations": len(frequent_merchants),
                "total_spending_at_frequent_locations": round(sum(m['total_spending'] for m in frequent_merchants), 2),
                "top_category": self._get_top_category(frequent_merchants),
                "correlations": correlations
            },
            "total_transactions_analyzed": len(transactions)
        }
    
    def _categorize_merchant(self, merchant_name: str) -> str:
        """Categorize merchant based on name patterns.
        
        Args:
            merchant_name: Merchant name
        
        Returns:
            Category name
        """
        name_lower = merchant_name.lower()
        
        # Grocery stores
        if any(word in name_lower for word in ['grocery', 'food', 'supermarket', 'whole foods', 'kroger', 'safeway', 'walmart']):
            return "Grocery"
        
        # Restaurants
        if any(word in name_lower for word in ['restaurant', 'cafe', 'coffee', 'starbucks', 'mcdonalds', 'pizza', 'dining']):
            return "Restaurant"
        
        # Gas stations
        if any(word in name_lower for word in ['gas', 'fuel', 'shell', 'chevron', 'exxon', 'bp']):
            return "Gas Station"
        
        # Entertainment
        if any(word in name_lower for word in ['theater', 'movie', 'cinema', 'netflix', 'spotify', 'entertainment']):
            return "Entertainment"
        
        # Shopping
        if any(word in name_lower for word in ['store', 'shop', 'retail', 'amazon', 'target', 'mall']):
            return "Shopping"
        
        # Pharmacy
        if any(word in name_lower for word in ['pharmacy', 'drug', 'cvs', 'walgreens']):
            return "Pharmacy"
        
        # Subscription services (already detected separately, but include here)
        if any(word in name_lower for word in ['subscription', 'membership', 'premium']):
            return "Subscription"
        
        return "Other"
    
    def _get_top_category(self, merchants: List[Dict]) -> Optional[str]:
        """Get the top spending category.
        
        Args:
            merchants: List of merchant dictionaries
        
        Returns:
            Top category name or None
        """
        if not merchants:
            return None
        
        category_totals = defaultdict(float)
        for merchant in merchants:
            category_totals[merchant['category']] += merchant['total_spending']
        
        if category_totals:
            return max(category_totals.items(), key=lambda x: x[1])[0]
        return None
    
    def _calculate_merchant_correlations(
        self,
        merchants: List[Dict],
        transactions: List[Transaction]
    ) -> Dict[str, Any]:
        """Calculate correlations between merchant visits and spending patterns.
        
        Args:
            merchants: List of frequent merchants
            transactions: All transactions
        
        Returns:
            Correlation insights
        """
        if len(merchants) < 2:
            return {"message": "Insufficient merchants for correlation analysis"}
        
        # Create time series data
        df = pd.DataFrame([
            {
                'date': txn.date,
                'merchant': txn.merchant_name or "Unknown",
                'amount': abs(txn.amount)
            }
            for txn in transactions
        ])
        
        if df.empty:
            return {"message": "No transaction data for correlation"}
        
        # Group by date and merchant
        daily_merchant_spending = df.groupby(['date', 'merchant'])['amount'].sum().unstack(fill_value=0)
        
        # Calculate correlations between top merchants
        top_merchants = [m['merchant_name'] for m in merchants[:5]]  # Top 5
        available_merchants = [m for m in top_merchants if m in daily_merchant_spending.columns]
        
        if len(available_merchants) < 2:
            return {"message": "Insufficient overlapping merchants for correlation"}
        
        correlations = {}
        for i, merchant1 in enumerate(available_merchants):
            for merchant2 in available_merchants[i+1:]:
                if merchant1 in daily_merchant_spending.columns and merchant2 in daily_merchant_spending.columns:
                    corr = daily_merchant_spending[merchant1].corr(daily_merchant_spending[merchant2])
                    if not pd.isna(corr):
                        correlations[f"{merchant1} vs {merchant2}"] = round(corr, 3)
        
        return {
            "merchant_correlations": correlations,
            "interpretation": "Positive correlation suggests merchants visited together; negative suggests alternatives"
        }

