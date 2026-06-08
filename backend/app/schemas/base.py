"""Base schema with project-wide Pydantic configuration."""

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict


class BaseSchema(PydanticBaseModel):
    """Base schema for all API response/request schemas.

    - ``from_attributes=True`` — enables ORM mode for SQLAlchemy models
    - ``extra='forbid'`` — rejects undeclared fields (prevents typos)
    """

    model_config: ConfigDict = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )
