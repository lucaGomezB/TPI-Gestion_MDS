"""Tests for MoodleWSClient with mocked HTTP responses.

Tests cover:
- Valid grade fetch (numeric, textual, empty)
- Authentication error (invalid token)
- Connection timeout with retry logic
- Invalid URL handling
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.integrations.exceptions import (
    MoodleAuthenticationError,
    MoodleConnectionError,
    MoodleServerError,
)
from app.integrations.moodle_ws import MoodleWSClient


class MockResponse:
    """A simple async context manager response mock."""

    def __init__(self, status: int, json_data: object = None, text_data: str = "") -> None:
        self.status = status
        self._json_data = json_data
        self._text_data = text_data

    async def json(self) -> object:
        return self._json_data

    async def text(self) -> str:
        return self._text_data

    async def __aenter__(self) -> "MockResponse":
        return self

    async def __aexit__(self, *args: object) -> None:
        pass


@pytest.fixture
def client() -> MoodleWSClient:
    """Return a MoodleWSClient with test credentials."""
    return MoodleWSClient(
        ws_url="https://moodle.example.com",
        ws_token="test-token-123",
        timeout=5,
    )


# ── Grade items tests ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_grade_items_success(client: MoodleWSClient) -> None:
    """Test successful fetch of grade items."""
    mock_response = {
        "gradeitems": [
            {"id": 1, "itemname": "Trabajo Practico 1", "grademax": 100},
            {"id": 2, "itemname": "Examen Parcial", "grademax": 10},
        ]
    }

    with patch.object(client, "_call", AsyncMock(return_value=mock_response)):
        items = await client.get_grade_items(course_id=42)

    assert len(items) == 2
    assert items[0].itemname == "Trabajo Practico 1"
    assert items[0].grademax == 100
    assert items[1].id == 2


# ── Grades tests ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_grades_numeric(client: MoodleWSClient) -> None:
    """Test fetch of numeric grades."""
    mock_response = {
        "courseid": 42,
        "gradeitems": [
            {"id": 1, "itemname": "TP 1", "grademax": 100, "grademin": 0},
        ],
        "grades": [
            {"userid": 101, "rawgrade": 85.0, "grademax": 100},
            {"userid": 102, "rawgrade": 92.0, "grademax": 100},
        ],
    }

    with patch.object(client, "_call", AsyncMock(return_value=mock_response)):
        result = await client.get_grades(course_id=42)

    assert result.courseid == 42
    assert len(result.grade_items) == 1
    assert len(result.grades) == 2
    assert result.grades[0].userid == 101
    assert result.grades[0].rawgrade == 85.0
    assert result.grades[1].rawgrade == 92.0


@pytest.mark.asyncio
async def test_get_grades_textual(client: MoodleWSClient) -> None:
    """Test fetch of textual (scale-based) grades."""
    mock_response = {
        "courseid": 42,
        "gradeitems": [],
        "grades": [
            {"userid": 101, "grade": "Satisfactorio"},
            {"userid": 102, "grade": "No satisfactorio"},
        ],
    }

    with patch.object(client, "_call", AsyncMock(return_value=mock_response)):
        result = await client.get_grades(course_id=42)

    assert len(result.grades) == 2
    assert result.grades[0].grade == "Satisfactorio"
    assert result.grades[1].grade == "No satisfactorio"


@pytest.mark.asyncio
async def test_get_grades_empty(client: MoodleWSClient) -> None:
    """Test fetch of grades for a course with no grades."""
    mock_response = {"courseid": 42, "gradeitems": [], "grades": []}

    with patch.object(client, "_call", AsyncMock(return_value=mock_response)):
        result = await client.get_grades(course_id=42)

    assert result.courseid == 42
    assert len(result.grade_items) == 0
    assert len(result.grades) == 0


# ── Enrolled users tests ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_enrolled_users_success(client: MoodleWSClient) -> None:
    """Test successful fetch of enrolled users."""
    mock_response = [
        {"id": 101, "fullname": "Juan Perez", "email": "juan@example.com"},
        {"id": 102, "fullname": "Maria Gomez", "email": "maria@example.com"},
    ]

    with patch.object(client, "_call", AsyncMock(return_value=mock_response)):
        users = await client.get_enrolled_users(course_id=42)

    assert len(users) == 2
    assert users[0].fullname == "Juan Perez"
    assert users[0].email == "juan@example.com"
    assert users[1].id == 102


@pytest.mark.asyncio
async def test_enrolled_user_missing_email(client: MoodleWSClient) -> None:
    """Test enrolled user without email is still processed."""
    mock_response = [
        {"id": 101, "fullname": "Juan Perez"},
        {"id": 102, "fullname": "Maria Gomez", "email": "maria@example.com"},
    ]

    with patch.object(client, "_call", AsyncMock(return_value=mock_response)):
        users = await client.get_enrolled_users(course_id=42)

    assert len(users) == 2
    assert users[0].email is None
    assert users[1].email == "maria@example.com"


# ── Get users tests ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_users_by_email(client: MoodleWSClient) -> None:
    """Test fetching users by email criteria."""
    mock_response = {
        "users": [
            {"id": 101, "fullname": "Juan Perez", "email": "juan@example.com"},
        ]
    }

    with patch.object(client, "_call", AsyncMock(return_value=mock_response)):
        users = await client.get_users([{"key": "email", "value": "juan@example.com"}])

    assert len(users) == 1
    assert users[0].fullname == "Juan Perez"


# ── Authentication & error tests ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_authentication_error_from_moodle_exception(client: MoodleWSClient) -> None:
    """Test that Moodle exception in JSON body raises MoodleAuthenticationError."""
    mock_data = {
        "exception": "moodle_exception",
        "errorcode": "invalidtoken",
        "message": "Invalid token",
    }

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value = MockResponse(status=200, json_data=mock_data)

        with pytest.raises(MoodleAuthenticationError, match="Invalid token"):
            await client.get_grade_items(course_id=42)


@pytest.mark.asyncio
async def test_retry_on_timeout_eventually_succeeds(client: MoodleWSClient) -> None:
    """Test retry logic: timeout then success on second attempt."""
    mock_response = {"gradeitems": [{"id": 1, "itemname": "TP 1"}]}

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.side_effect = [
            asyncio.TimeoutError(),
            MockResponse(status=200, json_data=mock_response),
        ]

        items = await client.get_grade_items(course_id=42)

    assert len(items) == 1
    assert items[0].itemname == "TP 1"
    assert mock_get.call_count == 2


@pytest.mark.asyncio
async def test_retry_exhausted_still_fails(client: MoodleWSClient) -> None:
    """Test that after exhausting retries (2), the error is raised."""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.side_effect = asyncio.TimeoutError()

        with pytest.raises(MoodleConnectionError, match="timed out"):
            await client.get_grade_items(course_id=42)

    assert mock_get.call_count == 3  # initial + 2 retries


@pytest.mark.asyncio
async def test_moodle_5xx_triggers_retry(client: MoodleWSClient) -> None:
    """Test retry on 5xx server errors with eventual success."""
    mock_response = {"gradeitems": [{"id": 1, "itemname": "TP 1"}]}

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.side_effect = [
            MockResponse(status=500, text_data="Internal Server Error"),
            MockResponse(status=200, json_data=mock_response),
        ]

        items = await client.get_grade_items(course_id=42)

    assert len(items) == 1
    assert mock_get.call_count == 2


@pytest.mark.asyncio
async def test_moodle_5xx_all_retries_fail(client: MoodleWSClient) -> None:
    """Test that all retries are exhausted on persistent 5xx."""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value = MockResponse(status=500, text_data="Server Error")

        with pytest.raises(MoodleServerError):
            await client.get_grade_items(course_id=42)

    assert mock_get.call_count == 3


@pytest.mark.asyncio
async def test_moodle_403_no_retry(client: MoodleWSClient) -> None:
    """Test that HTTP 403 raises MoodleAuthenticationError without retry."""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value = MockResponse(status=403, text_data="Invalid token")

        with pytest.raises(MoodleAuthenticationError):
            await client.get_grade_items(course_id=42)

    assert mock_get.call_count == 1


@pytest.mark.asyncio
async def test_invalid_url_raises_connection_error(client: MoodleWSClient) -> None:
    """Test connection error on invalid URL."""
    bad_client = MoodleWSClient(ws_url="not-a-valid-url", ws_token="test", timeout=5)

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.side_effect = MoodleConnectionError("Connection failed")

        with pytest.raises(MoodleConnectionError):
            await bad_client.get_grades(course_id=1)
