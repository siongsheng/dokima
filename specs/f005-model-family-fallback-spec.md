# F005: Model Family Fallback

Now I have full understanding of the architecture. Let me write the complete corrected spec for F005. The key insight: spawn_agent() at line 149 currently ignores the return code — it returns all output regardless of failure. Provider failures produce error text in stderr that goes undetected. The fix is straightforward.
    
    Here is the COMPLETE corrected spec:
    
    
    
    F005: Model Family Fallback — Spec
    
    Version: 1.0.0 | Date: 2026-06-28 | Status: Awaiting Implementation
    Confidence: High | Impact: MEDIUM
    
    1. Executive Summary
    
    When DeepSeek (primary provider) is down or rate-limited, Dokima pipelines fail silently — spawn_agent returns error text as if it were valid output, and downstream phases proceed with garbage. F005 adds provider fallback so the panel detects the failure, retries with a configured alternative, and logs the event. This is the last missing resilience primitive before the panel is safe to run unattended.
    
    2. Constitution Check
    
    - Solves user's own pain? YES — Shaun's DeepSeek provider has had outages; pipelines stall until manual intervention.
    - Weekend-buildable? YES — ~80 lines in spawn_agent, ~100 lines of env-var parsing, ~120 lines of tests.
    - Evidence people will pay? N/A — infrastructure resilience for the panel itself, not a SaaS feature.
    - Tech stack boring and proven? YES — pure Python env-var parsing + retry logic. No new dependencies.
    - Avoids AI hype categories? YES — deterministic retry logic, not AI.
    
    3. Ponytail Guard — Pre-Spec Review
    
    
    Ponytail Guard — Pre-Spec Review
    Feature: F005: Model Family Fallback
    Rung: 5 — installed dependency (hermes CLI) can retry with different providers; we need ~80 lines of wrapper logic
    Existing solution: spawn_agent already accepts model parameter (line 149) but doesn't retry on failure
    Spec needed: Yes
    Spec scope: Add fallback detection + retry loop inside spawn_agent, env-var config, log event
    
    
    4. Decision Table
    
    Option: A: Per-call-site retry (modify every spawn_agent call site)
    Resilience: Full
    Complexity: High — 12+ call sites to patch
    Cost: Maintenance burden
    Verdict: Reject
    ────────────────────────────────────────
    Option: B: Panel-level wrapper (wrap spawn_agent in new function)
    Resilience: Full
    Complexity: Medium — new function, all callers updated
    Cost: Migration churn
    Verdict: Reject
    ────────────────────────────────────────
    Option: C: Internal retry inside spawn_agent itself
    Resilience: Full
    Complexity: Low — one function, one env var read, one retry
    Cost: Zero call-site changes
    Verdict: Accept
    ────────────────────────────────────────
    Option: D: Hermes-level fallback (configure in hermes profiles)
    Resilience: Partial — depends on hermes features
    Complexity: Very low
    Cost: Panel can't control it
    Verdict: Reject
    
    Rationale: Option C is a drop-in fix. spawn_agent already accepts model — we add fallback detection (parse stderr for known failure patterns) and one automatic retry with a different provider/model. All 12+ call sites benefit without modification.
    
    5. Impact
    
    Panel operators get automatic recovery from provider outages — no manual restart needed. Pipelines that would have silently consumed error output now retry with a working provider. Operators see a ⚠ FALLBACK log line so they know the event occurred.
    
    6. What Changed
    
    - dokima (MODIFIED — spawn_agent function, line 149): Add fallback detection + retry logic. Parse stderr for provider failure patterns, retry with PANEL_FALLBACK_MODEL if configured.
    - dokima (MODIFIED — top-level constants, near line 19): Add FALLBACK_MODEL env-var read at module init.
    - tests/test_f005_fallback.py (NEW): Unit tests for fallback detection, retry trigger, retry suppression (don't infinite-loop), env-var parsing.
    - specs/conventions.md (MODIFIED): Document PANEL_FALLBACK_MODEL env var and fallback behavior.
    
    7. Confidence + Impact Markers
    
    Confidence: High — the retry pattern is trivial; the only risk is false-positive failure detection matching valid output.
    Impact: MEDIUM — affects all pipeline phases, but failure mode is graceful (proceeds with original output if fallback also fails).
    
    8. API/Interface Proposal
    
    New environment variable:
    
    PANEL_FALLBACK_MODEL=openrouter/anthropic/claude-sonnet-4
    
    Format: provider/model_name (same format spawn_agent already parses at line 154). If unset, fallback is disabled — current behavior preserved.
    
    9. Security Considerations
    
    N/A — env-var read only. No new network surfaces, no credential handling changes, no injection vectors. Fallback model string is passed directly to hermes CLI via list args (already shell-safe).
    
    10. Documentation Impact
    
    specs/conventions.md: Add "Model Fallback" section documenting PANEL_FALLBACK_MODEL env var, failure detection patterns, and retry behavior.
    
    11. Data Model
    
    No persistent state. Transient: FALLBACK_MODEL string loaded from env at module init (cached in global). Per-invocation: boolean fallback_used flag logged to stderr.
    
    12. Task Breakdown
    
    ### Task 1: Add FALLBACK_MODEL env-var constant
    **Files:** dokima
    **Dependencies:** [none]
    **Description:** Read PANEL_FALLBACK_MODEL from env at module init, store as FALLBACK_MODEL global near line 19.
    
    ### Task 2: Add provider failure detection helper
    **Files:** dokima
    **Dependencies:** [none]
    **Description:** Create _detect_provider_failure(output) that scans combined stdout+stderr for patterns: "rate limit", "503", "Service Unavailable", "provider.error", "model.not.*found", "connection refused". Returns True on match.
    
    ### Task 3: Add fallback retry logic to spawn_agent
    **Files:** dokima
    **Dependencies:** [Task 1, Task 2]
    **Description:** After the existing proc.wait() loop (line 188), if FALLBACK_MODEL is set and _detect_provider_failure(result) is True: print ⚠ FALLBACK: retrying with {FALLBACK_MODEL}, re-invoke the same hermes command with --provider and -m flags from FALLBACK_MODEL, return that result instead.
    
    ### Task 4: Write unit tests for fallback detection
    **Files:** tests/test_f005_fallback.py
    **Dependencies:** [Task 2]
    **Description:** Test _detect_provider_failure with known error patterns ("rate limit exceeded", "503 Service Unavailable", "connection refused"), negative cases (valid output, normal agent response), and edge cases (empty string, None).
    
    ### Task 5: Write unit tests for fallback retry
    **Files:** tests/test_f005_fallback.py
    **Dependencies:** [Task 3, Task 4]
    **Description:** Test spawn_agent fallback: mock subprocess.Popen to fail first call (exit 1 + error stderr), succeed second call. Verify fallback was used, verify original error output is NOT returned. Test fallback suppression when PANEL_FALLBACK_MODEL is unset.
    
    ### Task 6: Test fallback does NOT fire on legitimate output
    **Files:** tests/test_f005_fallback.py
    **Dependencies:** [Task 3]
    **Description:** Verify that valid agent output containing words like "error handling" or "rate" does NOT trigger false-positive fallback. Test boundary: output containing "Error: file not found" (legitimate code error, not provider failure).
    
    ### Task 7: Update conventions.md
    **Files:** specs/conventions.md
    **Dependencies:** [Task 3]
    **Description:** Add "Model Fallback" section under conventions.md documenting PANEL_FALLBACK_MODEL, failure patterns detected, retry behavior, and how to verify fallback fired (grep stderr for "⚠ FALLBACK").
    
    13. Panel Split
    
    - Wave 1 (sequential): Task 1 → Task 2 → Task 3 (core logic builds on helpers)
    - Wave 2 (parallel): Task 4, Task 6, Task 7 (tests + docs — independent, touch different files)
    - Wave 3 (sequential): Task 5 (depends on core logic being complete)
    
    Total: 3 waves, 2-3 coders max.
    
    14. Build & Deploy
    
    No deployment changes. CI already runs python3 -m pytest tests/ -q. After merge: git push origin main. No env vars required — fallback is opt-in (if PANEL_FALLBACK_MODEL is unset, behavior is unchanged).
    
    15. Risk Register
    
    #: R1
    Risk: False-positive failure detection matches valid output
    Severity: MEDIUM
    Mitigation: Tight regex patterns, negative test cases (Task 6),
      prefix-anchored patterns
    Trigger: "error" appears in legitimate agent output
    ────────────────────────────────────────
    #: R2
    Risk: Fallback provider also down → double failure
    Severity: LOW
    Mitigation: Fallback is one-shot — return original error if fallback also
      fails; don't loop
    Trigger: Both providers down simultaneously
    ────────────────────────────────────────
    #: R3
    Risk: Fallback model not installed/configured in hermes
    Severity: MEDIUM
    Mitigation: hermes CLI will produce its own clear error; we return that
      rather than swallowing it
    Trigger: User misconfigures PANEL_FALLBACK_MODEL
    ────────────────────────────────────────
    #: R4
    Risk: Rate-limit cascading: fallback hits same rate limit
    Severity: LOW
    Mitigation: Different provider = different rate limit pool; unlikely to
      hit both
    Trigger: Both providers share infrastructure
    
    16. Anti-Creep
    
    Features explicitly NOT in scope:
    - Per-profile fallback chains (strategist→claude, coder→gemini) — one global fallback suffices for now
    - Multi-level fallback (try A, then B, then C) — YAGNI, one retry is enough
    - Health checks / pre-flight provider validation — adds latency; fail-on-use is simpler
    - Automatic fallback MODEL selection — operator configures it explicitly
    - Provider-specific fallback logic (DeepSeek-specific error codes) — generic pattern matching only
    
    17. Sign-Off Checklist
    
    - [ ] PANEL_FALLBACK_MODEL env var name and format approved
    - [ ] Failure detection patterns reviewed (no false positives on real agent output)
    - [ ] Fallback behavior: one retry, not infinite loop — confirmed
    - [ ] Fallback log message format approved (⚠ FALLBACK: ...)
    - [ ] Tests cover: detection true positive, detection true negative, retry success, retry suppression when unset
    - [ ] No call-site changes needed — spawn_agent signature unchanged for existing callers
    - [ ] conventions.md update reviewed
    - [ ] CI passes: python3 -m pytest tests/ -q
    - [ ] Manual test: set PANEL_FALLBACK_MODEL to invalid provider, verify error is returned (not swallowed)
    - [ ] Manual test: set PANEL_FALLBACK_MODEL to valid alternative, simulate primary failure, verify fallback works
    
    
    
    Summary: 7 tasks, ~180 LOC, 3 waves. Drop-in fix — zero call-site changes. Opt-in via single env var. Preserves all existing behavior when unset.
