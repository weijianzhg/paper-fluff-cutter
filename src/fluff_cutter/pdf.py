"""PDF handling for LLM analysis."""

import base64
from pathlib import Path


def read_pdf_as_base64(pdf_path: str | Path) -> str:
    """
    Read a PDF file and encode it as base64.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Base64-encoded PDF data.

    Raises:
        FileNotFoundError: If the PDF file doesn't exist.
        ValueError: If the file is not a PDF.
    """
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"File is not a PDF: {pdf_path}")

    with open(pdf_path, "rb") as f:
        pdf_data = f.read()

    return base64.standard_b64encode(pdf_data).decode("utf-8")


def get_pdf_filename(pdf_path: str | Path) -> str:
    """
    Get the filename from a PDF path.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        The filename.
    """
    return Path(pdf_path).name
