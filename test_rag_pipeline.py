"""Test script for RAG pipeline validation and enhancement."""

import os
import sys
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ingest.schema import get_session, User
from recommend.validator import RecommendationValidator
from recommend.knowledge_base import RecommendationKnowledgeBase
from recommend.rag_enhancer import RAGEnhancementEngine
from recommend.persona_recommendation_generator import PersonaRecommendationGenerator


def test_validator():
    """Test the recommendation validator."""
    print("\n" + "="*60)
    print("TEST 1: Recommendation Validator")
    print("="*60)
    
    validator = RecommendationValidator()
    
    # Test 1: Valid recommendation
    valid_rec = {
        'title': 'Test Recommendation',
        'recommendation_text': 'You spend $150/month on coffee. Consider reducing to save money.',
        'action_items': [
            'Option 1: Reduce visits by 25% - Save $37.50/month',
            'Option 2: Switch to local coffee shop - Save $30/month',
            'Option 3: Make coffee at home - Save $120/month'
        ],
        'expected_impact': 'Save up to $120/month by reducing coffee spending'
    }
    
    result = validator.validate(valid_rec)
    print(f"✓ Valid recommendation: {result['status']} (score: {result['quality_score']:.2f})")
    assert result['status'] == 'valid', f"Expected 'valid', got {result['status']}"
    
    # Test 2: Recommendation with $0 values
    invalid_rec = {
        'title': 'Test Recommendation',
        'recommendation_text': 'You spend $0/month on this category.',
        'action_items': ['Option 1: Save $0 by doing X'],
        'expected_impact': 'Save $0/year'
    }
    
    result = validator.validate(invalid_rec)
    print(f"✓ Invalid recommendation with $0: {result['status']} (score: {result['quality_score']:.2f})")
    print(f"  Issues: {result['issues']}")
    assert result['status'] != 'valid', "Should not be valid"
    
    # Test 3: Recommendation with insufficient action items
    few_items_rec = {
        'title': 'Test Recommendation',
        'recommendation_text': 'You spend $100/month.',
        'action_items': ['Option 1: Do something'],
        'expected_impact': 'Save money'
    }
    
    result = validator.validate(few_items_rec)
    print(f"✓ Recommendation with <3 items: {result['status']} (score: {result['quality_score']:.2f})")
    assert len(result['issues']) > 0, "Should have issues"
    
    print("✅ Validator tests passed!\n")


def test_knowledge_base():
    """Test the knowledge base."""
    print("\n" + "="*60)
    print("TEST 2: Knowledge Base")
    print("="*60)
    
    kb = RecommendationKnowledgeBase()
    
    # Test retrieving knowledge for Coffee category
    knowledge = kb.retrieve_relevant_knowledge(category='Coffee')
    print(f"✓ Retrieved knowledge for 'Coffee' category:")
    print(f"  - Tips: {len(knowledge.get('tips', []))} items")
    print(f"  - Alternatives: {len(knowledge.get('alternatives', []))} items")
    print(f"  - Strategies: {len(knowledge.get('savings_strategies', []))} items")
    assert len(knowledge.get('tips', [])) > 0, "Should have tips"
    
    # Test with user context
    user_context = {
        'monthly_spending': 150,
        'visits_per_week': 4,
        'avg_spending_per_visit': 5.50,
        'monthly_income': 3000
    }
    
    knowledge = kb.retrieve_relevant_knowledge(
        category='Coffee',
        user_context=user_context
    )
    print(f"✓ Knowledge with user context: {knowledge.get('user_context_summary', 'N/A')}")
    assert 'user_context_summary' in knowledge, "Should have user context summary"
    
    # Test extracting context from data points
    data_points = {
        'merchant_name': 'Starbucks',
        'monthly_spending': 150,
        'visits_per_week': 4,
        'avg_spending_per_visit': 5.50
    }
    
    context = kb.extract_user_context_from_data(data_points)
    print(f"✓ Extracted context: {context}")
    assert context.get('category') == 'Coffee', "Should infer category from merchant name"
    
    print("✅ Knowledge base tests passed!\n")


def test_rag_enhancer_without_api():
    """Test RAG enhancer without API key (should fallback gracefully)."""
    print("\n" + "="*60)
    print("TEST 3: RAG Enhancer (Without API Key)")
    print("="*60)
    
    # Temporarily remove API key if set
    original_key = os.environ.get('OPENAI_API_KEY')
    if 'OPENAI_API_KEY' in os.environ:
        del os.environ['OPENAI_API_KEY']
    
    enhancer = RAGEnhancementEngine()
    
    test_rec = {
        'title': 'Reduce Coffee Spending',
        'recommendation_text': 'You spend $0/month on coffee.',
        'action_items': ['Option 1: Save $0'],
        'expected_impact': 'Save $0/year'
    }
    
    # Should return original recommendation when API key is missing
    enhanced = enhancer.enhance_recommendation(test_rec)
    print(f"✓ Enhancer handles missing API key gracefully")
    assert enhanced == test_rec, "Should return original when API key missing"
    
    # Restore API key if it was set
    if original_key:
        os.environ['OPENAI_API_KEY'] = original_key
    
    print("✅ RAG enhancer (without API) tests passed!\n")


