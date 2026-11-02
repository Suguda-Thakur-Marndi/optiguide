def test_root_endpoint_identification(client):
    """GET / should provide application identification metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "OptiGuide API"
    assert data["version"] == "1.0.0"
    assert data["status"] == "running"
    assert "environment" in data


def test_root_health_endpoint(client):
    """GET /health should return basic operational liveness status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "optiguide-api"
    assert data["version"] == "1.0.0"
    assert "timestamp" in data
