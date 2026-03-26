"""Tests for app.core.errors — error classes and handler."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.errors import (
    AppError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    ValidationError,
    app_error_handler,
)


class TestAppError:
    def test_status_code_and_message(self):
        err = AppError(status_code=500, message="Something broke")
        assert err.status_code == 500
        assert err.message == "Something broke"
        assert err.details is None

    def test_with_details(self):
        err = AppError(status_code=400, message="Bad", details={"field": "email"})
        assert err.details == {"field": "email"}


class TestNotFoundError:
    def test_default_message(self):
        err = NotFoundError()
        assert err.status_code == 404
        assert err.message == "Resource not found"

    def test_custom_resource(self):
        err = NotFoundError("Document")
        assert err.message == "Document not found"


class TestForbiddenError:
    def test_default_message(self):
        err = ForbiddenError()
        assert err.status_code == 403
        assert err.message == "Access denied"

    def test_custom_message(self):
        err = ForbiddenError("No permission")
        assert err.message == "No permission"


class TestConflictError:
    def test_default_message(self):
        err = ConflictError()
        assert err.status_code == 409
        assert err.message == "Resource already exists"


class TestRateLimitError:
    def test_default_message(self):
        err = RateLimitError()
        assert err.status_code == 429
        assert err.message == "Rate limit exceeded"


class TestValidationError:
    def test_status_code(self):
        err = ValidationError(message="Invalid input", details=["field required"])
        assert err.status_code == 422
        assert err.details == ["field required"]


class TestAppErrorHandler:
    @pytest.mark.anyio
    async def test_response_format(self):
        request = MagicMock()
        err = AppError(status_code=404, message="Not found", details={"id": "123"})

        response = await app_error_handler(request, err)

        assert response.status_code == 404
        import json
        body = json.loads(response.body)
        assert body["ok"] is False
        assert body["error"]["message"] == "Not found"
        assert body["error"]["details"] == {"id": "123"}

    @pytest.mark.anyio
    async def test_response_no_details(self):
        request = MagicMock()
        err = AppError(status_code=500, message="Oops")

        response = await app_error_handler(request, err)

        import json
        body = json.loads(response.body)
        assert body["error"]["details"] is None
