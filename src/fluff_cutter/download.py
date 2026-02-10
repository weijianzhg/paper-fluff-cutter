"""Download PDF papers from URLs."""

import re
from pathlib import Path
from urllib.parse import urlparse

import httpx


def is_url(paper_path: str) -> bool:
    """
    Check if the input looks like a URL.

    Args:
        paper_path: The input string to check.

    Returns:
        True if it looks like an HTTP(S) URL.
    """
    return paper_path.startswith("http://") or paper_path.startswith("https://")


def normalize_arxiv_url(url: str) -> str:
    """
    Normalize an arxiv URL to point to the PDF.

    Converts abstract URLs (/abs/) to PDF URLs (/pdf/) and ensures
    a clean download URL.

    Args:
        url: An arxiv URL.

    Returns:
        The normalized PDF URL.
    """
    parsed = urlparse(url)
    if parsed.hostname and "arxiv.org" not in parsed.hostname:
        return url

    # Convert /abs/ to /pdf/
    path = parsed.path
    path = re.sub(r"/abs/", "/pdf/", path)

    return parsed._replace(path=path).geturl()


def _filename_from_url(url: str) -> str:
    """
    Derive a PDF filename from a URL.

    Examples:
        https://arxiv.org/pdf/2411.19870 -> 2411.19870.pdf
        https://example.com/paper.pdf -> paper.pdf

    Args:
        url: The URL to derive a filename from.

    Returns:
        A filename string ending in .pdf.
    """
    parsed = urlparse(url)
    # Get the last path component
    path = parsed.path.rstrip("/")
    name = path.split("/")[-1] if path else "downloaded_paper"

    # Ensure .pdf extension
    if not name.lower().endswith(".pdf"):
        name = f"{name}.pdf"

    return name


def download_pdf(url: str, output_dir: Path | None = None) -> Path:
    """
    Download a PDF from a URL and save it locally.

    If the file already exists locally, the download is skipped.

    Args:
        url: The URL to download from.
        output_dir: Directory to save the file in. Defaults to current working directory.

    Returns:
        Path to the downloaded PDF file.

    Raises:
        RuntimeError: If the download fails or the response is not a PDF.
        httpx.HTTPStatusError: If the server returns an error status code.
    """
    # Normalize arxiv URLs
    url = normalize_arxiv_url(url)

    filename = _filename_from_url(url)
    output_dir = output_dir or Path.cwd()
    output_path = output_dir / filename

    # Skip download if file already exists
    if output_path.exists():
        return output_path

    # Download the PDF
    with httpx.Client(follow_redirects=True, timeout=60.0) as client:
        response = client.get(url)
        response.raise_for_status()

    # Validate that the response is actually a PDF
    content_type = response.headers.get("content-type", "")
    is_pdf_content_type = "application/pdf" in content_type
    starts_with_pdf_magic = response.content[:5] == b"%PDF-"

    if not is_pdf_content_type and not starts_with_pdf_magic:
        raise RuntimeError(
            f"URL did not return a PDF (content-type: {content_type}). "
            "Please provide a direct link to a PDF file."
        )

    # Write to disk
    output_path.write_bytes(response.content)

    return output_path
