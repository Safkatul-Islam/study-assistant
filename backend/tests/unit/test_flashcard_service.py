"""Tests for app.services.flashcard — generation, parsing, CRUD, study queue."""
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import structlog

from app.core.errors import AppError, NotFoundError, RateLimitError
from app.db.models.flashcard import FlashcardDifficulty
from app.services.flashcard import (
    FlashcardItemSchema,
    FlashcardListSchema,
    GenerationResult,
    _check_daily_limit,
    _page_label,
    _parse_flashcard_json,
    generate_flashcards,
    get_flashcard,
    get_study_queue,
    update_flashcard,
)


@pytest.fixture
def log():
    return structlog.get_logger()


def _mock_scalar_one(value):
    result = MagicMock()
    result.scalar_one.return_value = value
    return result


def _mock_scalar_result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


def _mock_scalars_result(values):
    result = MagicMock()
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = values
    result.scalars.return_value = scalars_mock
    return result


# ---------------------------------------------------------------------------
# _parse_flashcard_json
# ---------------------------------------------------------------------------
class TestParseFlashcardJson:
    def test_valid_json(self, log):
        content = json.dumps({
            "flashcards": [
                {"front": "What is X?", "back": "X is Y.", "chunk_index": 0},
                {"front": "Define Z.", "back": "Z is W.", "chunk_index": 1},
            ]
        })
        result = _parse_flashcard_json(content, log)
        assert len(result) == 2
        assert result[0].front == "What is X?"
        assert result[1].chunk_index == 1

    def test_code_fenced_json(self, log):
        raw = '```json\n{"flashcards": [{"front": "Q?", "back": "A.", "chunk_index": 0}]}\n```'
        result = _parse_flashcard_json(raw, log)
        assert len(result) == 1
        assert result[0].front == "Q?"

    def test_invalid_json_raises_503(self, log):
        with pytest.raises(AppError) as exc_info:
            _parse_flashcard_json("not json {{{", log)
        assert exc_info.value.status_code == 503

    def test_missing_fields_raises_503(self, log):
        content = json.dumps({"flashcards": [{"front": "Q?"}]})  # missing back
        with pytest.raises(AppError) as exc_info:
            _parse_flashcard_json(content, log)
        assert exc_info.value.status_code == 503

    def test_empty_list(self, log):
        content = json.dumps({"flashcards": []})
        result = _parse_flashcard_json(content, log)
        assert result == []

    def test_truncation_to_max(self, log):
        cards = [{"front": f"Q{i}?", "back": f"A{i}.", "chunk_index": 0} for i in range(50)]
        content = json.dumps({"flashcards": cards})
        with patch("app.services.flashcard.settings", MagicMock(flashcard_max_per_document=10)):
            result = _parse_flashcard_json(content, log)
        assert len(result) == 10


# ---------------------------------------------------------------------------
# _check_daily_limit
# ---------------------------------------------------------------------------
class TestCheckDailyLimit:
    @pytest.mark.anyio
    async def test_under_limit_passes(self, mock_db, user_id):
        mock_db.execute.return_value = _mock_scalar_one(3)
        with patch("app.services.flashcard.settings", MagicMock(daily_flashcard_generation_limit=10)):
            await _check_daily_limit(mock_db, user_id)  # should not raise

    @pytest.mark.anyio
    async def test_at_limit_raises_429(self, mock_db, user_id):
        mock_db.execute.return_value = _mock_scalar_one(10)
        with patch("app.services.flashcard.settings", MagicMock(daily_flashcard_generation_limit=10)):
            with pytest.raises(RateLimitError):
                await _check_daily_limit(mock_db, user_id)


