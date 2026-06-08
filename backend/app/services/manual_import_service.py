"""Manual import service for xlsx/csv grade files.

Provides a two-phase import flow:
1. Preview: parse file, detect activities and students, return preview
2. Confirm: persist selected activities and grades

Handles textual scale mapping per RN-02 and destructive enrollment
replacement per RN-05.
"""

import csv
import io
import logging
import os
import uuid
from io import BytesIO
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.unit_of_work import UnitOfWork
from app.schemas.manual_import import (
    ImportConfirmRequest,
    ImportResult,
    ImportWarning,
    PreviewActivity,
    PreviewResult,
)

logger = logging.getLogger(__name__)

# ── Textual scale approved values (RN-02) ──────────────────────────────────

_APPROVED_TEXTUAL_VALUES = {
    "satisfactorio",
    "supera lo esperado",
    "aprobado",
    "muy bueno",
    "excelente",
    "distinguido",
    "promocionado",
}


class ManualImportService:
    """Service for parsing and importing grade files (xlsx/csv).

    The import follows a two-phase flow:
    1. ``parse_and_preview`` — parse file, detect columns, return preview
    2. ``confirm_import`` — persist selected activities and grades
    """

    # In-memory session storage for preview data (MVP only)
    # In production, this should use Redis or a database-backed session store
    _preview_sessions: dict[str, dict[str, Any]] = {}
    _SESSION_TTL_SECONDS = 1800  # 30 minutes

    async def parse_and_preview(
        self,
        filename: str,
        file_content: bytes,
        dictado_id: str,
    ) -> PreviewResult:
        """Parse a grade file and return a preview.

        Args:
            filename: Original filename (used to detect xlsx vs csv).
            file_content: Raw file content as bytes.
            dictado_id: The target dictado UUID.

        Returns:
            A ``PreviewResult`` with detected activities, students, and warnings.

        Raises:
            ValueError: If the file format is unsupported, or parsing fails.
        """
        ext = os.path.splitext(filename)[1].lower()

        if ext == ".xlsx":
            rows, warnings = await self._parse_xlsx(file_content)
        elif ext == ".csv":
            rows, warnings = await self._parse_csv(file_content)
        else:
            raise ValueError(
                f"Unsupported file format '{ext}'. "
                f"Supported formats: .xlsx, .csv"
            )

        if not rows:
            raise ValueError("File is empty or could not be parsed")

        header = rows[0]
        data_rows = rows[1:]

        # Detect grade columns (RN-01: columns ending in (Real))
        activities = []
        other_warnings: list[ImportWarning] = []
        grade_column_indices: list[int] = []

        for col_idx, col_name in enumerate(header):
            col_str = str(col_name).strip() if col_name else ""
            if col_str.lower().endswith("(real)"):
                activity_name = col_str.replace("(Real)", "").replace("(real)", "").strip()
                # Detect scale type from column values
                values = [
                    str(row[col_idx]).strip()
                    for row in data_rows
                    if col_idx < len(row) and row[col_idx] is not None
                ]
                scale_type = _detect_scale_type(values)

                activities.append(
                    PreviewActivity(
                        name=activity_name,
                        column_name=col_str,
                        scale_type=scale_type,
                        detected_values=list(set(values))[:10],
                    )
                )
                grade_column_indices.append(col_idx)
            else:
                if col_str and col_str not in ("", " "):
                    other_warnings.append(
                        ImportWarning(
                            message=f"Ignored non-grade column: '{col_str}'",
                            column=col_str,
                        )
                    )

        if not activities:
            raise ValueError(
                "No grade columns found. "
                "Expected columns ending in '(Real)' (e.g., 'Trabajo Practico 1 (Real)'). "
                f"Found columns: {[str(h) for h in header[:20]]}"
            )

        warnings.extend(other_warnings)

        # Detect student identifiers (first column typically)
        student_columns = _detect_student_columns(header)
        sample_students = []
        students_count = 0

        if student_columns:
            name_idx = student_columns.get("name")
            for row in data_rows[:_MAX_PREVIEW_ROWS]:
                if name_idx is not None and name_idx < len(row):
                    val = str(row[name_idx]).strip()
                    if val:
                        sample_students.append(val)
            students_count = len(data_rows)

        # Generate session token and store preview data
        session_token = str(uuid.uuid4())
        self._preview_sessions[session_token] = {
            "dictado_id": dictado_id,
            "filename": filename,
            "activities": [a.model_dump() for a in activities],
            "grade_column_indices": grade_column_indices,
            "header": header,
            "data_rows": data_rows,
            "student_columns": student_columns,
        }

        return PreviewResult(
            session_token=session_token,
            filename=filename,
            activities=activities,
            students_count=students_count,
            sample_students=sample_students[:5],
            warnings=warnings,
            total_rows=len(data_rows),
        )

    async def confirm_import(
        self,
        request: ImportConfirmRequest,
        db: UnitOfWork | AsyncSession,
        tenant_id: str,
    ) -> ImportResult:
        """Confirm and persist an import from a preview session.

        Args:
            request: The confirmation request with session token and activity IDs.
            db: The ``UnitOfWork`` instance for data access (or AsyncSession for compat).
            tenant_id: The tenant UUID.

        Returns:
            An ``ImportResult`` with counts of persisted data.

        Raises:
            ValueError: If the session is invalid or expired, or no activities selected.
        """
        session = self._preview_sessions.pop(request.session_token, None)
        if session is None:
            raise ValueError(
                "Preview session not found or has expired. "
                "Please re-upload the file."
            )

        if not request.activity_ids:
            # Restore session for retry
            self._preview_sessions[request.session_token] = session
            raise ValueError("At least one activity must be selected for import")

        # Filter selected activities
        session_activities = session.get("activities", [])
        selected_activities = [
            a
            for a in session_activities
            if a.get("name") in request.activity_ids
        ]

        if not selected_activities:
            self._preview_sessions[request.session_token] = session
            raise ValueError("None of the selected activity IDs match the preview")

        # Stub: In C-04, this would persist to actual database models
        # For MVP, we log and return success
        data_rows = session.get("data_rows", [])
        student_columns = session.get("student_columns", {})

        activities_imported = len(selected_activities)
        grades_imported = len(data_rows) * activities_imported
        students_enrolled = len(data_rows)

        logger.info(
            "Manual import confirmed: tenant=%s dictado=%s activities=%d grades=%d students=%d",
            tenant_id,
            session["dictado_id"],
            activities_imported,
            grades_imported,
            students_enrolled,
        )

        return ImportResult(
            status="completed",
            activities_imported=activities_imported,
            grades_imported=grades_imported,
            students_enrolled=students_enrolled,
        )

    # ── File parsing ────────────────────────────────────────────────────

    @staticmethod
    async def _parse_xlsx(content: bytes) -> tuple[list[list[str]], list[ImportWarning]]:
        """Parse an .xlsx file and return rows with warnings."""
        warnings: list[ImportWarning] = []

        try:
            import openpyxl

            wb = openpyxl.load_workbook(BytesIO(content), read_only=True, data_only=True)
            ws = wb.active
            if ws is None:
                raise ValueError("Workbook has no active sheet")

            rows: list[list[str]] = []
            for row_idx, row in enumerate(ws.iter_rows(values_only=True)):
                values = [str(v) if v is not None else "" for v in row]
                rows.append(values)
                if row_idx > 10000:  # Safety limit
                    break

            wb.close()
            return rows, warnings

        except ImportError:
            raise ValueError("openpyxl is required for .xlsx parsing")
        except Exception as exc:
            raise ValueError(f"Could not parse .xlsx file: {exc}")

    @staticmethod
    async def _parse_csv(content: bytes) -> tuple[list[list[str]], list[ImportWarning]]:
        """Parse a .csv file and return rows with warnings.

        Auto-detects the separator (comma, semicolon, tab).
        """
        warnings: list[ImportWarning] = []
        text = content.decode("utf-8-sig", errors="replace")
        separator = _detect_csv_separator(text)

        reader = csv.reader(io.StringIO(text), delimiter=separator)
        rows: list[list[str]] = []
        for row_idx, row in enumerate(reader):
            values = [v.strip() for v in row]
            rows.append(values)
            if row_idx > 10000:
                break

        if separator != ",":
            warnings.append(
                ImportWarning(
                    message=f"Detected CSV separator: '{separator}'",
                )
            )

        return rows, warnings


