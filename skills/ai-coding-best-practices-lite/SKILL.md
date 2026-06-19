---
name: ai-coding-best-practices-lite
description: "Stripped coding best practices for coder agents — TDD, task granularity, anti-patterns, verification gates only."
version: 1.0.0
---

# AI Coding Best Practices (Lite — Coder Edition)

Stripped for the coder: only the rules the coder must follow during implementation.

## 1. TDD Enforcement (CRITICAL)

Follow TDD: Red → Green → Refactor.
1. Write simplest failing test first
2. Minimum code to pass
3. Refactor only after green
4. NEVER modify or delete tests to pass — fix code, not test

### Two-Commit Requirement

Tests and code MUST be in SEPARATE commits with distinct timestamps.

```
RED COMMIT (must show FIRST in git log):
  git add <test files only>
  git commit -m "test: <description>"

GREEN COMMIT (must show SECOND, later timestamp):
  git add <impl files only>
  git commit -m "feat: <description>"
```

## 2. Task Granularity

- One function/component/test-file per task. 5-15 min each.
- After each task: run tests, commit if green.
- Implement ALL tasks from the spec. Do not stop until ALL done.

## 3. No Scope Creep

- NEVER add features not in the spec.
- If you think something is missing, flag CLARIFICATION NEEDED: — do NOT implement.
- If env vars unavailable, create test skeleton with skip + comment.

## 4. Verification Gates

Before marking complete:
1. Tests pass
2. Type check / build passes
3. Lint passes
4. No scope creep

## 5. Anti-Patterns (BLOCKERS)

- Skipping tests
- Deleting failing tests
- Bundling tests + code in one commit
- Adding features not in spec
- Auto-committing without verification
