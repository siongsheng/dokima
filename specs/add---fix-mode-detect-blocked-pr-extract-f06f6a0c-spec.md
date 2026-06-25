# Add --fix mode: detect BLOCKED PR, extract blockers from TL review, feed to coder as fix-only tasks (no new features, no refactors), run vet→nm→TL always full pipeline, update PR. See specs/fix-mode/plan.md for 16 edge cases.

Now let me check the test structure and search for existing fix-mode related patterns in the codebase.

Now let me read the full fix-mode plan and the remaining sections I need.

I have a thorough understanding of the project now. Let me produce the spec.
    
    Ponytail Guard — Pre-Spec Review
    
    Feature: --fix mode (detect BLOCKED PR, extract blockers, feed to coder)
    Rung: 7 — genuine new orchestration. The TL auto-fix loopback in run_phase5_tech_lead (lines 2331-2391) handles some objective blockers during the main pipeline run, but it only fires within the same pipeline invocation, can't handle subjective blockers, and there's no independent CLI entry point to trigger a fix cycle on an already-BLOCKED PR.
    Existing solution: Partial (TL auto-fix loopback for objective blockers only)
    Spec needed: Yes
    Spec scope: CLI flag integration, BLOCKED PR discovery, blocker extraction from PR body, fix-only coder prompt, and re-verification pipeline
    
    Now writing the spec.

Now let me verify the spec against plan.md edge cases systematically:

Spec written and verified.
    
    
    
    Spec Complete: --fix Mode
    
    File: /home/opc/dokima/specs/fix-mode/spec.md
    Confidence: High
    Impact: MEDIUM
    
    Summary
    
    dokima --fix [project_dir] — detects the most recent BLOCKED PR, extracts blockers from the TL review section, feeds them to the coder as a fix-only task, and runs vet→nm→TL always full pipeline.
    
    Key Design Decisions
    
    Decision: Skip Phase 1 (strategist)
    Rationale: Spec already exists; blockers ARE the requirements
    ────────────────────────────────────────
    Decision: Work on existing PR branch
    Rationale: No new branch/PR — fixes update the existing one
    ────────────────────────────────────────
    Decision: Always run full pipeline
    Rationale: Fixes are high-risk — they can break working code
    ────────────────────────────────────────
    Decision: No auto-loop
    Rationale: One fix attempt per invocation; prevents infinite cycles
    ────────────────────────────────────────
    Decision: Architectural blockers → abort
    Rationale: Requires human decision, not coder fix
    ────────────────────────────────────────
    Decision: Reuse existing phases 3/4/5
    Rationale: run_phase3_vet, run_phase4_nm, run_phase5_tech_lead run
      unchanged
    
    Scope
    
    - 10 tasks, 3 parallelizable waves
    - ~370-420 LOC net new (dokima: ~250-300, tests: ~120, README: ~25)
    - 3 new functions: discover_blocked_pr(), extract_blockers_from_pr(), run_fix_mode()
    - All 16 edge cases from specs/archive/fix-mode/plan.md covered
    
    What's NOT built
    
    - Auto-loop fix cycles (manual invocation only)
    - Fixing merged/closed PRs
    - Creating new branches or PRs
    - Auto-merging after fix
    - Fixing multiple PRs in one invocation
    - Running strategist for fix-mode
    
    Sign-Off Checklist
    
    16 items in the spec — covering flag parsing, PR discovery, blocker extraction, architectural filtering, human gate (interactive + non-interactive), coder constraints, pipeline phases, PR body updates, env var gating, all 16 edge cases, tests, and docs.