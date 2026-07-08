# F046: Fix Mode Branch Isolation

## Impact
`dokima fix --issue N` creates a proper fix branch, never commits to main directly.

### Task 1: Enforce branch isolation in fix mode
**Files:** pipeline.py
**Dependencies:** [none]
**Parallelizable:** no
**Description:** In run_fix_mode_issue(): after branch creation, verify coder is on the correct branch before spawning. In vet phase: verify the branch being tested is not main/master/default. Add enforcement to coder prompt: make branch checkout mandatory with verification. Add test.
