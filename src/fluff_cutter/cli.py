"""Command-line interface for Paper Fluff Cutter."""

import argparse
import getpass
import sys
from pathlib import Path

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
from .providers import AnthropicProvider, OpenAIProvider, OpenRouterProvider

PROVIDERS = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "openrouter": OpenRouterProvider,
}


def _mask_key(key: str) -> str:
    """Mask an API key for display, showing only first 4 and last 4 chars."""
    if len(key) <= 12:
        return "*" * len(key)
    return f"{key[:4]}...{key[-4:]}"


def prompt_with_default(prompt: str, default: str = "", password: bool = False) -> str:
    """
    Prompt user for input with an optional default value.

    Args:
        prompt: The prompt to display.
        default: Default value if user presses enter.
        password: If True, mask input using getpass.

    Returns:
        User input or default value.
    """
    if default and not password:
        full_prompt = f"{prompt} [{default}]: "
    elif default and password:
        full_prompt = f"{prompt} [{_mask_key(default)}]: "
    else:
        full_prompt = f"{prompt}: "

    if password:
        value = getpass.getpass(full_prompt)
    else:
        value = input(full_prompt)

    return value.strip() if value.strip() else default


def cmd_init(args):
    """Handle the init subcommand."""
    print("Paper Fluff Cutter Configuration")
    print("=" * 40)
    print()

    # Load existing configuration (includes env vars)
    existing_config = load_config()
    existing_openai_key = existing_config.get("openai_api_key")
    existing_anthropic_key = existing_config.get("anthropic_api_key")
    existing_openrouter_key = existing_config.get("openrouter_api_key")

    # Show current status
    if existing_openai_key or existing_anthropic_key or existing_openrouter_key:
        print("Current configuration:")
        if existing_openai_key:
            print(f"  OpenAI API Key: {_mask_key(existing_openai_key)}")
        if existing_anthropic_key:
            print(f"  Anthropic API Key: {_mask_key(existing_anthropic_key)}")
        if existing_openrouter_key:
            print(f"  OpenRouter API Key: {_mask_key(existing_openrouter_key)}")
        print()

    config = {}

    # OpenAI API Key
    print("Enter your API keys (press Enter to keep existing or skip):")
    print()

    openai_key = prompt_with_default(
        "OpenAI API Key",
        default=existing_openai_key or "",
        password=True,
    )
    if openai_key:
        config["openai_api_key"] = openai_key
        if openai_key != existing_openai_key:
            print("  OpenAI API key updated")
        else:
            print("  OpenAI API key kept")

    # Anthropic API Key
    anthropic_key = prompt_with_default(
        "Anthropic API Key",
        default=existing_anthropic_key or "",
        password=True,
    )
    if anthropic_key:
        config["anthropic_api_key"] = anthropic_key
        if anthropic_key != existing_anthropic_key:
            print("  Anthropic API key updated")
        else:
            print("  Anthropic API key kept")

    # OpenRouter API Key
    openrouter_key = prompt_with_default(
        "OpenRouter API Key",
        default=existing_openrouter_key or "",
        password=True,
    )
    if openrouter_key:
        config["openrouter_api_key"] = openrouter_key
        if openrouter_key != existing_openrouter_key:
            print("  OpenRouter API key updated")
        else:
            print("  OpenRouter API key kept")

    if not config:
        print()
        print("No API keys provided. Configuration not saved.")
        print("You can set keys via environment variables instead:")
        print("  export OPENAI_API_KEY=sk-...")
        print("  export ANTHROPIC_API_KEY=sk-ant-...")
        print("  export OPENROUTER_API_KEY=sk-or-...")
        return

    # Default provider
    print()
    available_providers = []
    if "openai_api_key" in config:
        available_providers.append("openai")
    if "anthropic_api_key" in config:
        available_providers.append("anthropic")
    if "openrouter_api_key" in config:
        available_providers.append("openrouter")

    current_default = existing_config.get("default_provider")
    if len(available_providers) > 1:
        default_choice = current_default if current_default in available_providers else None
        if not default_choice:
            default_choice = "anthropic" if "anthropic" in available_providers else "openai"

        print(f"Available providers: {', '.join(available_providers)}")
        while True:
            default_provider = prompt_with_default("Default provider", default=default_choice)
            if default_provider in available_providers:
                break
            print(f"Please choose from: {', '.join(available_providers)}")
    else:
        default_provider = available_providers[0]

    config["default_provider"] = default_provider

    # Model configuration
    print()
    print("Configure default models (press Enter for provider defaults):")
    print()

    if "openai_api_key" in config:
        openai_default = OpenAIProvider(api_key="").default_model
        current_openai_model = existing_config.get("openai_model", openai_default)
        openai_model = prompt_with_default("OpenAI model", default=current_openai_model)
        if openai_model != openai_default:
            config["openai_model"] = openai_model
            print(f"  OpenAI model set to: {openai_model}")
        else:
            print(f"  Using default: {openai_default}")

    if "anthropic_api_key" in config:
        anthropic_default = AnthropicProvider(api_key="").default_model
        current_anthropic_model = existing_config.get("anthropic_model", anthropic_default)
        anthropic_model = prompt_with_default("Anthropic model", default=current_anthropic_model)
        if anthropic_model != anthropic_default:
            config["anthropic_model"] = anthropic_model
            print(f"  Anthropic model set to: {anthropic_model}")
        else:
            print(f"  Using default: {anthropic_default}")

    if "openrouter_api_key" in config:
        openrouter_default = OpenRouterProvider(api_key="").default_model
        current_openrouter_model = existing_config.get("openrouter_model", openrouter_default)
        openrouter_model = prompt_with_default("OpenRouter model", default=current_openrouter_model)
        if openrouter_model != openrouter_default:
            config["openrouter_model"] = openrouter_model
            print(f"  OpenRouter model set to: {openrouter_model}")
        else:
            print(f"  Using default: {openrouter_default}")

    # Save configuration
    save_config(config)

    print()
    print(f"Configuration saved to: {get_config_path()}")
    print(f"Default provider: {default_provider}")
    print()
    print("You're ready to analyze papers!")
    print("  fluff-cutter analyze <paper.pdf>")


