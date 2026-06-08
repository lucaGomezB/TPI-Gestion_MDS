"""Async Moodle Web Services client using aiohttp.

Provides typed access to Moodle WS functions with:
- Token-based authentication (wstoken as query parameter)
- Configurable timeout (default 30s)
- Retry logic: 2 retries with exponential backoff (1s, 3s) on 5xx/network errors
- Error wrapping into typed exceptions
"""

import asyncio
import logging
from typing import Any

import aiohttp

from app.integrations.exceptions import (
    MoodleAuthenticationError,
    MoodleConnectionError,
    MoodleServerError,
)
from app.integrations.models import (
    MoodleEnrolledUser,
    MoodleGrade,
    MoodleGradeItem,
    MoodleGradeResponse,
    MoodleUserProfile,
)

logger = logging.getLogger(__name__)

# ── Retry constants ──────────────────────────────────────────────────────────

_RETRY_DELAYS = [1.0, 3.0]  # seconds
_MAX_RETRIES = 2


class MoodleWSClient:
    """Async client for Moodle Web Services (REST protocol, Moodle 3.1+).

    Usage::

        client = MoodleWSClient(ws_url="https://moodle.example.com", ws_token="abc123")
        grades = await client.get_grades(course_id=42)
        users = await client.get_enrolled_users(course_id=42)
    """

    def __init__(
        self,
        ws_url: str,
        ws_token: str,
        timeout: int = 30,
    ) -> None:
        self._ws_url = ws_url.rstrip("/")
        self._ws_token = ws_token
        self._timeout = timeout
        self._session: aiohttp.ClientSession | None = None

    # ── Session management ──────────────────────────────────────────────

    async def _get_session(self) -> aiohttp.ClientSession:
        """Return or create a reusable aiohttp session.

        Uses a TCP connector with connection reuse and a per-host limit.
        """
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit_per_host=10)
            timeout_obj = aiohttp.ClientTimeout(total=self._timeout)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout_obj,
            )
        return self._session

    async def close(self) -> None:
        """Close the underlying aiohttp session if open."""
        if self._session is not None and not self._session.closed:
            await self._session.close()

    # ── Core request method ──────────────────────────────────────────────

    async def _call(
        self,
        ws_function: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a Moodle WS function via REST and return parsed JSON.

        Implements retry logic:
        - 2 retries with exponential backoff (1s, 3s) on 5xx or network errors
        - No retry on 4xx (including authentication errors)

        Args:
            ws_function: The Moodle WS function name (e.g. ``core_grades_get_grades``).
            params: Additional query parameters for the WS function.

        Returns:
            The parsed JSON response as a dictionary.

        Raises:
            MoodleAuthenticationError: If the token is invalid (HTTP 403 with error).
            MoodleConnectionError: If the server is unreachable or times out.
            MoodleServerError: If the server returns a 5xx error.
        """
        session = await self._get_session()

        url = f"{self._ws_url}/webservice/rest/server.php"
        query_params: dict[str, Any] = {
            "wstoken": self._ws_token,
            "wsfunction": ws_function,
            "moodlewsrestformat": "json",
        }
        if params:
            query_params.update(params)

        last_exception: Exception | None = None

        for attempt in range(_MAX_RETRIES + 1):
            try:
                async with session.get(url, params=query_params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # Moodle can return 200 with an exception in the JSON body
                        if isinstance(data, dict) and "exception" in data:
                            error_msg = data.get("message", "Unknown Moodle error")
                            error_code = data.get("errorcode", "")
                            if error_code in ("invalidtoken", "accessexception"):
                                raise MoodleAuthenticationError(error_msg)
                            raise MoodleServerError(error_msg)
                        return data

                    if resp.status == 403:
                        raise MoodleAuthenticationError(
                            f"Moodle authentication failed (HTTP {resp.status})"
                        )

                    if resp.status >= 500:
                        error_text = await resp.text()
                        last_exception = MoodleServerError(
                            f"Moodle server error (HTTP {resp.status}): {error_text[:200]}"
                        )
                        if attempt < _MAX_RETRIES:
                            delay = _RETRY_DELAYS[attempt]
                            logger.warning(
                                "Moodle 5xx error (attempt %d/%d), retrying in %.1fs: %s",
                                attempt + 1,
                                _MAX_RETRIES + 1,
                                delay,
                                error_text[:100],
                            )
                            await asyncio.sleep(delay)
                            continue
                        raise last_exception  # type: ignore[misc]

                    # Other non-5xx errors (4xx except 403)
                    error_text = await resp.text()
                    raise MoodleConnectionError(
                        f"Moodle returned HTTP {resp.status}: {error_text[:200]}"
                    )

            except asyncio.TimeoutError:
                last_exception = MoodleConnectionError(
                    f"Moodle request timed out after {self._timeout}s"
                )
                if attempt < _MAX_RETRIES:
                    delay = _RETRY_DELAYS[attempt]
                    logger.warning(
                        "Moodle timeout (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES + 1,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                raise last_exception

            except aiohttp.ClientError as exc:
                last_exception = MoodleConnectionError(
                    f"Moodle connection error: {exc}"
                )
                if attempt < _MAX_RETRIES:
                    delay = _RETRY_DELAYS[attempt]
                    logger.warning(
                        "Moodle connection error (attempt %d/%d), retrying in %.1fs: %s",
                        attempt + 1,
                        _MAX_RETRIES + 1,
                        delay,
                        exc,
                    )
                    await asyncio.sleep(delay)
                    continue
                raise last_exception

        # Should not reach here, but satisfies the type checker
        raise MoodleConnectionError("Max retries exceeded")

    # ── WS function wrappers ─────────────────────────────────────────────

    async def get_grade_items(self, course_id: int) -> list[MoodleGradeItem]:
        """Fetch grade items (activity catalog) for a course.

        Wraps ``gradereport_user_get_grade_items``.

        Args:
            course_id: The Moodle course ID.

        Returns:
            A list of ``MoodleGradeItem`` instances.
        """
        data = await self._call(
            "gradereport_user_get_grade_items",
            params={"courseid": course_id},
        )
        items = data.get("gradeitems", []) if isinstance(data, dict) else []
        return [MoodleGradeItem(**item) for item in items]

    async def get_grades(self, course_id: int) -> MoodleGradeResponse:
        """Fetch grades for all users in a course.

        Wraps ``core_grades_get_grades``.

        Args:
            course_id: The Moodle course ID.

        Returns:
            A ``MoodleGradeResponse`` with grade items and per-user grades.
        """
        data = await self._call(
            "core_grades_get_grades",
            params={"courseid": course_id},
        )
        grade_items = [
            MoodleGradeItem(**item) for item in data.get("gradeitems", [])
        ]
        grades = [
            MoodleGrade(**g) for g in data.get("grades", [])
        ]
        return MoodleGradeResponse(
            courseid=data.get("courseid", course_id),
            grade_items=grade_items,
            grades=grades,
        )

    async def get_enrolled_users(self, course_id: int) -> list[MoodleEnrolledUser]:
        """Fetch enrolled users for a course.

        Wraps ``core_enrol_get_enrolled_users``.

        Args:
            course_id: The Moodle course ID.

        Returns:
            A list of ``MoodleEnrolledUser`` instances.
        """
        data = await self._call(
            "core_enrol_get_enrolled_users",
            params={"courseid": course_id},
        )
        raw_list = data if isinstance(data, list) else []
        return [MoodleEnrolledUser(**u) for u in raw_list]

    async def get_users(
        self, criteria: list[dict[str, str]]
    ) -> list[MoodleUserProfile]:
        """Fetch user profiles matching given criteria.

        Wraps ``core_user_get_users``.

        Args:
            criteria: A list of ``{"key": field, "value": value}`` dicts.

        Returns:
            A list of ``MoodleUserProfile`` instances.
        """
        # Build criteria params: criteria[0][key], criteria[0][value], ...
        params: dict[str, Any] = {}
        for i, criterion in enumerate(criteria):
            params[f"criteria[{i}][key]"] = criterion.get("key", "")
            params[f"criteria[{i}][value]"] = criterion.get("value", "")

        data = await self._call("core_user_get_users", params=params)
        users = data.get("users", []) if isinstance(data, dict) else []
        return [MoodleUserProfile(**u) for u in users]
