# Task Breakdown: F005: Model Family Fallback

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
