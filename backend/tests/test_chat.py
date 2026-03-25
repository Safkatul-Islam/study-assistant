"""Tests for the chat service — citation extraction, message building, rate limiting."""
import json
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.services.chat import (
    CITATION_PATTERN,
    CitationData,
    _build_rag_messages,
    _extract_citations,
    _page_label,
)


def _make_chunk(chunk_id: str, content: str, page_start: int = 1, page_end: int = 2, token_count: int = 100):
    """Create a mock Chunk object."""
    chunk = MagicMock()
    chunk.id = uuid.UUID(chunk_id) if len(chunk_id) == 36 else chunk_id
    chunk.content = content
    chunk.page_start = page_start
    chunk.page_end = page_end
    chunk.token_count = token_count
    chunk.chunk_index = 0
    return chunk


def _make_message(role_value: str, content: str):
    """Create a mock ChatMessage."""
    msg = MagicMock()
    msg.role = MagicMock(value=role_value)
    msg.content = content
    return msg


class TestCitationPattern:
    def test_matches_valid_uuid(self):
        text = "Based on [CHUNK:12345678-1234-1234-1234-123456789abc] this is true."
        matches = CITATION_PATTERN.findall(text)
        assert matches == ["12345678-1234-1234-1234-123456789abc"]

    def test_matches_multiple(self):
        text = "[CHUNK:aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa] and [CHUNK:bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb]"
        matches = CITATION_PATTERN.findall(text)
        assert len(matches) == 2

    def test_no_match_for_invalid(self):
        text = "No citation [CHUNK:invalid] here"
        matches = CITATION_PATTERN.findall(text)
        # Pattern matches hex-dash sequences, "invalid" won't match
        assert matches == []


class TestExtractCitations:
    def test_extracts_citations_from_response(self):
        chunk_id = "12345678-1234-1234-1234-123456789abc"
        chunk = _make_chunk(chunk_id, "Some content about biology", page_start=5, page_end=6)

        response = f"The answer is X [CHUNK:{chunk_id}] and it's important."
        citations = _extract_citations(response, [chunk])

        assert len(citations) == 1
        assert citations[0].chunk_id == chunk_id
        assert citations[0].page_start == 5
        assert citations[0].page_end == 6
        assert citations[0].snippet == "Some content about biology"

    def test_deduplicates_citations(self):
        chunk_id = "12345678-1234-1234-1234-123456789abc"
        chunk = _make_chunk(chunk_id, "Content")

        response = f"First [CHUNK:{chunk_id}] and again [CHUNK:{chunk_id}]."
        citations = _extract_citations(response, [chunk])

        assert len(citations) == 1

    def test_ignores_unknown_chunk_ids(self):
        known_id = "12345678-1234-1234-1234-123456789abc"
        unknown_id = "99999999-9999-9999-9999-999999999999"
        chunk = _make_chunk(known_id, "Content")

        response = f"[CHUNK:{known_id}] and [CHUNK:{unknown_id}]"
        citations = _extract_citations(response, [chunk])

        assert len(citations) == 1
        assert citations[0].chunk_id == known_id

    def test_empty_response(self):
        chunk = _make_chunk("12345678-1234-1234-1234-123456789abc", "Content")
        citations = _extract_citations("No citations here.", [chunk])
        assert citations == []

    def test_snippet_truncation(self):
        chunk_id = "12345678-1234-1234-1234-123456789abc"
        long_content = "A" * 500
        chunk = _make_chunk(chunk_id, long_content)

        response = f"See [CHUNK:{chunk_id}]"
        citations = _extract_citations(response, [chunk])

        assert len(citations[0].snippet) == 200


class TestBuildRagMessages:
    def test_builds_system_prompt_with_context(self):
        chunk_id = "12345678-1234-1234-1234-123456789abc"
        chunk = _make_chunk(chunk_id, "Biology is the study of life", page_start=1, page_end=1)

        system_prompt, messages = _build_rag_messages(
            history=[],
            context_chunks=[chunk],
            user_message="What is biology?",
        )

        assert f"[CHUNK:{chunk_id}]" in system_prompt
        assert "Biology is the study of life" in system_prompt
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == "What is biology?"

    def test_includes_history(self):
        history = [
            _make_message("user", "Hello"),
            _make_message("assistant", "Hi there!"),
        ]

        _, messages = _build_rag_messages(
            history=history,
            context_chunks=[],
            user_message="What is biology?",
        )

        assert len(messages) == 3  # 2 history + 1 current
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "Hi there!"
        assert messages[2]["content"] == "What is biology?"

    def test_no_context_chunks(self):
        system_prompt, messages = _build_rag_messages(
            history=[],
            context_chunks=[],
            user_message="Hello",
        )

        assert "(No relevant content found)" in system_prompt
        assert len(messages) == 1


class TestPageLabel:
    def test_none_pages(self):
        assert _page_label(None, None) == "Pages unknown"

    def test_single_page(self):
        assert _page_label(5, 5) == "Page 5"

    def test_page_range(self):
        assert _page_label(3, 7) == "Pages 3-7"

    def test_start_only(self):
        assert _page_label(3, None) == "Page 3"
