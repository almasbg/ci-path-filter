"""
ci_path_filter - CI/CD Path-Based Filter Tool
=============================================

A command-line tool and Python library designed to optimize CI/CD pipelines by
matching changed files against glob patterns and exporting results in dotenv
(.env) format.
"""

from ci_path_filter.config import ConfigError, load_config
from ci_path_filter.evaluator import evaluate_all_filters, evaluate_filter
from ci_path_filter.exporter import format_env, write_env_file
from ci_path_filter.matcher import match_glob, normalize_path

__version__ = "0.1.0"

__all__ = [
    "ConfigError",
    "__version__",
    "evaluate_all_filters",
    "evaluate_filter",
    "format_env",
    "load_config",
    "match_glob",
    "normalize_path",
    "write_env_file",
]
