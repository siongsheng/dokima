# Task Breakdown: F038: Surface nm and TL findings in PR body — when nm runs (Phase 4) or TL reviews (Phase 5), inject their findings into the PR body as and sections. At depth=vet+nm (no TL), nm findings still appear. Currently nm output is invisible (37K chars logged but never surfaced); TL findings only appear via a separate PR comment. SHOULD FIX items from both nm and TL are extracted as GitHub issues regardless of depth.

### Task 1: Add _extract_nm_summary helper in utils.py
**Files:** from spec
**Dependencies:** [none]
**Description:** Add _extract_nm_summary helper in utils.py

### Task 2: Inject ### nm Review into PR body after nm Phase 4
**Files:** from spec
**Dependencies:** [none]
**Description:** Inject ### nm Review into PR body after nm Phase 4

### Task 3: Update TL PR body injection to preserve and refresh nm section
**Files:** from spec
**Dependencies:** [none]
**Description:** Update TL PR body injection to preserve and refresh nm section
