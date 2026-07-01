"""Tests for GET /api/v1/health.

Covers the response contract relied on by the frontend, Cloud Run health probes,
and load balancers. No GCP credentials required — uses the null-lifespan client.
"""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    def test_returns_200(self, client: TestClient):
        assert client.get("/api/v1/health").status_code == 200

    def test_content_type_is_json(self, client: TestClient):
        assert "application/json" in client.get("/api/v1/health").headers["content-type"]

    def test_status_field_is_healthy(self, client: TestClient):
        assert client.get("/api/v1/health").json()["status"] == "healthy"

    def test_version_field_present_and_is_string(self, client: TestClient):
        data = client.get("/api/v1/health").json()
        assert "version" in data
        assert isinstance(data["version"], str)

    def test_uptime_is_non_negative_integer(self, client: TestClient):
        data = client.get("/api/v1/health").json()
        assert isinstance(data["uptime"], int)
        assert data["uptime"] >= 0

    def test_services_array_present(self, client: TestClient):
        data = client.get("/api/v1/health").json()
        assert "services" in data
        assert isinstance(data["services"], list)

    def test_services_contains_fastapi_entry(self, client: TestClient):
        names = [s["name"] for s in client.get("/api/v1/health").json()["services"]]
        assert "FastAPI" in names

    def test_each_service_has_name_and_status(self, client: TestClient):
        for svc in client.get("/api/v1/health").json()["services"]:
            assert "name" in svc
            assert "status" in svc

    def test_checked_at_field_present(self, client: TestClient):
        assert "checkedAt" in client.get("/api/v1/health").json()

    def test_idempotent_across_multiple_calls(self, client: TestClient):
        """Health probe must always return 200."""
        for _ in range(3):
            assert client.get("/api/v1/health").status_code == 200
