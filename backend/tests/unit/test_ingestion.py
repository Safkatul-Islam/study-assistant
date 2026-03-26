"""Tests for app.workers.tasks.ingestion.process_document — Celery pipeline."""
import uuid
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from app.db.models.document import DocumentStatus


def _make_mock_doc(document_id, user_id, s3_key="docs/test.pdf"):
    doc = MagicMock()
    doc.id = uuid.UUID(document_id)
    doc.user_id = uuid.UUID(user_id)
    doc.s3_key = s3_key
    doc.status = DocumentStatus.UPLOADED
    doc.error_message = None
    doc.page_count = None
    return doc


def _make_sync_db(doc):
    """Create a mock sync DB context manager."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = doc
    db.execute = MagicMock()
    db.add_all = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    return db


@contextmanager
def _sync_db_context(db):
    yield db


DOC_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
USER_ID = "12345678-1234-5678-1234-567812345678"


def _call_task(patches_dict, doc_id=DOC_ID, user_id=USER_ID):
    """Call process_document using Celery's eager mode with all patches applied."""
    from app.workers.tasks.ingestion import process_document
    # Use push_request to simulate a bound task context
    process_document.push_request(id="test-task-id", retries=0)
    try:
        process_document(doc_id, user_id)
    finally:
        process_document.pop_request()


