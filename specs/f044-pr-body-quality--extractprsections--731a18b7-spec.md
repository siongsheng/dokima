# F044: PR body quality — `extract_pr_sections()` currently dumps the strategist's full spec into Why/Impact instead of extracting concise summaries. Fix: trim Why to first 2 sentences (max 200 chars), Impact to product-value-only (strip meta-commentary and internal thinking), strip nm Review of shell commands and reasoning noise.

Now I have full context. Let me produce the corrected spec.
    
    Ponytail Guard — Pre-Spec Review:
    - Feature: F044 PR body quality — trim extract_pr_sections output
    - Rung: 6 — One-line fixes insufficient, existing extraction logic works but needs trimming/filtering layered on
    - Existing solution: extract_pr_sections() already parses Why/Impact/What Changed. _extract_nm_summary() already extracts nm findings. Both just dump raw text — needs filtering.
    - Spec needed: yes
    - Spec scope: Add 3-4 helpers + wire them into existing functions. Tests for all new behavior.
    
    
    F044: PR Body Quality — Trim extract_pr_sections() Output
    
    Executive Summary
    
    extract_pr_sections() currently dumps the strategist's full spec into PR body
    Why/Impact sections, producing walls of text that bury the signal. F044 adds
    sentence-boundary-aware trimming (Why = first 2 sentences, max 200 chars),
    product-value-only Impact filtering (strips meta-commentary, strategist
    thinking, model sign-off chatter), and nm Review noise stripping (removes shell
    commands, reasoning noise, terminal output). All changes confined to
    spec_extract.py and its test file. No new dependencies. (High confidence)
    
    Constitution Check
    
    Axiom: Solves user's own pain
    Status: ✅
    Notes: Shaun reviews PRs — wall-of-text Why/Impact is his daily annoyance
    ────────────────────────────────────────
    Axiom: Weekend-buildable
    Status: ✅
    Notes: ~200 LOC total, 3 sequential tasks, ~1 hour
    ────────────────────────────────────────
    Axiom: Evidence people will pay
    Status: N/A
    Notes: Internal tool, not SaaS
    ────────────────────────────────────────
    Axiom: Tech stack boring/proven
    Status: ✅
    Notes: Python regex + string ops, no new deps
    ────────────────────────────────────────
    Axiom: Avoids AI hype
    Status: ✅
    Notes: Pure text processing, no AI involved
    
    Impact Assessment
    
    Affected by this change:
    - spec_extract.py — extract_pr_sections() (+3 helpers, ~120 LOC changed net)
    - spec_extract.py — _extract_nm_summary() (+1 helper, ~30 LOC changed net)
    - tests/test_spec_extract.py — new test methods (+~100 LOC)
    - tests/test_f038_nm_injection.py — may need nm output fixture updates if noise patterns change extraction behavior
    
    Downstream dependents (callers of extract_pr_sections, verified via rg):
    - pipeline.py lines 2314, 2462, 2602 — PR body assembly. These pass raw spec text in, get formatted markdown back. The format stays backward-compatible — same ## Why / ## Impact / ## What Changed structure, just cleaner content.
    - spec_extract.py line 237 — _check_pr_body_quality() uses extract_pr_sections internally to detect thin fallback. The trim change may affect detection thresholds — must verify.
    
    Internal helpers added:
    - _trim_to_sentences(text, max_sentences, max_chars) — sentence-boundary-aware truncation
    - _filter_impact_product_only(text) — strips meta-commentary from Impact text
    - _strip_nm_noise(text) — removes shell commands and reasoning noise from nm output
    
    Constraints honored:
    - No new external dependencies (stdlib only)
    - Backward-compatible return format (same ## section structure)
    - No changes to panel scheduling or pipeline orchestration
    - Must pass existing test suite: python3 -m pytest tests/test_spec_extract.py tests/test_f038_nm_injection.py -q
    
    What Changed
    
    - extract_pr_sections(): Why trimmed to first 2 sentences (max 200 chars). Impact filtered to product-value-only — meta-commentary, strategist internal thinking, and model sign-off chatter stripped. Position: legacy fallback also trimmed.
    - _extract_nm_summary(): key_findings text filtered through _strip_nm_noise() — removes shell commands, reasoning preamble, terminal output blocks. Risk and auto-fix detection unchanged.
    - _trim_to_sentences(): New helper. Splits on . , ! , ?  sentence boundaries. Handles abbreviation edge cases (Dr., Mr., Inc., etc. — does NOT split on these).
    - _filter_impact_product_only(): New helper. Pattern-based removal of meta-commentary phrases, strategist instruction echoes ("Here is the COMPLETE corrected spec", "Write a spec for F044"), model sign-off lines ("The spec is ready", "Do you want me to proceed", "Shall I implement this"), and ponytail guard verdicts.
    - _strip_nm_noise(): New helper. Removes shell command blocks ( , $ command), reasoning noise ("Let me think", "I should check", "The code looks fine but"), terminal output (lines starting with √, ✗, ✓ preceded by ANSI), and multi-line "You are running" boilerplate already handled by existing filter.
    
    Feature Breakdown
    
    Task 1: Add _trim_to_sentences and _filter_impact_product_only helpers + wire into extract_pr_sections()
    Files: spec_extract.py
    Dependencies: none
    Parallelizable: no
    Description: Add two new helpers to spec_extract.py: (1) _trim_to_sentences(text, max_sentences=2, max_chars=200) — splits on sentence-ending punctuation followed by space, preserves abbreviations (Dr., Mr., Inc., i.e., e.g., etc.), enforces max character cap with ellipsis; (2) _filter_impact_product_only(text) — strips meta-commentary phrases ("the spec was a skeleton", "Here is the COMPLETE corrected spec", "Write a spec for"), model sign-off lines matching chatter_patterns from clean_spec_content, and ponytail guard verdict blocks. Wire both into extract_pr_sections(): apply _trim_to_sentences() to Why text (both the Position: match and the feature description fallback), apply _filter_impact_product_only() to Impact text (all four fallback paths). Existing Position: truncation at 400 chars replaced by sentence-aware 200-char cap. No change to What Changed extraction or thin-fallback logic.
    
    Task 2: Add _strip_nm_noise helper + wire into _extract_nm_summary()
    Files: spec_extract.py
    Dependencies: Task 1
    Parallelizable: no
    Description: Add _strip_nm_noise(text) helper to spec_extract.py. Removes: (a) shell command blocks — triple-backtick fenced code blocks containing shell commands, and lines starting with $ ; (b) reasoning noise — lines matching "Let me think", "I should", "Looking at", "Let me check", "The code looks", "I can see", "This is because", "First, let me", "Now I need to"; (c) terminal output — ANSI escape sequences, lines starting with ✓/✗/√ preceded by whitespace-only context; (d) mid-text "You are running" / "STAGE N" boilerplate (supplements existing content_start filter which only handles line-start). Wire into _extract_nm_summary(): apply _strip_nm_noise() to the assembled key_findings text after the existing content_start collection loop, before the char_count truncation. Risk extraction, auto-fix detection, and SHOULD FIX extraction are NOT filtered — those operate on raw text and must see all content.
    
    Task 3: Add tests for trimmed PR body output and nm noise stripping
    Files: tests/test_spec_extract.py
    Dependencies: Task 2
    Parallelizable: no
    Description: Add test methods to TestSpecExtractFunctions class in test_spec_extract.py: (a) test_trim_to_sentences_two — verifies 3-sentence text → 2 sentences retained; (b) test_trim_to_sentences_char_cap — verifies text truncated at 200 chars with "..." appended; (c) test_trim_to_sentences_abbreviations — Dr., Mr., Inc., i.e., e.g. don't split; (d) test_filter_impact_strips_meta — "Here is the COMPLETE corrected spec" removed from Impact; (e) test_filter_impact_strips_chatter — model sign-off lines ("Do you want me to proceed?") removed; (f) test_filter_impact_preserves_product — "This reduces PR body noise by 80%" preserved; (g) test_extract_pr_sections_trimmed_why — end-to-end: spec with 5-sentence Position → Why has 2 sentences max 200 chars; (h) test_extract_pr_sections_clean_impact — Impact from full spec has meta-commentary stripped; (i) test_strip_nm_noise_shell_commands — "$ npm test" removed; (j) test_strip_nm_noise_reasoning — "Let me think about this" removed; (k) test_strip_nm_noise_preserves_findings — "RISK: HIGH" and "Missing error handling in utils.py:42" preserved; (l) test_extract_nm_summary_noise_stripped — _extract_nm_summary key_findings is clean after filtering. Run test suite: python3 -m pytest tests/test_spec_extract.py tests/test_f038_nm_injection.py -q.
    
    Data Model
    
    No new persistent entities. Function signatures:
    
    
    _truncate_to_sentences(text: str, max_sentences: int = 2, max_chars: int = 200) -> str
      Returns: trimmed string, with "..." appended if truncated
    
    _filter_impact_product_only(text: str) -> str
      Returns: text with meta-commentary/chatter lines removed
    
    _strip_nm_noise(text: str) -> str
      Returns: text with shell commands, reasoning noise, terminal output removed
    
    
    Existing return shapes preserved:
    - extract_pr_sections() → same markdown format (## Why\n\n...\n\n## Impact\n\n...\n\n## What Changed\n...), cleaner content
    - _extract_nm_summary() → same dict shape, key_findings field now noise-stripped
    
    Test Plan
    
    Happy Path
    - Spec with 5-sentence Why/Impact → PR body has 2-sentence Why, clean Impact, bullet What Changed. nm output with shell commands → key_findings has only risk assessment text.
    
    Edge Cases
    - Empty Impact section: filter_impact returns empty string → Impact section omits (no "## Impact" header in output — current behavior preserved)
    - Single-sentence Why: ≤ 200 chars → returned as-is, no ellipsis
    - Why exactly 200 chars: no ellipsis appended (under cap)
    - Why 201 chars: truncated at last sentence boundary before 200, ellipsis appended
    - No sentence boundaries found: fall back to simple 200-char truncation with ellipsis
    - Position: match with no periods: treated as single sentence, truncated at 200 chars
    - Impact all meta-commentary: after filtering, text empty → section omitted (fallback chain proceeds to next pattern)
    - nm output empty: _strip_nm_noise returns empty string (no-op on empty input)
    - nm output has ANSI codes mid-text: stripped, surrounding text preserved
    - Reasoning noise embedded in finding text: line is removed entirely, not partially
    - Abbreviations at end of sentence: "Visit Dr. Smith then" → splits correctly after "Smith" not "Dr"
    
    Failure Modes
    - Regex ReDoS: Large input (50K chars) with pathological patterns → timeout guard. Verify < 10ms for 37K char nm output (current max)
    - Unicode sentence boundaries: Chinese/Japanese 。and ！→ existing . ` split won't match, falls through to char-cap truncation. Acceptable — strategist specs are English
    - Backward compat break: Existing caller expects long Why text → mitigated: signature unchanged, PR body assembly code unchanged
    
    Contract Invariants
    - extract_pr_sections() always returns text containing ## Why — never None or empty
    - _extract_nm_summary() always returns a dict with all 5 keys — even on error
    - No new imports beyond re (already imported in spec_extract.py)
    - Test suite must pass: python3 -m pytest tests/ -q — 1033 tests
    
    Risk Register
    
    #: R1
    Risk: Sentence-boundary regex misses abbreviations → truncated mid-word
    Severity: LOW
    Mitigation: Abbreviation skip-list tested explicitly in Task 3
    Trigger: Test failure in test_trim_to_sentences_abbreviations
    ────────────────────────────────────────
    #: R2
    Risk: _filter_impact_product_only over-strips → Impact section goes empty
      when it had real content
    Severity: MEDIUM
    Mitigation: Conservative pattern matching — only strip known
      meta-commentary phrases, not aggressive heuristics
    Trigger: Impact section disappears from PR body
    ────────────────────────────────────────
    #: R3
    Risk: _strip_nm_noise removes actual findings that resemble reasoning
    Severity: MEDIUM
    Mitigation: Patterns target sentence-initial reasoning, not embedded
      phrases. Test j covers this explicitly
    Trigger: Key nm finding disappears from PR
    ────────────────────────────────────────
    #: R4
    Risk: _check_pr_body_quality threshold breaks
    Severity: LOW
    Mitigation: Threshold is 100 chars for "thin fallback" — trimmed output
      should still exceed this for real specs
    Trigger: PR body quality gate flags false positive
    ────────────────────────────────────────
    #: R5
    Risk: Existing tests depend on exact nm output format
    Severity: LOW
    Mitigation: Run full suite before merge. Only key_findings field changes —
      structural assertions unchanged
    Trigger: test_f038_nm_injection.py failures
    
    Anti-Creep
    
    Features explicitly NOT in scope:
    - No Impact summarization via LLM — text trimming only, no AI summarization
    - No changes to What Changed extraction — bullets work fine, leave them
    - No changes to TL Review formatting — _build_tl_review_body untouched
    - No changes to PR body assembly in pipeline.py — only the content extracted by extract_pr_sections and _extract_nm_summary changes
    - No new config knobs — trim thresholds (200 chars, 2 sentences) are constants, not configurable
    - No multi-language sentence detection — English-only punctuation boundaries
    - No nm output caching or persistence changes
    
    Sign-Off Checklist
    
    - [ ] _trim_to_sentences preserves abbreviations (Dr., Mr., Inc., i.e., e.g., etc.)
    - [ ] _filter_impact_product_only strips "Here is the COMPLETE corrected spec" from a real spec excerpt
    - [ ] _filter_impact_product_only strips model sign-off lines but preserves "This fixes a race condition in"
    - [ ] _strip_nm_noise removes $ npm test and triple-backtick shell blocks
    - [ ] _strip_nm_noise removes "Let me think about this approach" but preserves "RISK: HIGH"
    - [ ] extract_pr_sections() still returns ## Why → ## Impact → ## What Changed structure
    - [ ] PR body from a real spec (e.g., f043 spec) is readable end-to-end without strategist walls
    - [ ] python3 -m pytest tests/test_spec_extract.py tests/test_f038_nm_injection.py -q — all pass
    - [ ] python3 -m pytest tests/ -q — full suite passes (1033 tests)
    - [ ] _check_pr_body_quality does not false-positive on trimmed output
    - [ ] No new Python warnings from python3 -m py_compile spec_extract.py
    - [ ] python3 -c "from spec_extract import _trim_to_sentences, _filter_impact_product_only, _strip_nm_noise" succeeds