"""Structured JSON logging via stdlib logging + custom JSONFormatter."""

import json
import logging
from datetime import UTC, datetime


class JSONFormatter(logging.Formatter):
    """Format log records as JSON objects.

    Produces structured JSON with keys:
        timestamp (ISO 8601), level, name, message, and any extra fields
    set on the LogRecord (e.g., via ``extra=`` or directly on ``record.__dict__``).
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string."""
        log_entry: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }

        # Include any extra fields set on the record
        # Skip stdlib-internal attributes and our own explicit keys
        skip_keys = {
            "args", "asctime", "created", "exc_info", "exc_text", "filename",
            "funcName", "levelname", "levelno", "lineno", "message", "module",
            "msecs", "msg", "name", "pathname", "process", "processName",
            "relativeCreated", "stack_info", "thread", "threadName", "taskName",
        }
        for key, value in record.__dict__.items():
            if key not in skip_keys and key not in log_entry:
                log_entry[key] = value  # type: ignore[literal-required]

        return json.dumps(log_entry, default=str, ensure_ascii=False)
