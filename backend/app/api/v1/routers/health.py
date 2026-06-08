"""Health check endpoint — used by load balancers and monitoring."""

from datetime import UTC, datetime

from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])

APP_VERSION = "0.1.0"


@router.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return the current service status.

    Used by:
    - Load balancer health probes
    - Docker healthcheck
    - Monitoring / uptime checks
    """
    return HealthResponse(
        status="ok",
        version=APP_VERSION,
        timestamp=datetime.now(tz=UTC),
    )
