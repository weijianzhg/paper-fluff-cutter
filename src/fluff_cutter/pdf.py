"""PDF handling for LLM analysis."""

import base64
import io
from pathlib import Path

from pypdf import PdfReader, PdfWriter

# Default max pages when auto-truncating (roughly ~150K tokens for most papers)
DEFAULT_MAX_PAGES = 50


def get_pdf_page_count(pdf_path: str | Path) -> int:
    """
    Get the number of pages in a PDF file.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Number of pages in the PDF.
    """
    pdf_path = Path(pdf_path)
    reader = PdfReader(pdf_path)
    return len(reader.pages)


def truncate_pdf(pdf_path: str | Path, max_pages: int) -> bytes:
    """
    Read a PDF and return only the first N pages as bytes.

    Args:
        pdf_path: Path to the PDF file.
        max_pages: Maximum number of pages to include.

    Returns:
        PDF data as bytes containing only the first max_pages pages.
    """
    pdf_path = Path(pdf_path)
    reader = PdfReader(pdf_path)

    writer = PdfWriter()
    for i in range(min(max_pages, len(reader.pages))):
        writer.add_page(reader.pages[i])

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def read_pdf_as_base64(
    pdf_path: str | Path,
    max_pages: int | None = None,
) -> tuple[str, int, bool]:
    """
    Read a PDF file and encode it as base64, optionally truncating to max pages.

    Args:
        pdf_path: Path to the PDF file.
        max_pages: Maximum number of pages to include. If None, includes all pages.

    Returns:
        Tuple of (base64-encoded PDF data, total page count, was_truncated).

    Raises:
        FileNotFoundError: If the PDF file doesn't exist.
        ValueError: If the file is not a PDF.
    """
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"File is not a PDF: {pdf_path}")

    total_pages = get_pdf_page_count(pdf_path)
    was_truncated = False

    if max_pages is not None and total_pages > max_pages:
        pdf_data = truncate_pdf(pdf_path, max_pages)
        was_truncated = True
    else:
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()

    return base64.standard_b64encode(pdf_data).decode("utf-8"), total_pages, was_truncated


def get_pdf_filename(pdf_path: str | Path) -> str:
    """
    Get the filename from a PDF path.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        The filename.
    """
    return Path(pdf_path).name
