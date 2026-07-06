# Task Breakdown: F038: Surface nm and TL findings in PR body — when nm runs (Phase 4) or TL reviews (Phase 5), inject their findings into the PR body as and sections. At depth=vet+nm (no TL), nm findings still appear. Currently nm output is invisible (37K chars logged but never surfaced); TL findings only appear via a separate PR comment. SHOULD FIX items from both nm and TL are extracted as GitHub issues regardless of depth.

### Task 1: Wire nm SHOULD FIX → GitHub issues in run_pipeline Phase 4 block
**Files:** pipeline.py
**Dependencies:** [none]
**Description:** Wire nm SHOULD FIX → GitHub issues in run_pipeline Phase 4 block

### Task 2: Add test for nm SHOULD FIX issue creation path
**Files:** tests/test_f038_nm_injection.py
**Dependencies:** 1
**Description:** Add test for nm SHOULD FIX issue creation path
