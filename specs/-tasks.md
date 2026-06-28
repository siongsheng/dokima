# Task Breakdown: .

### Task 1: Human Gate — Spec Approval
**Files:** No code changes — user reviews spec in less/vim
**Dependencies:** [none]
**Description:** Human Gate — Spec Approval

### Task 2: Strategist — Spec Generation
**Files:** dokima (spawn_agent + spec parser), specs/<feature>-spec.md, specs/<feature>-tasks.md
**Dependencies:** [none]
**Description:** Strategist — Spec Generation

### Task 3: TL Spec Pre-Review — Architecture + Test Plan Review
**Files:** dokima (TL spawn, verdict extraction)
**Dependencies:** 2
**Description:** TL Spec Pre-Review — Architecture + Test Plan Review

### Task 4: Coder — RED→GREEN Implementation
**Files:** dokima (spawn_agent_with_fallback, TDD enforcement, worktree management), feature branch files
**Dependencies:** 3
**Description:** Coder — RED→GREEN Implementation

### Task 5: vet — Build + Test Verification
**Files:** ~/bin/vet, dokima (vet spawn, retry loop)
**Dependencies:** 4
**Description:** vet — Build + Test Verification

### Task 6: nm — Adversarial Review
**Files:** ~/bin/nm, dokima (nm spawn, PR creation)
**Dependencies:** 5
**Description:** nm — Adversarial Review

### Task 7: Tech Lead — Spec Compliance + Quality Verdict
**Files:** dokima (verdict extraction, blocker parser, status update)
**Dependencies:** 6
**Description:** Tech Lead — Spec Compliance + Quality Verdict
