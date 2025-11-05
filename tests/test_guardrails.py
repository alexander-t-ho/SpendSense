"""Unit tests for guardrails."""

import pytest
from sqlalchemy.orm import Session
from ingest.schema import get_session, User, Consent

# Import guardrails modules directly to avoid circular import issues
# Import directly from module files to bypass __init__.py
import sys
from pathlib import Path
guardrails_path = Path(__file__).parent.parent / "guardrails"
sys.path.insert(0, str(guardrails_path.parent))

# Import guardrails modules directly to avoid circular imports
import importlib.util

# Import consent module directly
consent_spec = importlib.util.spec_from_file_location("consent", guardrails_path / "consent.py")
consent_module = importlib.util.module_from_spec(consent_spec)
consent_spec.loader.exec_module(consent_module)

# Import tone module directly
tone_spec = importlib.util.spec_from_file_location("tone", guardrails_path / "tone.py")
tone_module = importlib.util.module_from_spec(tone_spec)
tone_spec.loader.exec_module(tone_module)


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


def test_consent_manager_initialization(db_session):
    """Test that ConsentManager can be initialized."""
    manager = consent_module.ConsentManager(db_session)
    assert manager is not None


def test_consent_manager_get_consent_none(db_session, sample_user):
    """Test getting consent when none exists."""
    manager = consent_module.ConsentManager(db_session)
    consent_obj = manager.get_consent(sample_user.id)
    assert consent_obj is None or consent_obj.consented == False


def test_consent_manager_grant_consent(db_session, sample_user):
    """Test granting consent."""
    manager = consent_module.ConsentManager(db_session)
    manager.grant_consent(sample_user.id)
    
    consent_obj = manager.get_consent(sample_user.id)
    assert consent_obj is not None
    assert consent_obj.consented == True


def test_consent_manager_require_consent_raises(db_session, sample_user):
    """Test that require_consent raises PermissionError when no consent."""
    manager = consent_module.ConsentManager(db_session)
    
    with pytest.raises(PermissionError):
        manager.require_consent(sample_user.id)


def test_tone_validator_initialization():
    """Test that ToneValidator can be initialized."""
    validator = tone_module.ToneValidator()
    assert validator is not None


def test_tone_validator_check_rationale_clean():
    """Test tone validation with clean text."""
    validator = tone_module.ToneValidator()
    clean_text = "We noticed an opportunity to optimize your spending."
    
    is_valid, issues = validator.check_rationale(clean_text)
    assert is_valid == True
    assert len(issues) == 0


def test_tone_validator_check_rationale_shaming():
    """Test tone validation detects shaming language."""
    validator = tone_module.ToneValidator()
    shaming_text = "You're overspending on unnecessary items."
    
    is_valid, issues = validator.check_rationale(shaming_text)
    assert is_valid == False
    assert len(issues) > 0


def test_tone_validator_sanitize():
    """Test tone sanitization."""
    validator = tone_module.ToneValidator()
    shaming_text = "You're overspending on unnecessary items."
    
    sanitized = validator.sanitize(shaming_text)
    assert sanitized != shaming_text
    assert "overspending" not in sanitized.lower()

