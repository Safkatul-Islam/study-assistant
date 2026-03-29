"""Integration tests for M5 document management endpoints — rename, tags, download URL."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.core.errors import NotFoundError
from tests.integration.conftest import TEST_DOCUMENT_ID, _make_mock_document


class TestRenameDocument:
    @pytest.fixture(autouse=True)
    def _patches(self):
        self._get_doc = patch(
            "app.api.documents.router.get_user_document", new_callable=AsyncMock
        )
        self._rename = patch(
            "app.api.documents.router.rename_document", new_callable=AsyncMock
        )
        self.mock_get = self._get_doc.start()
        self.mock_rename = self._rename.start()
        yield
        self._get_doc.stop()
        self._rename.stop()

    async def test_rename_success(self, client):
        doc = _make_mock_document()
        doc.tags = None
        self.mock_get.return_value = doc

        renamed = _make_mock_document()
        renamed.title = "Renamed Document"
        renamed.tags = None
        self.mock_rename.return_value = renamed

        resp = await client.patch(
            f"/documents/{TEST_DOCUMENT_ID}", json={"title": "Renamed Document"}
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["document"]["title"] == "Renamed Document"

    async def test_rename_not_found_404(self, client):
        self.mock_get.side_effect = NotFoundError("Document")

        fake_id = uuid.uuid4()
        resp = await client.patch(
            f"/documents/{fake_id}", json={"title": "New Title"}
        )

        assert resp.status_code == 404
        assert resp.json()["ok"] is False


class TestUpdateTags:
    @pytest.fixture(autouse=True)
    def _patches(self):
        self._get_doc = patch(
            "app.api.documents.router.get_user_document", new_callable=AsyncMock
        )
        self._update_tags = patch(
            "app.api.documents.router.update_document_tags", new_callable=AsyncMock
        )
        self.mock_get = self._get_doc.start()
        self.mock_update = self._update_tags.start()
        yield
        self._get_doc.stop()
        self._update_tags.stop()

    async def test_update_tags_success(self, client):
        doc = _make_mock_document()
        self.mock_get.return_value = doc

        import json

        updated = _make_mock_document()
        updated.tags = json.dumps(["physics", "exam"])
        self.mock_update.return_value = updated

        resp = await client.put(
            f"/documents/{TEST_DOCUMENT_ID}/tags",
            json={"tags": ["physics", "exam"]},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["tags"] == ["physics", "exam"]

    async def test_update_tags_empty(self, client):
        doc = _make_mock_document()
        self.mock_get.return_value = doc

        updated = _make_mock_document()
        updated.tags = None
        self.mock_update.return_value = updated

        resp = await client.put(
            f"/documents/{TEST_DOCUMENT_ID}/tags",
            json={"tags": []},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["tags"] == []


class TestGetDownloadUrl:
    @pytest.fixture(autouse=True)
    def _patches(self):
        self._get_doc = patch(
            "app.api.documents.router.get_user_document", new_callable=AsyncMock
        )
        self._download_url = patch(
            "app.api.documents.router.get_download_url",
            return_value="https://s3.example.com/download?signed=1",
        )
        self.mock_get = self._get_doc.start()
        self.mock_download = self._download_url.start()
        yield
        self._get_doc.stop()
        self._download_url.stop()

    async def test_get_download_url_success(self, client):
        doc = _make_mock_document()
        self.mock_get.return_value = doc

        resp = await client.get(f"/documents/{TEST_DOCUMENT_ID}/download-url")

        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["url"] == "https://s3.example.com/download?signed=1"

    async def test_get_download_url_not_found_404(self, client):
        self.mock_get.side_effect = NotFoundError("Document")

        fake_id = uuid.uuid4()
        resp = await client.get(f"/documents/{fake_id}/download-url")

        assert resp.status_code == 404
        assert resp.json()["ok"] is False
