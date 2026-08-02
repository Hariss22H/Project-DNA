"""Application-level HTTP exceptions and handlers."""

from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError
from starlette.exceptions import HTTPException as StarletteHTTPException

DB_UNAVAILABLE_MESSAGE = (
    "Cannot reach MongoDB right now. If you use MongoDB Atlas, open Network Access "
    "and allow your current IP (or 0.0.0.0/0 for the hackathon demo), then restart the API."
)


class AppError(Exception):
    """Domain error that maps to a consistent API error payload."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 400,
        code: str = "app_error",
        details: Optional[Any] = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details
        super().__init__(message)


def _error_body(
    *,
    code: str,
    message: str,
    details: Any = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
    }
    if details is not None:
        body["error"]["details"] = details
    return body


def register_exception_handlers(app: FastAPI) -> None:
    """Attach global exception handlers to the FastAPI app."""

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(code=exc.code, message=exc.message, details=exc.details),
        )

    @app.exception_handler(PyMongoError)
    async def mongo_error_handler(_: Request, exc: PyMongoError) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content=_error_body(
                code="database_unavailable",
                message=DB_UNAVAILABLE_MESSAGE,
                details=str(exc)[:300],
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail
        message = detail if isinstance(detail, str) else "Request failed"
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(code="http_error", message=message, details=detail if not isinstance(detail, str) else None),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_error_body(
                code="validation_error",
                message="Request validation failed",
                details=exc.errors(),
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
        # Motor/pymongo sometimes wraps timeout/SSL failures as generic Exceptions.
        text = str(exc)
        lowered = text.lower()
        if any(token in lowered for token in ("ssl handshake", "server selection timeout", "tlsv1_alert")):
            return JSONResponse(
                status_code=503,
                content=_error_body(
                    code="database_unavailable",
                    message=DB_UNAVAILABLE_MESSAGE,
                    details=text[:300],
                ),
            )
        return JSONResponse(
            status_code=500,
            content=_error_body(
                code="internal_error",
                message="An unexpected error occurred",
                details=text,
            ),
        )
