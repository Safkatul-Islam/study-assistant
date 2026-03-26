"""Integration tests for /api/v1/documents endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.errors import NotFoundError
from app.db.models.document import DocumentStatus
from tests.integration.conftest import (
    NOW,
    TEST_DOCUMENT_ID,
    TEST_USER_ID,
    _make_mock_document,
)


class TestInitUpload:
    @pytest.fixture(autouse=True)
    def _patches(self):
        self._create_doc = patch(
            "app.api.documents.router.create_document", new_callable=AsyncMock
        )
        self._presigned = patch(
            "app.api.documents.router.generate_presigned_upload_url",
            return_value="https://s3.example.com/upload?signed=1",
        )
        self.mock_create = self._create_doc.start()
        self.mock_presigned = self._presigned.start()
        yield
        self._create_doc.stop()
        self._presigned.stop()

    async def test_init_upload_success_201(self, client):
        doc = _make_mock_document(status=DocumentStatus.UPLOADED)
        self.mock_create.return_value = doc

        resp = await client.post(
            "/documents/init-upload",
            json={"file_name": "notes.pdf", "file_size": 5000, "content_type": "application/pdf"},
        )

        assert resp.status_code == 201
        body = resp.json()
        assert body["ok"] is True
        assert body["document_id"] == str(TEST_DOCUMENT_ID)
        assert "upload_url" in body

    async def test_init_upload_wrong_content_type_422(self, client):
        resp = await client.post(
            "/documents/init-upload",
            json={"file_name": "notes.docx", "file_size": 5000, "content_type": "application/msword"},
        )

        assert resp.status_code == 422
        assert resp.json()["ok"] is False


class TestCompleteUpload:
    @pytest.fixture(autouse=True)
    def _patches(self):
        self._get_doc = patch(
            "app.api.documents.router.get_user_document", new_callable=AsyncMock
        )
        self._update_status = patch(
            "app.api.documents.router.update_document_status", new_callable=AsyncMock
        )
        self._process = patch("app.api.documents.router.process_document")
        self.mock_get = self._get_doc.start()
        self.mock_update = self._update_status.start()
        self.mock_process = self._process.start()
        yield
        self._get_doc.stop()
        self._update_status.stop()
        self._process.stop()

    async def test_complete_upload_success_200(self, client):
        doc = _make_mock_document(status=DocumentStatus.UPLOADED)
        self.mock_get.return_value = doc

        updated_doc = _make_mock_document(status=DocumentStatus.PROCESSING)
        self.mock_update.return_value = updated_doc

        resp = await client.post(
            "/documents/complete-upload",
            json={"document_id": str(TEST_DOCUMENT_ID)},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["document"]["status"] == "processing"


class TestListDocuments:
    @pytest.fixture(autouse=True)
    def _patches(self):
        self._list = patch(
            "app.api.documents.router.get_user_documents", new_callable=AsyncMock
        )
        self.mock_list = self._list.start()
        yield
        self._list.stop()

    async def test_list_returns_documents_200(self, client):
        doc = _make_mock_document()
        self.mock_list.return_value = [doc]

        resp = await client.get("/documents")

        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert len(body["documents"]) == 1
        assert body["documents"][0]["title"] == "Test Document"

    async def test_list_empty_200(self, client):
        self.mock_list.return_value = []

        resp = await client.get("/documents")

        assert resp.status_code == 200
        assert resp.json()["documents"] == []


class TestGetDocument:
    @pytest.fixture(autouse=True)
    def _patches(self):
        self._get = patch(
            "app.api.documents.router.get_user_document", new_callable=AsyncMock
        )
        self.mock_get = self._get.start()
        yield
        self._get.stop()

    async def test_get_document_200(self, client):
        doc = _make_mock_document()
        self.mock_get.return_value = doc

        resp = await client.get(f"/documents/{TEST_DOCUMENT_ID}")

        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["document"]["id"] == str(TEST_DOCUMENT_ID)

    async def test_get_document_not_found_404(self, client):
        self.mock_get.side_effect = NotFoundError("Document")

        resp = await client.get(f"/documents/{TEST_DOCUMENT_ID}")

        assert resp.status_code == 404
        assert resp.json()["ok"] is False


class TestDeleteDocument:
    @pytest.fixture(autouse=True)
    def _patches(self):
        self._get = patch(
            "app.api.documents.router.get_user_document", new_callable=AsyncMock
        )
        self._delete = patch(
            "app.api.documents.router.delete_user_document", new_callable=AsyncMock
        )
        self._s3_del = patch(
            "app.api.documents.router.delete_s3_object",
        )
        self.mock_get = self._get.start()
        self.mock_delete = self._delete.start()
        self.mock_s3 = self._s3_del.start()
        yield
        self._get.stop()
        self._delete.stop()
        self._s3_del.stop()

    async def test_delete_document_204(self, client):
        doc = _make_mock_document()
        self.mock_get.return_value = doc

        resp = await client.delete(f"/documents/{TEST_DOCUMENT_ID}")

        assert resp.status_code == 204

    async def test_delete_not_found_404(self, client):
        self.mock_get.side_effect = NotFoundError("Document")

        resp = await client.delete(f"/documents/{TEST_DOCUMENT_ID}")

        assert resp.status_code == 404
