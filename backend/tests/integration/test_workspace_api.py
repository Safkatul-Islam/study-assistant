"""Integration tests for /api/v1/documents/{id}/summary and chat endpoints."""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.errors import AppError, NotFoundError
from app.db.models.chat import MessageRole
from app.db.models.document import DocumentStatus
from app.services.summary import StructuredSummary
from tests.integration.conftest import (
    NOW,
    TEST_DOCUMENT_ID,
    TEST_SESSION_ID,
    TEST_USER_ID,
    _make_mock_document,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_chat_session(session_id=TEST_SESSION_ID):
    s = MagicMock()
    s.id = session_id
    s.title = "New Chat"
    s.created_at = NOW
    return s


def _mock_chat_message(role=MessageRole.ASSISTANT, content="Hello!", citations=None):
    m = MagicMock()
    m.id = uuid.uuid4()
    m.role = role
    m.content = content
    m.citations = json.dumps(citations) if citations else None
    m.created_at = NOW
    return m


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


class TestGetSummary:
    @pytest.fixture(autouse=True)
    def _patches(self):
        self._get_doc = patch(
            "app.api.workspace.router.get_user_document", new_callable=AsyncMock
        )
        self._summary = patch(
            "app.api.workspace.router.summary_service.get_or_generate_summary",
            new_callable=AsyncMock,
        )
        self.mock_get_doc = self._get_doc.start()
        self.mock_summary = self._summary.start()
        yield
        self._get_doc.stop()
        self._summary.stop()

    async def test_summary_success_200(self, client):
        doc = _make_mock_document(status=DocumentStatus.READY)
        self.mock_get_doc.return_value = doc

        summary = StructuredSummary(
            executive_summary=["Point A"],
            key_concepts=["Concept 1"],
            definitions={"term": "def"},
            possible_questions=["Q1?"],
        )
        self.mock_summary.return_value = (summary, True)

        resp = await client.get(f"/documents/{TEST_DOCUMENT_ID}/summary")

        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["cached"] is True
        assert body["summary"]["executive_summary"] == ["Point A"]

    async def test_summary_not_ready_422(self, client):
        doc = _make_mock_document(status=DocumentStatus.PROCESSING)
        self.mock_get_doc.return_value = doc

        resp = await client.get(f"/documents/{TEST_DOCUMENT_ID}/summary")

        assert resp.status_code == 422
        assert resp.json()["ok"] is False


# ---------------------------------------------------------------------------
# Chat — send message
# ---------------------------------------------------------------------------


class TestChat:
    @pytest.fixture(autouse=True)
    def _patches(self):
        self._get_doc = patch(
            "app.api.workspace.router.get_user_document", new_callable=AsyncMock
        )
        self._send = patch(
            "app.api.workspace.router.chat_service.send_message",
            new_callable=AsyncMock,
        )
        self.mock_get_doc = self._get_doc.start()
        self.mock_send = self._send.start()
        yield
        self._get_doc.stop()
        self._send.stop()

    async def test_send_message_200(self, client):
        doc = _make_mock_document(status=DocumentStatus.READY)
        self.mock_get_doc.return_value = doc

        session = _mock_chat_session()
        assistant_msg = _mock_chat_message(content="Here is the answer.")
        chat_result = MagicMock()
        self.mock_send.return_value = (session, assistant_msg, chat_result)

        resp = await client.post(
            f"/documents/{TEST_DOCUMENT_ID}/chat",
            json={"message": "What is this about?"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["session_id"] == str(TEST_SESSION_ID)
        assert body["message"]["content"] == "Here is the answer."

    async def test_chat_empty_message_422(self, client):
        resp = await client.post(
            f"/documents/{TEST_DOCUMENT_ID}/chat",
            json={"message": ""},
        )

        assert resp.status_code == 422

    async def test_chat_not_ready_422(self, client):
        doc = _make_mock_document(status=DocumentStatus.PROCESSING)
        self.mock_get_doc.return_value = doc

        resp = await client.post(
            f"/documents/{TEST_DOCUMENT_ID}/chat",
            json={"message": "Tell me something."},
        )

        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Chat — list sessions
# ---------------------------------------------------------------------------


class TestListSessions:
    @pytest.fixture(autouse=True)
    def _patches(self):
        self._get_doc = patch(
            "app.api.workspace.router.get_user_document", new_callable=AsyncMock
        )
        self._sessions = patch(
            "app.api.workspace.router.chat_service.get_document_sessions",
            new_callable=AsyncMock,
        )
        self.mock_get_doc = self._get_doc.start()
        self.mock_sessions = self._sessions.start()
        yield
        self._get_doc.stop()
        self._sessions.stop()

    async def test_list_sessions_200(self, client):
        doc = _make_mock_document(status=DocumentStatus.READY)
        self.mock_get_doc.return_value = doc

        session = _mock_chat_session()
        self.mock_sessions.return_value = [session]

        resp = await client.get(f"/documents/{TEST_DOCUMENT_ID}/chat")

        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert len(body["sessions"]) == 1
        assert body["sessions"][0]["id"] == str(TEST_SESSION_ID)

    async def test_list_sessions_empty_200(self, client):
        doc = _make_mock_document(status=DocumentStatus.READY)
        self.mock_get_doc.return_value = doc
        self.mock_sessions.return_value = []

        resp = await client.get(f"/documents/{TEST_DOCUMENT_ID}/chat")

        assert resp.status_code == 200
        assert resp.json()["sessions"] == []


# ---------------------------------------------------------------------------
# Chat — get history
# ---------------------------------------------------------------------------


class TestGetHistory:
    @pytest.fixture(autouse=True)
    def _patches(self):
        self._get_doc = patch(
            "app.api.workspace.router.get_user_document", new_callable=AsyncMock
        )
        self._history = patch(
            "app.api.workspace.router.chat_service.get_session_with_messages",
            new_callable=AsyncMock,
        )
        self.mock_get_doc = self._get_doc.start()
        self.mock_history = self._history.start()
        yield
        self._get_doc.stop()
        self._history.stop()

    async def test_get_history_200(self, client):
        doc = _make_mock_document(status=DocumentStatus.READY)
        self.mock_get_doc.return_value = doc

        session = _mock_chat_session()
        msg = _mock_chat_message(role=MessageRole.USER, content="Hi")
        self.mock_history.return_value = (session, [msg])

        resp = await client.get(
            f"/documents/{TEST_DOCUMENT_ID}/chat/{TEST_SESSION_ID}"
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["session"]["id"] == str(TEST_SESSION_ID)
        assert len(body["messages"]) == 1
        assert body["messages"][0]["role"] == "user"

    async def test_get_history_not_found_404(self, client):
        doc = _make_mock_document(status=DocumentStatus.READY)
        self.mock_get_doc.return_value = doc
        self.mock_history.side_effect = NotFoundError("Chat session")

        resp = await client.get(
            f"/documents/{TEST_DOCUMENT_ID}/chat/{TEST_SESSION_ID}"
        )

        assert resp.status_code == 404
