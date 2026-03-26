"""Tests for the usage logging service."""
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.db.models.usage_log import UsageAction
from app.services.usage import log_usage


class TestLogUsage:
    @pytest.mark.anyio
    async def test_creates_usage_log(self):
        db = AsyncMock()
        user_id = uuid.uuid4()
        doc_id = uuid.uuid4()

        result = await log_usage(
            db=db,
            user_id=user_id,
            action=UsageAction.CHAT,
            tokens_used=150,
            document_id=doc_id,
            metadata={"model": "claude-sonnet"},
        )

        db.add.assert_called_once()
        db.flush.assert_awaited_once()

        # Verify the UsageLog that was added
        added_log = db.add.call_args[0][0]
        assert added_log.user_id == user_id
        assert added_log.action == UsageAction.CHAT
        assert added_log.tokens_used == 150
        assert added_log.document_id == doc_id
        assert json.loads(added_log.metadata_json) == {"model": "claude-sonnet"}

    @pytest.mark.anyio
    async def test_none_metadata(self):
        db = AsyncMock()

        await log_usage(
            db=db,
            user_id=uuid.uuid4(),
            action=UsageAction.SUMMARY,
            tokens_used=500,
        )

        added_log = db.add.call_args[0][0]
        assert added_log.metadata_json is None
        assert added_log.document_id is None
