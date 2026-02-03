"""Tests for output formatting."""

from fluff_cutter.output import format_analysis, save_analysis


class TestFormatAnalysis:
    """Tests for format_analysis function."""

    def test_includes_title(self):
        """Should include the paper title in output."""
        result = format_analysis(
            title="Test Paper Title",
            analysis="Some analysis",
            model_info="TestModel",
        )

        assert "# Paper Analysis: Test Paper Title" in result

    def test_includes_analysis_content(self):
        """Should include the analysis content."""
        analysis_text = "This is the detailed analysis of the paper."

        result = format_analysis(
            title="Title",
            analysis=analysis_text,
            model_info="Model",
        )

        assert analysis_text in result

    def test_includes_model_info(self):
        """Should include model information in footer."""
        result = format_analysis(
            title="Title",
            analysis="Analysis",
            model_info="Anthropic (claude-opus-4-5)",
        )

        assert "Anthropic (claude-opus-4-5)" in result

    def test_includes_date_format(self):
        """Should include a date in YYYY-MM-DD format."""
        result = format_analysis(
            title="Title",
            analysis="Analysis",
            model_info="Model",
        )

        # Check that output contains a date-like pattern
        import re

        assert re.search(r"\d{4}-\d{2}-\d{2}", result) is not None


class TestSaveAnalysis:
    """Tests for save_analysis function."""

    def test_saves_to_file(self, tmp_path):
        """Should save formatted analysis to file."""
        output_path = tmp_path / "analysis.md"

        save_analysis(
            title="Test Paper",
            analysis="Test analysis content",
            model_info="TestModel",
            output_path=str(output_path),
        )

        assert output_path.exists()
        content = output_path.read_text()
        assert "Test Paper" in content
        assert "Test analysis content" in content

    def test_creates_valid_markdown(self, tmp_path):
        """Should create valid markdown file."""
        output_path = tmp_path / "analysis.md"

        save_analysis(
            title="Paper Title",
            analysis="Analysis here",
            model_info="Model",
            output_path=str(output_path),
        )

        content = output_path.read_text()
        assert content.startswith("# ")  # Markdown heading
