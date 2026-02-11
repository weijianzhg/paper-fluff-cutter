"""Tests for PDF download handling."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from fluff_cutter.download import (
    _filename_from_url,
    download_pdf,
    is_url,
    normalize_arxiv_url,
)


class TestIsUrl:
    """Tests for is_url function."""

    def test_https_url(self):
        """Should return True for HTTPS URLs."""
        assert is_url("https://arxiv.org/pdf/2411.19870") is True

    def test_http_url(self):
        """Should return True for HTTP URLs."""
        assert is_url("http://example.com/paper.pdf") is True

    def test_local_path(self):
        """Should return False for local file paths."""
        assert is_url("paper.pdf") is False

    def test_relative_path(self):
        """Should return False for relative paths."""
        assert is_url("./papers/paper.pdf") is False

    def test_absolute_path(self):
        """Should return False for absolute paths."""
        assert is_url("/home/user/paper.pdf") is False

    def test_empty_string(self):
        """Should return False for empty string."""
        assert is_url("") is False


class TestNormalizeArxivUrl:
    """Tests for normalize_arxiv_url function."""

    def test_converts_abs_to_pdf(self):
        """Should convert /abs/ to /pdf/ for arxiv URLs."""
        url = "https://arxiv.org/abs/2411.19870"
        result = normalize_arxiv_url(url)
        assert result == "https://arxiv.org/pdf/2411.19870"

    def test_keeps_pdf_url_unchanged(self):
        """Should not modify already-correct arxiv PDF URLs."""
        url = "https://arxiv.org/pdf/2411.19870"
        result = normalize_arxiv_url(url)
        assert result == "https://arxiv.org/pdf/2411.19870"

    def test_non_arxiv_url_unchanged(self):
        """Should not modify non-arxiv URLs."""
        url = "https://example.com/abs/paper.pdf"
        result = normalize_arxiv_url(url)
        assert result == "https://example.com/abs/paper.pdf"

    def test_arxiv_with_version(self):
        """Should handle arxiv URLs with version numbers."""
        url = "https://arxiv.org/abs/2411.19870v2"
        result = normalize_arxiv_url(url)
        assert result == "https://arxiv.org/pdf/2411.19870v2"


class TestFilenameFromUrl:
    """Tests for _filename_from_url function."""

    def test_arxiv_pdf_url(self):
        """Should derive filename from arxiv PDF URL."""
        result = _filename_from_url("https://arxiv.org/pdf/2411.19870")
        assert result == "2411.19870.pdf"

    def test_url_with_pdf_extension(self):
        """Should keep existing .pdf extension."""
        result = _filename_from_url("https://example.com/paper.pdf")
        assert result == "paper.pdf"

    def test_url_with_trailing_slash(self):
        """Should handle trailing slashes."""
        result = _filename_from_url("https://arxiv.org/pdf/2411.19870/")
        assert result == "2411.19870.pdf"

    def test_url_with_pdf_extension_case_insensitive(self):
        """Should recognize .PDF extension."""
        result = _filename_from_url("https://example.com/paper.PDF")
        assert result == "paper.PDF"


class TestDownloadPdf:
    """Tests for download_pdf function."""

    def _make_pdf_bytes(self):
        """Create minimal valid PDF bytes."""
        return b"%PDF-1.4 fake pdf content"

    def test_downloads_and_saves_pdf(self, tmp_path):
        """Should download PDF and save to output directory."""
        pdf_bytes = self._make_pdf_bytes()
        mock_response = MagicMock()
        mock_response.content = pdf_bytes
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.raise_for_status = MagicMock()

        with patch("fluff_cutter.download.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            result = download_pdf("https://arxiv.org/pdf/2411.19870", output_dir=tmp_path)

        assert result == tmp_path / "2411.19870.pdf"
        assert result.exists()
        assert result.read_bytes() == pdf_bytes

    def test_skips_download_if_file_exists(self, tmp_path):
        """Should skip download if file already exists."""
        existing = tmp_path / "2411.19870.pdf"
        existing.write_bytes(b"%PDF-1.4 existing")

        with patch("fluff_cutter.download.httpx.Client") as mock_client_cls:
            result = download_pdf("https://arxiv.org/pdf/2411.19870", output_dir=tmp_path)
            mock_client_cls.assert_not_called()

        assert result == existing

    def test_normalizes_arxiv_abs_url(self, tmp_path):
        """Should normalize arxiv /abs/ URLs to /pdf/ before downloading."""
        pdf_bytes = self._make_pdf_bytes()
        mock_response = MagicMock()
        mock_response.content = pdf_bytes
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.raise_for_status = MagicMock()

        with patch("fluff_cutter.download.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            result = download_pdf("https://arxiv.org/abs/2411.19870", output_dir=tmp_path)

        # Should have called get with the /pdf/ URL
        mock_client.get.assert_called_once_with("https://arxiv.org/pdf/2411.19870")
        assert result.name == "2411.19870.pdf"

    def test_raises_on_non_pdf_response(self, tmp_path):
        """Should raise RuntimeError if response is not a PDF."""
        mock_response = MagicMock()
        mock_response.content = b"<html>Not a PDF</html>"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.raise_for_status = MagicMock()

        with patch("fluff_cutter.download.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            with pytest.raises(RuntimeError, match="URL did not return a PDF"):
                download_pdf("https://example.com/not-a-pdf", output_dir=tmp_path)

    def test_accepts_pdf_by_magic_bytes(self, tmp_path):
        """Should accept response with PDF magic bytes even without PDF content-type."""
        pdf_bytes = self._make_pdf_bytes()
        mock_response = MagicMock()
        mock_response.content = pdf_bytes
        mock_response.headers = {"content-type": "application/octet-stream"}
        mock_response.raise_for_status = MagicMock()

        with patch("fluff_cutter.download.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            result = download_pdf("https://example.com/paper", output_dir=tmp_path)

        assert result.exists()

    def test_raises_on_http_error(self, tmp_path):
        """Should propagate HTTP errors."""
        with patch("fluff_cutter.download.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.side_effect = httpx.HTTPStatusError(
                "404 Not Found",
                request=MagicMock(),
                response=MagicMock(status_code=404),
            )
            mock_client_cls.return_value = mock_client

            with pytest.raises(httpx.HTTPStatusError):
                download_pdf("https://example.com/missing.pdf", output_dir=tmp_path)
