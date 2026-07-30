"""Output formatting for paper analysis."""

import re
import sys
from datetime import datetime
from typing import Any

import yaml


def strip_leading_h1(analysis: str) -> str:
    """Remove a model-generated H1 because the note supplies its own title."""
    return re.sub(r"\A\s*#[ \t]+[^\n]*(?:\n+|$)", "", analysis, count=1).strip()


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
    """
    content = format_analysis(
        title,
        analysis,
        model_info,
        paper_metadata=paper_metadata,
        source=source,
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
