"""Integration tests for end-to-end flows."""

import pytest
from sqlalchemy.orm import Session
from ingest.schema import get_session, User, Consent
from guardrails.consent import ConsentManager
from recommend.generator import RecommendationGenerator
from personas.assigner import PersonaAssigner


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
def sample_user_with_consent(db_session):
    """Create a sample user with consent."""
    user = User(id="test-user-1", name="Test User", email="test@example.com")
    db_session.add(user)
    db_session.commit()
    
    consent_manager = ConsentManager(db_session)
    consent_manager.grant_consent(user.id)
    
    return user


def test_consent_to_recommendation_flow(db_session, sample_user_with_consent, tmp_path):
    """Test end-to-end flow: consent -> persona assignment -> recommendations."""
    db_path = str(tmp_path / "test.db")
    
    # Verify consent
    consent_manager = ConsentManager(db_session)
    consent = consent_manager.get_consent(sample_user_with_consent.id)
    assert consent is not None
    assert consent.consented == True
    
    # Assign persona
    persona_assigner = PersonaAssigner(db_session, db_path)
    persona_assignment = persona_assigner.assign_persona(sample_user_with_consent.id, 180)
    assert 'primary_persona' in persona_assignment
    persona_assigner.close()
    
    # Generate recommendations
    generator = RecommendationGenerator(db_session, db_path)
    recommendations = generator.generate_recommendations(sample_user_with_consent.id, window_days=180)
    assert recommendations is not None
    assert 'persona' in recommendations
    assert 'education_items' in recommendations
    generator.close()


def test_recommendations_include_persona_info(db_session, sample_user_with_consent, tmp_path):
    """Test that recommendations include persona information."""
    db_path = str(tmp_path / "test.db")
    generator = RecommendationGenerator(db_session, db_path)
    
    recommendations = generator.generate_recommendations(sample_user_with_consent.id, window_days=180)
    
    persona_info = recommendations['persona']
    assert 'id' in persona_info
    assert 'name' in persona_info
    assert 'risk_level' in persona_info
    
    generator.close()

