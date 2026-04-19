"""Command-line interface for Paper Fluff Cutter."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from . import __version__
from .analyzer import parse_analysis_response, stream_analysis_chunks
from .config import (
    get_api_key,
    get_config_path,
    get_default_model,
    get_default_provider,
    is_configured,
    load_config,
    save_config,
)
from .download import download_pdf, is_url
from .output import save_analysis
from .pdf import DEFAULT_MAX_PAGES, get_pdf_filename, read_pdf_as_base64
from .providers import AnthropicProvider, OpenAIProvider, OpenRouterProvider
from .wiki import (
    add_paper_to_wiki,
    doctor_wiki,
    find_wiki_root,
    init_wiki,
    list_papers,
    query_wiki,
    rebuild_wiki,
    remove_paper_from_wiki,
    validate_wiki_root,
    wiki_status,
)

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
    """Prompt user for input with an optional default value."""
    if default and not password:
        full_prompt = f"{prompt} [{default}]: "
    elif default and password:
        full_prompt = f"{prompt} [{_mask_key(default)}]: "
    else:
        full_prompt = f"{prompt}: "

    value = getpass.getpass(full_prompt) if password else input(full_prompt)
    return value.strip() if value.strip() else default


def cmd_init(args):
    """Handle the init subcommand."""
    print("Paper Fluff Cutter Configuration")
    print("=" * 40)
    print()

    existing_config = load_config()
    existing_openai_key = existing_config.get("openai_api_key")
    existing_anthropic_key = existing_config.get("anthropic_api_key")
    existing_openrouter_key = existing_config.get("openrouter_api_key")

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

    print("Enter your API keys (press Enter to keep existing or skip):")
    print()

    openai_key = prompt_with_default(
        "OpenAI API Key",
        default=existing_openai_key or "",
        password=True,
    )
    if openai_key:
        config["openai_api_key"] = openai_key
        print(
            "  OpenAI API key updated"
            if openai_key != existing_openai_key
            else "  OpenAI API key kept"
        )

    anthropic_key = prompt_with_default(
        "Anthropic API Key", default=existing_anthropic_key or "", password=True
    )
    if anthropic_key:
        config["anthropic_api_key"] = anthropic_key
        print(
            "  Anthropic API key updated"
            if anthropic_key != existing_anthropic_key
            else "  Anthropic API key kept"
        )

    openrouter_key = prompt_with_default(
        "OpenRouter API Key", default=existing_openrouter_key or "", password=True
    )
    if openrouter_key:
        config["openrouter_api_key"] = openrouter_key
        print(
            "  OpenRouter API key updated"
            if openrouter_key != existing_openrouter_key
            else "  OpenRouter API key kept"
        )

    if not config:
        print()
        print("No API keys provided. Configuration not saved.")
        print("You can set keys via environment variables instead:")
        print("  export OPENAI_API_KEY=***")
        print("  export ANTHROPIC_API_KEY=***")
        print("  export OPENROUTER_API_KEY=***")
        return

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

    save_config(config)

    print()
    print(f"Configuration saved to: {get_config_path()}")
    print(f"Default provider: {default_provider}")
    print()
    print("You're ready to analyze papers!")
    print("  fluff-cutter analyze <paper.pdf>")


def _create_provider(provider: str | None, model: str | None):
    if not is_configured():
        print("Error: No API keys configured.", file=sys.stderr)
        print("Run 'fluff-cutter init' to set up your API keys.", file=sys.stderr)
        print("Or set environment variables:", file=sys.stderr)
        print("  export OPENAI_API_KEY=***", file=sys.stderr)
        print("  export ANTHROPIC_API_KEY=***", file=sys.stderr)
        print("  export OPENROUTER_API_KEY=***", file=sys.stderr)
        sys.exit(1)

    config = load_config()
    provider_name = provider or get_default_provider(config)
    api_key = get_api_key(provider_name, config)
    if not api_key:
        print(f"Error: No API key configured for {provider_name}.", file=sys.stderr)
        print(f"Run 'fluff-cutter init' or set {provider_name.upper()}_API_KEY.", file=sys.stderr)
        sys.exit(1)

    model_to_use = model or get_default_model(provider_name, config)
    provider_class = PROVIDERS[provider_name]
    return provider_class(api_key=api_key, model=model_to_use)


def _resolve_local_paper_path(paper_path: str, download_dir: Path | None = None) -> str:
    if is_url(paper_path):
        print(f"Downloading paper from: {paper_path}")
        try:
            local_path = str(download_pdf(paper_path, output_dir=download_dir))
        except Exception as exc:
            print(f"Error downloading paper: {exc}", file=sys.stderr)
            sys.exit(1)
        print(f"  Saved to: {local_path}")
        return local_path
    return paper_path


def analyze_source(
    paper_path: str,
    provider: str | None = None,
    model: str | None = None,
    max_pages: int | None = None,
    download_dir: Path | None = None,
) -> tuple[dict[str, str], str]:
    local_paper_path = _resolve_local_paper_path(paper_path, download_dir=download_dir)
    if not Path(local_paper_path).exists():
        print(f"Error: File not found: {local_paper_path}", file=sys.stderr)
        sys.exit(1)

    llm_provider = _create_provider(provider, model)

    print(f"Analyzing paper: {local_paper_path}")
    print(f"Using: {llm_provider.get_model_info()}")
    print()
    print("Reading PDF...")
    try:
        pdf_base64, total_pages, was_truncated = read_pdf_as_base64(local_paper_path, max_pages)
        filename = get_pdf_filename(local_paper_path)
        if was_truncated:
            print(f"  PDF truncated: analyzing first {max_pages} of {total_pages} pages")
        else:
            print(f"  PDF loaded successfully ({total_pages} pages)")
    except Exception as exc:
        print(f"Error reading PDF: {exc}", file=sys.stderr)
        sys.exit(1)

    print("Analyzing paper (streaming output)...")
    try:
        raw_response = ""
        for chunk in stream_analysis_chunks(llm_provider, pdf_base64, filename):
            raw_response += chunk
            print(chunk, end="", flush=True)
        print()
        result = parse_analysis_response(raw_response, llm_provider)
    except Exception as exc:
        error_msg = str(exc)
        if "too long" in error_msg.lower() and "token" in error_msg.lower() and not was_truncated:
            print()
            print(
                f"  Paper exceeds token limit. Auto-truncating to {DEFAULT_MAX_PAGES} pages...",
                file=sys.stderr,
            )
            try:
                pdf_base64, total_pages, _ = read_pdf_as_base64(local_paper_path, DEFAULT_MAX_PAGES)
                print(f"  Retrying with first {DEFAULT_MAX_PAGES} of {total_pages} pages...")
                raw_response = ""
                for chunk in stream_analysis_chunks(llm_provider, pdf_base64, filename):
                    raw_response += chunk
                    print(chunk, end="", flush=True)
                print()
                result = parse_analysis_response(raw_response, llm_provider)
            except Exception as retry_error:
                print(f"Error during analysis: {retry_error}", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"Error during analysis: {exc}", file=sys.stderr)
            sys.exit(1)

    print()
    return result, local_paper_path


def cmd_analyze(args):
    """Handle the analyze subcommand."""
    result, local_paper_path = analyze_source(
        args.paper_path,
        provider=args.provider,
        model=args.model,
        max_pages=args.max_pages,
    )
    if not args.print_output:
        output_path = args.output or str(Path(local_paper_path).with_suffix(".md"))
        save_analysis(result["title"], result["analysis"], result["model_info"], output_path)
        print(f"Analysis saved to: {output_path}")


def _resolve_wiki_root(root_arg: str | None) -> Path:
    try:
        if root_arg:
            return validate_wiki_root(Path(root_arg).expanduser().resolve())
        return validate_wiki_root(find_wiki_root())
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        print("Run 'fluff-cutter wiki init <path>' first.", file=sys.stderr)
        sys.exit(1)


def cmd_wiki_init(args):
    root = init_wiki(args.path)
    print(f"Initialized wiki at: {root}")


def cmd_wiki_add(args):
    root = _resolve_wiki_root(args.root)
    result, local_paper_path = analyze_source(
        args.paper_path,
        provider=args.provider,
        model=args.model,
        max_pages=args.max_pages,
        download_dir=root / "raw" / "pdfs",
    )
    page_path = add_paper_to_wiki(
        root,
        source_ref=args.paper_path,
        pdf_path=local_paper_path,
        title=result["title"],
        analysis=result["analysis"],
        model_info=result["model_info"],
    )
    print(f"Wiki page saved to: {page_path}")


def cmd_wiki_remove(args):
    root = _resolve_wiki_root(args.root)
    removed = remove_paper_from_wiki(root, args.paper, delete_pdf=args.delete_pdf)
    print(f"Removed paper: {removed['slug']}")
    print(f"  page_deleted: {removed['page_deleted']}")
    print(f"  pdf_deleted: {removed['pdf_deleted']}")


def cmd_wiki_query(args):
    root = _resolve_wiki_root(args.root)
    result = query_wiki(root, args.question, top_k=args.top_k)
    print(f"question: {result['question']}")
    if not result["matches"]:
        print("No matching wiki pages found.")
        return
    for match in result["matches"]:
        print(f"- {match['title']} ({match['score']})")
        print(f"  {match['snippet']}")


def cmd_wiki_rebuild(args):
    root = _resolve_wiki_root(args.root)
    result = rebuild_wiki(root)
    print(f"Rebuilt wiki artifacts for {result['paper_count']} paper(s).")


def cmd_wiki_doctor(args):
    root = _resolve_wiki_root(args.root)
    report = doctor_wiki(root)
    if report["ok"]:
        print("Wiki looks healthy.")
        return
    print("Wiki issues:")
    for issue in report["issues"]:
        print(f"- {issue}")
    sys.exit(1)


def cmd_wiki_ls(args):
    root = _resolve_wiki_root(args.root)
    papers = list_papers(root)
    if not papers:
        print("No papers in wiki yet.")
        return
    for paper in papers:
        print(f"{paper['slug']} | {paper['title']} | {paper['added']}")


def cmd_wiki_status(args):
    root = _resolve_wiki_root(args.root)
    status = wiki_status(root)
    for key, value in status.items():
        print(f"{key}: {value}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fluff-cutter",
        description="Paper Fluff Cutter - Extract the core value from academic papers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  fluff-cutter init
  fluff-cutter analyze paper.pdf
  fluff-cutter analyze https://arxiv.org/pdf/2411.19870
  fluff-cutter wiki init ./research-wiki
  fluff-cutter wiki add https://arxiv.org/pdf/2411.19870 --root ./research-wiki
  fluff-cutter wiki query "agents planning" --root ./research-wiki
        """,
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", metavar="command")

    init_parser = subparsers.add_parser(
        "init", help="Configure API keys and default settings interactively"
    )
    init_parser.set_defaults(func=cmd_init)

    analyze_parser = subparsers.add_parser(
        "analyze", help="Analyze an academic paper and extract its core value"
    )
    analyze_parser.add_argument("paper_path", help="Path to PDF file or URL to analyze")
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

    wiki_parser = subparsers.add_parser("wiki", help="Manage a persistent paper wiki")
    wiki_subparsers = wiki_parser.add_subparsers(dest="wiki_command", metavar="wiki-command")

    wiki_init_parser = wiki_subparsers.add_parser("init", help="Initialize a wiki project")
    wiki_init_parser.add_argument("path", help="Directory to initialize")
    wiki_init_parser.set_defaults(func=cmd_wiki_init)

    wiki_add_parser = wiki_subparsers.add_parser(
        "add",
        help="Analyze a paper and add it to the wiki",
    )
    wiki_add_parser.add_argument("paper_path", help="Path or URL to a paper PDF")
    wiki_add_parser.add_argument(
        "--root",
        help="Wiki root directory (defaults to nearest fluff-cutter.yaml)",
    )
    wiki_add_parser.add_argument(
        "-p", "--provider", choices=["openai", "anthropic", "openrouter"], help="LLM provider"
    )
    wiki_add_parser.add_argument("-m", "--model", help="Specific model override")
    wiki_add_parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum pages to analyze",
    )
    wiki_add_parser.set_defaults(func=cmd_wiki_add)

    wiki_remove_parser = wiki_subparsers.add_parser("remove", help="Remove a paper from the wiki")
    wiki_remove_parser.add_argument("paper", help="Paper slug, title, or markdown path")
    wiki_remove_parser.add_argument("--root", help="Wiki root directory")
    wiki_remove_parser.add_argument(
        "--delete-pdf",
        action="store_true",
        help="Also delete the stored PDF",
    )
    wiki_remove_parser.set_defaults(func=cmd_wiki_remove)

    wiki_query_parser = wiki_subparsers.add_parser("query", help="Query the wiki")
    wiki_query_parser.add_argument("question", help="Question or keyword query")
    wiki_query_parser.add_argument("--root", help="Wiki root directory")
    wiki_query_parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of matches to return",
    )
    wiki_query_parser.set_defaults(func=cmd_wiki_query)

    wiki_rebuild_parser = wiki_subparsers.add_parser(
        "rebuild",
        help="Rebuild derived wiki artifacts",
    )
    wiki_rebuild_parser.add_argument("--root", help="Wiki root directory")
    wiki_rebuild_parser.set_defaults(func=cmd_wiki_rebuild)

    wiki_doctor_parser = wiki_subparsers.add_parser("doctor", help="Check wiki health")
    wiki_doctor_parser.add_argument("--root", help="Wiki root directory")
    wiki_doctor_parser.set_defaults(func=cmd_wiki_doctor)

    wiki_ls_parser = wiki_subparsers.add_parser("ls", help="List papers in the wiki")
    wiki_ls_parser.add_argument("--root", help="Wiki root directory")
    wiki_ls_parser.set_defaults(func=cmd_wiki_ls)

    wiki_status_parser = wiki_subparsers.add_parser("status", help="Show wiki status summary")
    wiki_status_parser.add_argument("--root", help="Wiki root directory")
    wiki_status_parser.set_defaults(func=cmd_wiki_status)

    return parser


def main():
    """Main entry point for the CLI."""
    parser = build_parser()
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
