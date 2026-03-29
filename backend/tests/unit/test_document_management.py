"""Tests for document management service functions — rename, tags, download URL."""

import json
from unittest.mock import patch

import pytest

from app.api.documents.service import (
    get_download_url,
    rename_document,
    update_document_tags,
)


class TestRenameDocument:
    @pytest.mark.anyio
    async def test_updates_title(self, mock_db, mock_document):
        result = await rename_document(mock_db, mock_document, "New Title")

        assert mock_document.title == "New Title"
        mock_db.flush.assert_awaited_once()
        assert result is mock_document


class TestUpdateDocumentTags:
    @pytest.mark.anyio
    async def test_with_tags(self, mock_db, mock_document):
        tags = ["physics", "chapter-1", "exam-prep"]

        result = await update_document_tags(mock_db, mock_document, tags)

        assert mock_document.tags == json.dumps(tags)
        mock_db.flush.assert_awaited_once()
        assert result is mock_document

    @pytest.mark.anyio
    async def test_empty_list_sets_none(self, mock_db, mock_document):
        result = await update_document_tags(mock_db, mock_document, [])

        assert mock_document.tags is None
        mock_db.flush.assert_awaited_once()
        assert result is mock_document


class TestGetDownloadUrl:
    def test_calls_generate_presigned_download_url(self, mock_document):
        mock_document.s3_key = "users/abc/doc123/notes.pdf"

        with patch(
            "app.api.documents.service.generate_presigned_download_url",
            return_value="https://s3.example.com/download?signed=1",
        ) as mock_presigned:
            url = get_download_url(mock_document)

        mock_presigned.assert_called_once_with("users/abc/doc123/notes.pdf")
        assert url == "https://s3.example.com/download?signed=1"
