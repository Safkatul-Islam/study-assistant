"""Tests for app.api.auth.service — register, authenticate, tokens, refresh."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.errors import AppError, ConflictError
from app.api.auth.service import (
    authenticate_user,
    generate_tokens,
    refresh_tokens,
    register_user,
)


def _mock_scalar_result(value):
    """Create a mock execute result that returns value from scalar_one_or_none."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


class TestRegisterUser:
    @pytest.mark.anyio
    async def test_success(self, mock_db):
        mock_db.execute.return_value = _mock_scalar_result(None)

        with patch("app.api.auth.service.hash_password", return_value="hashed_pw"):
            user = await register_user(mock_db, "new@test.com", "pass123", "New User")

        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()
        added_user = mock_db.add.call_args[0][0]
        assert added_user.email == "new@test.com"
        assert added_user.hashed_password == "hashed_pw"
        assert added_user.full_name == "New User"

    @pytest.mark.anyio
    async def test_duplicate_email_raises_conflict(self, mock_db, mock_user):
        mock_db.execute.return_value = _mock_scalar_result(mock_user)

        with pytest.raises(ConflictError) as exc_info:
            await register_user(mock_db, "test@example.com", "pass", "Name")
        assert exc_info.value.status_code == 409


class TestAuthenticateUser:
    @pytest.mark.anyio
    async def test_success(self, mock_db, mock_user):
        mock_db.execute.return_value = _mock_scalar_result(mock_user)

        with patch("app.api.auth.service.verify_password", return_value=True):
            user = await authenticate_user(mock_db, "test@example.com", "correct")

        assert user.id == mock_user.id

    @pytest.mark.anyio
    async def test_wrong_email_raises_401(self, mock_db):
        mock_db.execute.return_value = _mock_scalar_result(None)

        with pytest.raises(AppError) as exc_info:
            await authenticate_user(mock_db, "no@user.com", "pass")
        assert exc_info.value.status_code == 401

    @pytest.mark.anyio
    async def test_wrong_password_raises_401(self, mock_db, mock_user):
        mock_db.execute.return_value = _mock_scalar_result(mock_user)

        with patch("app.api.auth.service.verify_password", return_value=False):
            with pytest.raises(AppError) as exc_info:
                await authenticate_user(mock_db, "test@example.com", "wrong")
            assert exc_info.value.status_code == 401

    @pytest.mark.anyio
    async def test_inactive_user_raises_401(self, mock_db, mock_user):
        mock_user.is_active = False
        mock_db.execute.return_value = _mock_scalar_result(mock_user)

        with patch("app.api.auth.service.verify_password", return_value=True):
            with pytest.raises(AppError) as exc_info:
                await authenticate_user(mock_db, "test@example.com", "pass")
            assert exc_info.value.status_code == 401
            assert "inactive" in exc_info.value.message.lower()


class TestGenerateTokens:
    def test_returns_access_and_refresh(self, mock_user):
        with (
            patch("app.api.auth.service.create_access_token", return_value="acc_tok"),
            patch("app.api.auth.service.create_refresh_token", return_value="ref_tok"),
        ):
            tokens = generate_tokens(mock_user)

        assert tokens["access_token"] == "acc_tok"
        assert tokens["refresh_token"] == "ref_tok"


class TestRefreshTokens:
    @pytest.mark.anyio
    async def test_success(self, mock_db, mock_user):
        user_id = str(mock_user.id)
        mock_db.execute.return_value = _mock_scalar_result(mock_user)

        with (
            patch("app.api.auth.service.decode_token", return_value={"type": "refresh", "sub": user_id}),
            patch("app.api.auth.service.create_access_token", return_value="new_acc"),
            patch("app.api.auth.service.create_refresh_token", return_value="new_ref"),
        ):
            user, tokens = await refresh_tokens(mock_db, "valid_refresh_token")

        assert user.id == mock_user.id
        assert tokens["access_token"] == "new_acc"

    @pytest.mark.anyio
    async def test_invalid_token_raises_401(self, mock_db):
        from jose import JWTError

        with patch("app.api.auth.service.decode_token", side_effect=JWTError("bad")):
            with pytest.raises(AppError) as exc_info:
                await refresh_tokens(mock_db, "bad_token")
            assert exc_info.value.status_code == 401

    @pytest.mark.anyio
    async def test_wrong_type_raises_401(self, mock_db):
        with patch("app.api.auth.service.decode_token", return_value={"type": "access", "sub": "id"}):
            with pytest.raises(AppError) as exc_info:
                await refresh_tokens(mock_db, "access_token_not_refresh")
            assert exc_info.value.status_code == 401

    @pytest.mark.anyio
    async def test_missing_sub_raises_401(self, mock_db):
        with patch("app.api.auth.service.decode_token", return_value={"type": "refresh"}):
            with pytest.raises(AppError) as exc_info:
                await refresh_tokens(mock_db, "no_sub_token")
            assert exc_info.value.status_code == 401

    @pytest.mark.anyio
    async def test_inactive_user_raises_401(self, mock_db, mock_user):
        mock_user.is_active = False
        mock_db.execute.return_value = _mock_scalar_result(mock_user)

        with patch("app.api.auth.service.decode_token", return_value={"type": "refresh", "sub": str(mock_user.id)}):
            with pytest.raises(AppError) as exc_info:
                await refresh_tokens(mock_db, "token")
            assert exc_info.value.status_code == 401

    @pytest.mark.anyio
    async def test_user_not_found_raises_401(self, mock_db):
        mock_db.execute.return_value = _mock_scalar_result(None)

        with patch("app.api.auth.service.decode_token", return_value={"type": "refresh", "sub": str(uuid.uuid4())}):
            with pytest.raises(AppError) as exc_info:
                await refresh_tokens(mock_db, "token")
            assert exc_info.value.status_code == 401
