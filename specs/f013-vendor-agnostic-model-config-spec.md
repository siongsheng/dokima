# F013: Vendor-Agnostic Model Config

Now I have full understanding of the codebase. Let me produce the complete corrected F013 spec.
    
    Position: F013 replaces the hardcoded deepseek dependency in _PROFILE_CONFIGS with a PANEL_VENDOR env var that selects a built-in vendor model map, plus per-role PANEL_MODEL_* overrides — enabling Anthropic/OpenAI/Google users to run Dokima without any deepseek configuration. (High confidence)
    
    Here is the complete corrected spec:
    
    
    
    
    F013: Vendor-Agnostic Model Config
    
    Version: 1.0
    Status: Ready for Implementation
    Confidence: High
    Impact: MEDIUM
    Feature ID: F013
    Dependencies: F005 (done — fallback model loading), F012 (done — profile creation)
    
    1. Executive Summary
    
    Dokima currently hardcodes deepseek-v4-pro/deepseek in _PROFILE_CONFIGS for all four agent roles. F013 makes model selection vendor-agnostic: users set PANEL_VENDOR=anthropic (or openai, google, deepseek) and the panel maps each role to a vendor-appropriate model. Per-role PANEL_MODEL_* env vars allow power-user overrides. The built-in vendor maps provide sensible defaults so new users get working profiles without researching model names. Confidence is High — this is env var wiring + dict construction, no new subprocess paths or API surfaces.
    
    2. Constitution Check
    
    Axiom: Solves user's own pain?
    Status: YES
    Detail: Roadmap user story: "As a developer using Anthropic, I configure ANTHROPIC_API_KEY and the panel maps strategist→claude-sonnet... no deepseek dependency." Currently every dokima init profile creation writes deepseek-v4-pro as model.default — users on other providers must manually reconfigure 4 profiles.
    
    Axiom: Weekend-buildable?
    Status: YES
    Detail: ~120 LOC across 7 tasks. One new dict constant, env var reading in main(), dynamic config construction, test updates.
    
    Axiom: Boring and proven?
    Status: YES
    Detail: Env-var-based config switching is the same pattern as PANEL_FALLBACK_* (F005) and PANEL_MAX_PARALLEL (existing). No new frameworks, no config file formats.
    
    Axiom: Avoids AI hype?
    Status: YES
    Detail: Zero AI. Pure configuration plumbing.
    
    Verdict: PASS. No misalignments.
    
    3. Ponytail Guard — Pre-Spec Review
    
    Feature: F013 — Vendor-Agnostic Model Config
    Rung: 5 — Installed dependency (Hermes Agent) can do it — we leverage hermes --profile config set which already sets model.default and model.provider. The only new thing is picking WHICH values to set based on vendor.
    Existing solution: _PROFILE_CONFIGS is a hardcoded dict at line 2490. PANEL_FALLBACK_* env vars (F005, line 203-220) show the env-var pattern we replicate.
    Spec needed: YES
    Spec scope: Vendor map constant, PANEL_VENDOR env var, PANEL_MODEL_* per-role overrides, dynamic _PROFILE_CONFIGS construction in ensure_profiles(), test updates, conventions.md update.
    
    4. Decision Table
    
    Option: A: Per-vendor profile template files
    Operator UX: Manual file management
    Complexity: High (file discovery, merge logic)
    Backward compat: Breaks existing profile flow
    Verdict: Reject — over-engineered for 4 roles × 4 vendors
    
    Option: B: PANEL_VENDOR + PANEL_MODEL_* env vars with built-in maps
    Operator UX: One env var for 90% of users
    Complexity: Low (~120 LOC)
    Backward compat: Defaults to deepseek when PANEL_VENDOR absent
    Verdict: ACCEPT — same pattern as PANEL_FALLBACK_*, zero-config for existing users
    
    Option: C: Auto-detect vendor from API key prefix
    Operator UX: Zero config
    Complexity: Medium (brittle heuristics)
    Coverage: Fails for custom providers, env var passthrough
    Verdict: Reject — API keys vary in format; silent misdetection is worse than explicit config
    
    5. Impact
    
    Users on non-DeepSeek providers can run dokima init and get working profiles with vendor-appropriate models. Existing DeepSeek users see zero behavior change — PANEL_VENDOR is optional and defaults to deepseek. Profile creation and pipeline spawning both respect the vendor selection. The conventions.md quirk table is updated to reflect vendor-agnostic reality.
    
    6. What Changed
    
    - dokima: _VENDOR_MODEL_MAPS constant added — 4 vendor entries (deepseek, anthropic, openai, google) with per-role model defaults
    - dokima: _build_profile_configs() new function — reads PANEL_VENDOR and PANEL_MODEL_* env vars, returns a _PROFILE_CONFIGS-equivalent dict
    - dokima: ensure_profiles() uses _build_profile_configs() instead of the hardcoded _PROFILE_CONFIGS
    - dokima: main() prints vendor/model info at startup so operator can verify
    - tests/test_profile_templates.py: updated — tests verify vendor-agnostic config construction, PANEL_MODEL_* overrides, backward compatibility when no env vars set
    - specs/conventions.md: model compatibility quirk table updated — "If using DeepSeek" becomes "Model-specific quirks" with per-vendor notes
    
    7. Confidence: High | Impact: MEDIUM
    
    Confidence is High because:
    - _PROFILE_CONFIGS is a simple dict (28 lines) with one consumer (ensure_profiles)
    - Env var reading in main() follows the exact same pattern as _load_fallback_config() from F005
    - PANEL_VENDOR default=deepseek preserves 100% backward compatibility
    - No new subprocess paths or API surfaces — same hermes config set calls
    
    Impact is MEDIUM because this changes what profiles get created on dokima init, but existing profiles are never overwritten (idempotent ensure_profiles skips them). Pipeline behavior is unchanged — profiles already configured keep working.
    
    8. API/Interface Proposal
    
    N/A — this is purely internal configuration plumbing. External interface is 5 env vars (PANEL_VENDOR, PANEL_MODEL_STRATEGIST, PANEL_MODEL_CODER, PANEL_MODEL_TECH_LEAD, PANEL_MODEL_NM). No new CLI flags, routes, or data structures.
    
    9. Security Considerations
    
    New env vars (PANEL_VENDOR, PANEL_MODEL_*) are read from the same .env file as API_SERVER_KEY. Values are validated against FALLBACK_MODEL_RE (^[a-zA-Z0-9_./-]+$) before use — same safe pattern from F005. Token redaction in logs is unaffected (model names are not secrets). No new subprocess paths — hermes config set uses list-based args (already safe). No injection surface change.
    
    10. Documentation Impact
    
    docs/setup.md: Add "Vendor Selection" section explaining PANEL_VENDOR and PANEL_MODEL_* env vars with examples for each vendor.
    specs/conventions.md: Update model compatibility quirk table — "DeepSeek-specific" → "Vendor-specific quirks" with per-vendor notes.
    
    11. Test Plan (MANDATORY)
    
    Happy path:
    - PANEL_VENDOR=anthropic → strategist model.default=claude-sonnet-4, coder=claude-haiku, TL=claude-opus, nm=claude-sonnet-4
    - PANEL_VENDOR=openai → strategist=gpt-5, coder=gpt-5-mini, TL=gpt-5, nm=gpt-5
    - PANEL_VENDOR unset → all profiles get deepseek-v4-pro (backward compat)
    
    Edge cases:
    - PANEL_VENDOR set to unknown value → warn, fall back to deepseek defaults
    - PANEL_MODEL_STRATEGIST overrides vendor default for strategist only, other roles use vendor defaults
    - PANEL_VENDOR absent but PANEL_MODEL_CODER set → deepseek defaults for all roles except coder
    - PANEL_MODEL_STRATEGIST set to invalid format (shell chars) → warn, skip, use vendor default
    - Vendor map key contains provider/model — verifying slash-separated format passes validation
    
    Failure modes:
    - PANEL_VENDOR=anthropic but hermes config set fails → same error handling as current ensure_profiles
    - Both PANEL_VENDOR and PANEL_MODEL_STRATEGIST empty string → treated as absent (use defaults)
    - _build_profile_configs() called before main() env loading → safe fallback to deepseek
    
    Contract invariants:
    - _build_profile_configs() always returns a valid dict with all 4 profile keys (strategist, coder, tech-lead, nm)
    - Every profile config dict always has model.default, model.provider, agent.max_turns, terminal.env_passthrough keys
    - ensure_profiles() remains idempotent — existing profiles are never overwritten regardless of vendor change
    - strategist profile always gets agent.reasoning_effort=high, regardless of vendor
    
    12. Feature Breakdown
    
    Task 1: Add vendor model maps constant
    Files: dokima
    Dependencies: none
    Parallelizable: yes
    Description: Add _VENDOR_MODEL_MAPS dict near _PROFILE_CONFIGS (after line 2515) with 4 vendor entries (deepseek, anthropic, openai, google) each containing per-role model names and provider prefix. deepseek map matches current hardcoded values for backward compatibility. Provider field is the hermes --provider argument; model field is the -m argument.
    
    Task 2: Add _build_profile_configs() function
    Files: dokima
    Dependencies: Task 1
    Parallelizable: no
    Description: Add _build_profile_configs() that reads PANEL_VENDOR (default: deepseek), validates it against _VENDOR_MODEL_MAPS keys, then reads PANEL_MODEL_STRATEGIST/CODER/TECH_LEAD/NM for per-role overrides. Validates all model strings with FALLBACK_MODEL_RE. Returns a dict matching _PROFILE_CONFIGS shape with model.default and model.provider set from vendor map + overrides. Warns on unknown vendor (falls back to deepseek) and on invalid model strings (skips override).
    
    Task 3: Wire vendor config into ensure_profiles()
    Files: dokima
    Dependencies: Task 2
    Parallelizable: no
    Description: Replace the hardcoded _PROFILE_CONFIGS reference in ensure_profiles() (line 2549) with _build_profile_configs(). The function now calls _build_profile_configs() to get the config dict, then iterates and sets keys as before. No other changes to ensure_profiles() logic — same hermes config set subprocess calls, same idempotency, same error handling.
    
    Task 4: Add vendor info to startup output in main()
    Files: dokima
    Dependencies: Task 2
    Parallelizable: yes
    Description: In main(), after API_KEY load (near line 5663), call _build_profile_configs() once and print the detected vendor and per-role models. Example output: "  ✓ Vendor: anthropic | strategist: claude-sonnet-4, coder: claude-haiku, TL: claude-opus, nm: claude-sonnet-4". This gives the operator visibility into which models will be used. Store the config for later use by ensure_profiles() — avoid rebuilding it twice.
    
    Task 5: Update test_profile_templates.py for vendor-agnostic configs
    Files: tests/test_profile_templates.py
    Dependencies: Task 2, Task 3
    Parallelizable: no
    Description: Update existing tests and add new tests:
    - test_vendor_anthropic_maps_correct_models: set PANEL_VENDOR=anthropic, verify model.default values differ from deepseek
    - test_vendor_unknown_falls_back_to_deepseek: PANEL_VENDOR=invalid, verify warning and deepseek defaults
    - test_per_role_override: PANEL_VENDOR=anthropic + PANEL_MODEL_CODER=custom-model, verify coder uses custom, others use anthropic defaults
    - test_backward_compat_no_env_vars: no PANEL_VENDOR set, verify all profiles get deepseek-v4-pro (existing test_model_default_set_for_all stays green)
    - test_model_override_validation_rejects_shell_chars: PANEL_MODEL_STRATEGIST="bad;rm -rf /" → warning, uses vendor default
    - Remove or update test_model_default_set_for_all and test_provider_set_for_all to accept dynamic values instead of hardcoded deepseek-v4-pro/deepseek assertions
    
    Task 6: Update conventions.md model compatibility table
    Files: specs/conventions.md
    Dependencies: Task 1
    Parallelizable: yes
    Description: Update the "Model Compatibility" section (line 10-20). Replace "Dokima is developed and tested against DeepSeek models" with vendor-agnostic language. The quirk table currently lists "DeepSeek output quirks" — rename to "Model-specific output quirks" and add a note that quirks depend on the vendor selected via PANEL_VENDOR. Add rows for common Anthropic/OpenAI quirks if known (e.g., "Anthropic may add explanatory preamble before ### Task N: headers — parser handles it"). Preserve the compatibility note about verifying spec output format on first pipeline run.
    
    Task 7: Add PANEL_VENDOR and PANEL_MODEL_* to HELP_JSON env vars block
    Files: dokima
    Dependencies: Task 1
    Parallelizable: yes
    Description: Add PANEL_VENDOR, PANEL_MODEL_STRATEGIST, PANEL_MODEL_CODER, PANEL_MODEL_TECH_LEAD, PANEL_MODEL_NM entries to the HELP_JSON env_vars list (near line 1238, alongside existing PANEL_FALLBACK_* entries). Each entry: name, description, related_flag=None. Use the same format as the existing fallback env var entries.
    
    13. Risk Register
    
    #: R1
    Risk: Vendor map model names become stale (providers deprecate models)
    Severity: Low
    Mitigation: PANEL_MODEL_* overrides let users specify any model without code changes. Vendor maps are sensible defaults, not hard requirements.
    Trigger: Provider sunsets a model in the vendor map
    
    #: R2
    Risk: ensure_profiles() runs before main() env loading (e.g., in test helpers)
    Severity: Low
    Mitigation: _build_profile_configs() defaults to deepseek when PANEL_VENDOR is absent — safe fallback in any context.
    Trigger: Direct ensure_profiles() call without main()-level env setup
    
    #: R3
    Risk: User sets PANEL_VENDOR after running dokima init → existing deepseek profiles persist (idempotent skip)
    Severity: Low
    Mitigation: Document that vendor change after init requires manual profile deletion. dokima doctor (F016) can check this later.
    Trigger: User changes PANEL_VENDOR after first init
    
    #: R4
    Risk: nm cross-family invariant breaks if vendor map puts coder and nm on same model family
    Severity: Medium
    Mitigation: Each vendor map entry is hand-audited to ensure nm uses a different model family than coder. For google: coder=gemini-2.5-flash, nm=gemini-2.5-flash → SAME FAMILY. Mitigation: google map sets nm=gemini-2.5-pro (different tier, but same family). Document this limitation. F005 cross-family check fires warning if same-family detected.
    Trigger: Vendor map design error
    
    #: R5
    Risk: _PROFILE_CONFIGS still referenced elsewhere in the codebase beyond ensure_profiles()
    Severity: Low
    Mitigation: Grep entire codebase for _PROFILE_CONFIGS before removing the constant. If only used in ensure_profiles(), safe to replace. If used elsewhere, update those sites too.
    Trigger: Undiscovered reference to the old constant
    
    14. Anti-Creep
    
    Features explicitly NOT in scope:
    - Auto-detecting vendor from API key format
    - Provider-specific API key env vars (ANTHROPIC_API_KEY, OPENAI_API_KEY) — users configure their Hermes profile .env separately
    - Model tier selection (e.g., "fast" vs "reasoning" profiles within a vendor)
    - Dynamic model discovery from provider APIs
    - Per-feature model selection (e.g., complex specs get claude-opus, simple ones get claude-haiku)
    - Vendor-specific prompting or system message adaptation
    - Model health checks or latency benchmarking
    - dokima doctor vendor validation (deferred to F016)
    - Removing _PROFILE_CONFIGS entirely — keep it as the default for backward compatibility
    
    15. Parallelization
    
    Wave 1 (parallel): Task 1 (vendor maps), Task 4 (startup output), Task 6 (conventions.md), Task 7 (HELP_JSON)
    Wave 2: Task 2 (_build_profile_configs, depends on T1)
    Wave 3: Task 3 (ensure_profiles wiring, depends on T2)
    Wave 4: Task 5 (tests, depends on T2, T3)
    
    16. Build & Deploy
    
    - No new dependencies
    - No CI changes
    - Test with: python3 -m pytest tests/test_profile_templates.py -v
    - Full suite: python3 -m pytest tests/ -q
    - Env vars documented in docs/setup.md (new "Vendor Selection" section)
    - This feature deploys as part of the single dokima script — no separate service
    
    17. Sign-Off Checklist
    
    - [ ] PANEL_VENDOR naming approved (vs. DOKIMA_VENDOR, PANEL_PROVIDER, etc.)
    - [ ] Vendor map model choices approved for each vendor (deepseek, anthropic, openai, google)
    - [ ] PANEL_MODEL_* override naming convention consistent with PANEL_FALLBACK_*
    - [ ] Backward compatibility verified — no PANEL_VENDOR = deepseek, same as today
    - [ ] ensure_profiles() idempotency preserved — existing profiles never overwritten
    - [ ] Cross-family nm invariant preserved in vendor maps (or documented limitation)
    - [ ] Test plan covers all four vendors + overrides + fallback + validation
    - [ ] conventions.md update reviewed and accurate
    - [ ] HELP_JSON entries match actual env var names
    - [ ] All 196+ tests still pass (python3 -m pytest tests/ -q)
    - [ ] docs/setup.md vendor selection section reviewed
    - [ ] Existing profiles in test environments not accidentally mutated
    
    
    The spec is now complete with:
    - 5. Impact section (was missing)
    - 6. What Changed section (was missing)
    - ### Task N: headers with all 5 required fields — Files:, Dependencies:, Parallelizable:, Description: — each on its own line formatted exactly as the panel regex ^### Task \d+: requires