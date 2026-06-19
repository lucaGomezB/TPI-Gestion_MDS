"""Declarative base for all SQLAlchemy models.

Provides ``AppModel`` with:
- UUID primary key (auto-generated via Python uuid4)
- Automatic snake_case tablename derived from PascalCase class name
- Column defaults applied at Python instantiation time (not just flush)
"""

import re
from typing import Any
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
    - Column defaults (``mapped_column(default=...)``) applied at **Python init
      time**, not deferred to flush. This means ``model.attr`` reflects the
      default immediately after construction, enabling reliable unit-test
      assertions without a database session.
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

    def __init__(self, **kw: Any) -> None:
        """Construct instance, applying column defaults at Python level.

        SQLAlchemy 2.0 ``mapped_column(default=...)`` sets a *column-level*
        default that is applied during ORM flush, not at ``__init__`` time.
        This override ensures scalar and callable defaults are populated
        immediately on construction so that unit tests (which create models
        in memory without a session) see the expected default values.

        ``server_default`` columns (e.g. ``created_at``) are deliberately
        **not** populated here — they are server-side values that should
        remain ``None`` until the database assigns them.
        """
        # Set explicitly provided attributes (replicates the ORM-generated init)
        for k, v in kw.items():
            setattr(self, k, v)

        # Apply column-level defaults for attributes not explicitly provided.
        # SQLAlchemy 2.0 wraps callable defaults with __wrapped__ to inject
        # a ``ctx`` parameter for flush-time execution. We unwrap it here so
        # the default works at init time without a session context.
        mapper = self.__mapper__
        for col in mapper.columns:
            if col.key in kw:
                continue
            default = col.default
            if default is not None and not default.is_server_default:
                arg = default.arg
                if callable(arg):
                    # Unwrap SQLAlchemy's ctx-wrapped callable
                    original = getattr(arg, "__wrapped__", arg)
                    setattr(self, col.key, original())
                else:
                    setattr(self, col.key, arg)
