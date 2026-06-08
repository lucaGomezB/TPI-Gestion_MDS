"""Pydantic models for Moodle Web Services API responses.

Each model represents a typed response from a Moodle WS function call,
using ``extra='forbid'`` to reject unexpected fields.
"""

from pydantic import BaseModel, ConfigDict


class MoodleGradeItem(BaseModel):
    """A single grade item (activity) from Moodle.

    Maps to a ``gradereport_user_get_grade_items`` response entry.
    """

    model_config = ConfigDict(extra="forbid")

    id: int
    itemname: str | None = None
    itemtype: str | None = None
    graderaw: float | None = None
    grademax: float | None = None
    grademin: float | None = None
    scaleid: int | None = None


class MoodleGrade(BaseModel):
    """A single grade entry for a user on a grade item.

    Maps to a ``core_grades_get_grades`` grade entry.
    """

    model_config = ConfigDict(extra="forbid")

    userid: int
    grade: str | None = None
    rawgrade: float | None = None
    grademax: float | None = None
    grademin: float | None = None
    feedback: str | None = None


class MoodleGradeResponse(BaseModel):
    """Response from ``core_grades_get_grades``.

    Contains all grade items and per-user grades for a course.
    """

    model_config = ConfigDict(extra="forbid")

    courseid: int
    grade_items: list[MoodleGradeItem] = []
    grades: list[MoodleGrade] = []


class MoodleEnrolledUser(BaseModel):
    """A user enrolled in a Moodle course.

    Maps to a ``core_enrol_get_enrolled_users`` response entry.
    """

    model_config = ConfigDict(extra="forbid")

    id: int
    username: str | None = None
    fullname: str | None = None
    email: str | None = None
    firstname: str | None = None
    lastname: str | None = None


class MoodleUserProfile(BaseModel):
    """A Moodle user profile from ``core_user_get_users``.

    Contains standard user profile fields.
    """

    model_config = ConfigDict(extra="forbid")

    id: int
    username: str | None = None
    fullname: str | None = None
    email: str | None = None
    firstname: str | None = None
    lastname: str | None = None
    department: str | None = None
    institution: str | None = None
