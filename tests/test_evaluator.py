"""Unit tests for filter evaluation logic."""

from ci_path_filter.evaluator import evaluate_all_filters, evaluate_filter


class TestEvaluateFilter:
    """Test suite for single filter evaluation logic."""

    def test_single_file_matches_inclusion(self):
        inclusions = ["**/*.kt"]
        exclusions = ["!**/test/**"]
        changed = ["app/src/main/App.kt"]
        assert evaluate_filter(inclusions, exclusions, changed) is True

    def test_matching_file_is_excluded(self):
        inclusions = ["**/*.kt"]
        exclusions = ["**/test/**"]
        changed = ["app/src/test/FiltersTest.kt"]
        assert evaluate_filter(inclusions, exclusions, changed) is False

    def test_one_file_matches_even_if_another_is_excluded(self):
        """
        If App.kt is not excluded and FiltersTest.kt IS excluded,
        the filter should evaluate to True because at least one valid file matched.
        """
        inclusions = ["**/*.kt"]
        exclusions = ["**/test/**"]
        changed = ["app/src/main/App.kt", "app/src/test/FiltersTest.kt"]
        assert evaluate_filter(inclusions, exclusions, changed) is True

    def test_no_files_match_inclusion(self):
        inclusions = ["web/**/*.ts"]
        exclusions = []
        changed = ["app/src/main/App.kt", "README.md"]
        assert evaluate_filter(inclusions, exclusions, changed) is False

    def test_empty_changed_files_returns_false(self):
        inclusions = ["**/*.kt"]
        exclusions = []
        assert evaluate_filter(inclusions, exclusions, []) is False

    def test_all_files_excluded_returns_false(self):
        inclusions = ["**/*.kt"]
        exclusions = ["**/test/**"]
        changed = ["test/A.kt", "app/test/B.kt", "sub/test/C.kt"]
        assert evaluate_filter(inclusions, exclusions, changed) is False


class TestAssignmentScenario:
    """
    Verification against the exact example from CI_CD_Assignment.pdf:

    filters.yaml:
      kotlin_sources:
        - "**/*.kt"
        - "!**/test/**"
      tests:
        - "**/test/**/*.kt"
      documentation:
        - "README.md"
        - "docs/**"

    Changed files:
      - App.kt (Kotlin file, not in test directory)
      - FiltersTest.kt (in test directory: app/src/test/FiltersTest.kt)
      - README.md

    Expected Output:
      kotlin_sources=true
      tests=true
      documentation=true
    """

    def test_pdf_assignment_example(self):
        filters_config = {
            "kotlin_sources": (["**/*.kt"], ["**/test/**"]),
            "tests": (["**/test/**/*.kt"], []),
            "documentation": (["README.md", "docs/**"], []),
        }

        changed_files = [
            "App.kt",
            "app/src/test/FiltersTest.kt",
            "README.md",
        ]

        results = evaluate_all_filters(filters_config, changed_files)

        assert results == {
            "kotlin_sources": True,
            "tests": True,
            "documentation": True,
        }

    def test_partial_match_scenario(self):
        filters_config = {
            "backend": (["app/src/**/*.kt"], ["app/src/test/**"]),
            "frontend": (["web/**/*.ts", "web/**/*.tsx"], []),
            "docs": (["README.md", "docs/**/*.md"], []),
        }

        # Only frontend modified
        changed_files = ["web/components/Button.tsx"]
        results = evaluate_all_filters(filters_config, changed_files)

        assert results == {
            "backend": False,
            "frontend": True,
            "docs": False,
        }
