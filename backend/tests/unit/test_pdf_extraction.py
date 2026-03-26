"""Tests for app.services.pdf_extraction — PDF text extraction."""
import pytest
import fitz  # pymupdf

from app.services.pdf_extraction import (
    PDFExtractionResult,
    PageText,
    extract_text_from_pdf,
)


@pytest.fixture
def valid_pdf_bytes():
    """Create a minimal 2-page PDF with text using pymupdf."""
    doc = fitz.open()
    for i in range(2):
        page = doc.new_page()
        page.insert_text((72, 72), f"Page {i + 1} content about testing.")
    data = doc.tobytes()
    doc.close()
    return data


@pytest.fixture
def empty_text_pdf_bytes():
    """PDF with pages but no text."""
    doc = fitz.open()
    doc.new_page()
    data = doc.tobytes()
    doc.close()
    return data


class TestExtractTextFromPdf:
    def test_valid_pdf(self, valid_pdf_bytes):
        result = extract_text_from_pdf(valid_pdf_bytes)

        assert isinstance(result, PDFExtractionResult)
        assert result.page_count == 2
        assert len(result.pages) == 2
        assert result.total_chars > 0
        assert result.pages[0].page_number == 1
        assert "Page 1" in result.pages[0].text

    def test_page_text_is_frozen(self, valid_pdf_bytes):
        result = extract_text_from_pdf(valid_pdf_bytes)
        with pytest.raises(AttributeError):
            result.pages[0].text = "changed"

    def test_result_is_frozen(self, valid_pdf_bytes):
        result = extract_text_from_pdf(valid_pdf_bytes)
        with pytest.raises(AttributeError):
            result.page_count = 999

    def test_invalid_bytes_raises_value_error(self):
        with pytest.raises(ValueError, match="Failed to open PDF"):
            extract_text_from_pdf(b"not a pdf at all")

    def test_empty_text_pdf_raises_value_error(self, empty_text_pdf_bytes):
        with pytest.raises(ValueError, match="no extractable text"):
            extract_text_from_pdf(empty_text_pdf_bytes)

    def test_too_many_pages_raises_value_error(self):
        doc = fitz.open()
        for _ in range(5):
            page = doc.new_page()
            page.insert_text((72, 72), "Content")
        data = doc.tobytes()
        doc.close()

        with pytest.raises(ValueError, match="exceeding the limit"):
            extract_text_from_pdf(data, max_pages=3)

    def test_single_page_pdf(self):
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Single page content.")
        data = doc.tobytes()
        doc.close()

        result = extract_text_from_pdf(data)
        assert result.page_count == 1
        assert len(result.pages) == 1

    def test_pages_are_1_indexed(self, valid_pdf_bytes):
        result = extract_text_from_pdf(valid_pdf_bytes)
        assert result.pages[0].page_number == 1
        assert result.pages[1].page_number == 2
