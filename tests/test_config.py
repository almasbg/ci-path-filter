"""Unit tests for YAML configuration loading and validation."""

from pathlib import Path

import pytest

from ci_path_filter.config import ConfigError, load_config, parse_patterns


class TestParsePatterns:
    """Test suite for parsing pattern strings and lists."""

    def test_single_string_pattern(self):
        inclusions, exclusions = parse_patterns("README.md", "docs")
        assert inclusions == ["README.md"]
        assert exclusions == []

    def test_list_with_exclusions(self):
        raw = ["app/src/**/*.kt", "!app/src/test/**"]
        inclusions, exclusions = parse_patterns(raw, "backend")
        assert inclusions == ["app/src/**/*.kt"]
        assert exclusions == ["app/src/test/**"]

    def test_empty_string_in_patterns_ignored(self):
        raw = ["app/src/**/*.kt", "   ", ""]
        inclusions, exclusions = parse_patterns(raw, "backend")
        assert inclusions == ["app/src/**/*.kt"]
        assert exclusions == []

    def test_invalid_pattern_type_raises_config_error(self):
        with pytest.raises(ConfigError, match="must be a list of strings"):
            parse_patterns(12345, "backend")

    def test_non_string_item_inside_list_raises_config_error(self):
        with pytest.raises(ConfigError, match="must be a string"):
            parse_patterns(["app/src/**/*.kt", 999], "backend")


class TestLoadConfig:
    """Test suite for load_config file reading and schema validation."""

    def test_load_valid_yaml(self, tmp_path):
        config_file = tmp_path / "filters.yaml"
        config_file.write_text(
            """
filters:
  backend:
    - "app/src/**/*.kt"
    - "!app/src/test/**"
  frontend:
    - "web/**/*.ts"
            """,
            encoding="utf-8",
        )

        cfg = load_config(config_file)
        assert "backend" in cfg
        assert "frontend" in cfg
        assert cfg["backend"] == (["app/src/**/*.kt"], ["app/src/test/**"])
        assert cfg["frontend"] == (["web/**/*.ts"], [])

    def test_missing_file_raises_config_error(self, tmp_path):
        non_existent = tmp_path / "does_not_exist.yaml"
        with pytest.raises(ConfigError, match="Configuration file not found"):
            load_config(non_existent)

    def test_malformed_yaml_raises_config_error(self, tmp_path):
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text("filters: [unclosed list", encoding="utf-8")
        with pytest.raises(ConfigError, match="Failed to parse YAML"):
            load_config(bad_yaml)

    def test_non_dict_root_raises_config_error(self, tmp_path):
        not_dict = tmp_path / "not_dict.yaml"
        not_dict.write_text("- item1\n- item2", encoding="utf-8")
        with pytest.raises(ConfigError, match="root element must be a YAML mapping"):
            load_config(not_dict)

    def test_missing_filters_key_raises_config_error(self, tmp_path):
        missing_key = tmp_path / "missing_key.yaml"
        missing_key.write_text("other_key: 123", encoding="utf-8")
        with pytest.raises(ConfigError, match="Missing required top-level key 'filters'"):
            load_config(missing_key)

    def test_filters_not_a_dict_raises_config_error(self, tmp_path):
        invalid_type = tmp_path / "invalid_type.yaml"
        invalid_type.write_text("filters: ['not', 'a', 'dict']", encoding="utf-8")
        with pytest.raises(ConfigError, match="'filters' must be a dictionary"):
            load_config(invalid_type)

    def test_empty_or_non_string_filter_name_raises_config_error(self, tmp_path):
        bad_name = tmp_path / "bad_name.yaml"
        bad_name.write_text("filters:\n  ' ': ['app/*.kt']", encoding="utf-8")
        with pytest.raises(ConfigError, match="Filter name must be a non-empty string"):
            load_config(bad_name)

    def test_unreadable_file_raises_config_error(self, tmp_path, monkeypatch):
        test_file = tmp_path / "locked.yaml"
        test_file.write_text("filters: {}", encoding="utf-8")

        def mock_read_text(*args, **kwargs):
            raise PermissionError("Access denied")

        monkeypatch.setattr(Path, "read_text", mock_read_text)
        with pytest.raises(ConfigError, match="Could not read configuration file"):
            load_config(test_file)
