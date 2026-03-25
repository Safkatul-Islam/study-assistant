"""Tests for the LLM service (Anthropic wrapper)."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import anthropic
import pytest

from app.core.errors import AppError
from app.services.llm import LLMResponse, complete


@pytest.fixture
def mock_response():
    """Create a mock Anthropic API response."""
    response = MagicMock()
    response.content = [MagicMock(text="Hello, world!")]
    response.usage = MagicMock(input_tokens=10, output_tokens=5)
    return response


class TestLLMResponse:
    def test_total_tokens(self):
        r = LLMResponse(content="hi", input_tokens=10, output_tokens=5)
        assert r.total_tokens == 15

    def test_frozen(self):
        r = LLMResponse(content="hi", input_tokens=10, output_tokens=5)
        with pytest.raises(AttributeError):
            r.content = "changed"


class TestComplete:
    @pytest.mark.anyio
    async def test_success(self, mock_response):
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch("app.services.llm.anthropic.AsyncAnthropic", return_value=mock_client):
            result = await complete(
                system_prompt="You are helpful.",
                messages=[{"role": "user", "content": "Hi"}],
            )

        assert result.content == "Hello, world!"
        assert result.input_tokens == 10
        assert result.output_tokens == 5
        assert result.total_tokens == 15

    @pytest.mark.anyio
    async def test_retry_on_rate_limit(self, mock_response):
        mock_client = AsyncMock()
        # First call raises rate limit, second succeeds
        rate_limit_error = anthropic.RateLimitError(
            message="rate limited",
            response=MagicMock(status_code=429, headers={}),
            body={"error": {"message": "rate limited"}},
        )
        mock_client.messages.create = AsyncMock(
            side_effect=[rate_limit_error, mock_response]
        )

        with (
            patch("app.services.llm.anthropic.AsyncAnthropic", return_value=mock_client),
            patch("app.services.llm.asyncio.sleep", new_callable=AsyncMock),
        ):
            result = await complete(
                system_prompt="test",
                messages=[{"role": "user", "content": "Hi"}],
            )

        assert result.content == "Hello, world!"
        assert mock_client.messages.create.call_count == 2

    @pytest.mark.anyio
    async def test_retry_on_server_error(self, mock_response):
        mock_client = AsyncMock()
        server_error = anthropic.InternalServerError(
            message="server error",
            response=MagicMock(status_code=500, headers={}),
            body={"error": {"message": "server error"}},
        )
        mock_client.messages.create = AsyncMock(
            side_effect=[server_error, mock_response]
        )

        with (
            patch("app.services.llm.anthropic.AsyncAnthropic", return_value=mock_client),
            patch("app.services.llm.asyncio.sleep", new_callable=AsyncMock),
        ):
            result = await complete(
                system_prompt="test",
                messages=[{"role": "user", "content": "Hi"}],
            )

        assert result.content == "Hello, world!"

    @pytest.mark.anyio
    async def test_max_retries_exceeded_raises_503(self):
        mock_client = AsyncMock()
        rate_limit_error = anthropic.RateLimitError(
            message="rate limited",
            response=MagicMock(status_code=429, headers={}),
            body={"error": {"message": "rate limited"}},
        )
        mock_client.messages.create = AsyncMock(side_effect=rate_limit_error)

        with (
            patch("app.services.llm.anthropic.AsyncAnthropic", return_value=mock_client),
            patch("app.services.llm.asyncio.sleep", new_callable=AsyncMock),
            patch("app.services.llm.settings", MagicMock(
                anthropic_api_key="test-key",
                anthropic_model="claude-sonnet-4-20250514",
                llm_max_tokens=4096,
                llm_temperature=0.3,
                llm_max_retries=3,
            )),
        ):
            with pytest.raises(AppError) as exc_info:
                await complete(
                    system_prompt="test",
                    messages=[{"role": "user", "content": "Hi"}],
                )
            assert exc_info.value.status_code == 503

    @pytest.mark.anyio
    async def test_non_retryable_api_error(self):
        mock_client = AsyncMock()
        api_error = anthropic.AuthenticationError(
            message="invalid key",
            response=MagicMock(status_code=401, headers={}),
            body={"error": {"message": "invalid key"}},
        )
        mock_client.messages.create = AsyncMock(side_effect=api_error)

        with patch("app.services.llm.anthropic.AsyncAnthropic", return_value=mock_client):
            with pytest.raises(AppError) as exc_info:
                await complete(
                    system_prompt="test",
                    messages=[{"role": "user", "content": "Hi"}],
                )
            assert exc_info.value.status_code == 503

    @pytest.mark.anyio
    async def test_empty_response_content(self):
        mock_client = AsyncMock()
        response = MagicMock()
        response.content = []
        response.usage = MagicMock(input_tokens=5, output_tokens=0)
        mock_client.messages.create = AsyncMock(return_value=response)

        with patch("app.services.llm.anthropic.AsyncAnthropic", return_value=mock_client):
            result = await complete(
                system_prompt="test",
                messages=[{"role": "user", "content": "Hi"}],
            )

        assert result.content == ""
