"""Tests for app.dependencies.get_current_user — JWT extraction and validation."""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from jose import JWTError

from app.core.errors import AppError
from app.dependencies import get_current_user


def _mock_scalar_result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


class TestGetCurrentUser:
    @pytest.mark.anyio
    async def test_bearer_header_happy_path(self, mock_db, mock_user):
        mock_db.execute.return_value = _mock_scalar_result(mock_user)

        with patch(
            "app.dependencies.decode_token",
            return_value={"type": "access", "sub": str(mock_user.id)},
        ):
            user = await get_current_user(
                db=mock_db,
                authorization=f"Bearer valid_token",
                access_token=None,
            )

        assert user.id == mock_user.id

    @pytest.mark.anyio
    async def test_cookie_fallback(self, mock_db, mock_user):
        mock_db.execute.return_value = _mock_scalar_result(mock_user)

        with patch(
            "app.dependencies.decode_token",
            return_value={"type": "access", "sub": str(mock_user.id)},
        ):
            user = await get_current_user(
                db=mock_db,
                authorization=None,
                access_token="cookie_token",
            )

        assert user.id == mock_user.id

    @pytest.mark.anyio
    async def test_no_token_raises_401(self, mock_db):
        with pytest.raises(AppError) as exc_info:
            await get_current_user(db=mock_db, authorization=None, access_token=None)
        assert exc_info.value.status_code == 401
        assert "Not authenticated" in exc_info.value.message

    @pytest.mark.anyio
    async def test_invalid_token_raises_401(self, mock_db):
        with patch("app.dependencies.decode_token", side_effect=JWTError("bad")):
            with pytest.raises(AppError) as exc_info:
                await get_current_user(
                    db=mock_db,
                    authorization="Bearer bad_token",
                    access_token=None,
                )
            assert exc_info.value.status_code == 401
            assert "expired" in exc_info.value.message.lower() or "invalid" in exc_info.value.message.lower()

    @pytest.mark.anyio
    async def test_wrong_token_type_raises_401(self, mock_db):
        with patch(
            "app.dependencies.decode_token",
            return_value={"type": "refresh", "sub": str(uuid.uuid4())},
        ):
            with pytest.raises(AppError) as exc_info:
                await get_current_user(
                    db=mock_db,
                    authorization="Bearer refresh_token",
                    access_token=None,
                )
            assert exc_info.value.status_code == 401
            assert "token type" in exc_info.value.message.lower()

    @pytest.mark.anyio
    async def test_missing_sub_raises_401(self, mock_db):
        with patch(
            "app.dependencies.decode_token",
            return_value={"type": "access"},
        ):
            with pytest.raises(AppError) as exc_info:
                await get_current_user(
                    db=mock_db,
                    authorization="Bearer no_sub",
                    access_token=None,
                )
            assert exc_info.value.status_code == 401

    @pytest.mark.anyio
    async def test_inactive_user_raises_401(self, mock_db, mock_user):
        mock_user.is_active = False
        mock_db.execute.return_value = _mock_scalar_result(mock_user)

        with patch(
            "app.dependencies.decode_token",
            return_value={"type": "access", "sub": str(mock_user.id)},
        ):
            with pytest.raises(AppError) as exc_info:
                await get_current_user(
                    db=mock_db,
                    authorization="Bearer token",
                    access_token=None,
                )
            assert exc_info.value.status_code == 401

    @pytest.mark.anyio
    async def test_user_not_found_raises_401(self, mock_db):
        mock_db.execute.return_value = _mock_scalar_result(None)

        with patch(
            "app.dependencies.decode_token",
            return_value={"type": "access", "sub": str(uuid.uuid4())},
        ):
            with pytest.raises(AppError) as exc_info:
                await get_current_user(
                    db=mock_db,
                    authorization="Bearer token",
                    access_token=None,
                )
            assert exc_info.value.status_code == 401

    @pytest.mark.anyio
    async def test_bearer_header_preferred_over_cookie(self, mock_db, mock_user):
        """When both header and cookie are present, header takes precedence."""
        mock_db.execute.return_value = _mock_scalar_result(mock_user)

        with patch(
            "app.dependencies.decode_token",
            return_value={"type": "access", "sub": str(mock_user.id)},
        ) as mock_decode:
            await get_current_user(
                db=mock_db,
                authorization="Bearer header_token",
                access_token="cookie_token",
            )

        # Should have decoded the header token, not the cookie
        mock_decode.assert_called_once_with("header_token")

    @pytest.mark.anyio
    async def test_non_bearer_header_falls_to_cookie(self, mock_db, mock_user):
        """If authorization header doesn't start with 'Bearer ', fall back to cookie."""
        mock_db.execute.return_value = _mock_scalar_result(mock_user)

        with patch(
            "app.dependencies.decode_token",
            return_value={"type": "access", "sub": str(mock_user.id)},
        ) as mock_decode:
            await get_current_user(
                db=mock_db,
                authorization="Basic abc",
                access_token="cookie_token",
            )

        mock_decode.assert_called_once_with("cookie_token")