def cmd_analyze(args):
    """Handle the analyze subcommand."""
    paper_path = args.paper_path
    provider = args.provider
    model = args.model
    output = args.output
    print_output = args.print_output
    max_pages = args.max_pages

    # Check configuration
    if not is_configured():
        print("Error: No API keys configured.", file=sys.stderr)
        print("Run 'fluff-cutter init' to set up your API keys.", file=sys.stderr)
        print("Or set environment variables:", file=sys.stderr)
        print("  export OPENAI_API_KEY=sk-...", file=sys.stderr)
        print("  export ANTHROPIC_API_KEY=sk-ant-...", file=sys.stderr)
        sys.exit(1)

    # Validate paper path exists
    if not Path(paper_path).exists():
        print(f"Error: File not found: {paper_path}", file=sys.stderr)
        sys.exit(1)

    # Load config and determine provider
    config = load_config()
    provider_name = provider or get_default_provider(config)

    # Get API key for the selected provider
    api_key = get_api_key(provider_name, config)
    if not api_key:
        print(f"Error: No API key configured for {provider_name}.", file=sys.stderr)
        print(f"Run 'fluff-cutter init' or set {provider_name.upper()}_API_KEY.", file=sys.stderr)
        sys.exit(1)

    # Get model: CLI option > config file > provider default
    model_to_use = model or get_default_model(provider_name, config)

    # Create provider instance
    provider_class = PROVIDERS[provider_name]
    llm_provider = provider_class(api_key=api_key, model=model_to_use)

    print(f"Analyzing paper: {paper_path}")
    print(f"Using: {llm_provider.get_model_info()}")
    print()

    # Read PDF
    print("Reading PDF...")
    try:
        pdf_base64, total_pages, was_truncated = read_pdf_as_base64(paper_path, max_pages)
        filename = get_pdf_filename(paper_path)
        if was_truncated:
            print(f"  PDF truncated: analyzing first {max_pages} of {total_pages} pages")
        else:
            print(f"  PDF loaded successfully ({total_pages} pages)")
    except Exception as e:
        print(f"Error reading PDF: {e}", file=sys.stderr)
        sys.exit(1)

    # Analyze the paper (with auto-retry on token limit)
    print("Analyzing paper (this may take a minute)...")
    try:
        result = analyze_paper(llm_provider, pdf_base64, filename)
    except Exception as e:
        error_msg = str(e)
        # Check if it's a token limit error and we haven't already truncated
        if "too long" in error_msg.lower() and "token" in error_msg.lower() and not was_truncated:
            print()
            print(
                f"  Paper exceeds token limit. Auto-truncating to {DEFAULT_MAX_PAGES} pages...",
                file=sys.stderr,
            )
            try:
                pdf_base64, total_pages, _ = read_pdf_as_base64(paper_path, DEFAULT_MAX_PAGES)
                print(f"  Retrying with first {DEFAULT_MAX_PAGES} of {total_pages} pages...")
                result = analyze_paper(llm_provider, pdf_base64, filename)
            except Exception as retry_error:
                print(f"Error during analysis: {retry_error}", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"Error during analysis: {e}", file=sys.stderr)
            sys.exit(1)

    print()

    # Output results
    if print_output:
        print_analysis(result["title"], result["analysis"], result["model_info"])
    else:
        # Default output path: same name as input with .md extension
        output_path = output or str(Path(paper_path).with_suffix(".md"))
        save_analysis(result["title"], result["analysis"], result["model_info"], output_path)
        print(f"Analysis saved to: {output_path}")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="fluff-cutter",
        description="Paper Fluff Cutter - Extract the core value from academic papers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  fluff-cutter init
  fluff-cutter analyze paper.pdf
  fluff-cutter analyze paper.pdf --provider openai
  fluff-cutter analyze paper.pdf --output summary.md
  fluff-cutter analyze paper.pdf --print
        """,
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", metavar="command")

    # Init subcommand
    init_parser = subparsers.add_parser(
        "init", help="Configure API keys and default settings interactively"
    )
    init_parser.set_defaults(func=cmd_init)

    # Analyze subcommand
    analyze_parser = subparsers.add_parser(
        "analyze", help="Analyze an academic paper and extract its core value"
    )
    analyze_parser.add_argument("paper_path", help="Path to PDF file to analyze")
    analyze_parser.add_argument(
        "-p",
        "--provider",
        choices=["openai", "anthropic", "openrouter"],
        help="LLM provider to use (overrides config)",
    )
    analyze_parser.add_argument(
        "-m",
        "--model",
        help="Specific model to use (overrides provider default)",
    )
    analyze_parser.add_argument(
        "-o",
        "--output",
        help="Output file path (default: same name as input with .md extension)",
    )
    analyze_parser.add_argument(
        "--print",
        dest="print_output",
        action="store_true",
        help="Print to stdout instead of saving to file",
    )
    analyze_parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help=f"Maximum pages to analyze (default: auto-truncate at {DEFAULT_MAX_PAGES} if needed)",
    )
    analyze_parser.set_defaults(func=cmd_analyze)

    # Parse arguments
    args = parser.parse_args()

    # Execute the appropriate command
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
