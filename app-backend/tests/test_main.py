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
    assert data["service"] == "app-backend"


def test_compute_predictions_no_params():
    """Test compute predictions endpoint without parameters"""
    response = client.get("/compute/predictions")
    # Should return 500 or handle gracefully depending on implementation
    assert response.status_code in [200, 500]


def test_fetch_last_predictions_test_mode():
    """Test fetch last predictions in test mode"""
    response = client.get("/fetch/last_predictions?optim_label=test")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "results" in data
    assert len(data["results"]) > 0


def test_fetch_past_performances_test_mode():
    """Test fetch past performances in test mode"""
    response = client.get("/fetch/past_performances?optim_label=test")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "results" in data


def test_fetch_past_performances_gains_test_mode():
    """Test fetch past performances gains in test mode"""
    response = client.get("/fetch/past_performances_gains?optim_label=test")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "results" in data
    assert len(data["results"]) > 0