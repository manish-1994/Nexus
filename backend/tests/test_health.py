def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/api/v1/health/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"
    assert data["database"] == "connected"
    assert data["environment"] == "development"


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "NEXUS V3"
    assert data["version"] == "0.1.0"
    assert data["status"] == "running"
