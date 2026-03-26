"""Tests for app.services.chunking — text chunking with overlap."""
import pytest

from app.services.chunking import ChunkData, chunk_pages, count_tokens
from app.services.pdf_extraction import PageText


class TestCountTokens:
    def test_empty_string(self):
        assert count_tokens("") == 0

    def test_short_text(self):
        tokens = count_tokens("Hello world")
        assert tokens > 0
        assert tokens < 10


class TestChunkPages:
    def test_empty_pages(self):
        assert chunk_pages([]) == []

    def test_single_short_page(self):
        pages = [PageText(page_number=1, text="This is a short sentence.")]
        chunks = chunk_pages(pages, target_tokens=500)

        assert len(chunks) == 1
        assert chunks[0].chunk_index == 0
        assert chunks[0].page_start == 1
        assert chunks[0].page_end == 1
        assert "short sentence" in chunks[0].content

    def test_multiple_pages(self):
        pages = [
            PageText(page_number=1, text="Content from page one. It has multiple sentences."),
            PageText(page_number=2, text="Content from page two. Also has sentences here."),
        ]
        chunks = chunk_pages(pages, target_tokens=500)

        assert len(chunks) >= 1
        # All content should be represented
        all_content = " ".join(c.content for c in chunks)
        assert "page one" in all_content
        assert "page two" in all_content

    def test_chunk_indices_are_sequential(self):
        long_text = ". ".join([f"This is sentence number {i}" for i in range(100)])
        pages = [PageText(page_number=1, text=long_text)]
        chunks = chunk_pages(pages, target_tokens=50)

        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i

    def test_page_range_tracking(self):
        pages = [
            PageText(page_number=1, text="First page content here."),
            PageText(page_number=2, text="Second page content here."),
            PageText(page_number=3, text="Third page content here."),
        ]
        chunks = chunk_pages(pages, target_tokens=5000)

        # With a large target, everything fits in one chunk
        assert len(chunks) == 1
        assert chunks[0].page_start == 1
        assert chunks[0].page_end == 3

    def test_small_target_creates_multiple_chunks(self):
        long_text = ". ".join([f"Sentence {i} with some extra words for token count" for i in range(50)])
        pages = [PageText(page_number=1, text=long_text)]
        chunks = chunk_pages(pages, target_tokens=50)

        assert len(chunks) > 1

    def test_tiny_final_chunk_merged(self):
        """A final chunk smaller than 50 tokens should be merged into the previous one."""
        # Create text that will produce a tiny last chunk
        sentences = ["This is a medium length sentence about an important topic."] * 20
        sentences.append("Tiny.")
        text = " ".join(sentences)
        pages = [PageText(page_number=1, text=text)]

        chunks = chunk_pages(pages, target_tokens=100)

        # The last chunk should have at least 50 tokens (merged)
        if len(chunks) > 1:
            assert chunks[-1].token_count >= 50

    def test_chunk_data_is_frozen(self):
        pages = [PageText(page_number=1, text="Some content.")]
        chunks = chunk_pages(pages, target_tokens=500)

        with pytest.raises(AttributeError):
            chunks[0].content = "modified"

    def test_overlap_tokens(self):
        """With overlap, adjacent chunks should share some content."""
        long_text = ". ".join([f"Unique sentence number {i} with words" for i in range(60)])
        pages = [PageText(page_number=1, text=long_text)]
        chunks = chunk_pages(pages, target_tokens=50, overlap_tokens=30)

        if len(chunks) >= 2:
            # Check that there is some overlap between consecutive chunks
            words_0 = set(chunks[0].content.split())
            words_1 = set(chunks[1].content.split())
            overlap = words_0 & words_1
            assert len(overlap) > 0

    def test_token_count_populated(self):
        pages = [PageText(page_number=1, text="Hello world, this is a test.")]
        chunks = chunk_pages(pages, target_tokens=500)

        for chunk in chunks:
            assert chunk.token_count > 0
