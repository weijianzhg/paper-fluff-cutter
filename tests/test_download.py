"""Tests for PDF download handling."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from fluff_cutter.download import (
    _filename_from_url,
    download_pdf,
    is_url,
    normalize_arxiv_url,
    normalize_github_url,
    normalize_pdf_url,
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


class TestNormalizeGithubUrl:
    """Tests for GitHub file-view URL normalization."""

    def test_converts_blob_to_raw(self):
        url = "https://github.com/MoonshotAI/Kimi-K3/blob/main/k3_tech_report.pdf"

        assert normalize_github_url(url) == (
            "https://github.com/MoonshotAI/Kimi-K3/raw/main/k3_tech_report.pdf"
        )

    def test_preserves_query_and_fragment(self):
        url = "https://github.com/org/repo/blob/main/papers/report.pdf?download=1#page=2"

        assert normalize_github_url(url) == (
            "https://github.com/org/repo/raw/main/papers/report.pdf?download=1#page=2"
        )

    def test_keeps_non_blob_github_url_unchanged(self):
        url = "https://github.com/org/repo/releases/download/v1/report.pdf"

        assert normalize_github_url(url) == url

    def test_keeps_non_github_url_unchanged(self):
        url = "https://example.com/org/repo/blob/main/report.pdf"

        assert normalize_github_url(url) == url

    def test_does_not_match_github_lookalike_hostname(self):
        url = "https://github.com.example.com/org/repo/blob/main/report.pdf"

        assert normalize_github_url(url) == url

    def test_combined_normalizer_keeps_arxiv_support(self):
        assert normalize_pdf_url("https://arxiv.org/abs/2411.19870") == (
            "https://arxiv.org/pdf/2411.19870"
        )


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

    def test_does_not_reuse_different_pdf_with_same_basename(self, tmp_path):
        """Different URLs with the same basename should not reuse the wrong PDF."""
        existing = tmp_path / "2411.19870.pdf"
        existing.write_bytes(b"%PDF-1.4 existing")
        replacement = b"%PDF-1.4 different"
        mock_response = MagicMock()
        mock_response.content = replacement
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.raise_for_status = MagicMock()

        with patch("fluff_cutter.download.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            result = download_pdf("https://arxiv.org/pdf/2411.19870", output_dir=tmp_path)

        assert result != existing
        assert existing.read_bytes() == b"%PDF-1.4 existing"
        assert result.name.startswith("2411.19870-")
        assert result.read_bytes() == replacement

    def test_reuses_existing_path_when_downloaded_content_matches(self, tmp_path):
        """An identical download should keep the readable existing filename."""
        pdf_bytes = self._make_pdf_bytes()
        existing = tmp_path / "paper.pdf"
        existing.write_bytes(pdf_bytes)
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

            result = download_pdf("https://example.com/paper.pdf", output_dir=tmp_path)

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

    def test_normalizes_github_blob_url(self, tmp_path):
        """Should download GitHub file-view URLs through their raw-file path."""
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

            result = download_pdf(
                "https://github.com/MoonshotAI/Kimi-K3/blob/main/k3_tech_report.pdf",
                output_dir=tmp_path,
            )

        mock_client.get.assert_called_once_with(
            "https://github.com/MoonshotAI/Kimi-K3/raw/main/k3_tech_report.pdf"
        )
        assert result == tmp_path / "k3_tech_report.pdf"
        assert result.read_bytes() == pdf_bytes

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
