"""CLI tests for wiki workflow commands."""

from __future__ import annotations

import pytest

from fluff_cutter import cli
from fluff_cutter.wiki import add_paper_to_wiki, init_wiki


@pytest.fixture
def wiki_root(tmp_path):
    root = tmp_path / "research-wiki"
    init_wiki(root)
    return root


def test_main_wiki_init_creates_project(tmp_path, monkeypatch, capsys):
    root = tmp_path / "brand-new-wiki"
    monkeypatch.setattr(cli.sys, "argv", ["fluff-cutter", "wiki", "init", str(root)])

    cli.main()

    out = capsys.readouterr().out
    assert "Initialized wiki" in out
    assert (root / "fluff-cutter.yaml").exists()


def test_main_wiki_status_prints_counts(wiki_root, monkeypatch, capsys, tmp_path):
    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")
    add_paper_to_wiki(
        wiki_root,
        source_ref="https://example.com/agents",
        pdf_path=pdf_path,
        title="Agents for Useful Things",
        analysis="Agents coordinate tools and planning to solve real tasks.",
        model_info="OpenAI (gpt-5.2)",
    )

    monkeypatch.setattr(
        cli.sys,
        "argv",
        ["fluff-cutter", "wiki", "status", "--root", str(wiki_root)],
    )

    cli.main()

    out = capsys.readouterr().out
    assert "paper_count: 1" in out
    assert "query_count: 0" in out


def test_main_wiki_query_prints_matches(wiki_root, monkeypatch, capsys, tmp_path):
    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")
    add_paper_to_wiki(
        wiki_root,
        source_ref="https://example.com/agents",
        pdf_path=pdf_path,
        title="Agents for Useful Things",
        analysis="Agents coordinate tools and planning to solve real tasks.",
        model_info="OpenAI (gpt-5.2)",
    )

    monkeypatch.setattr(
        cli.sys,
        "argv",
        ["fluff-cutter", "wiki", "query", "agents planning", "--root", str(wiki_root)],
    )

    cli.main()

    out = capsys.readouterr().out
    assert "Agents for Useful Things" in out
    assert "planning" in out.lower()


def test_main_wiki_ls_prints_known_papers(wiki_root, monkeypatch, capsys, tmp_path):
    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")
    add_paper_to_wiki(
        wiki_root,
        source_ref="https://example.com/agents",
        pdf_path=pdf_path,
        title="Agents for Useful Things",
        analysis="Agents coordinate tools and planning to solve real tasks.",
        model_info="OpenAI (gpt-5.2)",
    )

    monkeypatch.setattr(cli.sys, "argv", ["fluff-cutter", "wiki", "ls", "--root", str(wiki_root)])

    cli.main()

    out = capsys.readouterr().out
    assert "agents-for-useful-things" in out
    assert "Agents for Useful Things" in out


def test_create_provider_prints_setup_guidance_when_unconfigured(monkeypatch, capsys):
    monkeypatch.setattr(cli, "is_configured", lambda: False)

    with pytest.raises(SystemExit):
        cli._create_provider(None, None)

    err = capsys.readouterr().err
    assert "Run 'fluff-cutter init'" in err
    assert "OPENAI_API_KEY" in err
    assert "OPENROUTER_API_KEY" in err


def test_wiki_status_rejects_uninitialized_root(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        cli.sys,
        "argv",
        ["fluff-cutter", "wiki", "status", "--root", str(tmp_path / "nope")],
    )

    with pytest.raises(SystemExit):
        cli.main()

    err = capsys.readouterr().err
    assert "Run 'fluff-cutter wiki init <path>' first." in err
