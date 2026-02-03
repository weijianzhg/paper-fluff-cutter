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
from .pdf import get_pdf_filename, read_pdf_as_base64
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


@main.command()
def init():
    """Initialize configuration with API keys, provider, and model settings."""
    click.echo("Paper Fluff Cutter Configuration")
    click.echo("=" * 40)
    click.echo()

    config = {}

    # OpenAI API Key
    click.echo("Enter your API keys (press Enter to skip):")
    click.echo()

    openai_key = click.prompt(
        "OpenAI API Key",
        default="",
        hide_input=True,
        show_default=False,
    )
    if openai_key:
        config["openai_api_key"] = openai_key
        click.echo("  ✓ OpenAI API key saved")

    # Anthropic API Key
    anthropic_key = click.prompt(
        "Anthropic API Key",
        default="",
        hide_input=True,
        show_default=False,
    )
    if anthropic_key:
        config["anthropic_api_key"] = anthropic_key
        click.echo("  ✓ Anthropic API key saved")

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

    if len(available_providers) > 1:
        default_provider = click.prompt(
            "Default provider",
            type=click.Choice(available_providers),
            default="anthropic" if "anthropic" in available_providers else "openai",
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
        openai_model = click.prompt(
            "OpenAI model",
            default=openai_default,
            show_default=True,
        )
        if openai_model != openai_default:
            config["openai_model"] = openai_model
            click.echo(f"  ✓ OpenAI model set to: {openai_model}")
        else:
            click.echo(f"  Using default: {openai_default}")

    if "anthropic_api_key" in config:
        anthropic_default = AnthropicProvider(api_key="").default_model
        anthropic_model = click.prompt(
            "Anthropic model",
            default=anthropic_default,
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
def analyze(paper_path: str, provider: str | None, model: str | None, output: str | None):
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
        pdf_base64 = read_pdf_as_base64(paper_path)
        filename = get_pdf_filename(paper_path)
        click.echo("  PDF loaded successfully")
    except Exception as e:
        click.echo(f"Error reading PDF: {e}", err=True)
        sys.exit(1)

    # Analyze the paper
    click.echo("Analyzing paper (this may take a minute)...")
    try:
        result = analyze_paper(llm_provider, pdf_base64, filename)
    except Exception as e:
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
