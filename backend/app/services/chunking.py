from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

import tiktoken

from app.services.pdf_extraction import PageText


@dataclass(frozen=True)
class ChunkData:
    chunk_index: int
    content: str
    page_start: int
    page_end: int
    token_count: int


@lru_cache(maxsize=1)
def _get_encoder() -> tiktoken.Encoding:
    return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Count tokens using cl100k_base encoding."""
    return len(_get_encoder().encode(text))


_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences, with fallbacks to paragraph and line breaks."""
    parts = _SENTENCE_RE.split(text)
    if len(parts) > 1:
        return parts

    parts = text.split("\n\n")
    if len(parts) > 1:
        return parts

    parts = text.split("\n")
    return parts


def chunk_pages(
    pages: list[PageText],
    target_tokens: int = 500,
    overlap_tokens: int = 50,
) -> list[ChunkData]:
    """Split page texts into overlapping chunks of approximately target_tokens size."""
    if not pages:
        return []

    # Build concatenated text with char-offset -> page-number mapping
    full_text = ""
    char_to_page: list[tuple[int, int]] = []  # (start_offset, page_number)

    for page in pages:
        char_to_page.append((len(full_text), page.page_number))
        if full_text:
            full_text += "\n\n"
            # The separator chars still belong to the previous page context
        full_text += page.text

    def _page_at_offset(offset: int) -> int:
        """Find which page a character offset belongs to."""
        result = char_to_page[0][1]
        for start, page_num in char_to_page:
            if start <= offset:
                result = page_num
            else:
                break
        return result

    # Split into sentences
    sentences = _split_sentences(full_text)

    # Track char offsets for each sentence
    sentence_offsets: list[int] = []
    current_offset = 0
    for sent in sentences:
        idx = full_text.find(sent, current_offset)
        sentence_offsets.append(idx if idx != -1 else current_offset)
        current_offset = (idx if idx != -1 else current_offset) + len(sent)

    # Greedy chunking with overlap
    chunks: list[ChunkData] = []
    i = 0

    while i < len(sentences):
        chunk_sentences: list[str] = []
        chunk_token_count = 0
        start_idx = i

        # Accumulate sentences until exceeding target
        while i < len(sentences):
            sent_tokens = count_tokens(sentences[i])
            if chunk_sentences and chunk_token_count + sent_tokens > target_tokens:
                break
            chunk_sentences.append(sentences[i])
            chunk_token_count += sent_tokens
            i += 1

        content = " ".join(chunk_sentences).strip()
        if not content:
            continue

        # Determine page range
        chunk_start_offset = sentence_offsets[start_idx]
        chunk_end_offset = sentence_offsets[i - 1] + len(sentences[i - 1]) - 1
        page_start = _page_at_offset(chunk_start_offset)
        page_end = _page_at_offset(chunk_end_offset)

        chunks.append(
            ChunkData(
                chunk_index=len(chunks),
                content=content,
                page_start=page_start,
                page_end=page_end,
                token_count=count_tokens(content),
            )
        )

        # Overlap: back up to include ~overlap_tokens from end of current chunk
        if i < len(sentences):
            overlap_count = 0
            j = i - 1
            while j > start_idx and overlap_count < overlap_tokens:
                overlap_count += count_tokens(sentences[j])
                j -= 1
            i = j + 1

    # Merge final chunk if too small (< 50 tokens)
    if len(chunks) > 1 and chunks[-1].token_count < 50:
        last = chunks.pop()
        prev = chunks.pop()
        merged_content = prev.content + " " + last.content
        chunks.append(
            ChunkData(
                chunk_index=prev.chunk_index,
                content=merged_content,
                page_start=prev.page_start,
                page_end=last.page_end,
                token_count=count_tokens(merged_content),
            )
        )

    return chunks
