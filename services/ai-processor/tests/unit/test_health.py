import pytest
from fastapi.testclient import TestClient

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ai-processor"
    assert "timestamp" in data

def test_health_check_response_format(client):
    """Test health check response format"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields
    required_fields = ["status", "timestamp", "service"]
    for field in required_fields:
        assert field in data
    
    # Check field types
    assert isinstance(data["status"], str)
    assert isinstance(data["timestamp"], str)
    assert isinstance(data["service"], str)