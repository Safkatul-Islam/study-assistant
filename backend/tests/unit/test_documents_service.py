"""Tests for app.api.documents.service — CRUD operations."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.errors import NotFoundError
from app.api.documents.service import (
    create_document,
    delete_user_document,
    get_user_document,
    get_user_documents,
    update_document_status,
)


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


class TestCreateDocument:
    @pytest.mark.anyio
    async def test_success(self, mock_db, user_id, document_id):
        doc = await create_document(
            db=mock_db,
            user_id=user_id,
            title="My Doc",
            file_name="doc.pdf",
            file_size=2048,
            s3_key="docs/doc.pdf",
            doc_id=document_id,
        )

        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()
        added = mock_db.add.call_args[0][0]
        assert added.title == "My Doc"
        assert added.file_name == "doc.pdf"
        assert added.user_id == user_id
        assert added.id == document_id

    @pytest.mark.anyio
    async def test_sets_uploaded_status(self, mock_db, user_id, document_id):
        from app.db.models.document import DocumentStatus

        await create_document(
            db=mock_db,
            user_id=user_id,
            title="Doc",
            file_name="f.pdf",
            file_size=100,
            s3_key="s3/key",
            doc_id=document_id,
        )

        added = mock_db.add.call_args[0][0]
        assert added.status == DocumentStatus.UPLOADED


class TestGetUserDocuments:
    @pytest.mark.anyio
    async def test_returns_list(self, mock_db, user_id, mock_document):
        mock_db.execute.return_value = _mock_scalars_result([mock_document])

        docs = await get_user_documents(mock_db, user_id)

        assert len(docs) == 1
        assert docs[0].id == mock_document.id

    @pytest.mark.anyio
    async def test_empty_list(self, mock_db, user_id):
        mock_db.execute.return_value = _mock_scalars_result([])

        docs = await get_user_documents(mock_db, user_id)

        assert docs == []


class TestGetUserDocument:
    @pytest.mark.anyio
    async def test_success(self, mock_db, mock_document, document_id, user_id):
        mock_db.execute.return_value = _mock_scalar_result(mock_document)

        doc = await get_user_document(mock_db, document_id, user_id)

        assert doc.id == document_id

    @pytest.mark.anyio
    async def test_not_found_raises(self, mock_db, document_id, user_id):
        mock_db.execute.return_value = _mock_scalar_result(None)

        with pytest.raises(NotFoundError) as exc_info:
            await get_user_document(mock_db, document_id, user_id)
        assert exc_info.value.status_code == 404

    @pytest.mark.anyio
    async def test_other_user_not_found(self, mock_db, document_id, other_user_id):
        mock_db.execute.return_value = _mock_scalar_result(None)

        with pytest.raises(NotFoundError):
            await get_user_document(mock_db, document_id, other_user_id)


class TestUpdateDocumentStatus:
    @pytest.mark.anyio
    async def test_updates_status(self, mock_db, mock_document):
        from app.db.models.document import DocumentStatus

        result = await update_document_status(mock_db, mock_document, DocumentStatus.PROCESSING)

        assert mock_document.status == DocumentStatus.PROCESSING
        mock_db.flush.assert_awaited_once()


class TestDeleteUserDocument:
    @pytest.mark.anyio
    async def test_success(self, mock_db, mock_document, document_id, user_id):
        mock_db.execute.return_value = _mock_scalar_result(mock_document)

        doc = await delete_user_document(mock_db, document_id, user_id)

        mock_db.delete.assert_called_once_with(mock_document)
        mock_db.flush.assert_awaited()

    @pytest.mark.anyio
    async def test_not_found_raises(self, mock_db, document_id, user_id):
        mock_db.execute.return_value = _mock_scalar_result(None)

        with pytest.raises(NotFoundError):
            await delete_user_document(mock_db, document_id, user_id)