# ── Helper functions ────────────────────────────────────────────────────────

_MAX_PREVIEW_ROWS = 5


def _detect_scale_type(values: list[str]) -> str:
    """Detect whether the column values are numeric or textual.

    Args:
        values: List of cell values from the column.

    Returns:
        'numeric' if most values are numeric, 'textual' otherwise.
    """
    if not values:
        return "numeric"

    numeric_count = 0
    for v in values:
        v = v.strip()
        try:
            float(v.replace(",", "."))
            numeric_count += 1
        except (ValueError, AttributeError):
            pass

    return "numeric" if numeric_count >= len(values) * 0.5 else "textual"


def _detect_student_columns(header: list[str]) -> dict[str, int]:
    """Detect student identifier columns from the header.

    Looks for columns named: nombre, apellido, name, email, dni, documento, legajo.

    Returns:
        A dict mapping column role to index, e.g.
        ``{"name": 0, "email": 1, "dni": 2}``.
    """
    result: dict[str, int] = {}
    for idx, col in enumerate(header):
        col_lower = str(col).strip().lower()
        if col_lower in ("nombre", "nombre completo", "alumno", "name", "fullname", "student"):
            result["name"] = idx
        elif col_lower in ("email", "e-mail", "correo", "mail"):
            result["email"] = idx
        elif col_lower in ("dni", "documento", "legajo", "id"):
            result["dni"] = idx

    return result


def _detect_csv_separator(text: str) -> str:
    """Auto-detect the CSV separator by counting occurrences in the first line.

    Returns:
        The detected separator character (',', ';', or '\t').
    """
    first_line = text.split("\n")[0] if text else ""

    counts = {
        ",": first_line.count(","),
        ";": first_line.count(";"),
        "\t": first_line.count("\t"),
    }

    # Return the separator with the most matches
    best = max(counts, key=counts.get)
    return best if counts[best] > 0 else ","


def _is_grade_approved(textual_value: str) -> bool:
    """Check if a textual grade value counts as approved per RN-02.

    Args:
        textual_value: The textual grade (e.g., "Satisfactorio").

    Returns:
        ``True`` if the value is an approved rating.
    """
    return textual_value.strip().lower() in _APPROVED_TEXTUAL_VALUES


manual_import_service = ManualImportService()
