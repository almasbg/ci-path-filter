.PHONY: help install dev test lint format run clean

help:
	@echo "Available commands:"
	@echo "  make install  - Install the package in editable mode with development dependencies"
	@echo "  make test     - Run test suite with coverage report"
	@echo "  make lint     - Run linter (ruff) and code format check"
	@echo "  make format   - Automatically reformat code with ruff"
	@echo "  make run      - Run CLI filter against sample changed files"
	@echo "  make clean    - Remove build artifacts, cache directories, and virtualenv files"

install:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check .
	ruff format --check .

format:
	ruff format .

run:
	ci-path-filter -c filters.yaml -f changed_files.example.txt -o .env
	@echo "Generated .env:"
	@cat .env 2>/dev/null || type .env

clean:
	python -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]"
	python -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in [pathlib.Path('.pytest_cache'), pathlib.Path('.ruff_cache'), pathlib.Path('build'), pathlib.Path('dist')]]"
