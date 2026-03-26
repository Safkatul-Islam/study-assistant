"""Integration tests for /api/v1/auth endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.errors import AppError, ConflictError
from tests.integration.conftest import NOW, TEST_USER_ID, _make_mock_user


def _tokens_dict():
    return {
        "access_token": "mock-access-token",
        "refresh_token": "mock-refresh-token",
    }


class TestRegister:
    @pytest.fixture(autouse=True)
    def _setup_patches(self):
        self._register_patch = patch("app.api.auth.router.register_user", new_callable=AsyncMock)
        self._tokens_patch = patch("app.api.auth.router.generate_tokens")
        self.mock_register = self._register_patch.start()
        self.mock_tokens = self._tokens_patch.start()
        yield
        self._register_patch.stop()
        self._tokens_patch.stop()

    async def test_register_success_201(self, auth_client):
        user = _make_mock_user()
        self.mock_register.return_value = user
        self.mock_tokens.return_value = _tokens_dict()

        resp = await auth_client.post(
            "/auth/register",
            json={"email": "new@example.com", "password": "securepass123", "full_name": "New User"},
        )

        assert resp.status_code == 201
        body = resp.json()
        assert body["ok"] is True
        assert body["access_token"] == "mock-access-token"
        assert body["refresh_token"] == "mock-refresh-token"
        assert body["user"]["email"] == "test@example.com"

    async def test_register_duplicate_email_409(self, auth_client):
        self.mock_register.side_effect = ConflictError("A user with this email already exists")

        resp = await auth_client.post(
            "/auth/register",
            json={"email": "dup@example.com", "password": "securepass123", "full_name": "Dup User"},
        )

        assert resp.status_code == 409
        body = resp.json()
        assert body["ok"] is False

    async def test_register_short_password_422(self, auth_client):
        resp = await auth_client.post(
            "/auth/register",
            json={"email": "x@example.com", "password": "short", "full_name": "X"},
        )

        assert resp.status_code == 422

    async def test_register_invalid_email_422(self, auth_client):
        resp = await auth_client.post(
            "/auth/register",
            json={"email": "not-an-email", "password": "securepass123", "full_name": "X"},
        )

        assert resp.status_code == 422

    async def test_register_missing_name_422(self, auth_client):
        resp = await auth_client.post(
            "/auth/register",
            json={"email": "x@example.com", "password": "securepass123"},
        )

        assert resp.status_code == 422


class TestLogin:
    @pytest.fixture(autouse=True)
    def _setup_patches(self):
        self._auth_patch = patch("app.api.auth.router.authenticate_user", new_callable=AsyncMock)
        self._tokens_patch = patch("app.api.auth.router.generate_tokens")
        self.mock_auth = self._auth_patch.start()
        self.mock_tokens = self._tokens_patch.start()
        yield
        self._auth_patch.stop()
        self._tokens_patch.stop()

    async def test_login_success_200(self, auth_client):
        user = _make_mock_user()
        self.mock_auth.return_value = user
        self.mock_tokens.return_value = _tokens_dict()

        resp = await auth_client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "correctpass"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["access_token"] == "mock-access-token"
        assert body["user"]["id"] == str(TEST_USER_ID)

    async def test_login_wrong_email_401(self, auth_client):
        self.mock_auth.side_effect = AppError(status_code=401, message="Invalid email or password")

        resp = await auth_client.post(
            "/auth/login",
            json={"email": "wrong@example.com", "password": "pass12345678"},
        )

        assert resp.status_code == 401
        assert resp.json()["ok"] is False

    async def test_login_wrong_password_401(self, auth_client):
        self.mock_auth.side_effect = AppError(status_code=401, message="Invalid email or password")

        resp = await auth_client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "wrongpass123"},
        )

        assert resp.status_code == 401


class TestRefresh:
    @pytest.fixture(autouse=True)
    def _setup_patches(self):
        self._refresh_patch = patch("app.api.auth.router.refresh_tokens", new_callable=AsyncMock)
        self.mock_refresh = self._refresh_patch.start()
        yield
        self._refresh_patch.stop()

    async def test_refresh_success_200(self, auth_client):
        user = _make_mock_user()
        self.mock_refresh.return_value = (user, _tokens_dict())

        resp = await auth_client.post(
            "/auth/refresh",
            json={"refresh_token": "valid-refresh-token"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["access_token"] == "mock-access-token"

    async def test_refresh_invalid_token_401(self, auth_client):
        self.mock_refresh.side_effect = AppError(
            status_code=401, message="Invalid or expired refresh token"
        )

        resp = await auth_client.post(
            "/auth/refresh",
            json={"refresh_token": "bad-token"},
        )

        assert resp.status_code == 401
        assert resp.json()["ok"] is False


class TestMe:
    async def test_me_returns_user_200(self, client, mock_user):
        resp = await client.get("/auth/me")

        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["user"]["email"] == mock_user.email
        assert body["user"]["full_name"] == mock_user.full_name

    async def test_me_no_auth_401(self, auth_client):
        """Without the auth override, missing token should 401."""
        resp = await auth_client.get("/auth/me")

        assert resp.status_code == 401
