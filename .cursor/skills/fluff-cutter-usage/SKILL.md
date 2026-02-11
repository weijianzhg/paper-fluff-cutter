---
name: fluff-cutter-usage
description: Analyze academic papers using the fluff-cutter CLI tool. Use when the user wants to analyze a research paper, review a PDF, extract key findings from a paper, or provides an arxiv/PDF URL to evaluate.
---

# Fluff Cutter - Paper Analysis Tool

A CLI tool that analyzes academic papers and extracts their core value by answering three questions:
1. Why should I care?
2. What's the actual innovation?
3. Is the evidence convincing?

## Prerequisites

The tool must be configured with at least one LLM API key before use. Check with:

```bash
fluff-cutter --version
```

If not installed: `pip install fluff-cutter`

If not configured, run `fluff-cutter init` or set environment variables:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
# or
export OPENAI_API_KEY=sk-...
# or
export OPENROUTER_API_KEY=sk-or-...
```

## Usage

### Analyze a local PDF

```bash
fluff-cutter analyze paper.pdf
```

Output is saved as `paper.md` by default (same name, `.md` extension).

### Analyze from URL

Pass a URL directly -- the PDF is downloaded to the current directory and reused on subsequent runs:

```bash
fluff-cutter analyze https://arxiv.org/pdf/2411.19870
```

Arxiv `/abs/` URLs are automatically converted to `/pdf/` URLs.

### Common options

```bash
# Save to a specific file
fluff-cutter analyze paper.pdf --output summary.md

# Print to stdout instead of saving
fluff-cutter analyze paper.pdf --print

# Use a specific provider
fluff-cutter analyze paper.pdf --provider openai

# Use a specific model
fluff-cutter analyze paper.pdf --provider anthropic --model claude-sonnet-4-5

# Limit pages for very long papers
fluff-cutter analyze paper.pdf --max-pages 30
```

### Providers

| Provider | Flag | Default Model |
|----------|------|---------------|
| Anthropic | `--provider anthropic` | claude-sonnet-4-5 |
| OpenAI | `--provider openai` | gpt-5.2 |
| OpenRouter | `--provider openrouter` | anthropic/claude-sonnet-4-5 |

## Typical workflow for an agent

1. Receive a paper URL or file path from the user
2. Run `fluff-cutter analyze <path-or-url> --print` to get the analysis to stdout
3. Present the key findings to the user
4. If the user wants the analysis saved, re-run without `--print` or with `--output <file>`

## Error handling

- If the paper exceeds token limits, the tool auto-truncates to 50 pages and retries
- If a URL returns a non-PDF response, the tool reports an error
- If no API key is configured, the tool suggests running `fluff-cutter init`
