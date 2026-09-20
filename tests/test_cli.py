"""Integration tests for the command-line interface (CLI)."""

import io
import sys

from ci_path_filter.cli import main


class TestCLI:
    """Test suite for CLI arguments, execution, and outputs."""

    def test_cli_positional_arguments(self, tmp_path, monkeypatch, capsys):
        config_file = tmp_path / "filters.yaml"
        config_file.write_text(
            """
              filters:
                backend:
                  - "app/src/**/*.kt"
                frontend:
                  - "web/**/*.ts"
            """,
            encoding="utf-8",
        )
        env_file = tmp_path / "output.env"

        exit_code = main(
            [
                "-c",
                str(config_file),
                "-o",
                str(env_file),
                "app/src/main/App.kt",
            ]
        )

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "backend=true" in captured.out
        assert "frontend=false" in captured.out

        # Verify .env file content
        assert env_file.is_file()
        file_content = env_file.read_text(encoding="utf-8")
        assert "backend=true" in file_content
        assert "frontend=false" in file_content

    def test_cli_files_file_option(self, tmp_path, capsys):
        config_file = tmp_path / "filters.yaml"
        config_file.write_text(
            """
filters:
  docs:
    - "README.md"
  tests:
    - "**/test/**"
            """,
            encoding="utf-8",
        )
        files_list = tmp_path / "changed.txt"
        files_list.write_text("README.md\napp/src/test/Foo.kt\n", encoding="utf-8")

        exit_code = main(
            [
                "-c",
                str(config_file),
                "-f",
                str(files_list),
            ]
        )

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "docs=true" in captured.out
        assert "tests=true" in captured.out

    def test_cli_missing_files_file_returns_exit_code_1(self, tmp_path, capsys):
        config_file = tmp_path / "filters.yaml"
        config_file.write_text("filters: {backend: ['app/*.kt']}", encoding="utf-8")
        exit_code = main(
            [
                "-c",
                str(config_file),
                "-f",
                str(tmp_path / "missing_files.txt"),
            ]
        )
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "File Error" in captured.err

    def test_cli_stdin_pipe(self, tmp_path, monkeypatch, capsys):
        config_file = tmp_path / "filters.yaml"
        config_file.write_text(
            """
filters:
  web:
    - "web/**/*.tsx"
            """,
            encoding="utf-8",
        )

        fake_stdin = io.StringIO("web/components/Navbar.tsx\n")
        monkeypatch.setattr(sys, "stdin", fake_stdin)
        # Mock isatty to False to simulate piped input
        monkeypatch.setattr(fake_stdin, "isatty", lambda: False)

        exit_code = main(["-c", str(config_file)])
        assert exit_code == 0

        captured = capsys.readouterr()
        assert "web=true" in captured.out

    def test_cli_missing_config_returns_exit_code_1(self, tmp_path, capsys):
        exit_code = main(["-c", str(tmp_path / "non_existent.yaml")])
        assert exit_code == 1

        captured = capsys.readouterr()
        assert "Configuration Error" in captured.err

    def test_cli_unexpected_error_returns_exit_code_1(self, monkeypatch, capsys):
        def mock_load_config(*args, **kwargs):
            raise RuntimeError("Database connection crashed")

        monkeypatch.setattr("ci_path_filter.cli.load_config", mock_load_config)

        exit_code = main(["-c", "any.yaml"])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Unexpected Error" in captured.err
