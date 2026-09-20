"""Glob pattern matching and path normalization engine."""

import re
from functools import lru_cache


def normalize_path(path: str) -> str:
    """
    Normalize path separators to POSIX forward slashes and strip redundant prefixes.

    - Replaces Windows backslashes `\\` with forward slashes `/`.
    - Strips leading `./` and trailing `/`.
    """
    p = path.strip().replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return p.strip("/")


def is_exclusion(pattern: str) -> bool:
    """Return True if the pattern begins with the exclusion prefix `!`."""
    return pattern.strip().startswith("!")


def strip_exclusion_prefix(pattern: str) -> str:
    """Remove leading `!` from an exclusion pattern."""
    p = pattern.strip()
    if p.startswith("!"):
        return p[1:].strip()
    return p


@lru_cache(maxsize=2048)
def glob_to_regex(pattern: str) -> re.Pattern[str]:
    """
    Compile a standard glob pattern into an anchored regular expression.

    Supported features:
    - `*` matches any character within a single path segment (does not cross `/`).
    - `**` matches zero or more path segments across directory levels.
    - `?` matches a single non-slash character.
    - Standard regex special characters are safely escaped.
    """
    p = normalize_path(pattern)
    i = 0
    n = len(p)
    tokens: list[str] = []

    # Handle leading **/ which can match zero segments at root or any subfolder
    if p.startswith("**/"):
        tokens.append("(?:^|.*/)")
        i = 3
    elif p == "**":
        tokens.append(".*")
        i = 2

    while i < n:
        if p[i : i + 4] == "/**/":
            tokens.append("(?:/|/.*/)")
            i += 4
        elif p[i : i + 3] == "/**" and i + 3 == n:
            tokens.append("(?:/.*)?")
            i += 3
        elif p[i : i + 2] == "**":
            tokens.append(".*")
            i += 2
        elif p[i] == "*":
            tokens.append("[^/]*")
            i += 1
        elif p[i] == "?":
            tokens.append("[^/]")
            i += 1
        else:
            tokens.append(re.escape(p[i]))
            i += 1

    regex_str = f"^{''.join(tokens)}$"
    return re.compile(regex_str)


def match_glob(pattern: str, file_path: str) -> bool:
    """
    Check if a given file path matches a glob pattern.

    :param pattern: Glob pattern (e.g. `**/*.kt`, `docs/**`, `web/**/*.ts`)
    :param file_path: File path to test
    :return: True if the file path matches the pattern
    """
    norm_path = normalize_path(file_path)
    # Strip exclusion mark if present for direct matching
    clean_pattern = strip_exclusion_prefix(pattern)
    regex = glob_to_regex(clean_pattern)
    return bool(regex.match(norm_path))
