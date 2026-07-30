"""Tests for output formatting."""

from datetime import datetime

import yaml

from fluff_cutter.output import (
    MAX_FILENAME_BYTES,
    MAX_FILENAME_TITLE_LENGTH,
    default_analysis_path,
    format_analysis,
    print_analysis_stream,
    save_analysis,
)


class TestDefaultAnalysisPath:
    """Tests for recognizable default output filenames."""

    def test_uses_title_and_extraction_date_next_to_pdf(self, tmp_path):
        result = default_analysis_path(
            tmp_path / "2411.19870.pdf",
            "Scaling: Does It Work?",
            datetime(2026, 7, 30),
        )

        assert result == tmp_path / "scaling-does-it-work-2411.19870-2026-07-30.md"

    def test_preserves_unicode_and_removes_unsafe_punctuation(self, tmp_path):
        result = default_analysis_path(
            tmp_path / "paper.pdf",
            "理解 AI / safely?",
            datetime(2026, 7, 30),
        )

        assert result.name == "理解-ai-safely-paper-2026-07-30.md"

    def test_uses_source_stem_to_disambiguate_same_title(self, tmp_path):
        created_at = datetime(2026, 7, 30)

        first = default_analysis_path(tmp_path / "first.pdf", "Same Title", created_at)
        second = default_analysis_path(tmp_path / "second.pdf", "Same Title", created_at)

        assert first.name == "same-title-first-2026-07-30.md"
        assert second.name == "same-title-second-2026-07-30.md"

    def test_hashes_source_transformations_that_could_collide(self, tmp_path):
        created_at = datetime(2026, 7, 30)

        uppercase = default_analysis_path(tmp_path / "Foo.pdf", "Same Title", created_at)
        lowercase = default_analysis_path(tmp_path / "foo.pdf", "Same Title", created_at)
        underscored = default_analysis_path(
            tmp_path / "downloaded_paper.pdf",
            "Same Title",
            created_at,
        )
        hyphenated = default_analysis_path(
            tmp_path / "downloaded-paper.pdf",
            "Same Title",
            created_at,
        )
        generic = default_analysis_path(tmp_path / "paper.pdf", "Same Title", created_at)
        title_named = default_analysis_path(
            tmp_path / "same-title.pdf",
            "Same Title",
            created_at,
        )

        assert uppercase != lowercase
        assert underscored != hyphenated
        assert generic != underscored
        assert generic != title_named

    def test_hashes_source_stems_that_share_a_truncated_prefix(self, tmp_path):
        created_at = datetime(2026, 7, 30)
        shared_prefix = "a" * 60

        first = default_analysis_path(
            tmp_path / f"{shared_prefix}-first.pdf",
            "Same Title",
            created_at,
        )
        second = default_analysis_path(
            tmp_path / f"{shared_prefix}-second.pdf",
            "Same Title",
            created_at,
        )

        assert first != second

    def test_limits_title_fragment_length(self, tmp_path):
        result = default_analysis_path(
            tmp_path / "paper.pdf",
            "A" * 200,
            datetime(2026, 7, 30),
        )

        title_fragment = result.name.removesuffix("-paper-2026-07-30.md")
        assert len(title_fragment) == MAX_FILENAME_TITLE_LENGTH

    def test_limits_multibyte_filename_to_filesystem_safe_size(self, tmp_path):
        result = default_analysis_path(
            tmp_path / "2411.19870.pdf",
            "𝒜" * 80,
            datetime(2026, 7, 30),
        )

        assert len(result.name.encode("utf-8")) <= MAX_FILENAME_BYTES
        assert result.name.endswith("-2411.19870-2026-07-30.md")

    def test_uses_paper_fallback_when_title_has_no_filename_characters(self, tmp_path):
        result = default_analysis_path(
            tmp_path / "paper.pdf",
            "?! /",
            datetime(2026, 7, 30),
        )

        assert result.name == "paper-2026-07-30.md"


class TestFormatAnalysis:
    """Tests for format_analysis function."""

    def test_includes_title(self):
        """Should include the paper title in output."""
        result = format_analysis(
            title="Test Paper Title",
            analysis="Some analysis",
            model_info="TestModel",
        )

        assert "# Test Paper Title" in result

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

        assert "model: Anthropic (claude-opus-4-5)" in result

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

    def test_renders_obsidian_properties_and_normalized_body(self):
        """Should render searchable properties and one H1 without machine metadata."""
        result = format_analysis(
            title="Scaling: Does It Work?",
            analysis="# Duplicate Title\n\n## Why Should I Care?\nBecause.",
            model_info="OpenAI (gpt-5.2)",
            paper_metadata={
                "authors": ["A. Researcher"],
                "published_year": 2026,
                "research_type": "empirical",
                "topics": ["language-models", "evaluation"],
                "concepts": ["scaling laws"],
                "prerequisites": [],
            },
            source="https://arxiv.org/abs/1234.5678",
        )

        _, frontmatter, body = result.split("---", 2)
        metadata = yaml.safe_load(frontmatter)
        assert metadata == {
            "title": "Scaling: Does It Work?",
            "source": "https://arxiv.org/abs/1234.5678",
            "created": metadata["created"],
            "content_type": "research-paper",
            "authors": ["A. Researcher"],
            "published_year": 2026,
            "research_type": "empirical",
            "concepts": ["scaling laws"],
            "prerequisites": [],
            "tags": ["paper", "summary", "language-models", "evaluation"],
            "model": "OpenAI (gpt-5.2)",
        }
        assert body.count("# Scaling: Does It Work?") == 1
        assert "Duplicate Title" not in body
        assert "## Why Should I Care?" in body


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
        assert content.startswith("---\n")
        assert "\n# Paper Title\n" in content


class TestPrintAnalysisStream:
    """Tests for print_analysis_stream function."""

    def test_prints_formatted_output(self, capsys):
        """Should print the same formatted content to stdout."""
        print_analysis_stream(
            title="Streamed Title",
            analysis="Streamed analysis body",
            model_info="StreamModel",
        )

        captured = capsys.readouterr()
        assert "# Streamed Title" in captured.out
        assert "Streamed analysis body" in captured.out
        assert "model: StreamModel" in captured.out

    def test_writes_multiple_chunks(self, monkeypatch):
        """Should write progressively rather than in one large print call."""

        class FakeStdout:
            def __init__(self):
                self.chunks = []
                self.flush_calls = 0

            def write(self, text):
                self.chunks.append(text)
                return len(text)

            def flush(self):
                self.flush_calls += 1

        fake_stdout = FakeStdout()
        monkeypatch.setattr("sys.stdout", fake_stdout)

        print_analysis_stream(
            title="Chunk Test",
            analysis="Line one\nLine two",
            model_info="Model",
        )

        assert len(fake_stdout.chunks) > 1
        assert fake_stdout.flush_calls == len(fake_stdout.chunks)
