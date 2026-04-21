"""Persistent wiki workflow support for Paper Fluff Cutter."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

CONFIG_FILENAME = "fluff-cutter.yaml"
RAW_PDFS_DIR = Path("raw") / "pdfs"
WIKI_DIR = Path("wiki")
PAPERS_DIR = WIKI_DIR / "papers"
INDEX_FILE = WIKI_DIR / "index.md"
OVERVIEW_FILE = WIKI_DIR / "overview.md"
LOG_FILE = WIKI_DIR / "log.md"


@dataclass(frozen=True)
class WikiPaths:
    root: Path

    @property
    def config(self) -> Path:
        return self.root / CONFIG_FILENAME

    @property
    def raw_pdfs(self) -> Path:
        return self.root / RAW_PDFS_DIR

    @property
    def papers(self) -> Path:
        return self.root / PAPERS_DIR

    @property
    def index(self) -> Path:
        return self.root / INDEX_FILE

    @property
    def overview(self) -> Path:
        return self.root / OVERVIEW_FILE

    @property
    def log(self) -> Path:
        return self.root / LOG_FILE


def _paths(root: Path | str) -> WikiPaths:
    return WikiPaths(Path(root).expanduser().resolve())


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "paper"


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _read_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    meta_text = text[4:end]
    body = text[end + 5 :]
    return yaml.safe_load(meta_text) or {}, body


def _paper_entries(root: Path | str) -> list[dict[str, Any]]:
    paths = _paths(root)
    entries = []
    for path in sorted(paths.papers.glob("*.md")):
        meta, body = _read_frontmatter(path)
        entries.append(
            {
                "path": path,
                "title": meta.get("title", path.stem),
                "slug": meta.get("slug", path.stem),
                "source": meta.get("source", ""),
                "pdf_path": meta.get("pdf_path", ""),
                "added": meta.get("added", ""),
                "model_info": meta.get("model_info", ""),
                "summary": _body_summary(body),
                "body": body,
            }
        )
    return entries


def _body_summary(body: str) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return ""


def _unique_slug(paths: WikiPaths, title: str) -> str:
    base = slugify(title)
    candidate = base
    counter = 2
    while (paths.papers / f"{candidate}.md").exists() or (
        paths.raw_pdfs / f"{candidate}.pdf"
    ).exists():
        candidate = f"{base}-{counter}"
        counter += 1
    return candidate


def init_wiki(root: Path | str) -> Path:
    paths = _paths(root)
    paths.root.mkdir(parents=True, exist_ok=True)
    paths.raw_pdfs.mkdir(parents=True, exist_ok=True)
    paths.papers.mkdir(parents=True, exist_ok=True)

    config = {
        "version": 1,
        "raw_pdfs_dir": str(RAW_PDFS_DIR),
        "wiki_dir": str(WIKI_DIR),
        "papers_dir": str(PAPERS_DIR),
    }
    _write_text(paths.config, yaml.safe_dump(config, sort_keys=False))

    if not paths.index.exists():
        _write_text(paths.index, "# Paper Wiki Index\n\n_No papers yet._\n")
    if not paths.overview.exists():
        _write_text(paths.overview, "# Wiki Overview\n\nNo papers added yet.\n")
    if not paths.log.exists():
        _write_text(paths.log, "# Wiki Log\n\n")
    return paths.root


def find_wiki_root(start: Path | str | None = None) -> Path:
    current = Path(start or Path.cwd()).expanduser().resolve()
    for candidate in [current, *current.parents]:
        if (candidate / CONFIG_FILENAME).exists():
            return candidate
    raise FileNotFoundError("Could not find fluff-cutter wiki root (missing fluff-cutter.yaml)")


def validate_wiki_root(root: Path | str) -> Path:
    paths = _paths(root)
    missing = []
    for path in [
        paths.config,
        paths.raw_pdfs,
        paths.papers,
        paths.index,
        paths.overview,
        paths.log,
    ]:
        if not path.exists():
            missing.append(path.relative_to(paths.root).as_posix())

    if missing:
        missing_str = ", ".join(missing)
        raise FileNotFoundError(
            "Directory is not an initialized fluff-cutter wiki: "
            f"{paths.root} (missing: {missing_str})"
        )
    return paths.root


def rebuild_wiki(root: Path | str) -> dict[str, Any]:
    paths = _paths(root)
    entries = _paper_entries(paths.root)

    if entries:
        lines = ["# Paper Wiki Index", "", f"Total papers: {len(entries)}", "", "## Papers", ""]
        for entry in entries:
            rel = entry["path"].relative_to(paths.root).as_posix()
            summary = entry["summary"] or "No summary yet."
            lines.append(f"- [{entry['title']}]({rel}) — {summary}")
        index_content = "\n".join(lines) + "\n"
    else:
        index_content = "# Paper Wiki Index\n\n_No papers yet._\n"
    _write_text(paths.index, index_content)

    overview_lines = [
        "# Wiki Overview",
        "",
        f"This wiki currently tracks {len(entries)} paper{'s' if len(entries) != 1 else ''}.",
        "",
    ]
    if entries:
        overview_lines.extend(["## Recent papers", ""])
        for entry in sorted(entries, key=lambda item: item["added"], reverse=True)[:10]:
            overview_lines.append(f"- {entry['title']}")
    else:
        overview_lines.append("No papers added yet.")
    _write_text(paths.overview, "\n".join(overview_lines) + "\n")

    return {"paper_count": len(entries), "index_path": paths.index, "overview_path": paths.overview}


def _append_log(root: Path | str, action: str, title: str, detail: str = "") -> None:
    paths = _paths(root)
    prefix = f"## [{today_str()}] {action} | {title}"
    with paths.log.open("a", encoding="utf-8") as handle:
        handle.write(prefix + "\n")
        if detail:
            handle.write(detail.rstrip() + "\n")
        handle.write("\n")


def add_paper_to_wiki(
    root: Path | str,
    source_ref: str,
    pdf_path: Path | str,
    title: str,
    analysis: str,
    model_info: str,
) -> Path:
    paths = _paths(root)
    pdf_path = Path(pdf_path).expanduser().resolve()
    slug = _unique_slug(paths, title)
    target_pdf = paths.raw_pdfs / f"{slug}.pdf"
    if pdf_path == target_pdf:
        pass
    elif pdf_path.parent == paths.raw_pdfs:
        shutil.move(str(pdf_path), target_pdf)
    else:
        shutil.copy2(pdf_path, target_pdf)

    page_path = paths.papers / f"{slug}.md"
    metadata = {
        "title": title,
        "slug": slug,
        "source": source_ref,
        "pdf_path": target_pdf.relative_to(paths.root).as_posix(),
        "added": today_str(),
        "model_info": model_info,
    }
    frontmatter = yaml.safe_dump(metadata, sort_keys=False).strip()
    body = f"---\n{frontmatter}\n---\n\n# {title}\n\n## Analysis\n\n{analysis.strip()}\n"
    _write_text(page_path, body)
    rebuild_wiki(paths.root)
    _append_log(paths.root, "ingest", title, f"source: {source_ref}")
    return page_path


def resolve_paper_slug(root: Path | str, identifier: str) -> str:
    paths = _paths(root)
    candidate = Path(identifier)
    if candidate.suffix == ".md":
        return candidate.stem
    if (paths.papers / f"{identifier}.md").exists():
        return identifier

    wanted = identifier.strip().lower()
    for entry in _paper_entries(paths.root):
        if entry["slug"] == wanted or entry["title"].lower() == wanted:
            return entry["slug"]
    raise FileNotFoundError(f"Paper not found: {identifier}")


def remove_paper_from_wiki(
    root: Path | str,
    identifier: str,
    delete_pdf: bool = False,
) -> dict[str, Any]:
    paths = _paths(root)
    slug = resolve_paper_slug(paths.root, identifier)
    page_path = paths.papers / f"{slug}.md"
    meta, _ = _read_frontmatter(page_path)
    title = meta.get("title", slug)
    pdf_deleted = False

    page_path.unlink()
    pdf_rel = meta.get("pdf_path")
    if delete_pdf and pdf_rel:
        pdf_path = paths.root / pdf_rel
        if pdf_path.exists():
            pdf_path.unlink()
            pdf_deleted = True

    rebuild_wiki(paths.root)
    _append_log(paths.root, "remove", title, f"slug: {slug}")
    return {"slug": slug, "page_deleted": True, "pdf_deleted": pdf_deleted}


_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "about",
    "for",
    "from",
    "how",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "which",
    "with",
}


def _tokenize(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9]+", text.lower()) if token not in _STOPWORDS]


def _snippet(text: str, tokens: list[str], width: int = 140) -> str:
    lower = text.lower()
    positions = [lower.find(token) for token in tokens if lower.find(token) != -1]
    if not positions:
        cleaned = " ".join(text.split())
        return cleaned[:width] + ("..." if len(cleaned) > width else "")
    start = max(min(positions) - 30, 0)
    snippet = " ".join(text[start : start + width].split())
    if start > 0:
        snippet = "..." + snippet
    return snippet + ("..." if start + width < len(text) else "")


def query_wiki(root: Path | str, question: str, top_k: int = 5) -> dict[str, Any]:
    tokens = _tokenize(question)
    matches = []
    for entry in _paper_entries(root):
        haystack = f"{entry['title']}\n{entry['summary']}\n{entry['body']}"
        hay_tokens = _tokenize(haystack)
        score = sum(hay_tokens.count(token) for token in tokens)
        if score > 0:
            matches.append(
                {
                    "title": entry["title"],
                    "slug": entry["slug"],
                    "path": entry["path"],
                    "score": score,
                    "snippet": _snippet(haystack, tokens),
                }
            )
    matches.sort(key=lambda item: (-item["score"], item["title"].lower()))
    return {"question": question, "matches": matches[:top_k]}


def doctor_wiki(root: Path | str) -> dict[str, Any]:
    paths = _paths(root)
    issues: list[str] = []
    index_text = paths.index.read_text(encoding="utf-8") if paths.index.exists() else ""
    paper_entries = _paper_entries(paths.root)

    for entry in paper_entries:
        rel = entry["path"].relative_to(paths.root).as_posix()
        if rel not in index_text:
            issues.append(f"Paper '{entry['title']}' is missing from index.md")
        if entry["pdf_path"] and not (paths.root / entry["pdf_path"]).exists():
            issues.append(f"Paper '{entry['title']}' references missing PDF: {entry['pdf_path']}")

    referenced_pdfs = {entry["pdf_path"] for entry in paper_entries if entry["pdf_path"]}
    for pdf_path in sorted(paths.raw_pdfs.glob("*.pdf")):
        rel = pdf_path.relative_to(paths.root).as_posix()
        if rel not in referenced_pdfs:
            issues.append(f"Found orphan PDF with no paper page: {rel}")

    return {"ok": not issues, "issues": issues}


def list_papers(root: Path | str) -> list[dict[str, Any]]:
    return [
        {
            "title": entry["title"],
            "slug": entry["slug"],
            "added": entry["added"],
            "path": entry["path"],
        }
        for entry in _paper_entries(root)
    ]


def wiki_status(root: Path | str) -> dict[str, Any]:
    paths = _paths(root)
    papers = _paper_entries(paths.root)
    referenced_pdfs = {entry["pdf_path"] for entry in papers if entry["pdf_path"]}
    pdf_count = len(list(paths.raw_pdfs.glob("*.pdf"))) if paths.raw_pdfs.exists() else 0
    orphan_pdf_count = 0
    if paths.raw_pdfs.exists():
        for pdf_path in paths.raw_pdfs.glob("*.pdf"):
            rel = pdf_path.relative_to(paths.root).as_posix()
            if rel not in referenced_pdfs:
                orphan_pdf_count += 1
    return {
        "paper_count": len(papers),
        "pdf_count": pdf_count,
        "orphan_pdf_count": orphan_pdf_count,
    }
