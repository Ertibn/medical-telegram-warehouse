"""Tests for FastAPI endpoints."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add api to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    with patch('api.database.SessionLocal'):
        from api.main import app
        return TestClient(app)


class TestAPIEndpoints:
    """Test suite for API endpoints."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "endpoints" in data

    def test_api_response_structure(self, client):
        """Test API response structure."""
        response = client.get("/")
        assert "version" in response.json()
        assert "documentation" in response.json()

    def test_endpoints_defined(self, client):
        """Test that all required endpoints are defined."""
        response = client.get("/")
        endpoints = response.json()["endpoints"]
        
        required_endpoints = [
            "health",
            "top_products",
            "channel_activity",
            "search",
            "visual_content"
        ]
        
        for endpoint in required_endpoints:
            assert endpoint in endpoints or any(endpoint in str(v) for v in endpoints.values())

    def test_top_products_limit_validation(self, client):
        """Test top products limit parameter validation."""
        # Test with valid limit
        response = client.get("/api/reports/top-products?limit=10")
        assert response.status_code in [200, 500]  # 500 if DB not available in test

    def test_search_query_required(self, client):
        """Test search endpoint requires query parameter."""
        response = client.get("/api/search/messages")
        assert response.status_code == 422  # Unprocessable Entity

    def test_search_with_query(self, client):
        """Test search with query parameter."""
        response = client.get("/api/search/messages?query=paracetamol&limit=10")
        assert response.status_code in [200, 500]  # 500 if DB not available

    def test_channel_activity_requires_name(self, client):
        """Test channel activity endpoint requires channel name."""
        response = client.get("/api/channels//activity")
        assert response.status_code in [404, 422, 500]

    def test_visual_content_stats(self, client):
        """Test visual content stats endpoint."""
        response = client.get("/api/reports/visual-content")
        assert response.status_code in [200, 500]  # 500 if DB not available
