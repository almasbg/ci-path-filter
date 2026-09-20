"""Exporter module to format and write filter results into .env files."""

from collections.abc import Mapping
from pathlib import Path


def format_env(results: Mapping[str, bool]) -> str:
    """
    Format evaluation results into a standard dotenv string.

    - Booleans are formatted in lowercase: `true` or `false`.
    - Keys are sorted alphabetically for deterministic, reproducible output.
    - Each line ends with a newline.
    """
    lines = [f"{key}={'true' if value else 'false'}" for key, value in sorted(results.items())]
    return "\n".join(lines) + ("\n" if lines else "")


def write_env_file(results: Mapping[str, bool], output_path: str | Path) -> Path:
    """
    Write evaluation results into a .env file on disk.

    - Ensures any missing parent directories are created.
    - Uses UTF-8 encoding.

    :param results: Mapping of filter names to boolean match results
    :param output_path: File path where .env will be saved
    :return: The resolved Path object of the written file
    """
    path = Path(output_path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    content = format_env(results)
    path.write_text(content, encoding="utf-8")
    return path
