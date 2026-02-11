# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-02-10

### Added

- URL download support: pass a PDF URL (e.g. `https://arxiv.org/pdf/2411.19870`) directly to `fluff-cutter analyze`
- Arxiv abstract URLs (`/abs/`) automatically converted to PDF URLs (`/pdf/`)
- Download caching: reused locally if the PDF was already downloaded
- Agent skill file (`.cursor/skills/fluff-cutter-usage/SKILL.md`) for AI agents
- `httpx` as explicit dependency

## [0.3.0] - 2026-02-04

### Added

- OpenRouter provider for access to 300+ models via a single API
- Universal PDF support through OpenRouter - works with any model
- `OPENROUTER_API_KEY` and `FLUFF_CUTTER_OPENROUTER_MODEL` environment variables
- OpenRouter configuration in `fluff-cutter init`

### Technical

- Uses `httpx` (transitive dependency) for OpenRouter API calls

## [0.2.0] - 2026-01-15

### Added

- `--max-pages` option for handling long papers
- Auto-truncation to 50 pages when token limit exceeded
- Config file migration from old location
- Interactive `init` command preserves existing API keys

### Changed

- Default Anthropic model updated to `claude-sonnet-4-5`
- Default output format changed to Markdown file (same name as input)
- Standardized config and CLI patterns

## [0.1.0] - 2026-01-10

### Added

- Initial release
- OpenAI and Anthropic provider support with native PDF input
- CLI with `init` and `analyze` commands
- Configuration via environment variables or config file
- Markdown output format
