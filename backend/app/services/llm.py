import asyncio
from dataclasses import dataclass

import anthropic
import structlog

from app.config import settings
from app.core.errors import AppError

logger = structlog.get_logger()


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int
    output_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


async def complete(
    system_prompt: str,
    messages: list[dict[str, str]],
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> LLMResponse:
    """Send a completion request to the Anthropic API with retry logic.

    Retries up to llm_max_retries times on rate limit (429) and server errors (5xx).
    Raises AppError(503) on permanent failure.
    """
    model = model or settings.anthropic_model
    max_tokens = max_tokens or settings.llm_max_tokens
    temperature = temperature if temperature is not None else settings.llm_temperature

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    last_error: Exception | None = None

    for attempt in range(1, settings.llm_max_retries + 1):
        try:
            response = await client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=messages,
            )

            content = response.content[0].text if response.content else ""

            return LLMResponse(
                content=content,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )

        except anthropic.RateLimitError as exc:
            last_error = exc
            delay = 2 ** (attempt - 1)
            logger.warning(
                "llm_rate_limited",
                attempt=attempt,
                retry_delay=delay,
                model=model,
            )
            await asyncio.sleep(delay)

        except anthropic.InternalServerError as exc:
            last_error = exc
            delay = 2 ** (attempt - 1)
            logger.warning(
                "llm_server_error",
                attempt=attempt,
                retry_delay=delay,
                error=str(exc),
                model=model,
            )
            await asyncio.sleep(delay)

        except anthropic.APIError as exc:
            # Non-retryable API error (auth, bad request, etc.)
            logger.error(
                "llm_api_error",
                error=str(exc),
                status_code=getattr(exc, "status_code", None),
                model=model,
            )
            raise AppError(
                status_code=503,
                message="AI service temporarily unavailable",
            ) from exc

    # All retries exhausted
    logger.error(
        "llm_max_retries_exceeded",
        attempts=settings.llm_max_retries,
        last_error=str(last_error),
        model=model,
    )
    raise AppError(
        status_code=503,
        message="AI service temporarily unavailable",
    )
