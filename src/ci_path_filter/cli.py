"""Command-line interface (CLI) for CI/CD path-based filter tool."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from ci_path_filter.config import ConfigError, load_config
from ci_path_filter.evaluator import evaluate_all_filters
from ci_path_filter.exporter import format_env, write_env_file


def parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    """Configure and parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="ci-path-filter",
        description=(
            "Evaluate path-based filters against changed files in CI/CD pipelines "
            "and export results in dotenv (.env) format."
        ),
    )

    parser.add_argument(
        "-c",
        "--config",
        dest="config_path",
        default="filters.yaml",
        help="Path to filters YAML configuration file (default: filters.yaml).",
    )

    parser.add_argument(
        "-o",
        "--output",
        dest="output_path",
        default=None,
        help="Path to output .env file. If omitted, results are printed to stdout.",
    )

    parser.add_argument(
        "-f",
        "--files-file",
        dest="files_file",
        default=None,
        help="Path to a text file containing changed file paths (one per line).",
    )

    parser.add_argument(
        "changed_files",
        nargs="*",
        help="List of changed file paths separated by spaces.",
    )

    return parser.parse_args(args)


def collect_changed_files(args: argparse.Namespace) -> list[str]:
    """
    Gather changed files from positional arguments, --files-file, or stdin.

    Priority:
    1. Positional arguments: `ci-path-filter file1.kt file2.ts`
    2. File list flag: `--files-file changed_files.txt`
    3. Stdin (if piped): `git diff --name-only | ci-path-filter`
    """
    files: list[str] = []

    # 1. From CLI positional arguments
    if args.changed_files:
        files.extend(args.changed_files)

    # 2. From a file containing file paths
    if args.files_file:
        files_path = Path(args.files_file)
        if not files_path.is_file():
            raise FileNotFoundError(f"Files list file not found: {files_path.resolve()}")
        lines = files_path.read_text(encoding="utf-8").splitlines()
        files.extend(line.strip() for line in lines if line.strip())

    # 3. From stdin if data is piped and no files were provided via args
    if not files and not sys.stdin.isatty():
        stdin_lines = sys.stdin.read().splitlines()
        files.extend(line.strip() for line in stdin_lines if line.strip())

    return files


def main(args: Sequence[str] | None = None) -> int:
    """
    CLI main entrypoint.

    :param args: Command line arguments (defaults to sys.argv[1:])
    :return: Exit status code (0 for success, non-zero for error)
    """
    parsed_args = parse_args(args)

    try:
        # Load and validate YAML filters configuration
        filters_config = load_config(parsed_args.config_path)

        # Collect changed files from args, file, or stdin
        changed_files = collect_changed_files(parsed_args)

        # Evaluate all filters against changed files
        results = evaluate_all_filters(filters_config, changed_files)

        # Export results: write to .env file and/or stdout
        formatted_output = format_env(results)

        if parsed_args.output_path:
            write_env_file(results, parsed_args.output_path)

        # Print formatted output to stdout
        sys.stdout.write(formatted_output)

        return 0

    except ConfigError as exc:
        sys.stderr.write(f"Configuration Error: {exc}\n")
        return 1
    except FileNotFoundError as exc:
        sys.stderr.write(f"File Error: {exc}\n")
        return 1
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"Unexpected Error: {exc}\n")
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
