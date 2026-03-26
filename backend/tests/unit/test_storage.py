"""Tests for app.services.storage — S3 presigned URLs, download, delete."""
from unittest.mock import MagicMock, patch

import pytest

from app.services.storage import (
    delete_s3_object,
    download_file_bytes,
    generate_presigned_download_url,
    generate_presigned_upload_url,
)


@pytest.fixture
def mock_s3_client():
    client = MagicMock()
    client.generate_presigned_url = MagicMock(return_value="https://s3.example.com/presigned")
    client.get_object = MagicMock(return_value={
        "Body": MagicMock(read=MagicMock(return_value=b"pdf-bytes"))
    })
    client.delete_object = MagicMock()
    return client


@pytest.fixture(autouse=True)
def patch_s3(mock_s3_client):
    with patch("app.services.storage.get_s3_client", return_value=mock_s3_client):
        yield mock_s3_client


class TestGeneratePresignedUploadUrl:
    def test_returns_url(self, mock_s3_client):
        url = generate_presigned_upload_url("docs/test.pdf")
        assert url == "https://s3.example.com/presigned"

    def test_calls_put_object(self, mock_s3_client):
        generate_presigned_upload_url("docs/test.pdf", content_type="application/pdf")
        mock_s3_client.generate_presigned_url.assert_called_once()
        args = mock_s3_client.generate_presigned_url.call_args
        assert args[0][0] == "put_object"
        assert args[1]["Params"]["ContentType"] == "application/pdf"
        assert args[1]["ExpiresIn"] == 300

    def test_default_content_type(self, mock_s3_client):
        generate_presigned_upload_url("docs/test.pdf")
        params = mock_s3_client.generate_presigned_url.call_args[1]["Params"]
        assert params["ContentType"] == "application/pdf"


class TestGeneratePresignedDownloadUrl:
    def test_returns_url(self, mock_s3_client):
        url = generate_presigned_download_url("docs/test.pdf")
        assert url == "https://s3.example.com/presigned"

    def test_calls_get_object(self, mock_s3_client):
        generate_presigned_download_url("docs/test.pdf")
        args = mock_s3_client.generate_presigned_url.call_args
        assert args[0][0] == "get_object"
        assert args[1]["ExpiresIn"] == 3600


class TestDownloadFileBytes:
    def test_returns_bytes(self, mock_s3_client):
        data = download_file_bytes("docs/test.pdf")
        assert data == b"pdf-bytes"

    def test_calls_get_object(self, mock_s3_client):
        download_file_bytes("docs/test.pdf")
        mock_s3_client.get_object.assert_called_once()


class TestDeleteS3Object:
    def test_calls_delete(self, mock_s3_client):
        delete_s3_object("docs/test.pdf")
        mock_s3_client.delete_object.assert_called_once()
