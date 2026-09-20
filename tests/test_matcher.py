"""Unit tests for path normalization and glob pattern matching."""

import pytest

from ci_path_filter.matcher import (
    is_exclusion,
    match_glob,
    normalize_path,
    strip_exclusion_prefix,
)


class TestPathNormalization:
    """Test suite for path normalization."""

    def test_normalize_windows_backslashes(self):
        assert normalize_path(r"app\src\main\App.kt") == "app/src/main/App.kt"

    def test_normalize_leading_dot_slash(self):
        assert normalize_path("./web/index.ts") == "web/index.ts"
        assert normalize_path(r".\app\src\test\App.kt") == "app/src/test/App.kt"

    def test_normalize_multiple_dot_slashes(self):
        assert normalize_path("././README.md") == "README.md"

    def test_normalize_trailing_and_leading_slashes(self):
        assert normalize_path("/docs/guide/") == "docs/guide"
        assert normalize_path("  src/App.kt  ") == "src/App.kt"


class TestExclusionHelpers:
    """Test suite for exclusion pattern prefix detection and stripping."""

    def test_is_exclusion(self):
        assert is_exclusion("!app/src/test/**") is True
        assert is_exclusion("!**/test/**") is True
        assert is_exclusion("app/src/**/*.kt") is False
        assert is_exclusion("README.md") is False

    def test_strip_exclusion_prefix(self):
        assert strip_exclusion_prefix("!app/src/test/**") == "app/src/test/**"
        assert strip_exclusion_prefix("!  **/test/**") == "**/test/**"
        assert strip_exclusion_prefix("web/**/*.ts") == "web/**/*.ts"


class TestGlobMatching:
    """Test suite for glob pattern matching rules."""

    @pytest.mark.parametrize(
        ("pattern", "path", "expected"),
        [
            # Standalone ** pattern
            ("**", "App.kt", True),
            ("**", "a/b/c/App.kt", True),
            # Embedded ** pattern
            ("src/**.kt", "src/App.kt", True),
            ("src/**.kt", "src/sub/App.kt", True),
            # Single asterisk * (matches within folder, does not cross /)
            ("*.kt", "App.kt", True),
            ("*.kt", "src/App.kt", False),
            ("src/*.kt", "src/App.kt", True),
            ("src/*.kt", "src/sub/App.kt", False),
            ("web/*.ts", "web/index.ts", True),
            ("web/*.ts", "web/components/Button.ts", False),
            # Recursive ** leading (zero or more path segments)
            ("**/*.kt", "App.kt", True),
            ("**/*.kt", "src/App.kt", True),
            ("**/*.kt", "app/src/main/kotlin/App.kt", True),
            ("**/*.kt", "README.md", False),
            # Sandwiched /**/ (zero or more middle segments)
            ("app/**/test.kt", "app/test.kt", True),
            ("app/**/test.kt", "app/src/test.kt", True),
            ("app/**/test.kt", "app/a/b/c/test.kt", True),
            ("app/**/test.kt", "other/test.kt", False),
            # Trailing /** (recursively matches folder and children)
            ("docs/**", "docs/README.md", True),
            ("docs/**", "docs/api/v1/spec.json", True),
            ("docs/**", "docs", True),
            ("docs/**", "src/docs/file.md", False),
            # Exclusion pattern target
            ("**/test/**", "test/FiltersTest.kt", True),
            ("**/test/**", "app/src/test/FiltersTest.kt", True),
            ("**/test/**", "app/src/main/App.kt", False),
            # Exact filename
            ("README.md", "README.md", True),
            ("README.md", "docs/README.md", False),
            # Single character ?
            ("test?.py", "test1.py", True),
            ("test?.py", "testA.py", True),
            ("test?.py", "test12.py", False),
            ("test?.py", "test.py", False),
        ],
    )
    def test_glob_patterns(self, pattern: str, path: str, expected: bool):
        assert match_glob(pattern, path) is expected

    def test_windows_paths_match_unix_patterns(self):
        """Verify Windows paths with backslashes match POSIX glob patterns."""
        pattern = "app/src/**/*.kt"
        windows_path = r"app\src\main\util\Helper.kt"
        assert match_glob(pattern, windows_path) is True
