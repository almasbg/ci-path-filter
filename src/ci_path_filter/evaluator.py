"""Filter evaluation logic based on inclusion and exclusion glob patterns."""

from collections.abc import Sequence

from ci_path_filter.matcher import match_glob


def evaluate_filter(
    inclusions: Sequence[str],
    exclusions: Sequence[str],
    changed_files: Sequence[str],
) -> bool:
    """
    Evaluate if a filter matches the list of changed files.

    A filter is considered matched (True) if:
    - ANY changed file matches at least one inclusion pattern
    - AND that specific file does NOT match any exclusion pattern
    """
    for file_path in changed_files:
        matches_inclusion = any(match_glob(pat, file_path) for pat in inclusions)
        matches_exclusion = any(match_glob(pat, file_path) for pat in exclusions)

        # Must match at least one inclusion AND must NOT match any exclusion
        if matches_inclusion and not matches_exclusion:
            return True

    return False


def evaluate_all_filters(
    filters_config: dict[str, tuple[list[str], list[str]]],
    changed_files: Sequence[str],
) -> dict[str, bool]:
    """
    Evaluate all configured filters against changed files.

    :param filters_config: Dict mapping filter name to (inclusions, exclusions)
    :param changed_files: List of file paths modified in the commit/MR
    :return: Dict mapping filter name to boolean evaluation result
    """
    results: dict[str, bool] = {}
    for filter_name, (inclusions, exclusions) in filters_config.items():
        results[filter_name] = evaluate_filter(inclusions, exclusions, changed_files)
    return results
