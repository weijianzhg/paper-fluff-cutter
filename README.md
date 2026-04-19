# Paper Fluff Cutter

A CLI tool that cuts through academic paper fluff to extract what actually matters.

Most research has close to zero value. This tool uses multimodal LLMs to analyze papers and answer three questions:

1. **Why should I care?** - What problem does this address and why does it matter?
2. **What's the actual innovation?** - What's the core idea in plain terms?
3. **Is the evidence convincing?** - Do the experiments actually support the claims?

Acknowledgement: the design of the fluff-cutter wiki is inspired by Andrej Karpathy's gist on cutting through paper fluff:
https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

## Quick Start

```bash
pip install fluff-cutter
fluff-cutter init          # set up API keys and defaults
fluff-cutter analyze paper.pdf
```

Requires Python 3.10+.

## Usage

```bash
# Local file
fluff-cutter analyze paper.pdf

# URL (arxiv /abs/ links are auto-converted to PDF)
fluff-cutter analyze https://arxiv.org/pdf/2411.19870

# Options
fluff-cutter analyze paper.pdf --output analysis.md   # custom output path
fluff-cutter analyze paper.pdf --print                 # stdout only, no file
fluff-cutter analyze paper.pdf --provider openai       # openai, anthropic, openrouter
fluff-cutter analyze paper.pdf --model gpt-5.2         # override default model
fluff-cutter analyze paper.pdf --max-pages 30          # limit pages for long papers
```

## Wiki workflow

For persistent research tracking, you can keep a markdown wiki alongside the raw PDFs:

```bash
# Create a wiki project
fluff-cutter wiki init ./research-wiki

# `wiki init` saves this as your default wiki root, so later commands work
# from anywhere unless you explicitly override with --root
fluff-cutter wiki add https://arxiv.org/pdf/2411.19870

# Inspect the wiki
fluff-cutter wiki ls
fluff-cutter wiki status
fluff-cutter wiki query "agents planning"

# Maintenance
fluff-cutter wiki rebuild --root ./research-wiki
fluff-cutter wiki doctor --root ./research-wiki
fluff-cutter wiki remove paper-slug --root ./research-wiki --delete-pdf
```

The wiki layout looks like this:

```text
research-wiki/
├── fluff-cutter.yaml
├── raw/
│   └── pdfs/
└── wiki/
    ├── papers/
    ├── topics/
    ├── concepts/
    ├── queries/
    ├── index.md
    ├── overview.md
    └── log.md
```

By default, results are printed to the terminal and saved as a `.md` file next to the input PDF.
Model output streams live during analysis (provider-side streaming), so you see tokens immediately instead of waiting for full completion.

## Supported Providers

| Provider | Default Model | Env Variable |
|----------|---------------|--------------|
| OpenAI | gpt-5.2 | `OPENAI_API_KEY` |
| Anthropic | claude-sonnet-4-5 | `ANTHROPIC_API_KEY` |
| OpenRouter | anthropic/claude-sonnet-4-5 | `OPENROUTER_API_KEY` |

All providers support native PDF input -- no external dependencies like poppler needed.

## Configuration

Run `fluff-cutter init` for interactive setup, or set environment variables directly:

```bash
export OPENAI_API_KEY=sk-your-key-here
export FLUFF_CUTTER_PROVIDER=anthropic          # default provider
export FLUFF_CUTTER_ANTHROPIC_MODEL=claude-sonnet-4-5  # override model
```

Config is read in this order (highest priority first): CLI flags, env variables, `~/.fluff-cutter/config.yaml`, provider defaults.

## License

MIT
