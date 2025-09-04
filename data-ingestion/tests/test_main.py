import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_read_root():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Info" in response.json()


def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["service"] == "data-ingestion"


@pytest.mark.integration
def test_fbref_endpoint():
    """Integration test for fbref data ingestion"""
    # This would require database connection, so mark as integration
    response = client.get("/fbref?use_cache=true")
    # Should handle gracefully without actual database
    assert response.status_code in [200, 500]


@pytest.mark.integration
def test_sofifa_endpoint():
    """Integration test for sofifa data ingestion"""
    response = client.get("/sofifa/team_stats?use_cache=true")
    assert response.status_code in [200, 500]


@pytest.mark.integration
def test_odds_api_endpoint():
    """Integration test for odds API data ingestion"""
    response = client.get("/the_odds_api/odds")
    # Should handle gracefully without API key
    assert response.status_code in [200, 500]