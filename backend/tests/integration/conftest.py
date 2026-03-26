"""Integration test fixtures for FastAPI endpoint testing.

Provides a configured async HTTP client with dependency overrides
for the database session and current user authentication.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.models.document import DocumentStatus


# ---------------------------------------------------------------------------
# Stable test IDs
# ---------------------------------------------------------------------------

TEST_USER_ID = uuid.UUID("12345678-1234-5678-1234-567812345678")
TEST_DOCUMENT_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
TEST_SESSION_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
TEST_FLASHCARD_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Mock factories
# ---------------------------------------------------------------------------


def _make_mock_user(
    user_id: uuid.UUID = TEST_USER_ID,
    email: str = "test@example.com",
    full_name: str = "Test User",
) -> MagicMock:
    user = MagicMock()
    user.id = user_id
    user.email = email
    user.full_name = full_name
    user.is_active = True
    user.hashed_password = "$2b$12$mock_hashed_password"
    user.created_at = NOW
    user.updated_at = NOW
    return user


def _make_mock_document(
    doc_id: uuid.UUID = TEST_DOCUMENT_ID,
    user_id: uuid.UUID = TEST_USER_ID,
    status: DocumentStatus = DocumentStatus.READY,
) -> MagicMock:
    doc = MagicMock()
    # Use string id so Pydantic DocumentOut (id: str, from_attributes=True) validates
    doc.id = str(doc_id)
    doc.user_id = user_id
    doc.title = "Test Document"
    doc.file_name = "test.pdf"
    doc.file_size = 1024
    doc.page_count = 10
    doc.s3_key = f"{user_id}/{doc_id}/test.pdf"
    doc.status = status
    doc.error_message = None
    doc.summary_cache = None
    doc.created_at = NOW
    doc.updated_at = NOW
    return doc


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_user():
    return _make_mock_user()


@pytest.fixture
def mock_document():
    return _make_mock_document()


@pytest.fixture
def mock_db():
    """Async database session mock with common methods."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.flush = AsyncMock()
    db.delete = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def test_app(mock_db, mock_user):
    """FastAPI app with dependency overrides for DB and auth."""
    from app.db.session import get_db
    from app.dependencies import get_current_user
    from app.main import app

    async def _override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    yield app

    app.dependency_overrides.clear()


@pytest.fixture
def test_app_no_auth(mock_db):
    """FastAPI app with only DB override — no auth bypass.

    Use this for auth endpoint tests where we mock the service layer instead.
    """
    from app.db.session import get_db
    from app.main import app

    async def _override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = _override_get_db

    yield app

    app.dependency_overrides.clear()


@pytest.fixture
async def client(test_app):
    """Async HTTP client pointed at /api/v1."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as ac:
        yield ac


@pytest.fixture
async def root_client(test_app):
    """Async HTTP client pointed at the root (for /health)."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_client(test_app_no_auth):
    """Async HTTP client for auth tests (no auth bypass)."""
    transport = ASGITransport(app=test_app_no_auth)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as ac:
        yield ac
