# Task Breakdown: F046: Fix mode branch isolation — coder commits directly to main instead of the fix branch. The coder prompt says "switch to branch fix/issue-N" but the coder ignores it or the pipeline doesn't enforce it. Fix: verify coder is on the correct branch before vet phase, or make the branch checkout mandatory in the prompt.

### Task 1: Push fix/issue branch to origin before spawning coder
**Files:** from spec
**Dependencies:** [none]
**Description:** Push fix/issue branch to origin before spawning coder

### Task 2: Add _verify_branch() helper function
**Files:** from spec
**Dependencies:** [none]
**Description:** Add _verify_branch() helper function

### Task 3: Add branch guard in vet phase (run_phase3_vet)
**Files:** from spec
**Dependencies:** [none]
**Description:** Add branch guard in vet phase (run_phase3_vet)

### Task 4: Harden coder prompt — mandatory branch checkout with pre-flight
**Files:** from spec
**Dependencies:** [none]
**Description:** Harden coder prompt — mandatory branch checkout with pre-flight

### Task 5: Add tests for branch isolation
**Files:** from spec
**Dependencies:** [none]
**Description:** Add tests for branch isolation
