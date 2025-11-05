# Actionable Recommendations System

## Overview

The recommendation system has been updated to generate **actionable, data-driven recommendations** that cite specific user data points (e.g., "We noticed your Visa ending in 4523 is at 68% utilization..."). This replaces generic article-style recommendations with personalized, actionable insights.

## Key Features

### 1. **Actionable Recommendation Library**

A library of recommendation templates (`recommend/actionable_recommendations.py`) organized by persona with:
- **Templates**: Personalized text templates with placeholders for user data
- **Action Items**: Specific steps users can take
- **Expected Impact**: Quantified benefits of following the recommendation
- **Priority Levels**: HIGH, MEDIUM, LOW based on urgency
- **Data Requirements**: Lists of data points needed for personalization

### 2. **Data Extraction**

The `RecommendationDataExtractor` class extracts specific data points from user accounts:
- **Credit Card Data**: Card details, utilization, interest charges, payment calculations
- **Subscription Data**: Recurring subscriptions, monthly spend, potential savings
- **Income Data**: Variable income patterns, cash buffer, budgeting recommendations
- **Savings Data**: Current savings, growth rates, APY optimization opportunities

### 3. **ChatGPT Integration (Optional)**

The `ChatGPTPersonalizer` class uses OpenAI's ChatGPT API to:
- Generate more natural, personalized recommendation text
- Enhance action items with contextual suggestions
- Maintain a friendly, supportive tone
- Fall back to template formatting if API is unavailable

### 4. **Personalized Recommendations**

Recommendations now include:
- **Personalized Text**: Cites specific data (e.g., "Visa ending in 4523", "$3,400 of $5,000 limit")
- **Action Items**: Concrete steps with personalized amounts
- **Expected Impact**: Quantified benefits (e.g., "Save $87/month in interest")
- **Priority Badges**: Visual indicators for urgency

## Example Recommendation

**Before** (Article-style):
```
Title: "How to Pay Down Credit Card Debt"
Description: "Learn strategies for paying off credit card debt..."
Rationale: "We noticed you have high credit utilization..."
```

**After** (Actionable):
```
Title: "Reduce Credit Card Utilization"
Recommendation Text: "We noticed your Visa ending in 4523 is at 68% utilization 
($3,400 of $5,000 limit). Bringing this below 30% could improve your credit score 
and reduce interest charges of $87/month."

Action Steps:
- Make a payment of at least $1,900 to bring utilization below 30%
- Set up automatic payments to avoid interest charges
- Consider a balance transfer to a card with 0% APR if eligible

Expected Impact: "Improve credit score by 15-30 points, save $1,044/year in 
interest charges"
```

## Recommendation Types by Persona

### High Utilization Persona
- Reduce credit card utilization (with specific card details)
- Reduce monthly interest charges
- Stop making only minimum payments
- Address overdue payments

### Variable Income Budgeter
- Build emergency fund with variable income
- Create percent-based budget
- Manage irregular paychecks

### Subscription-Heavy Persona
- Audit and optimize subscriptions
- Negotiate better subscription rates

### Savings Builder
- Optimize savings APY
- Set specific savings goals

### Balanced/Stable Persona
- Optimize financial habits
- Explore investment opportunities

## Setup

### 1. Environment Variables (Optional)

For ChatGPT personalization, set:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

If not set, the system will use template formatting (still personalized with data).

### 2. Dependencies

New dependencies added to `requirements.txt`:
- `openai==1.3.0` (optional, for ChatGPT)
- `requests==2.31.0` (for API calls)

### 3. Usage

The recommendation generator automatically uses actionable recommendations:

```python
from recommend.generator import RecommendationGenerator

generator = RecommendationGenerator(db_session, db_path)
recommendations = generator.generate_recommendations(user_id, window_days=180)
```

The `education_items` will now contain actionable recommendations with:
- `recommendation_text`: Personalized recommendation text
- `action_items`: List of action steps
- `expected_impact`: Expected outcomes
- `priority`: Priority level (high/medium/low)

## Frontend Display

The frontend (`ui/src/components/RecommendationsSection.tsx`) has been updated to display:
- Personalized recommendation text in a highlighted box
- Action items as a bulleted list
- Expected impact in a green success box
- Priority badges (red for high, yellow for medium, gray for low)

## Backward Compatibility

The system maintains backward compatibility:
- Old article-style recommendations still work (if `recommendation_text` is not present)
- Falls back gracefully if data extraction fails
- Template formatting used if ChatGPT is unavailable

## Data Requirements

Each recommendation template specifies required data points. The system:
1. Extracts available data for the user's persona
2. Filters recommendations based on data availability (at least 50% of required data)
3. Uses default values for missing data points
4. Still generates recommendations even with incomplete data

## Future Enhancements

Potential improvements:
- Add more recommendation types per persona
- A/B test ChatGPT vs. template formatting
- Add recommendation effectiveness tracking
- Support for multi-card recommendations
- Dynamic recommendation prioritization based on user behavior


