"""Integration tests for /api/v1/documents/{id}/flashcards endpoints."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.errors import NotFoundError
from app.db.models.document import DocumentStatus
from app.db.models.flashcard import FlashcardDifficulty
from tests.integration.conftest import (
    NOW,
    TEST_DOCUMENT_ID,
    TEST_FLASHCARD_ID,
    TEST_USER_ID,
    _make_mock_document,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DOC_URL = f"/documents/{TEST_DOCUMENT_ID}/flashcards"
CARD_URL = f"{DOC_URL}/{TEST_FLASHCARD_ID}"


def _make_mock_flashcard(
    card_id=TEST_FLASHCARD_ID,
    difficulty=FlashcardDifficulty.UNRATED,
):
    card = MagicMock()
    card.id = card_id
    card.front = "What is X?"
    card.back = "X is Y."
    card.difficulty = difficulty
    card.source_chunk_id = None
    card.last_reviewed_at = None
    card.created_at = NOW
    card.updated_at = NOW
    return card


def _generation_result(cards, was_cached=False):
    r = MagicMock()
    r.flashcards = cards
    r.generated_count = len(cards)
    r.was_cached = was_cached
    return r


# ---------------------------------------------------------------------------
# Generate flashcards
# ---------------------------------------------------------------------------


class TestGenerateFlashcards:
    @pytest.fixture(autouse=True)
    def _patches(self):
        self._get_doc = patch(
            "app.api.workspace.router.get_user_document", new_callable=AsyncMock
        )
        self._generate = patch(
            "app.api.workspace.router.flashcard_service.generate_flashcards",
            new_callable=AsyncMock,
        )
        self.mock_get_doc = self._get_doc.start()
        self.mock_generate = self._generate.start()
        yield
        self._get_doc.stop()
        self._generate.stop()

    async def test_generate_success_200(self, client):
        doc = _make_mock_document(status=DocumentStatus.READY)
        self.mock_get_doc.return_value = doc

        card = _make_mock_flashcard()
        self.mock_generate.return_value = _generation_result([card], was_cached=False)

        resp = await client.post(DOC_URL)

        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["generated_count"] == 1
        assert body["was_cached"] is False
        assert body["flashcards"][0]["front"] == "What is X?"

    async def test_generate_cached_200(self, client):
        doc = _make_mock_document(status=DocumentStatus.READY)
        self.mock_get_doc.return_value = doc

        card = _make_mock_flashcard()
        self.mock_generate.return_value = _generation_result([card], was_cached=True)

        resp = await client.post(DOC_URL, json={"regenerate": False})

        assert resp.status_code == 200
        assert resp.json()["was_cached"] is True

    async def test_generate_not_ready_422(self, client):
        doc = _make_mock_document(status=DocumentStatus.PROCESSING)
        self.mock_get_doc.return_value = doc

        resp = await client.post(DOC_URL)

        assert resp.status_code == 422
        assert resp.json()["ok"] is False


# ---------------------------------------------------------------------------
# List flashcards
# ---------------------------------------------------------------------------


class TestListFlashcards:
    @pytest.fixture(autouse=True)
    def _patches(self):
        self._get_doc = patch(
            "app.api.workspace.router.get_user_document", new_callable=AsyncMock
        )
        self._list = patch(
            "app.api.workspace.router.flashcard_service.list_flashcards",
            new_callable=AsyncMock,
        )
        self.mock_get_doc = self._get_doc.start()
        self.mock_list = self._list.start()
        yield
        self._get_doc.stop()
        self._list.stop()

    async def test_list_success_200(self, client):
        doc = _make_mock_document(status=DocumentStatus.READY)
        self.mock_get_doc.return_value = doc

        card = _make_mock_flashcard()
        self.mock_list.return_value = ([card], 1)

        resp = await client.get(DOC_URL)

        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["total"] == 1
        assert len(body["flashcards"]) == 1

    async def test_list_with_difficulty_filter_200(self, client):
        doc = _make_mock_document(status=DocumentStatus.READY)
        self.mock_get_doc.return_value = doc

        card = _make_mock_flashcard(difficulty=FlashcardDifficulty.HARD)
        self.mock_list.return_value = ([card], 1)

        resp = await client.get(DOC_URL, params={"difficulty": "hard"})

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["flashcards"][0]["difficulty"] == "hard"

    async def test_list_empty_200(self, client):
        doc = _make_mock_document(status=DocumentStatus.READY)
        self.mock_get_doc.return_value = doc
        self.mock_list.return_value = ([], 0)

        resp = await client.get(DOC_URL)

        assert resp.status_code == 200
        assert resp.json()["flashcards"] == []
        assert resp.json()["total"] == 0


# ---------------------------------------------------------------------------
# Study queue
# ---------------------------------------------------------------------------


class TestStudyQueue:
    @pytest.fixture(autouse=True)
    def _patches(self):
        self._get_doc = patch(
            "app.api.workspace.router.get_user_document", new_callable=AsyncMock
        )
        self._queue = patch(
            "app.api.workspace.router.flashcard_service.get_study_queue",
            new_callable=AsyncMock,
        )
        self.mock_get_doc = self._get_doc.start()
        self.mock_queue = self._queue.start()
        yield
        self._get_doc.stop()
        self._queue.stop()

    async def test_study_queue_200(self, client, mock_db):
        doc = _make_mock_document(status=DocumentStatus.READY)
        self.mock_get_doc.return_value = doc

        card = _make_mock_flashcard()
        self.mock_queue.return_value = [card]

        # Mock the stats query executed directly in the router
        stats_row = MagicMock()
        stats_row.total = 5
        stats_row.unrated = 2
        stats_row.easy = 1
        stats_row.medium = 1
        stats_row.hard = 1

        stats_result = MagicMock()
        stats_result.one.return_value = stats_row
        mock_db.execute.return_value = stats_result

        resp = await client.get(f"{DOC_URL}/study")

        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert len(body["flashcards"]) == 1
        assert body["stats"]["total"] == 5
        assert body["stats"]["hard"] == 1


# ---------------------------------------------------------------------------
# Update flashcard
# ---------------------------------------------------------------------------


class TestUpdateFlashcard:
    @pytest.fixture(autouse=True)
    def _patches(self):
        self._get_doc = patch(
            "app.api.workspace.router.get_user_document", new_callable=AsyncMock
        )
        self._update = patch(
            "app.api.workspace.router.flashcard_service.update_flashcard",
            new_callable=AsyncMock,
        )
        self.mock_get_doc = self._get_doc.start()
        self.mock_update = self._update.start()
        yield
        self._get_doc.stop()
        self._update.stop()

    async def test_update_difficulty_200(self, client):
        doc = _make_mock_document(status=DocumentStatus.READY)
        self.mock_get_doc.return_value = doc

        updated = _make_mock_flashcard(difficulty=FlashcardDifficulty.HARD)
        self.mock_update.return_value = updated

        resp = await client.patch(CARD_URL, json={"difficulty": "hard"})

        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["flashcard"]["difficulty"] == "hard"

    async def test_update_content_200(self, client):
        doc = _make_mock_document(status=DocumentStatus.READY)
        self.mock_get_doc.return_value = doc

        updated = _make_mock_flashcard()
        updated.front = "New question?"
        updated.back = "New answer."
        self.mock_update.return_value = updated

        resp = await client.patch(CARD_URL, json={"front": "New question?", "back": "New answer."})

        assert resp.status_code == 200
        assert resp.json()["flashcard"]["front"] == "New question?"


# ---------------------------------------------------------------------------
# Delete single flashcard
# ---------------------------------------------------------------------------


class TestDeleteFlashcard:
    @pytest.fixture(autouse=True)
    def _patches(self):
        self._get_doc = patch(
            "app.api.workspace.router.get_user_document", new_callable=AsyncMock
        )
        self._delete = patch(
            "app.api.workspace.router.flashcard_service.delete_flashcard",
            new_callable=AsyncMock,
        )
        self.mock_get_doc = self._get_doc.start()
        self.mock_delete = self._delete.start()
        yield
        self._get_doc.stop()
        self._delete.stop()

    async def test_delete_single_200(self, client):
        doc = _make_mock_document(status=DocumentStatus.READY)
        self.mock_get_doc.return_value = doc

        resp = await client.delete(CARD_URL)

        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    async def test_delete_not_found_404(self, client):
        doc = _make_mock_document(status=DocumentStatus.READY)
        self.mock_get_doc.return_value = doc
        self.mock_delete.side_effect = NotFoundError("Flashcard")

        resp = await client.delete(CARD_URL)

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Delete all flashcards
# ---------------------------------------------------------------------------


class TestDeleteAllFlashcards:
    @pytest.fixture(autouse=True)
    def _patches(self):
        self._get_doc = patch(
            "app.api.workspace.router.get_user_document", new_callable=AsyncMock
        )
        self._delete_all = patch(
            "app.api.workspace.router.flashcard_service.delete_all_flashcards",
            new_callable=AsyncMock,
        )
        self.mock_get_doc = self._get_doc.start()
        self.mock_delete_all = self._delete_all.start()
        yield
        self._get_doc.stop()
        self._delete_all.stop()

    async def test_delete_all_200(self, client):
        doc = _make_mock_document(status=DocumentStatus.READY)
        self.mock_get_doc.return_value = doc
        self.mock_delete_all.return_value = 5

        resp = await client.delete(DOC_URL)

        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["deleted_count"] == 5

    async def test_delete_all_zero_200(self, client):
        doc = _make_mock_document(status=DocumentStatus.READY)
        self.mock_get_doc.return_value = doc
        self.mock_delete_all.return_value = 0

        resp = await client.delete(DOC_URL)

        assert resp.status_code == 200
        assert resp.json()["deleted_count"] == 0
