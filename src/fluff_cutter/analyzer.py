"""Core paper analysis logic."""

from typing import Iterator

from .providers.base import BaseLLMProvider

ANALYSIS_PROMPT = """You are analyzing an academic paper. Your job is to cut through \
all the fluff and extract only what matters.

Answer these three questions concisely and critically:

1. WHY SHOULD I CARE?
   - What problem does this address?
   - Why does it matter to the world (not just academia)?

2. WHAT'S THE ACTUAL INNOVATION?
   - What is the core idea or proposal?
   - What makes it different from existing work?
   - Describe it in plain terms, no jargon.

3. IS THE EVIDENCE CONVINCING?
   - What experiments or evidence do they provide?
   - Are there obvious gaps or weaknesses?
   - Does the evidence actually support their claims?

Be brutally honest. If the paper is weak, say so.
If it's mostly fluff with a tiny kernel of insight, identify that kernel.

Also extract the paper's title at the beginning of your response in this format:
TITLE: [Paper Title]

Then provide your analysis."""


def parse_analysis_response(raw_response: str, provider: BaseLLMProvider) -> dict:
    """
    Parse a model response into title + analysis fields.

    Args:
        raw_response: Full response text from the model.
        provider: LLM provider that produced the response.

    Returns:
        Dictionary with 'title', 'analysis', and 'model_info' keys.
    """
    # Try to extract the title from the response
    title = "Unknown Title"
    analysis = raw_response

    lines = raw_response.strip().split("\n")
    for i, line in enumerate(lines):
        if line.strip().upper().startswith("TITLE:"):
            title = line.split(":", 1)[1].strip()
            # Remove the title line from the analysis
            analysis = "\n".join(lines[i + 1 :]).strip()
            break

    return {
        "title": title,
        "analysis": analysis,
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
