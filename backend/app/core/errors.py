from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class AppError(HTTPException):
    """Base application error with consistent envelope."""

    def __init__(self, status_code: int, message: str, details: Any = None):
        self.message = message
        self.details = details
        super().__init__(status_code=status_code, detail=message)


class NotFoundError(AppError):
    def __init__(self, resource: str = "Resource"):
        super().__init__(status_code=404, message=f"{resource} not found")


class ForbiddenError(AppError):
    def __init__(self, message: str = "Access denied"):
        super().__init__(status_code=403, message=message)


class ConflictError(AppError):
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(status_code=409, message=message)


class RateLimitError(AppError):
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(status_code=429, message=message)


class ValidationError(AppError):
    def __init__(self, message: str, details: Any = None):
        super().__init__(status_code=422, message=message, details=details)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "ok": False,
            "error": {
                "message": exc.message,
                "details": exc.details,
            },
        },
    )
