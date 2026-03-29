"""Integration tests for M5 auth profile endpoints — PATCH /auth/me, PUT /auth/me/password."""

from unittest.mock import AsyncMock, patch

import pytest

from app.core.errors import AppError
from tests.integration.conftest import _make_mock_user


class TestUpdateProfile:
    @pytest.fixture(autouse=True)
    def _patches(self):
        self._update_patch = patch(
            "app.api.auth.router.update_profile", new_callable=AsyncMock
        )
        self.mock_update = self._update_patch.start()
        yield
        self._update_patch.stop()

    async def test_update_profile_success(self, client, mock_user):
        updated_user = _make_mock_user(full_name="Jane Doe")
        self.mock_update.return_value = updated_user

        resp = await client.patch("/auth/me", json={"full_name": "Jane Doe"})

        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["user"]["full_name"] == "Jane Doe"

    async def test_update_profile_empty_name_422(self, client):
        resp = await client.patch("/auth/me", json={"full_name": ""})

        assert resp.status_code == 422

    async def test_update_profile_unauthorized_401(self, auth_client):
        resp = await auth_client.patch("/auth/me", json={"full_name": "Jane Doe"})

        assert resp.status_code == 401


class TestChangePassword:
    @pytest.fixture(autouse=True)
    def _patches(self):
        self._change_patch = patch(
            "app.api.auth.router.change_password", new_callable=AsyncMock
        )
        self.mock_change = self._change_patch.start()
        yield
        self._change_patch.stop()

    async def test_change_password_success(self, client):
        self.mock_change.return_value = None

        resp = await client.put(
            "/auth/me/password",
            json={"current_password": "oldpass12345", "new_password": "newpass12345"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["message"] == "Password updated"

    async def test_change_password_wrong_current_400(self, client):
        self.mock_change.side_effect = AppError(
            status_code=400, message="Current password is incorrect"
        )

        resp = await client.put(
            "/auth/me/password",
            json={"current_password": "wrongpass123", "new_password": "newpass12345"},
        )

        assert resp.status_code == 400
        assert resp.json()["ok"] is False

    async def test_change_password_too_short_422(self, client):
        resp = await client.put(
            "/auth/me/password",
            json={"current_password": "oldpass12345", "new_password": "short"},
        )

        assert resp.status_code == 422