def test_rag_enhancer_with_api():
    """Test RAG enhancer with API key."""
    print("\n" + "="*60)
    print("TEST 4: RAG Enhancer (With API Key)")
    print("="*60)
    
    api_key = os.environ.get('OPENAI_API_KEY')
    
    if not api_key:
        print("⚠️  OPENAI_API_KEY not set. Skipping API tests.")
        print("   Set OPENAI_API_KEY environment variable to test with OpenAI API.")
        return
    
    enhancer = RAGEnhancementEngine(api_key=api_key)
    
    if not enhancer.enabled:
        print("⚠️  RAG enhancer is not enabled. Skipping API tests.")
        return
    
    # Test recommendation with $0 values
    test_rec = {
        'title': 'Reduce Category Spending',
        'recommendation_text': 'You spend $0/month in this category. Consider reducing spending.',
        'action_items': ['Option 1: Do something'],
        'expected_impact': 'Save $0/year'
    }
    
    data_points = {
        'category': 'Restaurant',
        'category_monthly_spending': 300,
        'category_annual_spending': 3600
    }
    
    print("Calling RAG enhancer (this may take 10-30 seconds)...")
    try:
        enhanced = enhancer.enhance_recommendation(
            test_rec,
            data_points=data_points
        )
        
        print(f"✓ Enhanced recommendation:")
        print(f"  Title: {enhanced.get('title')}")
        print(f"  Text: {enhanced.get('recommendation_text', '')[:100]}...")
        print(f"  Action Items: {len(enhanced.get('action_items', []))} items")
        print(f"  Expected Impact: {enhanced.get('expected_impact', '')[:80]}...")
        
        # Verify enhancement
        assert len(enhanced.get('action_items', [])) >= 3, "Should have at least 3 action items"
        assert '$0' not in enhanced.get('recommendation_text', ''), "Should not have $0 in text"
        assert '$0' not in str(enhanced.get('action_items', [])), "Should not have $0 in action items"
        
        print("✅ RAG enhancer (with API) tests passed!\n")
        
    except Exception as e:
        print(f"❌ Error during RAG enhancement: {e}")
        print("   This might be due to API rate limits or network issues.")
        raise


def test_full_pipeline():
    """Test the full recommendation generation pipeline."""
    print("\n" + "="*60)
    print("TEST 5: Full Recommendation Pipeline")
    print("="*60)
    
    session = get_session()
    
    try:
        # Get a user from the database
        user = session.query(User).first()
        
        if not user:
            print("⚠️  No users found in database. Skipping full pipeline test.")
            print("   Please add users to the database first.")
            return
        
        print(f"✓ Testing with user: {user.email} (ID: {user.id})")
        
        # Initialize generator
        generator = PersonaRecommendationGenerator(session, "data/spendsense.db")
        
        # Generate recommendations
        print("Generating recommendations (this may take a while)...")
        recommendations = generator.generate_and_store_recommendations(
            user_id=user.id,
            window_days=180,
            num_recommendations=8
        )
        
        print(f"✓ Generated {len(recommendations)} recommendations")
        
        # Validate recommendations
        validator = RecommendationValidator()
        valid_count = 0
        enhanced_count = 0
        
        for rec in recommendations:
            validation = validator.validate(rec)
            if validation['status'] == 'valid':
                valid_count += 1
            else:
                enhanced_count += 1
                print(f"  - {rec.get('title')}: {validation['status']} ({len(validation['issues'])} issues)")
        
        print(f"✓ Validation results:")
        print(f"  - Valid: {valid_count}")
        print(f"  - Enhanced/Needs improvement: {enhanced_count}")
        
        # Check action items
        for rec in recommendations:
            action_items = rec.get('action_items', [])
            print(f"  - {rec.get('title')}: {len(action_items)} action items")
            assert len(action_items) >= 3, f"Should have at least 3 action items, got {len(action_items)}"
        
        print("✅ Full pipeline tests passed!\n")
        
        generator.close()
        
    except Exception as e:
        print(f"❌ Error during full pipeline test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("RAG PIPELINE TEST SUITE")
    print("="*60)
    
    try:
        # Test 1: Validator
        test_validator()
        
        # Test 2: Knowledge Base
        test_knowledge_base()
        
        # Test 3: RAG Enhancer without API
        test_rag_enhancer_without_api()
        
        # Test 4: RAG Enhancer with API (if key is set)
        test_rag_enhancer_with_api()
        
        # Test 5: Full pipeline
        test_full_pipeline()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED")
        print("="*60)
        print("\nNext steps:")
        print("1. Set OPENAI_API_KEY environment variable to test with real API")
        print("2. Generate recommendations for users via the API")
        print("3. Check that recommendations have 3-5 actionable options")
        print("4. Verify no $0 values appear in recommendations")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

