"""Declarative base for all SQLAlchemy models.

Provides ``AppModel`` with:
- UUID primary key (auto-generated via Python uuid4)
- Automatic snake_case tablename derived from PascalCase class name
"""

import re
from uuid import uuid4

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


def _snake_case(name: str) -> str:
    """Convert a PascalCase class name to snake_case.

    ``AppModel`` → ``app_model``
    ``CamelCaseModel`` → ``camel_case_model``
    """
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


class AppModel(DeclarativeBase):
    """Base class for all database models.

    Features:
    - UUID primary key (auto-generated via Python uuid4)
    - Automatic snake_case tablename derived from class name
    """

    __abstract__ = True

    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        return _snake_case(cls.__name__)  # type: ignore[return-value]

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
