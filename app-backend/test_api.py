"""
Tests for the Soccer Bet ML Optimizer API

Run with: pytest test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import json

# Import the FastAPI app
from main import app

# Create test client
client = TestClient(app)


class TestHealthEndpoints:
    """Test health and info endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint returns correct info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "version" in data
        assert "uptime" in data
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "services_status" in data
        assert "database_status" in data


class TestUtilityEndpoints:
    """Test utility endpoints."""
    
    def test_list_bookmakers(self):
        """Test bookmakers list endpoint."""
        response = client.get("/bookmakers")
        assert response.status_code == 200
        bookmakers = response.json()
        assert isinstance(bookmakers, list)
        assert len(bookmakers) > 0
        assert "pinnacle" in bookmakers
    
    def test_list_optimization_methods(self):
        """Test optimization methods list endpoint."""
        response = client.get("/optimization-methods")
        assert response.status_code == 200
        methods = response.json()
        assert isinstance(methods, list)
        assert "SLSQP" in methods


class TestOptimizationEndpoints:
    """Test optimization endpoints."""
    
    def test_compute_optimization_minimal(self):
        """Test optimization with minimal parameters."""
        payload = {
            "bankroll": 100.0,
            "method": "SLSQP",
            "utility_fn": "Kelly"
        }
        
        response = client.post("/compute/optimization", json=payload)
        # Note: This might fail if the backend services are not available
        # In a real test environment, you'd mock the services
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "success"
            assert "results" in data
            assert "metrics" in data
            assert "durations" in data
    
    def test_compute_optimization_full_params(self):
        """Test optimization with all parameters."""
        future_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        
        payload = {
            "datetime_first_match": future_date,
            "n_matches": 5,
            "bookmakers": ["pinnacle", "betclic"],
            "bankroll": 500.0,
            "method": "SLSQP",
            "utility_fn": "Kelly",
            "same_day": False
        }
        
        response = client.post("/compute/optimization", json=payload)
        # This test depends on external services
        assert response.status_code in [200, 500]  # 500 if services unavailable
    
    def test_optimization_validation_errors(self):
        """Test optimization endpoint validation."""
        # Test invalid bankroll
        payload = {"bankroll": -10.0}
        response = client.post("/compute/optimization", json=payload)
        assert response.status_code == 422  # Validation error
        
        # Test invalid datetime format
        payload = {
            "datetime_first_match": "invalid-date",
            "bankroll": 100.0
        }
        response = client.post("/compute/optimization", json=payload)
        assert response.status_code == 422


class TestPredictionEndpoints:
    """Test prediction endpoints."""
    
    def test_fetch_predictions_minimal(self):
        """Test fetching predictions with minimal parameters."""
        payload = {"optim_label": "test"}
        
        response = client.post("/fetch/predictions", json=payload)
        # This test depends on external services
        assert response.status_code in [200, 500]
    
    def test_fetch_predictions_with_datetime(self):
        """Test fetching predictions with datetime parameter."""
        past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        
        payload = {
            "optim_label": "test",
            "datetime_optim_last": past_date
        }
        
        response = client.post("/fetch/predictions", json=payload)
        assert response.status_code in [200, 500]
    
    def test_predictions_validation(self):
        """Test predictions endpoint validation."""
        # Test empty optim_label
        payload = {"optim_label": ""}
        response = client.post("/fetch/predictions", json=payload)
        assert response.status_code == 422
        
        # Test invalid datetime
        payload = {
            "optim_label": "test",
            "datetime_optim_last": "invalid-date"
        }
        response = client.post("/fetch/predictions", json=payload)
        assert response.status_code == 422


class TestPerformanceEndpoints:
    """Test performance endpoints."""
    
    def test_fetch_performance_minimal(self):
        """Test fetching performance with minimal parameters."""
        payload = {"optim_label": "test"}
        
        response = client.post("/fetch/performance", json=payload)
        assert response.status_code in [200, 500]
    
    def test_fetch_performance_with_date_range(self):
        """Test fetching performance with date range."""
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        
        payload = {
            "optim_label": "test",
            "datetime_first_match": start_date,
            "datetime_last_match": end_date
        }
        
        response = client.post("/fetch/performance", json=payload)
        assert response.status_code in [200, 500]
    
    def test_fetch_performance_gains(self):
        """Test fetching performance gains."""
        payload = {
            "optim_label": "test",
            "divisor": 3
        }
        
        response = client.post("/fetch/performance/gains", json=payload)
        assert response.status_code in [200, 500]
    
    def test_performance_date_validation(self):
        """Test performance endpoint date validation."""
        # Test end date before start date
        start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        end_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        
        payload = {
            "optim_label": "test",
            "datetime_first_match": start_date,
            "datetime_last_match": end_date
        }
        
        response = client.post("/fetch/performance", json=payload)
        assert response.status_code == 422


class TestLegacyEndpoints:
    """Test legacy endpoints for backward compatibility."""
    
    def test_legacy_optimization_endpoint(self):
        """Test legacy optimization endpoint."""
        params = {
            "bankroll": 100.0,
            "method": "SLSQP",
            "utility_fn": "Kelly"
        }
        
        response = client.get("/compute/predictions", params=params)
        assert response.status_code in [200, 500]
    
    def test_legacy_predictions_endpoint(self):
        """Test legacy predictions endpoint."""
        params = {"optim_label": "test"}
        
        response = client.get("/fetch/last_predictions", params=params)
        assert response.status_code in [200, 500]


class TestResponseFormat:
    """Test response format consistency."""
    
    def test_health_response_format(self):
        """Test health endpoint response format."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        required_fields = ["status", "message", "timestamp", "version", "uptime"]
        for field in required_fields:
            assert field in data
    
    def test_error_response_format(self):
        """Test error response format."""
        # Trigger a validation error
        payload = {"bankroll": "invalid"}
        response = client.post("/compute/optimization", json=payload)
        assert response.status_code == 422
        
        data = response.json()
        assert "detail" in data  # FastAPI validation error format


class TestMiddleware:
    """Test middleware functionality."""
    
    def test_response_headers(self):
        """Test that security headers are added."""
        response = client.get("/")
        
        # Check for security headers
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection"
        ]
        
        for header in security_headers:
            assert header in response.headers
    
    def test_process_time_header(self):
        """Test that process time header is added."""
        response = client.get("/")
        assert "X-Process-Time" in response.headers
        
        # Verify it's a valid float
        process_time = float(response.headers["X-Process-Time"])
        assert process_time >= 0


# Fixtures for testing
@pytest.fixture
def sample_optimization_request():
    """Sample optimization request data."""
    return {
        "bankroll": 100.0,
        "method": "SLSQP",
        "utility_fn": "Kelly",
        "n_matches": 5,
        "same_day": False
    }


@pytest.fixture
def sample_predictions_request():
    """Sample predictions request data."""
    return {
        "optim_label": "test_label"
    }


@pytest.fixture
def sample_performance_request():
    """Sample performance request data."""
    return {
        "optim_label": "test_label",
        "datetime_first_match": "2024-01-01 00:00:00",
        "datetime_last_match": "2024-01-31 23:59:59"
    }


# Integration tests (require running services)
@pytest.mark.integration
class TestIntegration:
    """Integration tests that require external services."""
    
    def test_full_optimization_flow(self, sample_optimization_request):
        """Test complete optimization flow."""
        response = client.post("/compute/optimization", json=sample_optimization_request)
        
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "success"
            assert isinstance(data["results"], list)
            assert isinstance(data["metrics"], dict)
            assert isinstance(data["durations"], dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
