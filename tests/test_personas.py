"""Unit tests for persona assignment."""

import pytest
from sqlalchemy.orm import Session
from ingest.schema import get_session, User
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
def sample_user(db_session):
    """Create a sample user for testing."""
    user = User(id="test-user-1", name="Test User", email="test@example.com")
    db_session.add(user)
    db_session.commit()
    return user


def test_persona_assigner_initialization(db_session, tmp_path):
    """Test that PersonaAssigner can be initialized."""
    db_path = str(tmp_path / "test.db")
    assigner = PersonaAssigner(db_session, db_path)
    assert assigner is not None
    assigner.close()


def test_assign_persona_returns_dict(db_session, sample_user, tmp_path):
    """Test that assign_persona returns a dictionary."""
    db_path = str(tmp_path / "test.db")
    assigner = PersonaAssigner(db_session, db_path)
    
    result = assigner.assign_persona(sample_user.id, 180)
    
    assert isinstance(result, dict)
    assert 'primary_persona' in result
    assert 'primary_persona_percentage' in result
    
    assigner.close()


def test_assign_persona_has_primary_persona(db_session, sample_user, tmp_path):
    """Test that assigned persona is valid."""
    from personas.definitions import get_persona_by_id
    
    db_path = str(tmp_path / "test.db")
    assigner = PersonaAssigner(db_session, db_path)
    
    result = assigner.assign_persona(sample_user.id, 180)
    primary_persona_id = result['primary_persona']
    
    # Verify persona exists
    persona = get_persona_by_id(primary_persona_id)
    assert persona is not None
    
    assigner.close()

