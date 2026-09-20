"""Configuration loader and schema validator for filters.yaml."""

from pathlib import Path
from typing import Any

import yaml

from ci_path_filter.matcher import is_exclusion, strip_exclusion_prefix


class ConfigError(Exception):
    """Raised when configuration file is missing, invalid YAML, or has incorrect schema."""


def parse_patterns(raw_patterns: Any, filter_name: str) -> tuple[list[str], list[str]]:
    """
    Parse pattern list into separate inclusions and exclusions lists.

    :param raw_patterns: List of pattern strings (or a single pattern string)
    :param filter_name: Name of the filter for error reporting
    :return: Tuple of (inclusions, exclusions)
    """
    if isinstance(raw_patterns, str):
        patterns = [raw_patterns]
    elif isinstance(raw_patterns, list):
        patterns = raw_patterns
    else:
        raise ConfigError(
            f"Filter '{filter_name}' patterns must be a list of strings or a single string, "
            f"got {type(raw_patterns).__name__}."
        )

    inclusions: list[str] = []
    exclusions: list[str] = []

    for item in patterns:
        if not isinstance(item, str):
            raise ConfigError(
                f"Pattern inside filter '{filter_name}' must be a string, got {type(item).__name__}: {item}"
            )
        clean = item.strip()
        if not clean:
            continue

        if is_exclusion(clean):
            exclusions.append(strip_exclusion_prefix(clean))
        else:
            inclusions.append(clean)

    return inclusions, exclusions


def load_config(config_path: str | Path) -> dict[str, tuple[list[str], list[str]]]:
    """
    Load and validate YAML filters configuration file.

    Expected YAML structure:
    -----------------------
    filters:
      backend:
        - "app/src/**/*.kt"
        - "!app/src/test/**"
      frontend:
        - "web/**/*.ts"

    :param config_path: Path to the YAML configuration file
    :return: Dictionary mapping filter name -> (inclusions_list, exclusions_list)
    """
    path = Path(config_path)
    if not path.is_file():
        raise ConfigError(f"Configuration file not found: {path.resolve()}")

    try:
        content = path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise ConfigError(f"Failed to parse YAML file '{path.name}': {exc}") from exc
    except Exception as exc:
        raise ConfigError(f"Could not read configuration file '{path.name}': {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError(
            f"Invalid configuration format in '{path.name}': root element must be a YAML mapping/dictionary."
        )

    if "filters" not in data:
        raise ConfigError(
            f"Missing required top-level key 'filters' in configuration file '{path.name}'."
        )

    raw_filters = data["filters"]
    if not isinstance(raw_filters, dict):
        raise ConfigError(
            f"'filters' must be a dictionary mapping filter names to pattern lists, "
            f"got {type(raw_filters).__name__}."
        )

    parsed_filters: dict[str, tuple[list[str], list[str]]] = {}
    for name, pattern_def in raw_filters.items():
        if not isinstance(name, str) or not name.strip():
            raise ConfigError(f"Filter name must be a non-empty string, got {name!r}.")

        filter_name = name.strip()
        inclusions, exclusions = parse_patterns(pattern_def, filter_name)
        parsed_filters[filter_name] = (inclusions, exclusions)

    return parsed_filters
