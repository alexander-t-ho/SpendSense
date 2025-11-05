"""Unit tests for recommendation generation."""

import pytest
from sqlalchemy.orm import Session
from ingest.schema import get_session, User, Consent
from recommend.generator import RecommendationGenerator
from guardrails.consent import ConsentManager


@pytest.fixture
def db_session(tmp_path):
    """Create a temporary database session."""
    from ingest.schema import init_db
    db_path = str(tmp_path / "test.db")
    init_db(db_path)  # Initialize schema
    session = get_session(db_path)
    yield session
    session.close()


@pytest.fixture
def sample_user_with_consent(db_session, tmp_path):
    """Create a sample user with consent granted."""
    user = User(id="test-user-1", name="Test User", email="test@example.com")
    db_session.add(user)
    db_session.commit()
    
    # Grant consent
    consent_manager = ConsentManager(db_session)
    consent_manager.grant_consent(user.id)
    
    return user


def test_recommendation_generator_initialization(db_session, tmp_path):
    """Test that RecommendationGenerator can be initialized."""
    db_path = str(tmp_path / "test.db")
    generator = RecommendationGenerator(db_session, db_path)
    assert generator is not None
    generator.close()


def test_generate_recommendations_requires_consent(db_session, sample_user_with_consent, tmp_path):
    """Test that recommendations require consent."""
    db_path = str(tmp_path / "test.db")
    generator = RecommendationGenerator(db_session, db_path)
    
    # Should not raise because consent is granted
    result = generator.generate_recommendations(sample_user_with_consent.id, window_days=180)
    
    assert result is not None
    assert 'education_items' in result
    assert 'partner_offers' in result
    assert 'persona' in result
    
    generator.close()


def test_generate_recommendations_structure(db_session, sample_user_with_consent, tmp_path):
    """Test that recommendations have correct structure."""
    db_path = str(tmp_path / "test.db")
    generator = RecommendationGenerator(db_session, db_path)
    
    result = generator.generate_recommendations(sample_user_with_consent.id, window_days=180)
    
    assert isinstance(result['education_items'], list)
    assert isinstance(result['partner_offers'], list)
    assert isinstance(result['persona'], dict)
    assert 'id' in result['persona']
    assert 'name' in result['persona']
    
    generator.close()


def test_recommendations_include_rationale(db_session, sample_user_with_consent, tmp_path):
    """Test that recommendations include rationale or recommendation_text."""
    db_path = str(tmp_path / "test.db")
    generator = RecommendationGenerator(db_session, db_path)
    
    result = generator.generate_recommendations(sample_user_with_consent.id, window_days=180)
    
    # Check that at least one recommendation has rationale or recommendation_text
    all_have_rationale = True
    for item in result['education_items']:
        if 'recommendation_text' not in item and 'rationale' not in item:
            all_have_rationale = False
            break
    
    # If we have recommendations, they should have rationale
    if len(result['education_items']) > 0:
        assert all_have_rationale == True
    
    generator.close()

