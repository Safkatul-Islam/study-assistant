"""Tests for app.core.security — password hashing, JWT token creation and decoding."""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import pytest
from jose import jwt, JWTError

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

TEST_SECRET = "test-jwt-secret-key-for-unit-tests"
TEST_ALGORITHM = "HS256"


@pytest.fixture(autouse=True)
def mock_settings():
    """Override settings for deterministic JWT tests."""
    mock = MagicMock()
    mock.jwt_secret_key = TEST_SECRET
    mock.jwt_algorithm = TEST_ALGORITHM
    mock.jwt_access_token_expire_minutes = 30
    mock.jwt_refresh_token_expire_days = 7
    with patch("app.core.security.settings", mock):
        yield mock


class TestHashPassword:
    def test_returns_bcrypt_hash(self):
        hashed = hash_password("my-password")
        assert hashed != "my-password"
        assert hashed.startswith("$2b$")

    def test_different_passwords_different_hashes(self):
        h1 = hash_password("password1")
        h2 = hash_password("password2")
        assert h1 != h2


class TestVerifyPassword:
    def test_correct_password(self):
        hashed = hash_password("secret123")
        assert verify_password("secret123", hashed) is True

    def test_wrong_password(self):
        hashed = hash_password("secret123")
        assert verify_password("wrong", hashed) is False


class TestCreateAccessToken:
    def test_token_contains_subject_and_type(self):
        token = create_access_token("user-123")
        payload = jwt.decode(token, TEST_SECRET, algorithms=[TEST_ALGORITHM])
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_token_expiry_is_in_future(self):
        token = create_access_token("user-123")
        payload = jwt.decode(token, TEST_SECRET, algorithms=[TEST_ALGORITHM])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        assert exp > datetime.now(timezone.utc)


class TestCreateRefreshToken:
    def test_token_contains_subject_and_type(self):
        token = create_refresh_token("user-456")
        payload = jwt.decode(token, TEST_SECRET, algorithms=[TEST_ALGORITHM])
        assert payload["sub"] == "user-456"
        assert payload["type"] == "refresh"

    def test_refresh_expiry_longer_than_access(self):
        access = create_access_token("user-1")
        refresh = create_refresh_token("user-1")
        a_payload = jwt.decode(access, TEST_SECRET, algorithms=[TEST_ALGORITHM])
        r_payload = jwt.decode(refresh, TEST_SECRET, algorithms=[TEST_ALGORITHM])
        assert r_payload["exp"] > a_payload["exp"]


class TestDecodeToken:
    def test_valid_token(self):
        token = create_access_token("user-789")
        payload = decode_token(token)
        assert payload["sub"] == "user-789"
        assert payload["type"] == "access"

    def test_expired_token_raises(self):
        expired_payload = {
            "sub": "user-1",
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        token = jwt.encode(expired_payload, TEST_SECRET, algorithm=TEST_ALGORITHM)
        with pytest.raises(JWTError):
            decode_token(token)

    def test_invalid_token_raises(self):
        with pytest.raises(JWTError):
            decode_token("not-a-real-token")
