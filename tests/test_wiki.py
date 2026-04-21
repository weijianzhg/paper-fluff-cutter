"""Tests for wiki workflow support."""

from __future__ import annotations

import pytest

from fluff_cutter.wiki import (
    add_paper_to_wiki,
    doctor_wiki,
    find_wiki_root,
    init_wiki,
    query_wiki,
    rebuild_wiki,
    remove_paper_from_wiki,
    resolve_paper_paths,
    resolve_paper_slug,
    validate_wiki_root,
    wiki_status,
)


def test_init_wiki_creates_expected_structure(tmp_path):
    root = tmp_path / "research-wiki"

    init_wiki(root)

    assert (root / "fluff-cutter.yaml").exists()
    assert (root / "raw" / "pdfs").is_dir()
    assert (root / "wiki" / "papers").is_dir()
    assert not (root / "wiki" / "topics").exists()
    assert not (root / "wiki" / "concepts").exists()
    assert not (root / "wiki" / "queries").exists()
    assert (root / "wiki" / "index.md").exists()
    assert (root / "wiki" / "overview.md").exists()
    assert (root / "wiki" / "log.md").exists()


def test_find_wiki_root_walks_up_from_nested_directory(tmp_path):
    root = tmp_path / "research-wiki"
    init_wiki(root)
    nested = root / "wiki" / "papers"

    assert find_wiki_root(nested) == root


def test_validate_wiki_root_rejects_uninitialized_directory(tmp_path):
    with pytest.raises(FileNotFoundError, match="initialized fluff-cutter wiki"):
        validate_wiki_root(tmp_path / "not-a-wiki")


@pytest.fixture
def initialized_wiki(tmp_path):
    root = tmp_path / "research-wiki"
    init_wiki(root)
    return root


def test_add_paper_to_wiki_creates_page_and_updates_artifacts(initialized_wiki, tmp_path):
    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    page_path = add_paper_to_wiki(
        initialized_wiki,
        source_ref="https://arxiv.org/abs/1234.5678",
        pdf_path=pdf_path,
        title="Agents for Useful Things",
        analysis="A practical paper about agents doing useful things.",
        model_info="OpenAI (gpt-5.2)",
    )

    assert page_path.exists()
    content = page_path.read_text()
    assert "title: Agents for Useful Things" in content
    assert "source: https://arxiv.org/abs/1234.5678" in content
    assert "A practical paper about agents doing useful things." in content

    copied_pdf = initialized_wiki / "raw" / "pdfs" / "agents-for-useful-things.pdf"
    assert copied_pdf.exists()
    assert copied_pdf.read_bytes() == b"%PDF-1.4 fake"

    index_text = (initialized_wiki / "wiki" / "index.md").read_text()
    assert "Agents for Useful Things" in index_text
    assert "wiki/papers/agents-for-useful-things.md" in index_text

    log_text = (initialized_wiki / "wiki" / "log.md").read_text()
    assert "ingest | Agents for Useful Things" in log_text

    status = wiki_status(initialized_wiki)
    assert status["paper_count"] == 1
    assert status["pdf_count"] == 1
    assert status["orphan_pdf_count"] == 0


def test_add_paper_to_wiki_renames_existing_raw_pdf_without_orphaning(initialized_wiki):
    downloaded_pdf = initialized_wiki / "raw" / "pdfs" / "downloaded.pdf"
    downloaded_pdf.write_bytes(b"%PDF-1.4 fake")

    page_path = add_paper_to_wiki(
        initialized_wiki,
        source_ref="https://arxiv.org/abs/9999.0001",
        pdf_path=downloaded_pdf,
        title="Slugged Title",
        analysis="Useful summary.",
        model_info="OpenAI (gpt-5.2)",
    )

    assert page_path.exists()
    assert not downloaded_pdf.exists()
    assert (initialized_wiki / "raw" / "pdfs" / "slugged-title.pdf").exists()
    assert doctor_wiki(initialized_wiki)["ok"] is True


def test_rebuild_wiki_regenerates_index_from_existing_pages(initialized_wiki):
    papers_dir = initialized_wiki / "wiki" / "papers"
    papers_dir.mkdir(parents=True, exist_ok=True)
    (papers_dir / "alpha-paper.md").write_text(
        "---\n"
        "title: Alpha Paper\n"
        "slug: alpha-paper\n"
        "source: https://example.com/alpha\n"
        "pdf_path: raw/pdfs/alpha-paper.pdf\n"
        "added: 2026-04-19\n"
        "model_info: TestModel\n"
        "---\n\n"
        "# Alpha Paper\n\nAlpha summary.\n",
        encoding="utf-8",
    )

    rebuild_wiki(initialized_wiki)

    index_text = (initialized_wiki / "wiki" / "index.md").read_text()
    assert "Alpha Paper" in index_text
    assert "wiki/papers/alpha-paper.md" in index_text

    overview_text = (initialized_wiki / "wiki" / "overview.md").read_text()
    assert "1 paper" in overview_text


def test_remove_paper_from_wiki_updates_index_and_optionally_deletes_pdf(
    initialized_wiki, tmp_path
):
    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")
    add_paper_to_wiki(
        initialized_wiki,
        source_ref="https://arxiv.org/abs/1234.5678",
        pdf_path=pdf_path,
        title="Delete Me",
        analysis="Disposable analysis.",
        model_info="OpenAI (gpt-5.2)",
    )

    removed = remove_paper_from_wiki(initialized_wiki, "delete-me", delete_pdf=True)

    assert removed["page_deleted"] is True
    assert removed["pdf_deleted"] is True
    assert not (initialized_wiki / "wiki" / "papers" / "delete-me.md").exists()
    assert not (initialized_wiki / "raw" / "pdfs" / "delete-me.pdf").exists()
    assert "Delete Me" not in (initialized_wiki / "wiki" / "index.md").read_text()