# ---------------------------------------------------------------------------
# generate_flashcards
# ---------------------------------------------------------------------------
class TestGenerateFlashcards:
    @pytest.mark.anyio
    async def test_cache_hit_returns_existing(self, mock_db, mock_document, user_id):
        """When existing flashcards exist and regenerate=False, return cached."""
        # _check_daily_limit returns under limit
        # count query returns 5 existing
        # select returns cached cards
        mock_cards = [MagicMock() for _ in range(5)]

        mock_db.execute.side_effect = [
            _mock_scalar_one(0),   # _check_daily_limit
            _mock_scalar_one(5),   # existing_count
            _mock_scalars_result(mock_cards),  # select existing
        ]

        result = await generate_flashcards(mock_db, mock_document, user_id, regenerate=False)

        assert result.was_cached is True
        assert result.generated_count == 5
        assert result.input_tokens == 0

    @pytest.mark.anyio
    async def test_cache_miss_generates_new(self, mock_db, mock_document, mock_chunks, user_id):
        """When no existing flashcards, generate via LLM."""
        from app.services.llm import LLMResponse

        llm_response = LLMResponse(
            content=json.dumps({"flashcards": [
                {"front": "Q1?", "back": "A1.", "chunk_index": 0},
            ]}),
            input_tokens=100,
            output_tokens=50,
        )

        mock_db.execute.side_effect = [
            _mock_scalar_one(0),                # _check_daily_limit
            _mock_scalar_one(0),                # existing_count = 0
            _mock_scalars_result(mock_chunks),  # fetch chunks
        ]

        with (
            patch("app.services.flashcard.llm.complete", new_callable=AsyncMock, return_value=llm_response),
            patch("app.services.flashcard.log_usage", new_callable=AsyncMock),
            patch("app.services.flashcard.settings", MagicMock(
                summary_max_context_tokens=100000,
                flashcard_max_per_document=30,
                flashcard_generation_temperature=0.4,
                anthropic_model="claude-sonnet-4-20250514",
                daily_flashcard_generation_limit=10,
            )),
        ):
            result = await generate_flashcards(mock_db, mock_document, user_id)

        assert result.was_cached is False
        assert result.generated_count == 1
        assert result.input_tokens == 100

    @pytest.mark.anyio
    async def test_regenerate_deletes_old(self, mock_db, mock_document, mock_chunks, user_id):
        """When regenerate=True, old flashcards are deleted first."""
        from app.services.llm import LLMResponse

        llm_response = LLMResponse(
            content=json.dumps({"flashcards": [
                {"front": "NewQ?", "back": "NewA.", "chunk_index": 0},
            ]}),
            input_tokens=80,
            output_tokens=40,
        )

        mock_db.execute.side_effect = [
            _mock_scalar_one(0),                # _check_daily_limit
            _mock_scalar_one(3),                # existing_count = 3
            MagicMock(),                        # delete old
            _mock_scalars_result(mock_chunks),  # fetch chunks
        ]

        with (
            patch("app.services.flashcard.llm.complete", new_callable=AsyncMock, return_value=llm_response),
            patch("app.services.flashcard.log_usage", new_callable=AsyncMock),
            patch("app.services.flashcard.settings", MagicMock(
                summary_max_context_tokens=100000,
                flashcard_max_per_document=30,
                flashcard_generation_temperature=0.4,
                anthropic_model="claude-sonnet-4-20250514",
                daily_flashcard_generation_limit=10,
            )),
        ):
            result = await generate_flashcards(mock_db, mock_document, user_id, regenerate=True)

        assert result.was_cached is False
        assert result.generated_count == 1

    @pytest.mark.anyio
    async def test_logs_usage(self, mock_db, mock_document, mock_chunks, user_id):
        """Usage logging should be called after generation."""
        from app.services.llm import LLMResponse

        llm_response = LLMResponse(
            content=json.dumps({"flashcards": [{"front": "Q?", "back": "A.", "chunk_index": 0}]}),
            input_tokens=50,
            output_tokens=25,
        )

        mock_db.execute.side_effect = [
            _mock_scalar_one(0),
            _mock_scalar_one(0),
            _mock_scalars_result(mock_chunks),
        ]

        with (
            patch("app.services.flashcard.llm.complete", new_callable=AsyncMock, return_value=llm_response),
            patch("app.services.flashcard.log_usage", new_callable=AsyncMock) as mock_log_usage,
            patch("app.services.flashcard.settings", MagicMock(
                summary_max_context_tokens=100000,
                flashcard_max_per_document=30,
                flashcard_generation_temperature=0.4,
                anthropic_model="claude-sonnet-4-20250514",
                daily_flashcard_generation_limit=10,
            )),
        ):
            await generate_flashcards(mock_db, mock_document, user_id)

        mock_log_usage.assert_awaited_once()


# ---------------------------------------------------------------------------
# get_study_queue
# ---------------------------------------------------------------------------
class TestGetStudyQueue:
    @pytest.mark.anyio
    async def test_returns_ordered_cards(self, mock_db, document_id, user_id):
        cards = [MagicMock(difficulty=FlashcardDifficulty.HARD), MagicMock(difficulty=FlashcardDifficulty.EASY)]
        mock_db.execute.return_value = _mock_scalars_result(cards)

        result = await get_study_queue(mock_db, document_id, user_id)

        assert len(result) == 2
        mock_db.execute.assert_called_once()


# ---------------------------------------------------------------------------
# get_flashcard
# ---------------------------------------------------------------------------
class TestGetFlashcard:
    @pytest.mark.anyio
    async def test_not_found_raises(self, mock_db, user_id):
        mock_db.execute.return_value = _mock_scalar_result(None)

        with pytest.raises(NotFoundError):
            await get_flashcard(mock_db, uuid.uuid4(), user_id)

    @pytest.mark.anyio
    async def test_found_returns_card(self, mock_db, user_id):
        card = MagicMock()
        mock_db.execute.return_value = _mock_scalar_result(card)

        result = await get_flashcard(mock_db, uuid.uuid4(), user_id)

        assert result is card


# ---------------------------------------------------------------------------
# update_flashcard
# ---------------------------------------------------------------------------
class TestUpdateFlashcard:
    @pytest.mark.anyio
    async def test_sets_last_reviewed_on_difficulty_change(self, mock_db, user_id):
        card = MagicMock()
        card.last_reviewed_at = None
        mock_db.execute.return_value = _mock_scalar_result(card)

        result = await update_flashcard(
            mock_db, uuid.uuid4(), user_id, difficulty=FlashcardDifficulty.HARD
        )

        assert result.difficulty == FlashcardDifficulty.HARD
        assert result.last_reviewed_at is not None

    @pytest.mark.anyio
    async def test_updates_front_and_back(self, mock_db, user_id):
        card = MagicMock()
        mock_db.execute.return_value = _mock_scalar_result(card)

        result = await update_flashcard(
            mock_db, uuid.uuid4(), user_id, front="New Q?", back="New A."
        )

        assert result.front == "New Q?"
        assert result.back == "New A."


# ---------------------------------------------------------------------------
# _page_label
# ---------------------------------------------------------------------------
class TestPageLabel:
    def test_none(self):
        assert _page_label(None, None) == "Pages unknown"

    def test_single(self):
        assert _page_label(3, 3) == "Page 3"

    def test_range(self):
        assert _page_label(1, 5) == "Pages 1-5"

    def test_end_none(self):
        assert _page_label(3, None) == "Page 3"
