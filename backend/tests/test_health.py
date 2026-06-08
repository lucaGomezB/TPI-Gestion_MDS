"""Tests for the health check endpoint."""

import httpx
import pytest
from app.api.v1.routers.health import router as health_router
from app.schemas.health import HealthResponse
from fastapi import FastAPI
from httpx import ASGITransport


@pytest.fixture
def app() -> FastAPI:
    """Create a minimal FastAPI app with only the health router mounted."""
    application = FastAPI()
    application.include_router(health_router)
    return application


@pytest.fixture
async def client(app: FastAPI) -> httpx.AsyncClient:
    """Create an async test client for the health-only app."""
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoint:
    """GET /api/health should return 200 with the expected shape."""

    @pytest.mark.asyncio
    async def test_health_returns_200(self, client: httpx.AsyncClient) -> None:
        """GET /api/health should return 200 OK."""
        response = await client.get("/api/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_returns_valid_json(self, client: httpx.AsyncClient) -> None:
        """Response body should be parseable JSON."""
        response = await client.get("/api/health")
        body = response.json()
        assert isinstance(body, dict)

    @pytest.mark.asyncio
    async def test_health_has_status_field(self, client: httpx.AsyncClient) -> None:
        """Response should contain 'status' with value 'ok'."""
        response = await client.get("/api/health")
        body = response.json()
        assert body["status"] == "ok"

    @pytest.mark.asyncio
    async def test_health_has_version_field(self, client: httpx.AsyncClient) -> None:
        """Response should contain 'version' with the app version."""
        response = await client.get("/api/health")
        body = response.json()
        assert body["version"] == "0.1.0"

    @pytest.mark.asyncio
    async def test_health_has_timestamp_field(self, client: httpx.AsyncClient) -> None:
        """Response should contain 'timestamp' as an ISO datetime string."""
        response = await client.get("/api/health")
        body = response.json()
        assert "timestamp" in body
        assert isinstance(body["timestamp"], str)
        assert "T" in body["timestamp"]

    @pytest.mark.asyncio
    async def test_health_response_matches_schema(self, client: httpx.AsyncClient) -> None:
        """Response body should be validatable against HealthResponse."""
        response = await client.get("/api/health")
        body = response.json()
        health = HealthResponse(**body)
        assert health.status == "ok"
        assert health.version == "0.1.0"
