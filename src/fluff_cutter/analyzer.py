"""Core paper analysis logic."""

import json
import re
from typing import Any, Iterator

from .providers.base import BaseLLMProvider

PAPER_METADATA_PATTERN = re.compile(
    r"<!--\s*paper-metadata\s*(.*?)\s*-->",
    re.DOTALL | re.IGNORECASE,
)
INCOMPLETE_PAPER_METADATA_PATTERN = re.compile(
    r"<!--\s*paper-metadata\b.*\Z",
    re.DOTALL | re.IGNORECASE,
)
RESEARCH_TYPES = (
    "empirical",
    "theoretical",
    "survey",
    "benchmark",
    "systems",
    "methods",
    "position",
    "case-study",
    "other",
)

ANALYSIS_PROMPT = """You are analyzing an academic paper. Your job is to cut through \
all the fluff and extract only what matters.

Start with the paper title in exactly this format:

TITLE: [Paper Title]

Then answer these three questions using Markdown level-two headings:

## Why Should I Care?
- What problem does this address?
- Why does it matter to the world (not just academia)?

## What's the Actual Innovation?
- What is the core idea or proposal?
- What makes it different from existing work?
- Describe it in plain terms, no jargon.

## Is the Evidence Convincing?
- What experiments or evidence do they provide?
- Are there obvious gaps or weaknesses?
- Does the evidence actually support their claims?

Be brutally honest. If the paper is weak, say so. If it is mostly fluff with a tiny
kernel of insight, identify that kernel.

End with exactly one HTML comment containing valid JSON in this shape:

<!-- paper-metadata
{
  "authors": ["Author One", "Author Two"],
  "published_year": 2025,
  "research_type": "empirical",
  "topics": ["machine-learning", "language-models"],
  "concepts": ["test-time compute", "verifier-guided search"],
  "prerequisites": ["transformer architecture"]
}
-->

Metadata rules:
- authors: the paper's authors in source order; use [] when unavailable
- published_year: the paper's four-digit publication year, otherwise null
- research_type: one of empirical, theoretical, survey, benchmark, systems, methods,
  position, case-study, or other
- topics: 3-8 reusable lowercase kebab-case topics; prefer common names
- concepts: 3-8 concise noun phrases naming ideas actually explained by the paper
- prerequisites: 0-5 concepts a reader should know first; use [] when none are evident
- Do not wrap the JSON in a Markdown code fence or add text after the comment."""


def _normalize_text_list(value: Any, *, max_items: int) -> list[str]:
    """Return a bounded, de-duplicated list of short strings."""
    if not isinstance(value, list):
        return []

    normalized = []
    seen = set()
    for item in value:
        if not isinstance(item, str):
            continue
        text = re.sub(r"\s+", " ", item).strip()
        if not text or len(text) > 100:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(text)
        if len(normalized) >= max_items:
            break
    return normalized


def _normalize_topic(value: str) -> str:
    """Normalize a model-provided topic into an Obsidian-compatible tag."""
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")[:50].rstrip("-")


def extract_paper_metadata(response: str) -> tuple[str, dict[str, Any]]:
    """Extract validated paper metadata and remove all machine comments."""
    matches = list(PAPER_METADATA_PATTERN.finditer(response))
    clean_response = PAPER_METADATA_PATTERN.sub("", response)
    clean_response = INCOMPLETE_PAPER_METADATA_PATTERN.sub("", clean_response).strip()
    raw_metadata = None

    for match in reversed(matches):
        try:
            candidate = json.loads(match.group(1))
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(candidate, dict):
            raw_metadata = candidate
            break

    if raw_metadata is None:
        return clean_response, {}

    metadata: dict[str, Any] = {}
    authors = _normalize_text_list(raw_metadata.get("authors"), max_items=20)
    if authors or raw_metadata.get("authors") == []:
        metadata["authors"] = authors

    published_year = raw_metadata.get("published_year")
    if (
        isinstance(published_year, int)
        and not isinstance(published_year, bool)
        and 1800 <= published_year <= 2100
    ):
        metadata["published_year"] = published_year

    research_type = raw_metadata.get("research_type")
    if isinstance(research_type, str) and research_type in RESEARCH_TYPES:
        metadata["research_type"] = research_type

    topics = []
    for topic in _normalize_text_list(raw_metadata.get("topics"), max_items=8):
        normalized_topic = _normalize_topic(topic)
        if normalized_topic and normalized_topic not in topics:
            topics.append(normalized_topic)
    if topics:
        metadata["topics"] = topics

    for field, max_items in (("concepts", 8), ("prerequisites", 5)):
        values = _normalize_text_list(raw_metadata.get(field), max_items=max_items)
        if values or raw_metadata.get(field) == []:
            metadata[field] = values

    return clean_response, metadata


def parse_analysis_response(raw_response: str, provider: BaseLLMProvider) -> dict:
    """
    Parse a model response into title + analysis fields.

    Args:
        raw_response: Full response text from the model.
        provider: LLM provider that produced the response.

    Returns:
        Dictionary with 'title', 'analysis', 'metadata', and 'model_info' keys.
    """
    clean_response, metadata = extract_paper_metadata(raw_response)

    # Try to extract the title from the response
    title = "Unknown Title"
    analysis = clean_response

    lines = clean_response.strip().split("\n")
    for i, line in enumerate(lines):
        if line.strip().upper().startswith("TITLE:"):
            title = line.split(":", 1)[1].strip()
            # Remove the title line from the analysis
            analysis = "\n".join(lines[i + 1 :]).strip()
            break

    return {
        "title": title,
        "analysis": analysis,
        "metadata": metadata,
        "model_info": provider.get_model_info(),
    }


def analyze_paper(provider: BaseLLMProvider, pdf_base64: str, filename: str) -> dict:
    """
    Analyze a paper using the provided LLM.

    Args:
        provider: The LLM provider to use for analysis.
        pdf_base64: Base64-encoded PDF data.
        filename: Original filename of the PDF.

    Returns:
        Dictionary with 'title', 'analysis', and 'model_info' keys.
    """
    raw_response = provider.analyze_paper(pdf_base64, filename, ANALYSIS_PROMPT)

    return parse_analysis_response(raw_response, provider)


def stream_analysis_chunks(
    provider: BaseLLMProvider, pdf_base64: str, filename: str
) -> Iterator[str]:
    """
    Stream analysis text chunks from the provider.

    Args:
        provider: The LLM provider to use.
        pdf_base64: Base64-encoded PDF data.
        filename: Original filename of the PDF.

    Yields:
        Incremental response text chunks.
    """
    yield from provider.analyze_paper_stream(pdf_base64, filename, ANALYSIS_PROMPT)
