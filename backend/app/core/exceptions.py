"""Application-level exception classes and standard HTTP exception handlers."""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse


class AppError(Exception):
    """Base exception for all application-level errors."""

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        status_code: int = 500,
    ) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def _sanitize_validation_errors(errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove non-JSON-serializable objects from Pydantic validation error ctx.

    Pydantic v2 stores the original ``ValueError`` (or other exception)
    in ``ctx['error']`` when a ``model_validator`` raises it.  Passing that
    object directly to ``json.dumps()`` raises ``TypeError: Object of type
    ValueError is not JSON serializable``.

    This function converts any ``Exception`` instance found inside ``ctx``
    to its string representation.
    """
    for error in errors:
        ctx = error.get("ctx")
        if isinstance(ctx, dict):
            error["ctx"] = {
                k: str(v) if isinstance(v, Exception) else v
                for k, v in ctx.items()
            }
    return errors


def register_exception_handlers(app: FastAPI) -> None:
    """Register standard HTTP exception handlers on the FastAPI app.

    Handles: 400, 401, 403, 404, 422, 500, 502
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        _request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"detail": _sanitize_validation_errors(exc.errors())},
        )

    @app.exception_handler(AppError)
    async def app_exception_handler(
        _request: Request, exc: AppError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
