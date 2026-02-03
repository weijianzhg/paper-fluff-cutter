"""Tests for PDF handling."""

import base64

import pytest

from fluff_cutter.pdf import get_pdf_filename, read_pdf_as_base64


@pytest.fixture
def sample_pdf(tmp_path):
    """Create a sample PDF file for testing."""
    # Minimal valid PDF content
    pdf_content = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>"
    pdf_path = tmp_path / "test_paper.pdf"
    pdf_path.write_bytes(pdf_content)
    return pdf_path


class TestReadPdfAsBase64:
    """Tests for read_pdf_as_base64 function."""

    def test_reads_pdf_and_encodes_base64(self, sample_pdf):
        """Should read PDF file and return base64 encoded string."""
        result = read_pdf_as_base64(sample_pdf)

        # Verify it's valid base64
        decoded = base64.standard_b64decode(result)
        assert decoded.startswith(b"%PDF")

    def test_accepts_string_path(self, sample_pdf):
        """Should accept string path as well as Path object."""
        result = read_pdf_as_base64(str(sample_pdf))

        assert isinstance(result, str)
        assert len(result) > 0

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
