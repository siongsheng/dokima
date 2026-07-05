# Task Breakdown: F035: GitLab support: swap gh CLI for glab or abstract VCS layer

### Task 1: Create vcs.py module with backend detection and PR operations
**Files:** vcs.py
**Dependencies:** [none]
**Description:** Create vcs.py module with backend detection and PR operations

### Task 2: Add issue, release, and repo operations to vcs.py
**Files:** vcs.py
**Dependencies:** 1
**Description:** Add issue, release, and repo operations to vcs.py

### Task 3: Extend detect_repo() for GitLab URLs and add VCS token utilities
**Files:** utils.py
**Dependencies:** 1
**Description:** Extend detect_repo() for GitLab URLs and add VCS token utilities

### Task 4: Migrate pipeline.py gh() calls to vcs.*()
**Files:** pipeline.py
**Dependencies:** 1, 2
**Description:** Migrate pipeline.py gh() calls to vcs.*()

### Task 5: Migrate roadmap.py gh() calls and release/docs-cache in utils.py
**Files:** roadmap.py, utils.py
**Dependencies:** 2, 3
**Description:** Migrate roadmap.py gh() calls and release/docs-cache in utils.py

### Task 6: Update agent profile config and env passthrough for VCS tokens
**Files:** utils.py
**Dependencies:** 3, 5
**Description:** Update agent profile config and env passthrough for VCS tokens

### Task 7: starts in Wave 6, Task 10 must start in Wave 7.
**Files:** from spec
**Dependencies:** [none]
**Description:** starts in Wave 6, Task 10 must start in Wave 7.

### Task 8: Write tests for vcs.py and integration
**Files:** tests/test_vcs.py
**Dependencies:** 1, 2, 3
**Description:** Write tests for vcs.py and integration

### Task 9: Update conftest.py mock fixtures for backward compat
**Files:** tests/conftest.py
**Dependencies:** 4, 5
**Description:** Update conftest.py mock fixtures for backward compat

### Task 10: Update AGENTS.md and README for GitLab support
**Files:** AGENTS.md, README.md
**Dependencies:** 7
**Description:** Update AGENTS.md and README for GitLab support
