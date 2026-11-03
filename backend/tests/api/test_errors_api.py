from fastapi import APIRouter
from pydantic import BaseModel, Field
from starlette.testclient import TestClient


class MockPayload(BaseModel):
    name: str = Field(..., min_length=3)
    score: int = Field(..., ge=0)


def test_404_not_found(client):
    response = client.get("/api/v1/non_existent_route")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "Not Found" in data["error"]["message"]
    assert isinstance(data["error"]["details"], list)


def test_405_method_not_allowed(client):
    response = client.post("/health")
    assert response.status_code == 405
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "METHOD_NOT_ALLOWED"


def test_validation_error_envelope(app, client):
    test_router = APIRouter()

    @test_router.post("/test-validation")
    def sample_endpoint(payload: MockPayload):
        return {"status": "ok"}

    app.include_router(test_router)

    # Invalid payload (score is negative, name too short)
    response = client.post("/test-validation", json={"name": "a", "score": -10})
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert len(data["error"]["details"]) > 0


def test_500_internal_server_error_sanitization(app):
    test_router = APIRouter()

    @test_router.get("/test-crash")
    def crash_endpoint():
        raise RuntimeError("Secret database password is hidden_secret_123")

    app.include_router(test_router)

    safe_client = TestClient(app, raise_server_exceptions=False)
    response = safe_client.get("/test-crash")
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    # Ensure raw secret string is never leaked
    assert "hidden_secret_123" not in data["error"]["message"]
