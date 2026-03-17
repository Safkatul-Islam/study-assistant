from dataclasses import dataclass

import fitz  # pymupdf


@dataclass(frozen=True)
class PageText:
    page_number: int  # 1-indexed
    text: str


@dataclass(frozen=True)
class PDFExtractionResult:
    pages: list[PageText]
    page_count: int
    total_chars: int


def extract_text_from_pdf(pdf_bytes: bytes, max_pages: int = 200) -> PDFExtractionResult:
    """Extract text from PDF bytes, returning per-page text.

    Raises ValueError for permanent failures (encrypted, empty, too large).
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise ValueError(f"Failed to open PDF: {exc}") from exc

    try:
        if doc.is_encrypted:
            raise ValueError("PDF is encrypted and cannot be processed")

        page_count = len(doc)
        if page_count == 0:
            raise ValueError("PDF has no pages")

        if page_count > max_pages:
            raise ValueError(
                f"PDF has {page_count} pages, exceeding the limit of {max_pages}"
            )

        pages: list[PageText] = []
        total_chars = 0

        for i in range(page_count):
            page = doc[i]
            text = page.get_text("text").strip()
            if text:
                pages.append(PageText(page_number=i + 1, text=text))
                total_chars += len(text)

        if total_chars == 0:
            raise ValueError(
                "PDF contains no extractable text (may be scanned/image-only)"
            )

        return PDFExtractionResult(
            pages=pages,
            page_count=page_count,
            total_chars=total_chars,
        )
    finally:
        doc.close()
