"""Tests for app.services.retrieval — vector similarity search."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.retrieval import RetrievalResult, retrieve_relevant_chunks


def _mock_scalars_result(values):
    result = MagicMock()
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = values
    result.scalars.return_value = scalars_mock
    return result


class TestRetrieveRelevantChunks:
    @pytest.mark.anyio
    async def test_returns_chunks(self, mock_db, mock_chunks, document_id):
        mock_db.execute.return_value = _mock_scalars_result(mock_chunks)

        with patch(
            "app.services.retrieval.generate_embeddings",
            return_value=MagicMock(embeddings=[[0.1, 0.2]], total_tokens=10),
        ):
            result = await retrieve_relevant_chunks(mock_db, document_id, "test query")

        assert isinstance(result, RetrievalResult)
        assert len(result.chunks) == 3
        assert result.query_tokens == 10

    @pytest.mark.anyio
    async def test_calls_generate_embeddings(self, mock_db, document_id):
        mock_db.execute.return_value = _mock_scalars_result([])

        with patch(
            "app.services.retrieval.generate_embeddings",
            return_value=MagicMock(embeddings=[[0.1]], total_tokens=5),
        ) as mock_embed:
            await retrieve_relevant_chunks(mock_db, document_id, "biology question")

        mock_embed.assert_called_once()
        call_args = mock_embed.call_args
        assert call_args[0][0] == ["biology question"]

    @pytest.mark.anyio
    async def test_uses_default_top_k(self, mock_db, document_id):
        mock_db.execute.return_value = _mock_scalars_result([])

        with (
            patch("app.services.retrieval.generate_embeddings", return_value=MagicMock(embeddings=[[0.1]], total_tokens=5)),
            patch("app.services.retrieval.settings", MagicMock(
                rag_top_k=6,
                embedding_model="text-embedding-3-small",
                embedding_batch_size=100,
                embedding_dimensions=1536,
            )),
        ):
            await retrieve_relevant_chunks(mock_db, document_id, "query")

        # The db.execute call includes a .limit(top_k)
        mock_db.execute.assert_called_once()

    @pytest.mark.anyio
    async def test_result_is_frozen(self):
        r = RetrievalResult(chunks=[], query_tokens=0)
        with pytest.raises(AttributeError):
            r.query_tokens = 99

    @pytest.mark.anyio
    async def test_empty_result(self, mock_db, document_id):
        mock_db.execute.return_value = _mock_scalars_result([])

        with patch(
            "app.services.retrieval.generate_embeddings",
            return_value=MagicMock(embeddings=[[0.1]], total_tokens=5),
        ):
            result = await retrieve_relevant_chunks(mock_db, document_id, "query")

        assert result.chunks == []
