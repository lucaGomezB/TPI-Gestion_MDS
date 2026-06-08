"""Custom exceptions for Moodle Web Services integration.

These exceptions provide typed error handling for Moodle WS operations.
Each maps to an appropriate HTTP status code for API responses.
"""


class MoodleError(Exception):
    """Base exception for all Moodle WS errors."""

    def __init__(self, message: str = "Moodle Web Services error") -> None:
        self.message = message
        super().__init__(self.message)


class MoodleConnectionError(MoodleError):
    """Raised when the Moodle server is unreachable or times out.

    Maps to HTTP 502. Retries are applied for this error type.
    """

    def __init__(self, message: str = "Could not connect to Moodle server") -> None:
        super().__init__(message)


class MoodleAuthenticationError(MoodleError):
    """Raised when the WS token is invalid or expired.

    Maps to HTTP 502. No retry for this error type (invalid credentials).
    """

    def __init__(self, message: str = "Moodle Web Services authentication failed") -> None:
        super().__init__(message)


class MoodleServerError(MoodleError):
    """Raised when Moodle returns a 5xx or unexpected server error.

    Maps to HTTP 502. Retries are applied for this error type.
    """

    def __init__(self, message: str = "Moodle server error") -> None:
        super().__init__(message)
