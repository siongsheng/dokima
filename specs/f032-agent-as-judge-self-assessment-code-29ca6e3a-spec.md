# F032: Agent-as-Judge self-assessment: coder answers 3 questions before pushing — does every spec requirement have code, what am I least confident about, what would TL flag. Catches empty PRs at source.

Now I have complete understanding of the project. Let me produce the corrected spec.
    
    
    
    Position: F032 is a prompt-only change — inject 3 self-assessment questions into the coder's pre-push instructions. Zero new logic, zero parsing, ~20 LOC. Confidence: High.
    
    
    
    F032: Agent-as-Judge Self-Assessment
    
    Version: 1.0.0  
    Status: Ready for implementation  
    Confidence: High — all scope is understood, no open questions  
    Feature ID: F032  
    Roadmap priority: P2
    
    Executive Summary
    
    F032 adds a self-assessment checkpoint to the coder phase: before pushing code, the coder must answer 3 questions about their own implementation. This is a behavioral intervention — the questions force the coder to re-read the spec, identify weak spots, and anticipate what the Tech Lead would flag. No new parsing, no gate logic, no pipeline changes beyond the prompt string itself. ~20 LOC added to pipeline.py.
    
    A post-hoc check already exists in the vet phase (commit 3277c93: "verify coder produced source changes at depth=vet") — it blocks PRs with no source code. F032 is the PREVENTIVE upstream companion: catch empty/incomplete PRs at source before push, not after.
    
    Constitution Check
    
    Axiom: Solves user pain?
    Status: ✅ Yes
    Notes: Empty/incomplete PRs waste TL review time. Coder self-reflection
      prevents them.
    ────────────────────────────────────────
    Axiom: Weekend-buildable?
    Status: ✅ Yes
    Notes: ~20 LOC in one file.
    ────────────────────────────────────────
    Axiom: Evidence people will pay?
    Status: N/A
    Notes: Internal tool improvement — not monetized.
    ────────────────────────────────────────
    Axiom: Tech stack boring and proven?
    Status: ✅ Yes
    Notes: Python string modification, no new deps.
    ────────────────────────────────────────
    Axiom: Avoids AI hype?
    Status: ✅ Yes
    Notes: Not "AI-powered" — it's a prompt engineering technique for an
      existing pipeline.
    
    No constitutional violations.
    
    Ponytail Guard — Pre-Spec Review
    
    
    Feature: Agent-as-Judge self-assessment
    Rung: 7 — minimum that works (prompt-only injection)
    Existing solution: Post-hoc vet check (commit 3277c93) catches empty PRs after push.
      F032 complements it with a PREVENTIVE upstream check.
    Spec needed: Yes — but minimal. Only the coder prompt string changes.
    Spec scope: Add 3 self-assessment questions to the coder's pre-push block in run_phase2_coder().
    
    
    Impact Assessment
    
    
    pipeline.py (+18/-0) — coder prompt string in run_phase2_coder(), lines 650-651
    
    
    Single file, single function, zero downstream effects. No new imports, no new dependencies, no API changes. The self-assessment answers appear in the coder output log but are not parsed by the panel.
    
    What Changed
    
    - pipeline.py run_phase2_coder(): Added 3 self-assessment questions to the coder prompt between "BEFORE PUSHING:" instructions and "Report:" tag. The questions ask: (1) spec requirement coverage, (2) least-confident implementation detail, (3) predicted TL flags. No logic changes — pure prompt addition.
    
    Feature Breakdown
    
    Task 1: Inject self-assessment questions into coder prompt
    - Files: pipeline.py
    - Dependencies: [none]
    - Parallelizable: no
    - Estimated LOC: ~18
    - Description: In run_phase2_coder(), add the 3-question self-assessment block to the coder prompt string, immediately after the BEFORE PUSHING block and before the "Report:" tag. The questions force the coder to re-read the spec, assess coverage, identify weak spots, and predict TL concerns before pushing.
    
    Task 2: Verify prompt injection in test suite
    - Files: tests/test_f032_self_assessment.py
    - Dependencies: [Task 1]
    - Parallelizable: no
    - Estimated LOC: ~50
    - Description: Write a unit test that verifies the coder prompt string includes the 3 self-assessment questions (Q1, Q2, Q3 headers) and the "Before pushing" instruction. Test uses the panel module's _make_coder_prompt or equivalent to validate the prompt template contains required strings.
    
    Data Model
    
    No new entities. No persistence. The self-assessment questions are prompt text only. Coder answers appear in OUTPUT_LOG as part of the coder's normal output stream — no structured parsing.
    
    Component Tree
    
    N/A — backend pipeline change only. No UI.
    
    API Routes
    
    N/A — no API changes.
    
    COTS Build-vs-Buy
    
    Component: Self-assessment prompt
    Decision: Build
    Justification: One string in an existing Python module. No library or
      service needed.
    ────────────────────────────────────────
    Component: Answer parsing
    Decision: NOT building
    Justification: Out of scope. The questions themselves are the
      intervention.
    
    Test Plan (MANDATORY)
    
    Happy Path
    - Coder prompt constructed by run_phase2_coder() contains Q1: SPEC COVERAGE, Q2: CONFIDENCE, Q3: TL PREDICTION substrings.
    - Coder prompt contains "Before pushing" context for the self-assessment block.
    - Prompt text is grammatically correct and unambiguous.
    - Self-assessment block does not break existing prompt structure (RED/GREEN commits, BEFORE PUSHING: lint+tests, Report: tag).
    
    Edge Cases
    - Empty prompt injection: Confirm no accidental deletion of adjacent prompt text. The self-assessment block is an ADDITION, not a replacement.
    - Prompt length: ~18 lines added to an existing ~75 line prompt. Total prompt remains well within model context limits.
    - Fix mode path: The coder prompt for fix mode (mode == "fix", line 574) does NOT get the self-assessment block. Fix mode uses a different prompt structure — verify the self-assessment is only added in the normal coder path.
    
    Failure Modes
    - Syntax error in prompt string: Python string concatenation error — caught by python3 -m py_compile pipeline.py (lint step).
    - Indentation break: Prompt string with wrong indentation — caught by Python compile step.
    - Missing closing quote: Broken multiline string — caught by compile step.
    
    Contract Invariants
    - The self-assessment block appears exactly once in the normal coder prompt path, not in fix mode.
    - The block comes AFTER "BEFORE PUSHING:" and BEFORE "Report:".
    - No existing prompt behavior is removed or altered.
    - All existing tests continue to pass (the panel's test suite at 673 tests).
    
    Panel Split
    
    Single sequential task wave — both tasks touch pipeline.py and the test file depends on Task 1. One coder agent.
    
    
    Wave 1: [Task 1]  →  Wave 2: [Task 2]
    
    
    Build & Deploy
    
    - Build: python3 -c "compile(open('pipeline.py').read(), 'pipeline.py', 'exec')" — Python syntax check.
    - Test: python3 -m pytest tests/test_f032_self_assessment.py -v — new test.
    - Full suite: python3 -m pytest tests/ -q — all 673+ tests must pass.
    - Lint: python3 -m py_compile pipeline.py
    - No env vars needed. No deployment steps beyond normal pipeline.
    - Branch: feat/f032-agent-as-judge-self-assessment-code-99fe357b (already exists per STATUS.md).
    
    Risk Register
    
    #: 1
    Risk: Prompt bloat — model ignores new section
    Severity: Low
    Mitigation: Questions are at the end, just before push, in the critical
      path. Models reliably follow terminal instructions.
    Trigger: Coder pushes without answering questions
    ────────────────────────────────────────
    #: 2
    Risk: Self-assessment adds LLM tokens but no behavioral change
    Severity: Low
    Mitigation: The questions are adversarial by design — "what would TL
      flag?" forces reflection. Even if the coder writes "nothing," it had to
      think about it.
    Trigger: No change in empty-PR rate after 5+ pipeline runs
    ────────────────────────────────────────
    #: 3
    Risk: Fix mode coder accidentally gets self-assessment
    Severity: Low
    Mitigation: Guarded by if mode == "fix" early return in prompt
      construction. Test verifies.
    Trigger: Fix-mode coder output includes Q1/Q2/Q3
    ────────────────────────────────────────
    #: 4
    Risk: Coder hallucinates "all covered" without checking spec
    Severity: Medium
    Mitigation: Q1 explicitly says "List any spec requirement that has NO
      implementation yet" — forces enumeration. The vet phase post-hoc check
      catches lies.
    Trigger: Vet phase BLOCKS an empty PR that self-assessed as "all covered"
    
    Anti-Creep
    
    - NOT building: Answer parsing, structured JSON extraction, gate logic that blocks push based on answers. The questions are the intervention — the coder's own reflection is the behavioral change.
    - NOT building: A dashboard or metrics for self-assessment quality. Answers live in OUTPUT_LOG. Manual review only.
    - NOT building: Fix-mode self-assessment. Fix mode has a different prompt structure and the TL has already flagged specific issues.
    - NOT building: Parallel coder worktree self-assessment. Worktrees use spawn_coder_in_worktree() which has its own prompt (line 331-346 in tasks.py). Out of scope — the worktree prompt is for single-task execution, not full-feature self-assessment.
    - NOT modifying: tasks.py, agent.py, utils.py, scripts/vet, scripts/nm, status.py, roadmap.py.
    
    Design Detail: Self-Assessment Prompt Text
    
    The exact text to inject (between the BEFORE PUSHING lint/test block and the "Report:" tag):
    
    
    SELF-ASSESSMENT (Agent-as-Judge) — Before pushing, answer these 3 questions in your output:
    
    Q1: SPEC COVERAGE — Does every requirement in the spec have corresponding code?
        List any spec requirement that has NO implementation yet.
        If every requirement is implemented, say "All requirements covered."
    
    Q2: CONFIDENCE — What implementation detail are you LEAST confident about?
        Be specific: name the file and behavior you're unsure about.
        If fully confident in everything, say "All confident — no weak spots."
    
    Q3: TL PREDICTION — If a Tech Lead reviewed this PR, what would they flag?
        Think adversarially: missing tests, unclear error handling, scope creep,
        spec non-compliance, architecture violations.
        If nothing, say "Nothing — this is clean."
    
    Answer all 3 questions before running git push.
    
    
    Injection point (in pipeline.py line ~650, within the coder prompt string): After CRITICAL RULES: block, after the "BEFORE PUSHING:" line and its lint/test instructions, just before the Report: tag.
    
    Sign-Off Checklist
    
    - [ ] Prompt text reviewed for clarity and non-ambiguity
    - [ ] Verified injection point does not break existing prompt flow
    - [ ] Fix mode path confirmed unaffected
    - [ ] Test verifies prompt contains Q1, Q2, Q3 substrings
    - [ ] Test verifies fix mode prompt does NOT contain self-assessment
    - [ ] Full test suite passes (673+ tests)
    - [ ] Python compile succeeds on pipeline.py
    - [ ] Code review: prompt text is additive only, no logic changes
    - [ ] Branch created and pushed: feat/f032-agent-as-judge-self-assessment-code-99fe357b
    - [ ] PR body includes Impact and What Changed sections
    - [ ] Roadmap updated: F032 marked [x] Done
    - [ ] STATUS.md updated
    
    
    
    Open Questions
    
    None. Confidence is High — this is a well-understood prompt engineering change with no unknown variables.