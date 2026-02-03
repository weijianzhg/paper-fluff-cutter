# Paper Fluff Cutter

[![PyPI version](https://badge.fury.io/py/fluff-cutter.svg)](https://pypi.org/project/fluff-cutter/)

A CLI tool that cuts through academic paper fluff to extract what actually matters.

Most research has close to zero value. This tool uses multimodal LLMs to analyze papers and answer the three questions every paper should be able to answer:

1. **Why should I care?** - What problem does this address and why does it matter?
2. **What's the actual innovation?** - What's the core idea in plain terms?
3. **Is the evidence convincing?** - Do the experiments actually support the claims?

## Installation

```bash
pip install fluff-cutter
```

Requires Python 3.10+.

### Development install

```bash
git clone https://github.com/weijianzhg/paper-fluff-cutter.git
cd paper-fluff-cutter
pip install -e .
```

## Configuration

### Option 1: Interactive setup (recommended)

```bash
fluff-cutter init
```

This will prompt you for your API keys, default provider, and model preferences, then save them to `~/.config/fluff-cutter/config.json`.

### Option 2: Environment variables

```bash
export OPENAI_API_KEY=sk-your-key-here
export ANTHROPIC_API_KEY=sk-ant-your-key-here
export FLUFF_CUTTER_PROVIDER=anthropic  # optional, default provider
export FLUFF_CUTTER_OPENAI_MODEL=gpt-5.2  # optional, override default model
export FLUFF_CUTTER_ANTHROPIC_MODEL=claude-sonnet-4-5  # optional, override default model
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
fluff-cutter analyze paper.pdf --provider openai --model gpt-5.2
fluff-cutter analyze paper.pdf --provider anthropic --model claude-sonnet-4-5
```

### Save output to file

```bash
fluff-cutter analyze paper.pdf --output analysis.md
```

### Long papers

For very long papers that exceed the model's token limit, you can limit the number of pages:

```bash
fluff-cutter analyze paper.pdf --max-pages 30
```

If you don't specify `--max-pages` and the paper exceeds the token limit, it will automatically truncate to the first 50 pages and retry.

## Supported Providers

| Provider | Default Model | Environment Variable |
|----------|---------------|---------------------|
| OpenAI | gpt-5.2 | `OPENAI_API_KEY` |
| Anthropic | claude-sonnet-4-5 | `ANTHROPIC_API_KEY` |

Both providers now support native PDF input - no external dependencies like poppler needed.

## Configuration Precedence

Configuration is loaded with the following precedence (highest to lowest):

1. Command-line arguments (`--provider`, `--model`)
2. Environment variables (`FLUFF_CUTTER_PROVIDER`, `FLUFF_CUTTER_OPENAI_MODEL`, `FLUFF_CUTTER_ANTHROPIC_MODEL`)
3. Config file (`~/.config/fluff-cutter/config.json`)
4. Provider defaults (gpt-5.2 for OpenAI, claude-sonnet-4-5 for Anthropic)

## License

MIT
