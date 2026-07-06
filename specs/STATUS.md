# Dokima Status — Session Log

> Auto-updated by the panel post-pipeline. Do not edit manually.
> Last updated: 2026-06-28

## Active
| Feature | Status | PR | Started |
|---------|--------|----|---------|
| F007: Strategist Read the Actual Product | [x] Done | — | 2026-06-27 |
| F008: Strategist Respects Existing Specs | [x] Done | — | 2026-06-27 |
| F002: Pipeline Integration Tests | [x] Done | — | 2026-06-28 |
| F019: Data-Driven Execution Mode | [x] Done | #11 | 2026-06-28 |
| F004: Deterministic Quality Gates | [x] Done | #12 | 2026-06-28 |
| F003: Edge Case & Robustness Tests | [x] Done | #13 | 2026-06-28 |
| F001: Security Hardening | [~] In Progress | — | 2026-06-27 |
- **F006: Error Recovery & Resume** — in progress since 2026-06-28 23:56, branch `feat/f006-error-recovery--resume` [panel]
- **F031: dokima init back-and-forth interview mode — strategist asks clarifying questions about users, goals, anti-goals, and constraints before producing constitution docs. Loops until confidence is High, then writes specs/mission.md, specs/tech-stack.md, specs/roadmap.md, specs/conventions.md.** — in progress since 2026-07-04 20:17, branch `feat/f031-dokima-init-back-and-forth-intervie-0b3eecfe` [panel]
- **F034: dokima fix --issue N: pull GitHub issue body, extract file/line/fix/verify from structured format, spawn coder to implement. Also upgrade SHOULD FIX issue creation to include What/Fix/Verify sections for coder-readability.** — in progress since 2026-07-05 10:13, branch `feat/f034-dokima-fix---issue-n-pull-github-is-acc18fcb` [panel]
- **F035: GitLab support: swap gh CLI for glab or abstract VCS layer** — in progress since 2026-07-05 15:04, branch `feat/f035-gitlab-support-swap-gh-cli-for-glab-b1d7132e` [panel]
- **F032: Agent-as-Judge self-assessment: coder answers 3 questions before pushing — does every spec requirement have code, what am I least confident about, what would TL flag. Catches empty PRs at source.** — in progress since 2026-07-06 08:50, branch `feat/f032-agent-as-judge-self-assessment-code-99fe357b` [panel]

## Archived
| Feature | Status | PR | Completed |
|---------|--------|----|-----------|
| F004 | [x] Done | #12 | 2026-06-28 |
| F003 | [x] Done | #13 | 2026-06-28 |
- **F001: Security Hardening** — done 2026-06-28 20:08, PR [#14](https://github.com/siongsheng/dokima/pull/14) [panel]
- **F005: Model Family Fallback** — done 2026-06-28 23:15, PR [#17](https://github.com/siongsheng/dokima/pull/17) [panel]
- **F009: Depth Gating Tuning** — done 2026-06-29 01:30, PR [#24](https://github.com/siongsheng/dokima/pull/24) [panel]
- **F011: Installer Script** — done 2026-06-29 02:15, PR [#36](https://github.com/siongsheng/dokima/pull/36) [panel]
- **F012: Profile Templates** — done 2026-06-29 02:39, PR [#37](https://github.com/siongsheng/dokima/pull/37) [panel]
- **F020: Structured CLI Output (`--help-json`)** — done 2026-06-29 03:04 [panel]
- **F023: Pipeline Self-Healing** — done 2026-06-29 08:42, PR [#29](https://github.com/siongsheng/dokima/pull/29) [auto-repair]
- **F022: Modular Architecture** — done 2026-06-29 08:42, PR [#30](https://github.com/siongsheng/dokima/pull/30) [auto-repair]
- **F021: Semantic Versioning + GitHub Releases** — done 2026-06-29 08:56, PR [#41](https://github.com/siongsheng/dokima/pull/41) [panel]
- **F010: Parallel Coder Robustness** — done 2026-06-29 09:46, PR [#43](https://github.com/siongsheng/dokima/pull/43) [panel]
- **F013: Vendor-Agnostic Model Config** — done 2026-06-29 12:12, PR [#42](https://github.com/siongsheng/dokima/pull/42) [auto-repair]
- **F014: nm Script Portability** — done 2026-06-29 12:12 [auto-repair]
- **F015: README & Quickstart Guide** — done 2026-06-29 12:12 [auto-repair]
- **F016: Config Validation (`dokima doctor`)** — done 2026-06-29 12:12 [auto-repair]
- **F017: Dokima-as-Service** — done 2026-06-29 12:12 [auto-repair]
- **F018: Multi-Repo Orchestration** — done 2026-06-29 12:12 [auto-repair]
- **F024: Auto-Release — Tagging, Changelog, and GitHub Releases** — done 2026-06-30 01:08, PR [#53](https://github.com/siongsheng/dokima/pull/53) [panel]
- **F026: Auto-Update Docs CLI Cache on Release** — done 2026-07-01 00:53, PR [#54](https://github.com/siongsheng/dokima/pull/54) [panel]
- **F027: Upgrade codebase-map.md to domain-aware format with Start Here, Domain Map, Impact Map, and Test Map sections. Inject map into strategist, coder-worktree, and tech-lead prompts.** — done 2026-07-02 20:04, PR [#60](https://github.com/siongsheng/dokima/pull/60) [panel]
- **F029: Auto-generate CLI reference page from cli-help.json during Vercel build instead of hand-written MDX. New flags and commands appear in docs automatically on every release.** — done 2026-07-03 00:10, PR [#61](https://github.com/siongsheng/dokima/pull/61) [panel]
- **F030: CLI redesign: replace --add/--next/--fix/--status/--stop/--kill/--list-crons/--version/--upgrade/--release with proper subcommands (dokima add, dokima next, etc). Flags (--force-full, --max-parallel) keep -- prefix. Update all tests, scripts, AGENTS.md, roadmap, and docs.** — done 2026-07-03 19:23, PR [#67](https://github.com/siongsheng/dokima/pull/67) [panel]
- **F028: Strategist enriches codebase-map.md during normal feature planning — appends architecture decisions and agent guidance discovered during exploration. Map accumulates real-world rationale across features with zero extra LLM calls.** — done 2026-07-04 14:46 [panel]
- **F033: Cross-run learning via conventions.md: when TL blocks a PR for a pattern violation, append a one-line rule to conventions.md. Next strategist reads it. No vector DB, no pattern extraction — human-readable rules that compound.** — done 2026-07-04 23:44, PR [#73](https://github.com/siongsheng/dokima/pull/73) [panel]
- **F036: Fix SHOULD FIX issue creation: extract from PR review text (not just nm_stdout), handle table-format findings (R1 | RELIABILITY | ... | SHOULD FIX). Add tests for all extraction formats.** — done 2026-07-05 01:29, PR [#74](https://github.com/siongsheng/dokima/pull/74) [panel]
- **F037: Blocker Resolution Tracking — cross-reference fix PRs to the original blocker PR they resolve. After `dokima fix` completes and TL approves, auto-update the original PR's `### Blockers` section with strikethrough + link to the resolution PR. Optionally create GitHub issues from blockers (matching SHOULD FIX pattern) and auto-close them when the fix PR merges.** — done 2026-07-06 05:03, PR [#81](https://github.com/siongsheng/dokima/pull/81) [panel]
