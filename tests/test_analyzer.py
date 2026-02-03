"""Tests for the analyzer module."""

from unittest.mock import MagicMock

from fluff_cutter.analyzer import ANALYSIS_PROMPT, analyze_paper


class TestAnalyzePaper:
    """Tests for analyze_paper function."""

    def test_calls_provider_with_correct_args(self):
        """Should call provider's analyze_paper with correct arguments."""
        mock_provider = MagicMock()
        mock_provider.analyze_paper.return_value = "TITLE: Test\n\nAnalysis"
        mock_provider.get_model_info.return_value = "TestProvider (test-model)"

        analyze_paper(mock_provider, "base64data", "paper.pdf")

        mock_provider.analyze_paper.assert_called_once_with(
            "base64data", "paper.pdf", ANALYSIS_PROMPT
        )

    def test_extracts_title_from_response(self):
        """Should extract title from model response."""
        mock_provider = MagicMock()
        mock_provider.analyze_paper.return_value = (
            "TITLE: Deep Learning for Cats\n\nAnalysis content"
        )
        mock_provider.get_model_info.return_value = "Model"

        result = analyze_paper(mock_provider, "base64", "paper.pdf")

        assert result["title"] == "Deep Learning for Cats"

    def test_extracts_title_case_insensitive(self):
        """Should handle various title formats."""
        mock_provider = MagicMock()
        mock_provider.analyze_paper.return_value = "title: Lower Case Title\n\nContent"
        mock_provider.get_model_info.return_value = "Model"

        result = analyze_paper(mock_provider, "base64", "paper.pdf")

        assert result["title"] == "Lower Case Title"

    def test_removes_title_line_from_analysis(self):
        """Should not include title line in analysis content."""
        mock_provider = MagicMock()
        mock_provider.analyze_paper.return_value = "TITLE: Paper Title\n\nActual analysis here"
        mock_provider.get_model_info.return_value = "Model"

        result = analyze_paper(mock_provider, "base64", "paper.pdf")

        assert "TITLE:" not in result["analysis"]
        assert "Actual analysis here" in result["analysis"]

    def test_handles_missing_title(self):
        """Should use default title when not found in response."""
        mock_provider = MagicMock()
        mock_provider.analyze_paper.return_value = "Just some analysis without a title"
        mock_provider.get_model_info.return_value = "Model"

        result = analyze_paper(mock_provider, "base64", "paper.pdf")

        assert result["title"] == "Unknown Title"

    def test_includes_model_info(self):
        """Should include model info in result."""
        mock_provider = MagicMock()
        mock_provider.analyze_paper.return_value = "TITLE: Test\n\nAnalysis"
        mock_provider.get_model_info.return_value = "Anthropic (claude-opus-4-5)"

        result = analyze_paper(mock_provider, "base64", "paper.pdf")

        assert result["model_info"] == "Anthropic (claude-opus-4-5)"

    def test_returns_expected_keys(self):
        """Should return dict with title, analysis, and model_info keys."""
        mock_provider = MagicMock()
        mock_provider.analyze_paper.return_value = "TITLE: Test\n\nAnalysis"
        mock_provider.get_model_info.return_value = "Model"

        result = analyze_paper(mock_provider, "base64", "paper.pdf")

        assert set(result.keys()) == {"title", "analysis", "model_info"}
