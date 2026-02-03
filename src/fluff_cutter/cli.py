"""Command-line interface for Paper Fluff Cutter."""

import sys

import click

from . import __version__
from .analyzer import analyze_paper
from .config import (
    get_api_key,
    get_config_path,
    get_default_model,
    get_default_provider,
    is_configured,
    load_config,
    save_config,
)
from .output import print_analysis, save_analysis
from .pdf import DEFAULT_MAX_PAGES, get_pdf_filename, read_pdf_as_base64
from .providers import AnthropicProvider, OpenAIProvider

PROVIDERS = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}


@click.group()
@click.version_option(version=__version__)
def main():
    """Paper Fluff Cutter - Extract the core value from academic papers."""
    pass


def _mask_key(key: str) -> str:
    """Mask an API key for display, showing only first 4 and last 4 chars."""
    if len(key) <= 12:
        return "*" * len(key)
    return f"{key[:4]}...{key[-4:]}"


@main.command()
def init():
    """Initialize configuration with API keys, provider, and model settings."""
    click.echo("Paper Fluff Cutter Configuration")
    click.echo("=" * 40)
    click.echo()

    # Load existing configuration (includes env vars)
    existing_config = load_config()
    existing_openai_key = existing_config.get("openai_api_key")
    existing_anthropic_key = existing_config.get("anthropic_api_key")

    # Show current status
    if existing_openai_key or existing_anthropic_key:
        click.echo("Current configuration:")
        if existing_openai_key:
            click.echo(f"  OpenAI API Key: {_mask_key(existing_openai_key)}")
        if existing_anthropic_key:
            click.echo(f"  Anthropic API Key: {_mask_key(existing_anthropic_key)}")
        click.echo()

    config = {}

    # OpenAI API Key
    click.echo("Enter your API keys (press Enter to keep existing or skip):")
    click.echo()

    openai_prompt = "OpenAI API Key"
    if existing_openai_key:
        openai_prompt += f" [{_mask_key(existing_openai_key)}]"

    openai_key = click.prompt(
        openai_prompt,
        default="",
        hide_input=True,
        show_default=False,
    )
    if openai_key:
        config["openai_api_key"] = openai_key
        click.echo("  ✓ OpenAI API key updated")
    elif existing_openai_key:
        config["openai_api_key"] = existing_openai_key
        click.echo("  ✓ OpenAI API key kept")

    # Anthropic API Key
    anthropic_prompt = "Anthropic API Key"
    if existing_anthropic_key:
        anthropic_prompt += f" [{_mask_key(existing_anthropic_key)}]"

    anthropic_key = click.prompt(
        anthropic_prompt,
        default="",
        hide_input=True,
        show_default=False,
    )
    if anthropic_key:
        config["anthropic_api_key"] = anthropic_key
        click.echo("  ✓ Anthropic API key updated")
    elif existing_anthropic_key:
        config["anthropic_api_key"] = existing_anthropic_key
        click.echo("  ✓ Anthropic API key kept")

    if not config:
        click.echo()
        click.echo("No API keys provided. Configuration not saved.")
        click.echo("You can set keys via environment variables instead:")
        click.echo("  export OPENAI_API_KEY=sk-...")
        click.echo("  export ANTHROPIC_API_KEY=sk-ant-...")
        return

    # Default provider
    click.echo()
    available_providers = []
    if "openai_api_key" in config:
        available_providers.append("openai")
    if "anthropic_api_key" in config:
        available_providers.append("anthropic")

    current_default = existing_config.get("default_provider")
    if len(available_providers) > 1:
        default_choice = current_default if current_default in available_providers else None
        if not default_choice:
            default_choice = "anthropic" if "anthropic" in available_providers else "openai"
        default_provider = click.prompt(
            "Default provider",
            type=click.Choice(available_providers),
            default=default_choice,
        )
    else:
        default_provider = available_providers[0]

    config["default_provider"] = default_provider

    # Model configuration
    click.echo()
    click.echo("Configure default models (press Enter for provider defaults):")
    click.echo()

    if "openai_api_key" in config:
        openai_default = OpenAIProvider(api_key="").default_model
        current_openai_model = existing_config.get("openai_model", openai_default)
        openai_model = click.prompt(
            "OpenAI model",
            default=current_openai_model,
            show_default=True,
        )
        if openai_model != openai_default:
            config["openai_model"] = openai_model
            click.echo(f"  ✓ OpenAI model set to: {openai_model}")
        else:
            click.echo(f"  Using default: {openai_default}")

    if "anthropic_api_key" in config:
        anthropic_default = AnthropicProvider(api_key="").default_model
        current_anthropic_model = existing_config.get("anthropic_model", anthropic_default)
        anthropic_model = click.prompt(
            "Anthropic model",
            default=current_anthropic_model,
            show_default=True,
        )
        if anthropic_model != anthropic_default:
            config["anthropic_model"] = anthropic_model
            click.echo(f"  ✓ Anthropic model set to: {anthropic_model}")
        else:
            click.echo(f"  Using default: {anthropic_default}")

    # Save configuration
    save_config(config)

    click.echo()
    click.echo(f"Configuration saved to: {get_config_path()}")
    click.echo(f"Default provider: {default_provider}")
    click.echo()
    click.echo("You're ready to analyze papers!")
    click.echo("  fluff-cutter analyze <paper.pdf>")


