"""Output formatting for paper analysis."""

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

MAX_FILENAME_TITLE_LENGTH = 80
MAX_FILENAME_SOURCE_BYTES = 48
MAX_FILENAME_BYTES = 240


def strip_leading_h1(analysis: str) -> str:
    """Remove a model-generated H1 because the note supplies its own title."""
    return re.sub(r"\A\s*#[ \t]+[^\n]*(?:\n+|$)", "", analysis, count=1).strip()


def _filename_slug(text: str) -> str:
    slug = re.sub(r"[^\w]+", "-", text.casefold(), flags=re.UNICODE)
    return slug.replace("_", "-").strip("-")


def _source_slug(text: str) -> str:
    slug = re.sub(r"[^\w.]+", "-", text.casefold(), flags=re.UNICODE)
    return slug.replace("_", "-").strip("-.")


def _truncate_utf8(text: str, max_bytes: int) -> str:
    """Truncate text without splitting a UTF-8 code point."""
    return text.encode("utf-8")[:max_bytes].decode("utf-8", errors="ignore")


def default_analysis_path(
    pdf_path: str | Path,
    title: str,
    created_at: datetime | None = None,
) -> Path:
    """Build a recognizable default filename from the paper title and extraction date."""
    title_slug = _filename_slug(title)
    title_slug = title_slug[:MAX_FILENAME_TITLE_LENGTH].rstrip("-") or "paper"
    extraction_date = (created_at or datetime.now()).strftime("%Y-%m-%d")
    source_slug = _truncate_utf8(
        _source_slug(Path(pdf_path).stem),
        MAX_FILENAME_SOURCE_BYTES,
    ).rstrip("-.")
    source_id = (
        f"-{source_slug}"
        if source_slug and source_slug not in {"paper", "downloaded-paper", title_slug}
        else ""
    )
    suffix = f"{source_id}-{extraction_date}.md"
    title_byte_budget = MAX_FILENAME_BYTES - len(suffix.encode("utf-8"))
    title_slug = _truncate_utf8(title_slug, title_byte_budget).rstrip("-") or "paper"
    return Path(pdf_path).with_name(f"{title_slug}{suffix}")


def build_paper_properties(
    *,
    model_info: str,
    paper_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the shared Obsidian properties for an analyzed paper."""
    extracted = paper_metadata or {}
    properties: dict[str, Any] = {"content_type": "research-paper"}
    for field in ("authors", "published_year", "research_type", "concepts", "prerequisites"):
        if field in extracted:
            properties[field] = extracted[field]
    properties["tags"] = ["paper", "summary", *extracted.get("topics", [])]
    properties["model"] = model_info
    return properties


def build_note_metadata(
    *,
    title: str,
    model_info: str,
    paper_metadata: dict[str, Any] | None = None,
    source: str | None = None,
    created_at: datetime | None = None,
) -> dict[str, Any]:
    """Build stable Obsidian properties for an analyzed paper."""
    metadata: dict[str, Any] = {"title": title}
    if source:
        metadata["source"] = source
    metadata["created"] = (created_at or datetime.now()).strftime("%Y-%m-%d")
    metadata.update(
        build_paper_properties(
            model_info=model_info,
            paper_metadata=paper_metadata,
        )
    )
    return metadata


def format_analysis(
    title: str,
    analysis: str,
    model_info: str,
    paper_metadata: dict[str, Any] | None = None,
    source: str | None = None,
    created_at: datetime | None = None,
) -> str:
    """
    Format the analysis as clean markdown.

    Args:
        title: The paper title.
        analysis: The raw analysis from the LLM.
        model_info: Information about the model used.
        paper_metadata: Validated metadata extracted from the model response.
        source: Original paper path or URL.
        created_at: Optional timestamp used for the created property.

    Returns:
        Formatted markdown string.
    """
    metadata = build_note_metadata(
        title=title,
        model_info=model_info,
        paper_metadata=paper_metadata,
        source=source,
        created_at=created_at,
    )
    frontmatter = yaml.safe_dump(
        metadata,
        sort_keys=False,
        allow_unicode=True,
        width=1000,
    ).strip()
    clean_analysis = strip_leading_h1(analysis)
    return f"---\n{frontmatter}\n---\n\n# {title}\n\n{clean_analysis}\n"


def print_analysis(title: str, analysis: str, model_info: str) -> None:
    """
    Print the formatted analysis to stdout.

    Args:
        title: The paper title.
        analysis: The raw analysis from the LLM.
        model_info: Information about the model used.
    """
    print(format_analysis(title, analysis, model_info))


def print_analysis_stream(title: str, analysis: str, model_info: str) -> None:
    """
    Print formatted analysis progressively to stdout.

    Args:
        title: The paper title.
        analysis: The raw analysis from the LLM.
        model_info: Information about the model used.
    """
    formatted = format_analysis(title, analysis, model_info)
    for chunk in formatted.splitlines(keepends=True):
        sys.stdout.write(chunk)
        sys.stdout.flush()


def save_analysis(
    title: str,
    analysis: str,
    model_info: str,
    output_path: str,
    paper_metadata: dict[str, Any] | None = None,
    source: str | None = None,
    created_at: datetime | None = None,
) -> None:
    """
    Save the formatted analysis to a file.

    Args:
        title: The paper title.
        analysis: The raw analysis from the LLM.
        model_info: Information about the model used.
        output_path: Path to save the output file.
        paper_metadata: Validated metadata extracted from the model response.
        source: Original paper path or URL.
        created_at: Optional timestamp shared with the generated filename.
    """
    content = format_analysis(
        title,
        analysis,
        model_info,
        paper_metadata=paper_metadata,
        source=source,
        created_at=created_at,
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
