import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def mock_db():
    """Mock async database session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.flush = AsyncMock()
    db.delete = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def user_id():
    return uuid.UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def other_user_id():
    return uuid.UUID("87654321-4321-8765-4321-876543218765")


@pytest.fixture
def document_id():
    return uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


@pytest.fixture
def mock_user(user_id):
    """Mock User ORM object."""
    user = MagicMock()
    user.id = user_id
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.is_active = True
    user.hashed_password = "$2b$12$mock_hashed_password"
    user.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    user.updated_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return user


@pytest.fixture
def mock_document(document_id, user_id):
    """Mock Document ORM object with READY status."""
    from app.db.models.document import DocumentStatus

    doc = MagicMock()
    doc.id = document_id
    doc.user_id = user_id
    doc.title = "Test Document"
    doc.file_name = "test.pdf"
    doc.file_size = 1024
    doc.page_count = 10
    doc.s3_key = "docs/test.pdf"
    doc.status = DocumentStatus.READY
    doc.error_message = None
    doc.summary_cache = None
    doc.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    doc.updated_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return doc


@pytest.fixture
def mock_chunks(document_id, user_id):
    """List of 3 mock Chunk ORM objects."""
    chunks = []
    for i in range(3):
        chunk = MagicMock()
        chunk.id = uuid.uuid4()
        chunk.document_id = document_id
        chunk.user_id = user_id
        chunk.chunk_index = i
        chunk.content = f"This is chunk {i} content about topic {i}."
        chunk.page_start = i + 1
        chunk.page_end = i + 1
        chunk.token_count = 50
        chunk.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        chunk.updated_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        chunks.append(chunk)
    return chunks