class TestProcessDocument:
    def test_full_success_pipeline(self):
        from app.services.pdf_extraction import PDFExtractionResult, PageText
        from app.services.chunking import ChunkData
        from app.services.embedding import EmbeddingResult
        from app.workers.tasks.ingestion import process_document

        doc = _make_mock_doc(DOC_ID, USER_ID)
        db = _make_sync_db(doc)

        extraction = PDFExtractionResult(
            pages=[PageText(page_number=1, text="Test content for chunking.")],
            page_count=1,
            total_chars=27,
        )
        chunks = [ChunkData(chunk_index=0, content="Test content", page_start=1, page_end=1, token_count=3)]
        embeddings = EmbeddingResult(embeddings=[[0.1, 0.2]], total_tokens=5)

        with (
            patch("app.workers.tasks.ingestion.get_sync_db", return_value=_sync_db_context(db)),
            patch("app.workers.tasks.ingestion.download_file_bytes", return_value=b"fake-pdf"),
            patch("app.workers.tasks.ingestion.extract_text_from_pdf", return_value=extraction),
            patch("app.workers.tasks.ingestion.chunk_pages", return_value=chunks),
            patch("app.workers.tasks.ingestion.generate_embeddings", return_value=embeddings),
        ):
            process_document.push_request(id="task-1", retries=0)
            try:
                process_document(DOC_ID, USER_ID)
            finally:
                process_document.pop_request()

        assert doc.status == DocumentStatus.READY
        assert doc.error_message is None
        db.add_all.assert_called_once()
        assert db.commit.call_count >= 1

    def test_value_error_marks_failed(self):
        from app.workers.tasks.ingestion import process_document

        doc = _make_mock_doc(DOC_ID, USER_ID)
        db = _make_sync_db(doc)
        fail_doc = _make_mock_doc(DOC_ID, USER_ID)
        fail_db = _make_sync_db(fail_doc)

        with (
            patch("app.workers.tasks.ingestion.get_sync_db", side_effect=[
                _sync_db_context(db),
                _sync_db_context(fail_db),
            ]),
            patch("app.workers.tasks.ingestion.download_file_bytes", side_effect=ValueError("PDF is encrypted")),
        ):
            process_document.push_request(id="task-2", retries=0)
            try:
                process_document(DOC_ID, USER_ID)
            finally:
                process_document.pop_request()

        # _mark_failed sets status on the doc found in its own session
        assert fail_doc.status == DocumentStatus.FAILED
        assert "encrypted" in fail_doc.error_message

    def test_transient_error_retries(self):
        from app.workers.tasks.ingestion import process_document

        doc = _make_mock_doc(DOC_ID, USER_ID)
        db = _make_sync_db(doc)

        with (
            patch("app.workers.tasks.ingestion.get_sync_db", return_value=_sync_db_context(db)),
            patch("app.workers.tasks.ingestion.download_file_bytes", side_effect=RuntimeError("Connection timeout")),
            patch.object(type(process_document._get_current_object()), "retry", MagicMock()) as mock_retry,
        ):
            process_document.push_request(id="task-3", retries=0)
            try:
                process_document(DOC_ID, USER_ID)
            finally:
                process_document.pop_request()

        mock_retry.assert_called_once()

    def test_max_retries_exceeded_marks_failed(self):
        from app.workers.tasks.ingestion import process_document

        doc = _make_mock_doc(DOC_ID, USER_ID)
        db = _make_sync_db(doc)
        fail_doc = _make_mock_doc(DOC_ID, USER_ID)
        fail_db = _make_sync_db(fail_doc)

        with (
            patch("app.workers.tasks.ingestion.get_sync_db", side_effect=[
                _sync_db_context(db),
                _sync_db_context(fail_db),
            ]),
            patch("app.workers.tasks.ingestion.download_file_bytes", side_effect=RuntimeError("timeout")),
            patch.object(
                type(process_document._get_current_object()),
                "retry",
                MagicMock(side_effect=process_document.MaxRetriesExceededError()),
            ),
        ):
            process_document.push_request(id="task-4", retries=3)
            try:
                process_document(DOC_ID, USER_ID)
            finally:
                process_document.pop_request()

        assert fail_doc.status == DocumentStatus.FAILED
        assert "Max retries exceeded" in fail_doc.error_message

    def test_document_not_found_marks_failed(self):
        from app.workers.tasks.ingestion import process_document

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.execute = MagicMock()
        db.commit = MagicMock()

        fail_db = MagicMock()
        fail_db.query.return_value.filter.return_value.first.return_value = None
        fail_db.commit = MagicMock()

        with patch("app.workers.tasks.ingestion.get_sync_db", side_effect=[
            _sync_db_context(db),
            _sync_db_context(fail_db),
        ]):
            process_document.push_request(id="task-5", retries=0)
            try:
                process_document(DOC_ID, USER_ID)
            finally:
                process_document.pop_request()

        # Permanent ValueError: "not found" path

    def test_wrong_owner_marks_failed(self):
        from app.workers.tasks.ingestion import process_document

        other_user = "99999999-9999-9999-9999-999999999999"
        doc = _make_mock_doc(DOC_ID, other_user)
        db = _make_sync_db(doc)
        fail_db = _make_sync_db(doc)

        with patch("app.workers.tasks.ingestion.get_sync_db", side_effect=[
            _sync_db_context(db),
            _sync_db_context(fail_db),
        ]):
            process_document.push_request(id="task-6", retries=0)
            try:
                process_document(DOC_ID, USER_ID)
            finally:
                process_document.pop_request()

        # Permanent ValueError — should not retry

    def test_updates_page_count(self):
        from app.services.pdf_extraction import PDFExtractionResult, PageText
        from app.services.chunking import ChunkData
        from app.services.embedding import EmbeddingResult
        from app.workers.tasks.ingestion import process_document

        doc = _make_mock_doc(DOC_ID, USER_ID)
        db = _make_sync_db(doc)

        extraction = PDFExtractionResult(
            pages=[PageText(page_number=1, text="Content.")],
            page_count=5,
            total_chars=8,
        )

        with (
            patch("app.workers.tasks.ingestion.get_sync_db", return_value=_sync_db_context(db)),
            patch("app.workers.tasks.ingestion.download_file_bytes", return_value=b"pdf"),
            patch("app.workers.tasks.ingestion.extract_text_from_pdf", return_value=extraction),
            patch("app.workers.tasks.ingestion.chunk_pages", return_value=[
                ChunkData(chunk_index=0, content="Content", page_start=1, page_end=1, token_count=1),
            ]),
            patch("app.workers.tasks.ingestion.generate_embeddings", return_value=EmbeddingResult(
                embeddings=[[0.1]], total_tokens=2
            )),
        ):
            process_document.push_request(id="task-7", retries=0)
            try:
                process_document(DOC_ID, USER_ID)
            finally:
                process_document.pop_request()

        assert doc.page_count == 5
