"""Moodle Web Services integration package.

Exports the async Moodle WS client, response models, and custom exceptions
for external consumption by services and API routers.
"""

from app.integrations.exceptions import (
    MoodleAuthenticationError,
    MoodleConnectionError,
    MoodleError,
    MoodleServerError,
)
from app.integrations.models import (
    MoodleEnrolledUser,
    MoodleGrade,
    MoodleGradeItem,
    MoodleGradeResponse,
    MoodleUserProfile,
)
from app.integrations.moodle_ws import MoodleWSClient

__all__ = [
    "MoodleAuthenticationError",
    "MoodleConnectionError",
    "MoodleError",
    "MoodleServerError",
    "MoodleEnrolledUser",
    "MoodleGrade",
    "MoodleGradeItem",
    "MoodleGradeResponse",
    "MoodleUserProfile",
    "MoodleWSClient",
]
