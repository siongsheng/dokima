# F032: Agent-as-Judge self-assessment: coder answers 3 questions before pushing — does every spec requirement have code, what am I least confident about, what would TL flag. Catches empty PRs at source.

Now I have all the ground truth. The original spec from git commit 1a4587e has Impact and What Changed sections but uses wrong task header format. Let me produce the complete corrected spec:
    
    
    
    
    F032: Agent-as-Judge Self-Assessment
    
    Version: 1.1.0 | Status: Done (spec-after-code) | Confidence: High
    
    1. Executive Summary
    
    F032 adds a self-assessment checkpoint to the coder phase: before pushing code, the coder must answer 3 questions about their own implementation. This is a behavioral intervention — the questions force the coder to re-read the spec, identify weak spots, and anticipate what the Tech Lead would flag. No new parsing or gate logic — ~16 LOC of prompt text injected into pipeline.py. Implementation is complete and merged (PR #69, commit 1a4587e). 
    
    A post-hoc check already exists in the vet phase (commit 3277c93: "verify coder produced source changes at depth=vet") — it blocks PRs with no source code. F032 is the PREVENTIVE upstream companion: catch empty/incomplete PRs at source before push, not after.
    
    2. Constitution Check
    
    Axiom: Solves user's own pain?
    Status: ✅ YES
    Evidence: Empty PRs waste TL review time. Self-reflection catches them
      before push.
    ────────────────────────────────────────
    Axiom: Weekend-buildable?
    Status: ✅ YES
    Evidence: ~16 LOC in one file, one test file.
    ────────────────────────────────────────
    Axiom: Evidence people will pay?
    Status: N/A
    Evidence: Internal tool improvement.
    ────────────────────────────────────────
    Axiom: Boring, proven tech stack?
    Status: ✅ YES
    Evidence: Python string modification, no new dependencies.
    ────────────────────────────────────────
    Axiom: Avoids AI hype categories?
    Status: ✅ YES
    Evidence: Not "AI-powered" — it's a prompt engineering technique for an
      existing pipeline.
    
    No constitutional violations.
    
    3. Ponytail Guard — Pre-Spec Review
    
    - Feature: Agent-as-Judge self-assessment
    - Rung: 7 — minimum that works (prompt-only injection)
    - Existing solution: Post-hoc vet check (commit 3277c93) catches empty PRs after push. F032 complements it with a PREVENTIVE upstream check.
    - Spec needed: Yes — but minimal. Only the coder prompt string changes.
    
    4. Impact
    
    Actual change grounded in git diff (commit 1a4587e):
    
    
    pipeline.py (+16/-0)           — run_phase2_coder() prompt string, lines 1024-1039
    tests/test_f032_self_assessment.py (+275/-0)   — 4 test functions
    
    
    Zero downstream effects. No new imports, no new dependencies, no API changes. The self-assessment answers appear in the coder output log but are not parsed by the panel. Single file touched in production code — prompt string injection between the CRITICAL RULES block and the "Report:" tag.
    
    No other files depend on the modified prompt section — the coder prompt string is self-contained within run_phase2_coder() and is not imported or referenced elsewhere.
    
    5. What Changed
    
    - pipeline.py (+16): Injected SELF-ASSESSMENT block into the coder prompt in run_phase2_coder(), between the CRITICAL RULES section and the "Report:" tag. The block contains: header "SELF-ASSESSMENT (Agent-as-Judge)", Q1 (SPEC COVERAGE), Q2 (CONFIDENCE), Q3 (TL PREDICTION), and "Answer all 3 questions before running git push." Each question includes guidance on what to write and what "all clear" looks like.
    - tests/test_f032_self_assessment.py (new, +275): Four tests: test_coder_prompt_contains_self_assessment (Q1/Q2/Q3 present in normal mode), test_coder_prompt_self_assessment_before_report (block appears before Report: tag), test_fix_mode_prompt_does_not_contain_self_assessment (absent in fix mode), test_self_assessment_block_is_not_empty (meaningful text, not just headers). Uses mocked spawn_agent to capture and inspect the actual prompt string constructed by run_phase2_coder().
    
    6. Feature Breakdown
    
    Task 1: Inject self-assessment questions into coder prompt string
    Files: pipeline.py
    Dependencies: [none]
    Parallelizable: no
    Description: In run_phase2_coder(), add the SELF-ASSESSMENT block between the CRITICAL RULES section and the "Report:" tag. The block contains 3 questions (Q1: SPEC COVERAGE, Q2: CONFIDENCE, Q3: TL PREDICTION) with guidance text. The block is additive only — no existing prompt text is removed. Estimated LOC: ~16.
    
    Task 2: Write prompt verification tests
    Files: tests/test_f032_self_assessment.py
    Dependencies: [Task 1]
    Parallelizable: no
    Description: Create test file with 4 test functions: (1) verify normal-mode coder prompt contains Q1/Q2/Q3 headers and "Before pushing" context, (2) verify self-assessment block appears before the "Report:" tag, (3) verify fix-mode prompt does NOT contain self-assessment questions, (4) verify the block has meaningful content (>100 chars, references spec requirements and TL). Use mocked spawn_agent to capture prompt strings. Estimated LOC: ~275.
    
    7. Data Model
    
    No new entities. No persistence. The self-assessment questions are prompt text only. Coder answers appear in OUTPUT_LOG as part of the coder's normal output stream — no structured parsing.
    
    8. API Routes
    
    N/A — no API changes. Backend pipeline change only.
    
    9. Component Tree
    
    N/A — backend pipeline change only. No UI.
    
    10. COTS Build-vs-Buy
    
    Component: Self-assessment prompt
    Decision: Build
    Justification: One string in an existing Python module. No library or
      service needed.
    ────────────────────────────────────────
    Component: Answer parsing
    Decision: NOT building
    Justification: Out of scope. The questions themselves are the intervention
      — coder reflection is the behavioral change.
    
    11. Test Plan (MANDATORY)
    
    Feature Area: Coder prompt contains self-assessment (normal mode)
    
    - Happy path: run_phase2_coder(mode="vet") constructs prompt containing "SELF-ASSESSMENT", "Q1: SPEC COVERAGE", "Q2: CONFIDENCE", "Q3: TL PREDICTION", "Before pushing". All substrings present in captured prompt.
    - Edge cases: Prompt length increase does not break model context limits (~16 lines added to ~75-line prompt). Self-assessment text is additive — no existing prompt sections removed.
    - Failure modes: Python string concatenation error → caught by python3 -m py_compile pipeline.py. Wrong indentation → compile error. Missing closing quote → compile error.
    - Contract invariants: Self-assessment block appears exactly once in normal coder path. Block comes AFTER CRITICAL RULES, BEFORE "Report:". No existing prompt behavior removed or altered.
    
    Feature Area: Fix mode exempt from self-assessment
    
    - Happy path: run_phase2_coder(mode="fix") constructs prompt without "SELF-ASSESSMENT" or Q1/Q2/Q3 strings.
    - Edge cases: Fix mode prompt structure is different from normal mode — confirm the self-assessment injection point is guarded by mode check. What if mode="fix" but somehow passes through the normal code path? → Verified: early return in prompt construction prevents this.
    - Failure modes: Accidental injection into fix prompt → test fails (assert NOT in prompt). Fix mode identified by mode=="fix" check.
    - Contract invariants: Fix mode coder prompt NEVER contains self-assessment questions. Normal mode coder prompt ALWAYS contains them.
    
    Feature Area: Block ordering and content quality
    
    - Happy path: SELF-ASSESSMENT block appears before "Report: both commit hashes" tag. Block length >100 chars. Block references "spec requirement" or "implementation" and "Tech Lead" or "TL".
    - Edge cases: What if the prompt string is reformatted (whitespace changes)? → substring assertions are resilient to formatting. What if the coder model strips SELF-ASSESSMENT from output? → The test checks the panel's prompt construction, not model output.
    - Failure modes: Block appears after Report: tag → test fails on index comparison. Block is only headers with no detail text → test fails on length/content assertions.
    - Contract invariants: sa_idx < report_idx always. Block content >100 chars always.
    
    12. Panel Split
    
    Single sequential wave — Task 2 depends on Task 1 (test file verifies prompt constructed by Task 1's code). One coder agent.
    
    
    Wave 1: [Task 1] → Wave 2: [Task 2]
    
    
    13. Build & Deploy
    
    - Build: python3 -c "compile(open('pipeline.py').read(), 'pipeline.py', 'exec')"
    - Lint: python3 -m py_compile pipeline.py
    - New tests: python3 -m pytest tests/test_f032_self_assessment.py -v
    - Full suite: python3 -m pytest tests/ -q (679 tests must pass)
    - No env vars, no deployment steps, no new dependencies.
    
    14. Risk Register
    
    #: 1
    Risk: Prompt bloat — model ignores new section
    Severity: LOW
    Mitigation: Questions are at the end, just before push, in the critical
      path. Models reliably follow terminal instructions.
    Trigger: Coder pushes without answering questions
    ────────────────────────────────────────
    #: 2
    Risk: Self-assessment adds LLM tokens but no behavioral change
    Severity: LOW
    Mitigation: Questions are adversarial by design — "what would TL flag?"
      forces reflection. Even "nothing" required thinking.
    Trigger: No change in empty-PR rate after 5+ pipeline runs
    ────────────────────────────────────────
    #: 3
    Risk: Fix mode coder accidentally gets self-assessment
    Severity: LOW
    Mitigation: Guarded by mode=="fix" in prompt construction. Test verifies.
    Trigger: Fix-mode coder output includes Q1/Q2/Q3
    ────────────────────────────────────────
    #: 4
    Risk: Coder hallucinates "all covered" without checking spec
    Severity: MEDIUM
    Mitigation: Q1 explicitly says "List any spec requirement that has NO
      implementation yet" — forces enumeration. Vet phase post-hoc check
      catches lies.
    Trigger: Vet phase BLOCKS PR that self-assessed as "all covered"
    
    15. Anti-Creep
    
    Explicitly OUT OF SCOPE:
    - NO answer parsing, structured JSON extraction, or gate logic that blocks push based on answers. The questions are the intervention.
    - NO dashboard or metrics for self-assessment quality. Answers live in OUTPUT_LOG.
    - NO fix-mode self-assessment. Fix mode prompt has different structure.
    - NO parallel coder worktree self-assessment. Worktrees use spawn_coder_in_worktree() with own prompt in tasks.py.
    - NO modification to tasks.py, agent.py, utils.py, scripts/vet, scripts/nm, status.py, roadmap.py.
    
    16. Design Detail: Self-Assessment Prompt Text
    
    The exact text injected (pipeline.py lines 1024-1039):
    
    
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
    
    
    Injection point: After the CRITICAL RULES block (after "DO NOT refactor code beyond what the task requires..."), before the "Report: both commit hashes" line. Position verified by test_f032: sa_idx < report_idx assertion.
    
    17. Sign-Off Checklist
    
    - [x] Prompt text reviewed for clarity
    - [x] Injection point does not break existing prompt flow (position confirmed: after CRITICAL RULES, before Report:)
    - [x] Fix mode path confirmed unaffected (test_fix_mode_prompt_does_not_contain_self_assessment)
    - [x] Test verifies Q1, Q2, Q3 present in normal mode (test_coder_prompt_contains_self_assessment)
    - [x] Test verifies block appears before Report: tag (test_coder_prompt_self_assessment_before_report)
    - [x] Test verifies block content is meaningful, not empty headers (test_self_assessment_block_is_not_empty)
    - [x] Full test suite passes (679 tests)
    - [x] python3 -m py_compile pipeline.py succeeds
    - [x] Code review: prompt text is additive only, no logic changes
    - [x] PR merged (#69, commit 1a4587e)
    - [x] Roadmap updated: F032 marked In Progress
    - [ ] Roadmap: F032 marked Done (pending final sign-off)