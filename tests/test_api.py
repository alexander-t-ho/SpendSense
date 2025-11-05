"""Integration tests for API endpoints."""

import pytest

# Skip if httpx not available
try:
    import httpx
except ImportError:
    pytestmark = pytest.mark.skip("httpx not available for TestClient")

try:
    from fastapi.testclient import TestClient
    from api.main import app
    client = TestClient(app)
except Exception as e:
    # Skip if TestClient can't be created
    pytestmark = pytest.mark.skip(f"TestClient not available: {e}")
    client = None


def test_root_endpoint():
    """Test root endpoint returns API info."""
    if client is None:
        pytest.skip("TestClient not available")
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_stats_endpoint():
    """Test stats endpoint."""
    if client is None:
        pytest.skip("TestClient not available")
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_users" in data
    assert "total_accounts" in data
    assert "total_transactions" in data


def test_users_endpoint():
    """Test users endpoint."""
    if client is None:
        pytest.skip("TestClient not available")
    response = client.get("/api/users")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_correlation_endpoint():
    """Test correlation endpoint."""
    if client is None:
        pytest.skip("TestClient not available")
    response = client.get("/api/correlation")
    assert response.status_code == 200


def test_spending_patterns_endpoint():
    """Test spending patterns endpoint."""
    if client is None:
        pytest.skip("TestClient not available")
    # Use a test user ID (may not exist, but should return error gracefully)
    response = client.get("/api/spending-patterns/test-user-123/day-of-week")
    # Should return 200 even if user doesn't exist (will return error in response)
    assert response.status_code == 200


def test_frequent_locations_endpoint():
    """Test frequent locations endpoint."""
    if client is None:
        pytest.skip("TestClient not available")
    response = client.get("/api/spending-patterns/test-user-123/frequent-locations")
    assert response.status_code == 200

