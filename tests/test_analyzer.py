"""Tests for the analyzer module."""

from unittest.mock import MagicMock

from fluff_cutter.analyzer import (
    ANALYSIS_PROMPT,
    analyze_paper,
    extract_paper_metadata,
    parse_analysis_response,
    stream_analysis_chunks,
)


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
        """Should use the filename when the response has no title."""
        mock_provider = MagicMock()
        mock_provider.analyze_paper.return_value = "Just some analysis without a title"
        mock_provider.get_model_info.return_value = "Model"

        result = analyze_paper(mock_provider, "base64", "paper.pdf")

        assert result["title"] == "Paper"

    def test_uses_title_from_machine_metadata(self):
        """Should recover the title when the model omits the visible TITLE line."""
        mock_provider = MagicMock()
        mock_provider.get_model_info.return_value = "Model"
        response = """## Why Should I Care?
It matters.

<!-- paper-metadata
{"title":"Kimi K3: Open Frontier Intelligence","authors":["Kimi Team"]}
-->"""

        result = parse_analysis_response(response, mock_provider, filename="k3_tech_report.pdf")

        assert result["title"] == "Kimi K3: Open Frontier Intelligence"
        assert result["metadata"] == {"authors": ["Kimi Team"]}
        assert result["analysis"] == "## Why Should I Care?\nIt matters."

    def test_rejects_placeholder_title_and_uses_metadata(self):
        """A literal Unknown Title line should not override extracted metadata."""
        mock_provider = MagicMock()
        mock_provider.get_model_info.return_value = "Model"
        response = """TITLE: Unknown Title

Body
<!-- paper-metadata
{"title":"Actual Paper Title"}
-->"""

        result = parse_analysis_response(response, mock_provider, filename="paper.pdf")

        assert result["title"] == "Actual Paper Title"
        assert result["analysis"] == "Body"

    def test_extracts_title_from_leading_markdown_h1(self):
        """Should accept a common model formatting variation."""
        mock_provider = MagicMock()
        mock_provider.get_model_info.return_value = "Model"

        result = parse_analysis_response("# Paper Title\n\n## Analysis\nBody", mock_provider)

        assert result["title"] == "Paper Title"
        assert result["analysis"] == "## Analysis\nBody"

    def test_uses_h1_after_rejected_placeholder_title(self):
        """A rejected TITLE marker should not block a valid following H1."""
        mock_provider = MagicMock()
        mock_provider.get_model_info.return_value = "Model"

        result = parse_analysis_response(
            "TITLE: Unknown Title\n\n# Actual Paper Title\n\n## Analysis\nBody",
            mock_provider,
            filename="paper.pdf",
        )

        assert result["title"] == "Actual Paper Title"
        assert result["analysis"] == "## Analysis\nBody"

    def test_does_not_treat_generic_h1_as_paper_title(self):
        """A generic response heading should not replace the filename fallback."""
        mock_provider = MagicMock()
        mock_provider.get_model_info.return_value = "Model"

        result = parse_analysis_response(
            "# Analysis\n\n## Why Should I Care?\nBody",
            mock_provider,
            filename="actual-paper.pdf",
        )

        assert result["title"] == "Actual Paper"
        assert result["analysis"] == "# Analysis\n\n## Why Should I Care?\nBody"

    def test_uses_readable_filename_as_last_resort(self):
        """Should never emit Unknown Title when a useful filename is available."""
        mock_provider = MagicMock()
        mock_provider.get_model_info.return_value = "Model"

        result = parse_analysis_response(
            "Just some analysis without a title",
            mock_provider,
            filename="k3_tech_report.pdf",
        )

        assert result["title"] == "K3 Tech Report"

    def test_includes_model_info(self):
        """Should include model info in result."""
        mock_provider = MagicMock()
        mock_provider.analyze_paper.return_value = "TITLE: Test\n\nAnalysis"
        mock_provider.get_model_info.return_value = "Anthropic (claude-opus-4-5)"

        result = analyze_paper(mock_provider, "base64", "paper.pdf")

        assert result["model_info"] == "Anthropic (claude-opus-4-5)"

    def test_returns_expected_keys(self):
        """Should return analysis fields plus normalized paper metadata."""
        mock_provider = MagicMock()
        mock_provider.analyze_paper.return_value = "TITLE: Test\n\nAnalysis"
        mock_provider.get_model_info.return_value = "Model"

        result = analyze_paper(mock_provider, "base64", "paper.pdf")

        assert set(result.keys()) == {"title", "analysis", "metadata", "model_info"}

    def test_extracts_metadata_without_leaking_machine_comment(self):
        """Should validate hidden metadata and remove it from visible analysis."""
        mock_provider = MagicMock()
        mock_provider.get_model_info.return_value = "Model"
        response = """<!-- paper-metadata
{"authors":["Ada Lovelace","Ada Lovelace",7],"published_year":2025,
"research_type":"empirical","topics":["Machine Learning","LLM Safety!"],
"concepts":["Verifier-guided search"],"prerequisites":[]}
-->
TITLE: Useful Paper

## Why Should I Care?
It matters."""

        result = parse_analysis_response(response, mock_provider)

        assert result["title"] == "Useful Paper"
        assert "paper-metadata" not in result["analysis"]
        assert result["metadata"] == {
            "authors": ["Ada Lovelace"],
            "published_year": 2025,
            "research_type": "empirical",
            "topics": ["machine-learning", "llm-safety"],
            "concepts": ["Verifier-guided search"],
            "prerequisites": [],
        }


def test_extract_paper_metadata_discards_invalid_values_and_all_comments():
    """Invalid or incomplete comments should not leak and invalid fields should be omitted."""
    response = """Body
<!-- paper-metadata not-json -->
<!-- paper-metadata
{"authors": [], "published_year": true, "research_type": "made-up",
"topics": ["AI", "AI"], "concepts": [], "prerequisites": ["x", "x"]}
-->
<!-- PAPER-METADATA
{"unfinished": true"""

    clean_response, metadata = extract_paper_metadata(response)

    assert clean_response == "Body"
    assert metadata == {
        "authors": [],
        "topics": ["ai"],
        "concepts": [],
        "prerequisites": ["x"],
    }


class TestStreamingHelpers:
    """Tests for analyzer streaming helpers."""

    def test_stream_analysis_chunks_uses_provider_stream_method(self):
        """Should call provider streaming method with analysis prompt."""
        mock_provider = MagicMock()
        mock_provider.analyze_paper_stream.return_value = iter(["part1", "part2"])

        chunks = list(stream_analysis_chunks(mock_provider, "base64data", "paper.pdf"))

        assert chunks == ["part1", "part2"]
        mock_provider.analyze_paper_stream.assert_called_once_with(
            "base64data", "paper.pdf", ANALYSIS_PROMPT
        )

    def test_parse_analysis_response_matches_analyze_paper_shape(self):
        """Should produce title/analysis/model_info dict from raw response."""
        mock_provider = MagicMock()
        mock_provider.get_model_info.return_value = "OpenAI (gpt-5.2)"

        result = parse_analysis_response("TITLE: Test Paper\n\nBody text", mock_provider)

        assert result["title"] == "Test Paper"
        assert result["analysis"] == "Body text"
        assert result["metadata"] == {}
        assert result["model_info"] == "OpenAI (gpt-5.2)"
