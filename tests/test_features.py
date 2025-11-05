"""Unit tests for feature pipeline."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ingest.schema import get_session, User, Account, Transaction
from features.pipeline import FeaturePipeline


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


def test_feature_pipeline_initialization(tmp_path):
    """Test that FeaturePipeline can be initialized."""
    db_path = str(tmp_path / "test.db")
    pipeline = FeaturePipeline(db_path)
    assert pipeline is not None
    pipeline.close()


def test_compute_features_for_user_empty(db_session, sample_user, tmp_path):
    """Test feature computation for user with no transactions."""
    db_path = str(tmp_path / "test.db")
    pipeline = FeaturePipeline(db_path)
    
    features = pipeline.compute_features_for_user(sample_user.id, 180)
    
    assert features is not None
    assert 'credit' in features
    assert 'income' in features
    assert 'subscriptions' in features
    assert 'savings' in features
    
    pipeline.close()


def test_feature_pipeline_window_days(db_session, sample_user, tmp_path):
    """Test that window_days parameter works correctly."""
    db_path = str(tmp_path / "test.db")
    pipeline = FeaturePipeline(db_path)
    
    # Test with 30 days
    features_30 = pipeline.compute_features_for_user(sample_user.id, 30)
    assert features_30 is not None
    
    # Test with 180 days
    features_180 = pipeline.compute_features_for_user(sample_user.id, 180)
    assert features_180 is not None
    
    pipeline.close()

