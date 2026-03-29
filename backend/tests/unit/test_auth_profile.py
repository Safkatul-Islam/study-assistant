"""Tests for auth profile service functions — update_profile, change_password."""

from unittest.mock import patch

import pytest

from app.core.errors import AppError
from app.api.auth.service import change_password, update_profile


class TestUpdateProfile:
    @pytest.mark.anyio
    async def test_updates_full_name(self, mock_db, mock_user):
        result = await update_profile(mock_db, mock_user, "Updated Name")

        assert mock_user.full_name == "Updated Name"
        mock_db.flush.assert_awaited_once()
        assert result is mock_user


class TestChangePassword:
    @pytest.mark.anyio
    async def test_success(self, mock_db, mock_user):
        with (
            patch("app.api.auth.service.verify_password", return_value=True),
            patch("app.api.auth.service.hash_password", return_value="new_hashed_pw"),
        ):
            await change_password(mock_db, mock_user, "current_pass", "new_pass123")

        assert mock_user.hashed_password == "new_hashed_pw"
        mock_db.flush.assert_awaited_once()

    @pytest.mark.anyio
    async def test_wrong_current_password_raises_400(self, mock_db, mock_user):
        with patch("app.api.auth.service.verify_password", return_value=False):
            with pytest.raises(AppError) as exc_info:
                await change_password(mock_db, mock_user, "wrong_pass", "new_pass123")

            assert exc_info.value.status_code == 400
            assert "incorrect" in exc_info.value.message.lower()
