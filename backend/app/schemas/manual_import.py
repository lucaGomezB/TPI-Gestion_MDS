"""Pydantic schemas for manual import (xlsx/csv) operations.

All schemas use ``extra='forbid'`` to reject undeclared fields.
"""

from pydantic import BaseModel, ConfigDict


class PreviewActivity(BaseModel):
    """A detected activity from a file upload."""

    model_config = ConfigDict(extra="forbid")

    name: str
    column_name: str
    scale_type: str = "numeric"  # 'numeric' or 'textual'
    detected_values: list[str] = []


class ImportWarning(BaseModel):
    """A warning or issue detected during file parsing."""

    model_config = ConfigDict(extra="forbid")

    message: str
    row: int | None = None
    column: str | None = None


class PreviewResult(BaseModel):
    """Result of a file preview before import confirmation."""

    model_config = ConfigDict(extra="forbid")

    session_token: str
    filename: str
    activities: list[PreviewActivity] = []
    students_count: int = 0
    sample_students: list[str] = []
    warnings: list[ImportWarning] = []
    total_rows: int = 0


class ImportConfirmRequest(BaseModel):
    """Request body for confirming a manual import."""

    model_config = ConfigDict(extra="forbid")

    session_token: str
    activity_ids: list[str]  # UUIDs of activities to include


class ImportResult(BaseModel):
    """Result of a confirmed manual import."""

    model_config = ConfigDict(extra="forbid")

    status: str = "completed"
    activities_imported: int = 0
    grades_imported: int = 0
    students_enrolled: int = 0
    errors: list[str] = []
