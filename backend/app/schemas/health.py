"""Health check response schema."""

from datetime import datetime

from app.schemas.base import BaseSchema


class HealthResponse(BaseSchema):
    """Response returned by the ``GET /api/health`` endpoint."""

    status: str
    version: str
    timestamp: datetime
