# Paper Fluff Cutter

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

This will prompt you for your API keys, default provider, and model preferences, then save them to `~/.fluff-cutter/config.yaml`.

### Option 2: Environment variables

```bash
export OPENAI_API_KEY=sk-your-key-here
export ANTHROPIC_API_KEY=sk-ant-your-key-here
export OPENROUTER_API_KEY=sk-or-your-key-here
export FLUFF_CUTTER_PROVIDER=anthropic  # optional, default provider
export FLUFF_CUTTER_OPENAI_MODEL=gpt-5.2  # optional, override default model
export FLUFF_CUTTER_ANTHROPIC_MODEL=claude-sonnet-4-5  # optional, override default model
export FLUFF_CUTTER_OPENROUTER_MODEL=anthropic/claude-sonnet-4-5  # optional, override default model
```

## Usage

### Basic usage

```bash
fluff-cutter analyze paper.pdf
```

By default, the analysis is saved to a `.md` file with the same name as the input (e.g., `paper.pdf` → `paper.md`).

### Specify output file

```bash
fluff-cutter analyze paper.pdf --output analysis.md
```

### Print to stdout

```bash
fluff-cutter analyze paper.pdf --print
```

### Specify provider

```bash
fluff-cutter analyze paper.pdf --provider openai
fluff-cutter analyze paper.pdf --provider anthropic
fluff-cutter analyze paper.pdf --provider openrouter
```

### Specify model

```bash
fluff-cutter analyze paper.pdf --provider openai --model gpt-5.2
fluff-cutter analyze paper.pdf --provider anthropic --model claude-sonnet-4-5
fluff-cutter analyze paper.pdf --provider openrouter --model google/gemini-2.5-pro
```

### Long papers

For very long papers that exceed the model's token limit, you can limit the number of pages:

```bash
fluff-cutter analyze paper.pdf --max-pages 30
```

If you don't specify `--max-pages` and the paper exceeds the token limit, it will automatically truncate to the first 50 pages and retry.

## Supported Providers

| Provider | Default Model | Environment Variable | Notes |
|----------|---------------|---------------------|-------|
| OpenAI | gpt-5.2 | `OPENAI_API_KEY` | Native PDF support |
| Anthropic | claude-sonnet-4-5 | `ANTHROPIC_API_KEY` | Native PDF support |
| OpenRouter | anthropic/claude-sonnet-4-5 | `OPENROUTER_API_KEY` | Access to 300+ models |

All providers support PDF input natively - no external dependencies like poppler needed.

## Configuration Precedence

Configuration is loaded with the following precedence (highest to lowest):

1. Command-line arguments (`--provider`, `--model`)
2. Environment variables (`FLUFF_CUTTER_PROVIDER`, `FLUFF_CUTTER_*_MODEL`)
3. Config file (`~/.fluff-cutter/config.yaml`)
4. Provider defaults

## License

MIT
