# Paper Fluff Cutter

A CLI tool that cuts through academic paper fluff to extract what actually matters.

Most research has close to zero value. This tool uses multimodal LLMs to analyze papers and answer the three questions every paper should be able to answer:

1. **Why should I care?** - What problem does this address and why does it matter?
2. **What's the actual innovation?** - What's the core idea in plain terms?
3. **Is the evidence convincing?** - Do the experiments actually support the claims?

## Installation

### Prerequisites

- Python 3.10+

### Install the tool

```bash
pip install -e .
```

## Configuration

### Option 1: Interactive setup (recommended)

```bash
fluff-cutter init
```

This will prompt you for your API keys and save them to `~/.config/fluff-cutter/config.json`.

### Option 2: Environment variables

```bash
export OPENAI_API_KEY=sk-your-key-here
export ANTHROPIC_API_KEY=sk-ant-your-key-here
export FLUFF_CUTTER_PROVIDER=anthropic  # optional, default provider
```

## Usage

### Basic usage

```bash
fluff-cutter analyze paper.pdf
```

### Specify provider

```bash
fluff-cutter analyze paper.pdf --provider openai
fluff-cutter analyze paper.pdf --provider anthropic
```

### Specify model

```bash
fluff-cutter analyze paper.pdf --provider openai --model gpt-4o
fluff-cutter analyze paper.pdf --provider anthropic --model claude-sonnet-4-20250514
```

### Save output to file

```bash
fluff-cutter analyze paper.pdf --output analysis.md
```

## Supported Providers

| Provider | Default Model | Environment Variable |
|----------|---------------|---------------------|
| OpenAI | gpt-4o | `OPENAI_API_KEY` |
| Anthropic | claude-sonnet-4-20250514 | `ANTHROPIC_API_KEY` |

Both providers now support native PDF input - no external dependencies like poppler needed.

## Configuration Precedence

Configuration is loaded with the following precedence (highest to lowest):

1. Command-line arguments (`--provider`, `--model`)
2. Environment variables
3. Config file (`~/.config/fluff-cutter/config.json`)

## License

MIT
