"""Output formatting for paper analysis."""

from datetime import datetime


def format_analysis(title: str, analysis: str, model_info: str) -> str:
    """
    Format the analysis as clean markdown.

    Args:
        title: The paper title.
        analysis: The raw analysis from the LLM.
        model_info: Information about the model used.

    Returns:
        Formatted markdown string.
    """
    date_str = datetime.now().strftime("%Y-%m-%d")

    output = f"""# Paper Analysis: {title}

{analysis}

---
*Analyzed with {model_info} on {date_str}*
"""
    return output


def print_analysis(title: str, analysis: str, model_info: str) -> None:
    """
    Print the formatted analysis to stdout.

    Args:
        title: The paper title.
        analysis: The raw analysis from the LLM.
        model_info: Information about the model used.
    """
    print(format_analysis(title, analysis, model_info))


def save_analysis(
    title: str, analysis: str, model_info: str, output_path: str
) -> None:
    """
    Save the formatted analysis to a file.

    Args:
        title: The paper title.
        analysis: The raw analysis from the LLM.
        model_info: Information about the model used.
        output_path: Path to save the output file.
    """
    content = format_analysis(title, analysis, model_info)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
