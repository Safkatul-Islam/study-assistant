"""Tests for app.services.embedding — OpenAI embedding generation."""
from unittest.mock import MagicMock, patch

import pytest

from app.services.embedding import EmbeddingResult, generate_embeddings


def _mock_embedding_response(embeddings, total_tokens=100):
    """Create a mock OpenAI embeddings response."""
    response = MagicMock()
    response.data = [MagicMock(embedding=e) for e in embeddings]
    response.usage = MagicMock(total_tokens=total_tokens)
    return response


@pytest.fixture
def mock_openai_client():
    client = MagicMock()
    return client


@pytest.fixture(autouse=True)
def patch_openai(mock_openai_client):
    with patch("app.services.embedding.OpenAI", return_value=mock_openai_client):
        yield mock_openai_client


@pytest.fixture(autouse=True)
def patch_sleep():
    with patch("app.services.embedding.time.sleep"):
        yield


class TestGenerateEmbeddings:
    def test_empty_list(self, mock_openai_client):
        result = generate_embeddings([])
        assert result.embeddings == []
        assert result.total_tokens == 0
        mock_openai_client.embeddings.create.assert_not_called()

    def test_single_text(self, mock_openai_client):
        mock_openai_client.embeddings.create.return_value = _mock_embedding_response(
            [[0.1, 0.2, 0.3]], total_tokens=5
        )

        result = generate_embeddings(["Hello world"])

        assert len(result.embeddings) == 1
        assert result.embeddings[0] == [0.1, 0.2, 0.3]
        assert result.total_tokens == 5

    def test_batching(self, mock_openai_client):
        """Texts exceeding batch_size should be split into multiple API calls."""
        mock_openai_client.embeddings.create.side_effect = [
            _mock_embedding_response([[0.1]], total_tokens=3),
            _mock_embedding_response([[0.2]], total_tokens=3),
        ]

        result = generate_embeddings(["text1", "text2"], batch_size=1)

        assert len(result.embeddings) == 2
        assert result.total_tokens == 6
        assert mock_openai_client.embeddings.create.call_count == 2

    def test_retry_on_429(self, mock_openai_client):
        rate_error = Exception("Error code: 429 rate limited")
        mock_openai_client.embeddings.create.side_effect = [
            rate_error,
            _mock_embedding_response([[0.1]], total_tokens=5),
        ]

        result = generate_embeddings(["test"])

        assert len(result.embeddings) == 1
        assert mock_openai_client.embeddings.create.call_count == 2

    def test_retry_on_5xx(self, mock_openai_client):
        server_error = Exception("500 Internal Server Error")
        mock_openai_client.embeddings.create.side_effect = [
            server_error,
            _mock_embedding_response([[0.1]], total_tokens=5),
        ]

        result = generate_embeddings(["test"])

        assert len(result.embeddings) == 1

    def test_max_retries_exceeded_raises(self, mock_openai_client):
        error = Exception("Error code: 429 rate limited")
        mock_openai_client.embeddings.create.side_effect = error

        with pytest.raises(RuntimeError, match="Embedding failed after"):
            generate_embeddings(["test"])

    def test_non_retryable_error_raises_immediately(self, mock_openai_client):
        auth_error = Exception("Error code: 401 Unauthorized")
        mock_openai_client.embeddings.create.side_effect = auth_error

        with pytest.raises(RuntimeError, match="Embedding failed"):
            generate_embeddings(["test"])

    def test_result_is_frozen(self):
        r = EmbeddingResult(embeddings=[[0.1]], total_tokens=5)
        with pytest.raises(AttributeError):
            r.total_tokens = 10