@main.command()
@click.argument("paper_path", type=click.Path(exists=True))
@click.option(
    "-p",
    "--provider",
    type=click.Choice(["openai", "anthropic"]),
    help="LLM provider to use",
)
@click.option(
    "-m",
    "--model",
    help="Specific model to use (overrides provider default)",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    help="Save output to file instead of printing",
)
@click.option(
    "--max-pages",
    type=int,
    default=None,
    help=f"Maximum pages to analyze (default: auto-truncate at {DEFAULT_MAX_PAGES} if needed)",
)
def analyze(
    paper_path: str,
    provider: str | None,
    model: str | None,
    output: str | None,
    max_pages: int | None,
):
    """Analyze an academic paper and extract its core value."""
    # Check configuration
    if not is_configured():
        click.echo("Error: No API keys configured.", err=True)
        click.echo("Run 'fluff-cutter init' to set up your API keys.", err=True)
        click.echo("Or set environment variables:", err=True)
        click.echo("  export OPENAI_API_KEY=sk-...", err=True)
        click.echo("  export ANTHROPIC_API_KEY=sk-ant-...", err=True)
        sys.exit(1)

    # Load config and determine provider
    config = load_config()
    provider_name = provider or get_default_provider(config)

    # Get API key for the selected provider
    api_key = get_api_key(provider_name, config)
    if not api_key:
        click.echo(f"Error: No API key configured for {provider_name}.", err=True)
        click.echo(f"Run 'fluff-cutter init' or set {provider_name.upper()}_API_KEY.", err=True)
        sys.exit(1)

    # Get model: CLI option > config file > provider default
    model_to_use = model or get_default_model(provider_name, config)

    # Create provider instance
    provider_class = PROVIDERS[provider_name]
    llm_provider = provider_class(api_key=api_key, model=model_to_use)

    click.echo(f"Analyzing paper: {paper_path}")
    click.echo(f"Using: {llm_provider.get_model_info()}")
    click.echo()

    # Read PDF
    click.echo("Reading PDF...")
    try:
        pdf_base64, total_pages, was_truncated = read_pdf_as_base64(paper_path, max_pages)
        filename = get_pdf_filename(paper_path)
        if was_truncated:
            click.echo(f"  PDF truncated: analyzing first {max_pages} of {total_pages} pages")
        else:
            click.echo(f"  PDF loaded successfully ({total_pages} pages)")
    except Exception as e:
        click.echo(f"Error reading PDF: {e}", err=True)
        sys.exit(1)

    # Analyze the paper (with auto-retry on token limit)
    click.echo("Analyzing paper (this may take a minute)...")
    try:
        result = analyze_paper(llm_provider, pdf_base64, filename)
    except Exception as e:
        error_msg = str(e)
        # Check if it's a token limit error and we haven't already truncated
        if "too long" in error_msg.lower() and "token" in error_msg.lower() and not was_truncated:
            click.echo()
            click.echo(
                f"  Paper exceeds token limit. Auto-truncating to {DEFAULT_MAX_PAGES} pages...",
                err=True,
            )
            try:
                pdf_base64, total_pages, _ = read_pdf_as_base64(paper_path, DEFAULT_MAX_PAGES)
                click.echo(f"  Retrying with first {DEFAULT_MAX_PAGES} of {total_pages} pages...")
                result = analyze_paper(llm_provider, pdf_base64, filename)
            except Exception as retry_error:
                click.echo(f"Error during analysis: {retry_error}", err=True)
                sys.exit(1)
        else:
            click.echo(f"Error during analysis: {e}", err=True)
            sys.exit(1)

    click.echo()

    # Output results
    if output:
        save_analysis(result["title"], result["analysis"], result["model_info"], output)
        click.echo(f"Analysis saved to: {output}")
    else:
        print_analysis(result["title"], result["analysis"], result["model_info"])


if __name__ == "__main__":
    main()
