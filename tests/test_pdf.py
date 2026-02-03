"""Tests for PDF handling."""

import base64
import io

import pytest
from pypdf import PdfWriter

from fluff_cutter.pdf import (
    DEFAULT_MAX_PAGES,
    get_pdf_filename,
    get_pdf_page_count,
    read_pdf_as_base64,
    truncate_pdf,
)


@pytest.fixture
def sample_pdf(tmp_path):
    """Create a sample single-page PDF file for testing."""
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)  # Letter size
    pdf_path = tmp_path / "test_paper.pdf"
    with open(pdf_path, "wb") as f:
        writer.write(f)
    return pdf_path


@pytest.fixture
def multi_page_pdf(tmp_path):
    """Create a multi-page PDF file for testing."""
    writer = PdfWriter()
    for _ in range(10):
        writer.add_blank_page(width=612, height=792)
    pdf_path = tmp_path / "multi_page.pdf"
    with open(pdf_path, "wb") as f:
        writer.write(f)
    return pdf_path


class TestGetPdfPageCount:
    """Tests for get_pdf_page_count function."""

    def test_returns_correct_page_count(self, sample_pdf):
        """Should return correct page count for single page PDF."""
        result = get_pdf_page_count(sample_pdf)
        assert result == 1

    def test_returns_correct_count_for_multi_page(self, multi_page_pdf):
        """Should return correct page count for multi-page PDF."""
        result = get_pdf_page_count(multi_page_pdf)
        assert result == 10


class TestTruncatePdf:
    """Tests for truncate_pdf function."""

    def test_truncates_to_specified_pages(self, multi_page_pdf, tmp_path):
        """Should truncate PDF to specified number of pages."""
        truncated_data = truncate_pdf(multi_page_pdf, 3)

        # Write to file and verify page count
        truncated_path = tmp_path / "truncated.pdf"
        truncated_path.write_bytes(truncated_data)

        assert get_pdf_page_count(truncated_path) == 3

    def test_returns_all_pages_if_less_than_max(self, multi_page_pdf, tmp_path):
        """Should return all pages if PDF has fewer than max_pages."""
        truncated_data = truncate_pdf(multi_page_pdf, 100)

        truncated_path = tmp_path / "truncated.pdf"
        truncated_path.write_bytes(truncated_data)

        assert get_pdf_page_count(truncated_path) == 10


class TestReadPdfAsBase64:
    """Tests for read_pdf_as_base64 function."""

    def test_reads_pdf_and_encodes_base64(self, sample_pdf):
        """Should read PDF file and return base64 encoded string."""
        result, page_count, was_truncated = read_pdf_as_base64(sample_pdf)

        # Verify it's valid base64
        decoded = base64.standard_b64decode(result)
        assert decoded.startswith(b"%PDF")
        assert page_count == 1
        assert was_truncated is False

    def test_accepts_string_path(self, sample_pdf):
        """Should accept string path as well as Path object."""
        result, page_count, was_truncated = read_pdf_as_base64(str(sample_pdf))

        assert isinstance(result, str)
        assert len(result) > 0

    def test_returns_page_count(self, multi_page_pdf):
        """Should return total page count."""
        _, page_count, _ = read_pdf_as_base64(multi_page_pdf)
        assert page_count == 10

    def test_truncates_when_max_pages_specified(self, multi_page_pdf):
        """Should truncate when max_pages is less than total pages."""
        result, page_count, was_truncated = read_pdf_as_base64(multi_page_pdf, max_pages=5)

        assert page_count == 10  # Original page count
        assert was_truncated is True

        # Verify the returned PDF is actually truncated
        decoded = base64.standard_b64decode(result)
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(decoded))
        assert len(reader.pages) == 5

    def test_no_truncation_when_under_max_pages(self, multi_page_pdf):
        """Should not truncate when max_pages exceeds total pages."""
        _, page_count, was_truncated = read_pdf_as_base64(multi_page_pdf, max_pages=100)

        assert page_count == 10
        assert was_truncated is False

    def test_raises_file_not_found(self, tmp_path):
        """Should raise FileNotFoundError for non-existent file."""
        non_existent = tmp_path / "does_not_exist.pdf"

        with pytest.raises(FileNotFoundError, match="PDF file not found"):
            read_pdf_as_base64(non_existent)

    def test_raises_value_error_for_non_pdf(self, tmp_path):
        """Should raise ValueError for non-PDF files."""
        txt_file = tmp_path / "document.txt"
        txt_file.write_text("Not a PDF")

        with pytest.raises(ValueError, match="File is not a PDF"):
            read_pdf_as_base64(txt_file)


class TestGetPdfFilename:
    """Tests for get_pdf_filename function."""

    def test_extracts_filename_from_path(self):
        """Should extract just the filename from a path."""
        result = get_pdf_filename("/path/to/research_paper.pdf")

        assert result == "research_paper.pdf"

    def test_handles_path_object(self, tmp_path):
        """Should handle Path objects."""
        pdf_path = tmp_path / "paper.pdf"

        result = get_pdf_filename(pdf_path)

        assert result == "paper.pdf"

    def test_handles_simple_filename(self):
        """Should handle simple filename without directory."""
        result = get_pdf_filename("paper.pdf")

        assert result == "paper.pdf"


class TestDefaultMaxPages:
    """Tests for DEFAULT_MAX_PAGES constant."""

    def test_default_max_pages_is_reasonable(self):
        """DEFAULT_MAX_PAGES should be a reasonable value."""
        assert DEFAULT_MAX_PAGES == 50
        assert isinstance(DEFAULT_MAX_PAGES, int)