def test_query_wiki_returns_ranked_matches_and_snippets(initialized_wiki, tmp_path):
    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")
    add_paper_to_wiki(
        initialized_wiki,
        source_ref="https://example.com/agents",
        pdf_path=pdf_path,
        title="Agents for Useful Things",
        analysis="Agents coordinate tools and planning to solve real tasks.",
        model_info="OpenAI (gpt-5.2)",
    )
    add_paper_to_wiki(
        initialized_wiki,
        source_ref="https://example.com/vision",
        pdf_path=pdf_path,
        title="Vision Models for Boring Benchmarks",
        analysis="Mostly benchmark churn, not much about agents.",
        model_info="OpenAI (gpt-5.2)",
    )

    result = query_wiki(initialized_wiki, "Which paper is about agents and planning?", top_k=2)

    assert result["question"] == "Which paper is about agents and planning?"
    assert result["matches"][0]["title"] == "Agents for Useful Things"
    assert "planning" in result["matches"][0]["snippet"].lower()
    assert result["matches"][0]["score"] >= result["matches"][1]["score"]


def test_wiki_status_reports_pdf_counts_and_orphans(initialized_wiki, tmp_path):
    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")
    add_paper_to_wiki(
        initialized_wiki,
        source_ref="https://example.com/agents",
        pdf_path=pdf_path,
        title="Agents for Useful Things",
        analysis="Agents coordinate tools and planning to solve real tasks.",
        model_info="OpenAI (gpt-5.2)",
    )

    orphan_pdf = initialized_wiki / "raw" / "pdfs" / "orphan.pdf"
    orphan_pdf.write_bytes(b"%PDF-1.4 fake")

    status = wiki_status(initialized_wiki)

    assert status == {"paper_count": 1, "pdf_count": 2, "orphan_pdf_count": 1}


def test_doctor_wiki_reports_index_drift_and_orphan_pdf(initialized_wiki, tmp_path):
    pdf_path = initialized_wiki / "raw" / "pdfs" / "orphan.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    paper_path = initialized_wiki / "wiki" / "papers" / "missing-from-index.md"
    paper_path.write_text(
        "---\n"
        "title: Missing From Index\n"
        "slug: missing-from-index\n"
        "source: https://example.com/missing\n"
        "pdf_path: raw/pdfs/missing-from-index.pdf\n"
        "added: 2026-04-19\n"
        "model_info: TestModel\n"
        "---\n\n"
        "# Missing From Index\n",
        encoding="utf-8",
    )

    report = doctor_wiki(initialized_wiki)

    assert any("missing from index" in issue for issue in report["issues"])
    assert any("orphan PDF" in issue for issue in report["issues"])


def test_resolve_paper_paths_returns_markdown_and_pdf_paths(initialized_wiki, tmp_path):
    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")
    page_path = add_paper_to_wiki(
        initialized_wiki,
        source_ref="https://example.com/agents",
        pdf_path=pdf_path,
        title="Agents for Useful Things",
        analysis="Agents coordinate tools and planning to solve real tasks.",
        model_info="OpenAI (gpt-5.2)",
    )

    resolved = resolve_paper_paths(initialized_wiki, "agents-for-useful-things")

    assert resolved["slug"] == "agents-for-useful-things"
    assert resolved["page_path"] == page_path
    assert resolved["pdf_path"] == initialized_wiki / "raw" / "pdfs" / "agents-for-useful-things.pdf"


def test_resolve_paper_paths_rejects_pdf_outside_raw_pdfs(initialized_wiki):
    page_path = initialized_wiki / "wiki" / "papers" / "bad-path.md"
    page_path.write_text(
        "---\n"
        "title: Bad Path\n"
        "slug: bad-path\n"
        "source: https://example.com/bad\n"
        "pdf_path: ../secret.pdf\n"
        "added: 2026-04-21\n"
        "model_info: TestModel\n"
        "---\n\n"
        "# Bad Path\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="outside raw/pdfs"):
        resolve_paper_paths(initialized_wiki, "bad-path")


def test_remove_paper_from_wiki_rejects_pdf_outside_raw_pdfs(initialized_wiki):
    pdf_path = initialized_wiki / "raw" / "pdfs" / "paper.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")
    page_path = initialized_wiki / "wiki" / "papers" / "bad-delete.md"
    page_path.write_text(
        "---\n"
        "title: Bad Delete\n"
        "slug: bad-delete\n"
        "source: https://example.com/bad-delete\n"
        "pdf_path: ../secret.pdf\n"
        "added: 2026-04-21\n"
        "model_info: TestModel\n"
        "---\n\n"
        "# Bad Delete\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="outside raw/pdfs"):
        remove_paper_from_wiki(initialized_wiki, "bad-delete", delete_pdf=True)


def test_resolve_paper_slug_accepts_slug_path_or_title(initialized_wiki, tmp_path):
    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")
    page_path = add_paper_to_wiki(
        initialized_wiki,
        source_ref="https://example.com/agents",
        pdf_path=pdf_path,
        title="Agents for Useful Things",
        analysis="A practical paper about agents doing useful things.",
        model_info="OpenAI (gpt-5.2)",
    )

    assert (
        resolve_paper_slug(initialized_wiki, "agents-for-useful-things")
        == "agents-for-useful-things"
    )
    assert resolve_paper_slug(initialized_wiki, str(page_path)) == "agents-for-useful-things"
    assert (
        resolve_paper_slug(initialized_wiki, "Agents for Useful Things")
        == "agents-for-useful-things"
    )

    with pytest.raises(FileNotFoundError):
        resolve_paper_slug(initialized_wiki, "does-not-exist")
