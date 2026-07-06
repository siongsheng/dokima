# Task Breakdown: F042: CI pipeline — add .github/workflows/test.yml running pytest on push/PR. Add complexity gates (max CC=30), lint (pyflakes), and type checking (mypy --strict for new modules).

### Task 1: Create .github/workflows/test.yml — main CI workflow YAML
**Files:** .github/workflows/test.yml
**Dependencies:** [none]
**Description:** Create .github/workflows/test.yml — main CI workflow YAML

### Task 2: Create pyproject.toml — mypy, pyflakes, and radon configuration
**Files:** pyproject.toml
**Dependencies:** 1
**Description:** Create pyproject.toml — mypy, pyflakes, and radon configuration

### Task 3: Create .mypy.ini — per-module typing strictness
**Files:** .mypy.ini
**Dependencies:** 1
**Description:** Create .mypy.ini — per-module typing strictness

### Task 4: Verify CI configuration — dry-run validation
**Files:** pyproject.toml, .mypy.ini, .github/workflows/test.yml
**Dependencies:** 1, 2, 3
**Description:** Verify CI configuration — dry-run validation
