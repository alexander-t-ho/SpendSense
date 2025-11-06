"""Test RAG pipeline via API endpoint."""

import os
import sys
import requests
import json
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ingest.schema import get_session, User, Recommendation


def test_via_api():
    """Test RAG pipeline via API endpoint."""
    print("\n" + "="*60)
    print("TESTING RAG PIPELINE VIA API")
    print("="*60)
    
    # Check if backend is running
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        print("✓ Backend server is running")
    except requests.exceptions.ConnectionError:
        print("❌ Backend server is not running!")
        print("   Please start the backend server first:")
        print("   ./start_backend.sh")
        return
    except Exception as e:
        print(f"❌ Error connecting to backend: {e}")
        return
    
    # Get a user from database
    session = get_session()
    try:
        user = session.query(User).first()
        if not user:
            print("❌ No users found in database. Please add users first.")
            return
        
        user_id = user.id
        print(f"✓ Using user: {user.email} (ID: {user_id})")
    finally:
        session.close()
    
    # Check API key status
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key:
        print(f"✓ OPENAI_API_KEY is set (RAG enhancement will be enabled)")
    else:
        print("⚠️  OPENAI_API_KEY not set (RAG enhancement will be disabled)")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
    
    # Generate recommendations
    print(f"\n📝 Generating recommendations for user {user_id}...")
    print("   This may take 30-60 seconds if RAG is enabled...")
    
    try:
        response = requests.post(
            f"http://localhost:8000/api/recommendations/generate/{user_id}",
            params={"window_days": 180, "num_recommendations": 8},
            timeout=120  # Longer timeout for RAG processing
        )
        
        if response.status_code != 200:
            print(f"❌ Error generating recommendations: {response.status_code}")
            print(f"   Response: {response.text}")
            return
        
        result = response.json()
        print(f"✓ Generated {result.get('count', 0)} recommendations")
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out (this might happen if RAG is processing)")
        print("   Try checking the backend logs or increasing timeout")
        return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Fetch the generated recommendations
    print("\n📊 Analyzing generated recommendations...")
    session = get_session()
    try:
        recommendations = session.query(Recommendation).filter(
            Recommendation.user_id == user_id,
            Recommendation.approved == False
        ).order_by(Recommendation.created_at.desc()).limit(10).all()
        
        print(f"✓ Found {len(recommendations)} recent recommendations")
        
        from recommend.validator import RecommendationValidator
        validator = RecommendationValidator()
        
        valid_count = 0
        enhanced_count = 0
        total_action_items = 0
        
        print("\n" + "-"*60)
        print("RECOMMENDATION ANALYSIS")
        print("-"*60)
        
        for i, rec in enumerate(recommendations[:5], 1):  # Show first 5
            validation = validator.validate({
                'title': rec.title,
                'recommendation_text': rec.description or '',
                'action_items': rec.action_items or [],
                'expected_impact': rec.expected_impact or ''
            })
            
            action_items = rec.action_items or []
            num_items = len(action_items) if isinstance(action_items, list) else 0
            
            status_icon = "✅" if validation['status'] == 'valid' else "⚠️"
            
            print(f"\n{i}. {status_icon} {rec.title}")
            print(f"   Status: {validation['status']} (score: {validation['quality_score']:.2f})")
            print(f"   Action Items: {num_items}")
            print(f"   Priority: {rec.priority}")
            
            if validation['issues']:
                print(f"   Issues: {', '.join(validation['issues'][:2])}")
            
            if num_items > 0:
                print(f"   First action: {action_items[0][:70]}...")
            
            if validation['status'] == 'valid':
                valid_count += 1
            else:
                enhanced_count += 1
            
            total_action_items += num_items
        
        print("\n" + "-"*60)
        print("SUMMARY")
        print("-"*60)
        print(f"Total recommendations: {len(recommendations)}")
        print(f"Valid: {valid_count}")
        print(f"Needs enhancement: {enhanced_count}")
        print(f"Average action items: {total_action_items / len(recommendations):.1f}")
        
        # Check for common issues
        issues_found = []
        for rec in recommendations:
            text = (rec.description or "") + " " + (rec.expected_impact or "")
            if '$0' in text or '{category}' in text or '{merchant_name}' in text:
                issues_found.append(rec.title)
        
        if issues_found:
            print(f"\n⚠️  Recommendations with placeholders or $0 values: {len(issues_found)}")
            if api_key:
                print("   This might indicate RAG enhancement is not working properly.")
            else:
                print("   Set OPENAI_API_KEY to enable RAG enhancement and fix these.")
        else:
            print("\n✅ No placeholders or $0 values found!")
        
        # Check action items count
        low_action_items = [rec for rec in recommendations 
                           if len(rec.action_items or []) < 3]
        if low_action_items:
            print(f"\n⚠️  Recommendations with <3 action items: {len(low_action_items)}")
            if api_key:
                print("   RAG should have enhanced these to have 3-5 items.")
        else:
            print("\n✅ All recommendations have 3+ action items!")
        
    finally:
        session.close()
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("1. Review recommendations in the admin dashboard")
    print("2. Approve recommendations to see them on user dashboard")
    print("3. Check that enhanced recommendations have no $0 values")
    print("4. Verify all recommendations have 3-5 actionable options")


if __name__ == "__main__":
    test_via_api()

