"""Tests for core.logging — JSONFormatter for structured logs."""

import json
import logging

from app.core.logging import JSONFormatter


class TestJSONFormatter:
    """JSONFormatter should emit valid JSON with required fields."""

    def _get_log_output(self, record: logging.LogRecord) -> dict:
        """Create a JSONFormatter, format the record, and return parsed JSON."""
        fmt = JSONFormatter()
        output = fmt.format(record)
        return json.loads(output)

    def test_output_is_valid_json(self):
        """Formatted output should be parseable as JSON."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=42,
            msg="hello world",
            args=(),
            exc_info=None,
        )
        result = self._get_log_output(record)
        assert isinstance(result, dict)

    def test_contains_timestamp(self):
        """Output should contain a 'timestamp' field."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=42,
            msg="test timestamp",
            args=(),
            exc_info=None,
        )
        result = self._get_log_output(record)
        assert "timestamp" in result
        assert isinstance(result["timestamp"], str)
        assert len(result["timestamp"]) > 0

    def test_contains_level(self):
        """Output should contain a 'level' field with the level name."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.WARNING,
            pathname=__file__,
            lineno=42,
            msg="warning message",
            args=(),
            exc_info=None,
        )
        result = self._get_log_output(record)
        assert result["level"] == "WARNING"

    def test_contains_logger_name(self):
        """Output should contain a 'name' field with the logger name."""
        record = logging.LogRecord(
            name="my.custom.logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=42,
            msg="named logger",
            args=(),
            exc_info=None,
        )
        result = self._get_log_output(record)
        assert result["name"] == "my.custom.logger"

    def test_contains_message(self):
        """Output should contain a 'message' field with the formatted message."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=42,
            msg="user %s logged in",
            args=("admin",),
            exc_info=None,
        )
        result = self._get_log_output(record)
        assert result["message"] == "user admin logged in"

    def test_includes_extra_fields(self):
        """Extra fields passed via extra= should appear in the JSON output."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname=__file__,
            lineno=42,
            msg="request failed",
            args=(),
            exc_info=None,
        )
        record.__dict__["request_id"] = "req-123"
        record.__dict__["user_id"] = "user-456"
        result = self._get_log_output(record)
        assert result["request_id"] == "req-123"
        assert result["user_id"] == "user-456"

    def test_different_levels(self):
        """Different log levels should be reflected correctly."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.CRITICAL,
            pathname=__file__,
            lineno=42,
            msg="critical error",
            args=(),
            exc_info=None,
        )
        result = self._get_log_output(record)
        assert result["level"] == "CRITICAL"

    def test_timestamp_is_isoformat(self):
        """Timestamp should be in ISO 8601 format."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=42,
            msg="check timestamp format",
            args=(),
            exc_info=None,
        )
        result = self._get_log_output(record)
        from datetime import datetime

        # ISO format includes T and timezone or Z
        assert "T" in result["timestamp"]
        # should parse successfully
        datetime.fromisoformat(result["timestamp"])
