# CI/CD Path-Based Filter System (`ci-path-filter`)

[![CI Pipeline](https://github.com/almasbg/ci-path-filter/actions/workflows/ci.yml/badge.svg)](https://github.com/almasbg/ci-path-filter/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A fast, lightweight, zero-bloat command-line tool designed to optimize CI/CD pipelines (such as GitLab CI, GitHub Actions, and Bitbucket Pipelines) by determining which jobs or pipelines should run based on changed file paths in a commit or merge request.

---

## Features

- **Standard Glob Matching**:
  - `*` matches any characters within a single directory segment.
  - `**` matches zero or more path segments across directory depths.
  - `?` matches a single non-slash character.
- **Exclusion Filters (`!`)**: Easily exclude specific paths (e.g. `!**/test/**`).
- **Strict Evaluation Rule**: A filter evaluates to `true` if **ANY** changed file matches at least one inclusion pattern **AND** does **NOT** match any exclusion pattern for that filter.
- **GitLab CI & GitHub Actions Compatible**: Generates clean `.env` format (`backend=false\nfrontend=true`) ready for consumption via dotenv artifacts.
- **Flexible File Input**: Accepts changed paths via CLI positional arguments, external text files (`--files-file`), or piped standard input (`stdin`).
- **High Performance**: Regex pattern caching (`lru_cache`) ensures fast matching across large monorepos with hundreds of files.
- **Cross-Platform**: Automatically normalizes Windows (`\`) and POSIX (`/`) path separators.

---

## Architecture & Directory Layout

The project adheres to a clean, production-ready `src`-layout with strict separation of concerns:

```text
ci-path-filter/
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI matrix (3.10-3.13, lint, test, smoke test)
├── .gitlab-ci.yml               # GitLab CI pipeline demo with dotenv artifact reports
├── src/
│   └── ci_path_filter/
│       ├── __init__.py          # Package exports & version
│       ├── cli.py               # Argument parsing, input collection, exit codes
│       ├── config.py            # YAML schema validation & pattern splitting
│       ├── matcher.py           # Path normalization & glob-to-regex engine
│       ├── evaluator.py         # Inclusion / exclusion filter evaluation
│       └── exporter.py          # .env formatting and file exporter
├── tests/
│   ├── __init__.py
│   ├── test_config.py           # Unit tests for YAML parsing & edge cases
│   ├── test_matcher.py          # Unit tests for glob patterns (*, **, !)
│   ├── test_evaluator.py        # Logic combinations & assignment scenarios
│   └── test_cli.py              # CLI integration tests & error handling
├── pyproject.toml               # PEP 517 / 621 packaging & test config
├── filters.yaml                 # Default filters configuration file
├── filters.example.yml          # Example configuration file
├── changed_files.example.txt    # Sample changed file paths for testing
├── LICENSE                      # MIT License
└── README.md                    # Setup, usage, and documented tradeoffs
```

---

## Installation

### Prerequisites
- Python `>= 3.10`

### Local Installation
```bash
# Clone the repository
git clone https://github.com/almasbg/ci-path-filter.git
cd ci-path-filter

# Install in editable mode
pip install -e .

# Or install with development and test dependencies
pip install -e ".[dev]"
```

---

## Usage

### 1. Configuration File (`filters.yaml`)

Define your named filters in a YAML file:

```yaml
filters:
  backend:
    - "app/src/**/*.kt"
    - "!app/src/test/**"
  frontend:
    - "web/**/*.ts"
    - "web/**/*.tsx"
  documentation:
    - "README.md"
    - "docs/**"
  tests:
    - "**/test/**/*.kt"
```

### 2. Running the CLI

#### Option A: Passing files directly as arguments
```bash
ci-path-filter -c filters.yaml -o .env App.kt web/index.ts
```

#### Option B: Piping changed files from Git (`stdin`)
```bash
git diff --name-only origin/main...HEAD | ci-path-filter -c filters.yaml -o .env
```

#### Option C: Reading from a file containing changed paths
```bash
git diff --name-only origin/main...HEAD > changed_files.txt
ci-path-filter -c filters.yaml -f changed_files.txt -o .env
```

### 3. Generated Output (`.env`)

The generated `.env` file contains sorted, deterministic boolean flags:

```env
backend=false
documentation=false
frontend=true
tests=false
```

---

## Integrating into Your CI/CD Pipelines

### GitLab CI Example (`.gitlab-ci.yml`)

External repositories can install `ci-path-filter` directly from Git into the pipeline runner:

```yaml
stages:
  - filter
  - backend
  - frontend

detect-changes:
  stage: filter
  image: python:3.13-slim
  before_script:
    - apt-get update && apt-get install -y --no-install-recommends git
    - pip install git+https://github.com/almasbg/ci-path-filter.git@main
  script:
    - git diff --name-only $CI_MERGE_REQUEST_DIFF_BASE_SHA $CI_COMMIT_SHA | ci-path-filter -c filters.yaml -o build.env
  artifacts:
    reports:
      dotenv: build.env

backend-job:
  stage: backend
  script:
    - ./gradlew test
  rules:
    - if: $backend == "true"

frontend-job:
  stage: frontend
  script:
    - npm test
  rules:
    - if: $frontend == "true"
```

### GitHub Actions Pipeline Example

In GitHub Actions, external repositories install `ci-path-filter` via Git, and the generated `.env` file is piped into `$GITHUB_ENV` to conditionally gate subsequent steps:

```yaml
name: Path Filtered CI

on:
  pull_request:
    branches: [main]

jobs:
  filter-and-run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install ci-path-filter
        run: pip install git+https://github.com/almasbg/ci-path-filter.git@main

      - name: Evaluate Path Filters
        run: |
          git diff --name-only origin/main...HEAD | ci-path-filter -c filters.yaml -o build.env
          cat build.env >> $GITHUB_ENV

      - name: Run Backend Tests
        if: env.backend == 'true'
        run: ./gradlew test

      - name: Run Frontend Tests
        if: env.frontend == 'true'
        run: npm test

      - name: Build Documentation
        if: env.docs == 'true'
        run: mkdocs build
```

---

## Development & Automated CI

### Local Testing & Quality Checks

Run tests and code quality tools directly:
```bash
# Run all unit and integration tests with coverage
pytest

# Run linter
ruff check .

# Check formatting
ruff format --check .

# Automatically format code
ruff format .

# Run sample CLI execution
ci-path-filter -c filters.yaml -f changed_files.example.txt -o .env
```

### Repository Automated CI Workflow (`.github/workflows/ci.yml`)

The repository's internal CI pipeline runs linting, formatting checks, and a Python matrix test suite on every pull request and push:

```yaml
name: CI Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    name: Code Quality & Formatting
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - run: |
          python -m pip install --upgrade pip
          pip install ruff
      - run: ruff format --check .
      - run: ruff check .

  test:
    name: Tests (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.10", "3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
      - run: pytest --cov=src --cov-report=term-missing --cov-report=xml
      - name: Smoke test CLI execution
        run: |
          ci-path-filter -c filters.yaml -f changed_files.example.txt -o smoke_test.env
          cat smoke_test.env
          test -f smoke_test.env
```

---

## Architectural Decisions & Trade-offs

Key architectural decisions and design trade-offs made in this implementation:

### Trade-off 1: Decoupled File Input vs Direct Git Subprocess Invocation
- **Decision**: The CLI accepts file paths via CLI arguments, external text file, or standard input (`stdin`) rather than invoking `git diff` directly within Python.
- **Rationale**: 
  1. Keeps the tool completely decoupled from the host environment's Git binary, version differences, and repository checkout state (e.g. shallow clones vs full checkouts in CI).
  2. Greatly simplifies unit testing and deterministic verification without needing mock git repositories.
  3. Allows chaining with any source control tool (Git, Mercurial, SVN, or local file lists).

### Trade-off 2: POSIX Path Normalization
- **Decision**: All incoming file paths and pattern definitions are converted to forward slashes (`/`), and leading `./` segments are stripped before matching.
- **Rationale**: Developers frequently run tests locally on Windows machines (`\`), while CI/CD runners (GitHub Actions / GitLab CI) typically execute on Linux (`/`). Normalizing ensures identical, deterministic matching results regardless of host operating system.

### Trade-off 3: Custom Glob-to-Regex Engine with LRU Caching
- **Decision**: Implemented a lightweight, anchored glob-to-regex converter with `@lru_cache` rather than relying on standard `pathlib.Path.match`.
- **Rationale**: Python's standard `pathlib.PurePosixPath.match("**/*.kt")` requires at least one directory segment and does not match root files like `App.kt`. Our compiler correctly adheres to the specification (`**` matches zero or more segments) and achieves `O(1)` cached performance when evaluating hundreds of files.

### Trade-off 4: Standard Library `argparse` vs Heavy CLI Frameworks (`Click`/`Typer`)
- **Decision**: Standard library `argparse` is used instead of third-party CLI packages like `click` or `typer`.
- **Rationale**: Keeps runtime dependencies to the absolute bare minimum (`pyyaml`), preventing supply-chain vulnerability exposure and ensuring sub-50ms cold startup times in short-lived CI/CD container environments.

### Trade-off 5: In-Memory File List vs Streaming Generators
- **Decision**: Changed files are collected into an in-memory list rather than a disk-backed or chunked stream.
- **Rationale**: Typical pull requests / merge requests in monorepos touch $10^1$ to $10^3$ files (well under a few megabytes of memory). Loading paths into memory allows instantaneous, non-blocking multi-filter evaluation while avoiding unnecessary file descriptor or generator management overhead.

### Trade-off 6: Strict Dotenv Compliance vs Multi-Format Exporters
- **Decision**: Exclusively outputs the POSIX dotenv format required by GitLab CI (`reports: dotenv`) and GitHub Actions.
- **Rationale**: Scoped out multi-format serialization (JSON/YAML/Markdown) to prevent feature creep. Dotenv output format is deterministically sorted, unquoted, and lowercase-boolean compliant for direct integration with pipeline orchestrators.

---

## License

This project is licensed under the MIT License.
