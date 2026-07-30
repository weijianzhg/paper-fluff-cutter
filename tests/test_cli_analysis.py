"""Tests for CLI analysis rendering and metadata plumbing."""

from __future__ import annotations

from argparse import Namespace
from datetime import datetime
from unittest.mock import ANY, MagicMock

from fluff_cutter import cli


def test_stream_provider_response_hides_chunked_machine_metadata(monkeypatch, capsys):
    provider = MagicMock()
    chunks = iter(
        [
            "TITLE: Useful Paper\n\n## Why Should I Care?\nUseful.\n\n<!-- paper-",
            'metadata\n{"title":"Useful Paper"}\n-->',
        ]
    )
    monkeypatch.setattr(cli, "stream_analysis_chunks", lambda *_args: chunks)

    raw_response = cli._stream_provider_response(provider, "base64", "paper.pdf")

    visible = capsys.readouterr().out
    assert "## Why Should I Care?" in visible
    assert "paper-metadata" not in visible
    assert '"title"' not in visible
    assert "paper-metadata" in raw_response


def test_cmd_analyze_passes_extracted_metadata_to_saved_note(monkeypatch, tmp_path):
    result = {
        "title": "Useful Paper",
        "analysis": "## Why Should I Care?\nUseful.",
        "metadata": {"authors": ["A. Author"], "topics": ["evaluation"]},
        "model_info": "OpenAI (gpt-5.2)",
    }
    paper_path = tmp_path / "paper.pdf"
    monkeypatch.setattr(cli, "analyze_source", lambda *_args, **_kwargs: (result, str(paper_path)))
    save_analysis = MagicMock()
    monkeypatch.setattr(cli, "save_analysis", save_analysis)
    output_path = tmp_path / "useful-paper-2026-07-30.md"
    default_analysis_path = MagicMock(return_value=output_path)
    monkeypatch.setattr(cli, "default_analysis_path", default_analysis_path)
    args = Namespace(
        paper_path="https://example.com/paper.pdf",
        provider=None,
        model=None,
        max_pages=None,
        print_output=False,
        output=None,
    )

    cli.cmd_analyze(args)

    default_analysis_path.assert_called_once()
    generated_path_args = default_analysis_path.call_args.args
    assert generated_path_args[:2] == (str(paper_path), "Useful Paper")
    assert isinstance(generated_path_args[2], datetime)
    save_analysis.assert_called_once_with(
        "Useful Paper",
        "## Why Should I Care?\nUseful.",
        "OpenAI (gpt-5.2)",
        str(output_path),
        paper_metadata={"authors": ["A. Author"], "topics": ["evaluation"]},
        source="https://example.com/paper.pdf",
        created_at=ANY,
    )


def test_cmd_analyze_preserves_explicit_output_path(monkeypatch, tmp_path):
    result = {
        "title": "Useful Paper",
        "analysis": "Useful.",
        "metadata": {},
        "model_info": "OpenAI (gpt-5.2)",
    }
    paper_path = tmp_path / "2411.19870.pdf"
    output_path = tmp_path / "my-note.md"
    monkeypatch.setattr(cli, "analyze_source", lambda *_args, **_kwargs: (result, str(paper_path)))
    save_analysis = MagicMock()
    monkeypatch.setattr(cli, "save_analysis", save_analysis)
    default_analysis_path = MagicMock()
    monkeypatch.setattr(cli, "default_analysis_path", default_analysis_path)
    args = Namespace(
        paper_path="https://arxiv.org/abs/2411.19870",
        provider=None,
        model=None,
        max_pages=None,
        print_output=False,
        output=str(output_path),
    )

    cli.cmd_analyze(args)

    default_analysis_path.assert_not_called()
    assert save_analysis.call_args.args[3] == str(output_path)


def test_cmd_wiki_add_passes_extracted_metadata_to_wiki(monkeypatch, tmp_path):
    result = {
        "title": "Useful Paper",
        "analysis": "## Why Should I Care?\nUseful.",
        "metadata": {"authors": ["A. Author"], "topics": ["evaluation"]},
        "model_info": "OpenAI (gpt-5.2)",
    }
    root = tmp_path / "wiki"
    local_pdf = root / "raw" / "pdfs" / "paper.pdf"
    monkeypatch.setattr(cli, "_resolve_wiki_root", lambda _root: root)
    analyze_source = MagicMock(return_value=(result, str(local_pdf)))
    monkeypatch.setattr(cli, "analyze_source", analyze_source)
    add_paper = MagicMock(return_value=root / "wiki" / "papers" / "useful-paper.md")
    monkeypatch.setattr(cli, "add_paper_to_wiki", add_paper)
    args = Namespace(
        root=None,
        paper_path="https://example.com/paper.pdf",
        provider=None,
        model=None,
        max_pages=None,
    )

    cli.cmd_wiki_add(args)

    analyze_source.assert_called_once_with(
        "https://example.com/paper.pdf",
        provider=None,
        model=None,
        max_pages=None,
        download_dir=root / "raw" / "pdfs",
    )
    add_paper.assert_called_once_with(
        root,
        source_ref="https://example.com/paper.pdf",
        pdf_path=str(local_pdf),
        title="Useful Paper",
        analysis="## Why Should I Care?\nUseful.",
        model_info="OpenAI (gpt-5.2)",
        paper_metadata={"authors": ["A. Author"], "topics": ["evaluation"]},
    )
