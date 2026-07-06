"""Dokima spec extraction — text processing from specs, PRs, issues, agent output.

All functions extracted from dokima monolith utils.py (F041: Split utils.py into domain modules).
"""

import sys, json, os, re, hashlib, datetime


# Cross-module import: _append_convention_rules() calls git() from git_ops
from git_ops import git


def extract_pr_sections(spec_text: str, feature: str) -> str:
    """Extract Why, Impact, and What Changed from the strategist's spec.
    Returns markdown sections: ## Why, ## Impact, ## What Changed.
    Handles both modern (## N. Section) and legacy (Field:) formats."""

    # 1. ## Why — feature purpose
    why = f"## Why\n\n{feature}"
    # Legacy: Position: <text>
    pos_m = re.search(
        r'Position:\s*(.+?)(?=\n\s*\n\s*(?:\d\.\s*DECISION|DECISION|IMPACT|CONFIDENCE|### Task|Task \d|\Z))',
        spec_text, re.DOTALL | re.IGNORECASE)
    if pos_m:
        pos = pos_m.group(1).strip()
        pos = re.sub(r'\s+', ' ', pos)
        if len(pos) > 400:
            pos = pos[:397] + "..."
        why += f"\n\n{pos}"

    # 2. ## Impact — what's affected (paragraph under ## N. Impact header)
    impact = ""
    # Modern: ^## N. Impact (section header, not **Impact:** metadata)
    imp_m = re.search(
        r'^##\s*\d*\.?\s*Impact\s*\n+(.+?)(?=\n##\s|\n###\s|\n\*\*Confidence|\Z)',
        spec_text, re.DOTALL | re.IGNORECASE | re.MULTILINE)
    if imp_m:
        impact_text = imp_m.group(1).strip()
        if impact_text:
            impact = f"## Impact\n\n{impact_text}"
    if not impact:
        # Legacy: Impact: <text> (colon format)
        imp_m = re.search(
            r'Impact:\s*(.+?)(?=\n\s*\n|\n(?:What Changed|Confidence|### Task|\Z))',
            spec_text, re.DOTALL | re.IGNORECASE)
        if imp_m and imp_m.group(1).strip():
            impact = f"## Impact\n\n{imp_m.group(1).strip()}"
    if not impact:
        # Fallback: Executive Summary section
        exec_m = re.search(
            r'^##?\s*Executive\s+Summary\s*\n+(.+?)(?=\n##\s|\n###\s|\n\*\*Confidence|\Z)',
            spec_text, re.DOTALL | re.IGNORECASE | re.MULTILINE)
        if exec_m and exec_m.group(1).strip():
            impact = f"## Impact\n\n{exec_m.group(1).strip()}"
    if not impact:
        # Fallback: Position: <text> (used in older spec formats)
        pos_m = re.search(
            r'Position:\s*(.+?)(?=\n\s*\n\s*(?:F\d{3}:|\Z))',
            spec_text, re.DOTALL | re.IGNORECASE)
        if pos_m and pos_m.group(1).strip():
            text = pos_m.group(1).strip()
            # Clean up: remove internal newlines, truncate
            text = re.sub(r'\n\s+', ' ', text)
            if len(text) > 500:
                text = text[:497] + "..."
            impact = f"## Impact\n\n{text}"

    # 3. ## What Changed — bullet list under ## N. What Changed header
    what_changed = ""
    # Modern: ^## N. What Changed (bullet list until next ## or EOF)
    wc_m = re.search(
        r'^##\s*\d*\.?\s*What\s+Changed\s*\n+((?:\s*[-*]\s*.+(?:\n|$))+)',
        spec_text, re.IGNORECASE | re.MULTILINE)
    if wc_m:
        what_changed = f"## What Changed\n{wc_m.group(1).strip()}"
    if not what_changed:
        # Legacy: What Changed: <bullet list>
        wc_m = re.search(
            r'What Changed:\s*\n((?:\s*[-*]\s*.+\n?)+)',
            spec_text, re.IGNORECASE)
        if wc_m:
            what_changed = f"## What Changed\n{wc_m.group(1).strip()}"

    parts = [why]
    if impact:
        parts.append(impact)
    if what_changed:
        parts.append(what_changed)

    result = "\n\n".join(parts)
    if len(result) < 100:
        result = f"## Why\n\n{feature}\n\n## Impact\n\nSee What Changed below.\n\n## What Changed\n\nSee diff for details."
    return result



def extract_agent_messages(session_output: str, last_only: bool = False) -> str:
    """Extract agent messages from hermes session transcript, stripping noise
    (prompt echo, tool output, init markers). Keeps ALL agent reasoning.

    When last_only=True (spec extraction), returns only the LAST agent message
    — which is the final spec output, free of intermediate exploration chatter."""
    # Hermes boxes: ╭─ ⚕ Hermes ──...──╮  ...content...  ╰──...──╯
    messages = re.findall(r'╭─ ⚕ Hermes .+?╮\n(.*?)╰─+╯', session_output, re.DOTALL)
    if messages:
        if last_only:
            return messages[-1].strip()
        return "\n\n".join(m.strip() for m in messages if m.strip())
    # Fallback for unknown format: return raw output
    return session_output



def clean_spec_content(raw: str) -> str:
    """Strip model thinking, Ponytail Guard verdicts, and session metadata
    from strategist output — keep only the actual spec content."""
    # Strip text before the first markdown header (agent exploration chatter)
    header_match = re.search(r'^#\s+', raw, re.MULTILINE)
    if header_match:
        raw = raw[header_match.start():]
    # Remove session resume text and everything after
    raw = re.sub(r'\nResume this session with:.*', '', raw, flags=re.DOTALL)
    # Remove Ponytail Guard blocks
    raw = re.sub(r'\n\s*Ponytail Guard verdict:.*?(\n\n|\Z)', '\n', raw, flags=re.DOTALL)
    # Remove model sign-off/chatter lines — only strip the single line, not everything after
    chatter_patterns = [
        r'The spec is ready.*',
        r'Do you want me to.*',
        r'Shall I.*',
        r'Let me know if.*',
        r'Would you like me to.*',
        r'I can make changes.*',
        r'Is there anything.*',
        r'Feel free to.*',
    ]
    for pat in chatter_patterns:
        raw = re.sub(rf'\n\s*{pat}\n?', '\n', raw, flags=re.IGNORECASE)
    # Strip leading/trailing blank lines
    raw = raw.strip()
    return raw



def verify_spec_quality(spec_text: str, confidence: str = "Medium") -> tuple:
    """Verify spec quality against structural and content gates.

    Checks that the spec has required section headers:
    - Impact section (## Impact or ## N. Impact)
    - What Changed section (## What Changed or ## N. What Changed)
    - Task breakdown headers (### Task N:)

    Also checks:
    - Task field completeness (Files, Dependencies, Parallelizable)
    - PR body quality: detect thin fallback from extract_pr_sections()
    - Brevity: warns if spec exceeds confidence-based char threshold

    Also checks PR body quality:
    - Detects when extract_pr_sections() returns thin fallback
      despite spec having >=200 chars of real Impact + What Changed content.

    Args:
        spec_text: The spec content to check.
        confidence: Confidence level ("High", "Medium", "Low").

    Returns:
        (passed: bool, failures: list[str]) — True + empty list means clean.
        Brevity warnings appear in failures but passed remains True (soft warning).
    """
    failures = []

    # Check 1: Impact section — ## Impact or ## N. Impact
    if not re.search(r'##\s+\d*\.?\s*Impact', spec_text):
        failures.append("Missing: Impact section")

    # Check 2: What Changed section — ## What Changed or ## N. What Changed
    if not re.search(r'##\s+\d*\.?\s*What Changed', spec_text):
        failures.append("Missing: What Changed section")

    # Check 3: Task breakdown headers — ### Task N:
    if not re.search(r'###\s+Task\s+\d+:', spec_text):
        failures.append("Missing: Task N: headers")

    # Check 4: Task field completeness — verify task blocks have all required fields
    # Parse task blocks using same approach as TaskDAG.parse
    task_block_pattern = re.compile(
        r'^\s*(?:###\s*)?Task\s*(\d+):[ \t]*(.*?)\n'
        r'(.*?)(?=^\s*(?:###\s*)?Task\s*\d+|^\s*####\s|\Z)',
        re.DOTALL | re.MULTILINE
    )
    for m in task_block_pattern.finditer(spec_text):
        tid = m.group(1)
        desc = m.group(2).strip()
        body = m.group(3)

        # Check description (task title)
        if not desc:
            failures.append(f"Task {tid}: missing Description field")

        # Check Files field
        files_m = re.search(r'^\s*(?:\*\*)?Files?:?(?:\*\*)?[ \t]*(.*?)\s*$', body, re.MULTILINE)
        if not files_m or not files_m.group(1).strip():
            failures.append(f"Task {tid}: missing Files field")
        elif files_m.group(1).strip().lower() in ('from spec', 'from spec files', 'n/a', 'tbd', 'see spec'):
            failures.append(f"Task {tid}: Files field is generic placeholder — must specify actual file paths (not '{files_m.group(1).strip()}')")

        # Check Dependencies field
        deps_m = re.search(r'^\s*(?:\*\*)?Dependencies?:?(?:\*\*)?[ \t]*(.*?)\s*$', body, re.MULTILINE)
        if not deps_m or not deps_m.group(1).strip():
            failures.append(f"Task {tid}: missing Dependencies field")

        # Check Parallelizable field
        par_m = re.search(r'^\s*(?:\*\*)?Parallelizable?:?(?:\*\*)?[ \t]*(.*?)\s*$', body, re.MULTILINE)
        if not par_m or not par_m.group(1).strip():
            failures.append(f"Task {tid}: missing Parallelizable field")

    # Check 5: Parallel tasks must have zero file overlap
    parallel_tasks = {}
    for m in task_block_pattern.finditer(spec_text):
        tid = m.group(1)
        body = m.group(3)
        par_m = re.search(r'^\s*(?:\*\*)?Parallelizable?:?(?:\*\*)?[ \t]*(.*?)\s*$', body, re.MULTILINE | re.IGNORECASE)
        if par_m and par_m.group(1).strip().lower() == "yes":
            files_m = re.search(r'^\s*(?:\*\*)?Files?:?(?:\*\*)?[ \t]*(.*?)\s*$', body, re.MULTILINE)
            if files_m:
                files = [f.strip().rstrip(',') for f in files_m.group(1).split(',') if f.strip()]
                parallel_tasks[tid] = set(files)
    task_ids = sorted(parallel_tasks.keys(), key=int)
    for i in range(len(task_ids)):
        for j in range(i + 1, len(task_ids)):
            overlap = parallel_tasks[task_ids[i]] & parallel_tasks[task_ids[j]]
            if overlap:
                failures.append(f"Task {task_ids[i]} + Task {task_ids[j]}: file overlap on parallel tasks — {', '.join(sorted(overlap))}")

    passed = len(failures) == 0
    return passed, failures



def _check_pr_body_quality(spec_text: str, failures: list) -> None:
    """Check if extract_pr_sections() returns thin fallback despite spec having
    >=200 chars of real Impact + What Changed content.

    extract_pr_sections requires bullet items for What Changed sections.
    If the section contains prose (no bullets), extract_pr_sections won't
    capture it and returns the thin fallback. This check independently
    extracts content with a broader pattern and flags the discrepancy.

    Args:
        spec_text: The full spec text.
        failures: Accumulated failure list (mutated in place).
    """
    pr_body = extract_pr_sections(spec_text, "PR Body")
    is_thin_fallback = len(pr_body) < 100 and "See diff for details" in pr_body
    if not is_thin_fallback:
        return

    # Independently extract Impact + What Changed content with broader patterns
    # (no bullet requirement for What Changed — extract_pr_sections requires bullets)
    impact_m = re.search(
        r'^##\s*\d*\.?\s*Impact\s*\n+(.+?)(?=\n##\s|\n###\s|\Z)',
        spec_text, re.DOTALL | re.IGNORECASE | re.MULTILINE
    )
    wc_m = re.search(
        r'^##\s*\d*\.?\s*What\s+Changed\s*\n+(.+?)(?=\n##\s|\n###\s|\Z)',
        spec_text, re.DOTALL | re.IGNORECASE | re.MULTILINE
    )

    impact_len = len(impact_m.group(1).strip()) if impact_m else 0
    wc_len = len(wc_m.group(1).strip()) if wc_m else 0

    if impact_len + wc_len >= 200:
        failures.append(
            "PR body degraded to fallback despite spec having real content."
        )



def extract_file_paths(text):
    """Extract file paths from blocker descriptions or task lists.
    Matches:
    - Backtick-quoted paths like `src/app/layout.tsx:29-33`
    - **Files:** lines in task extracts: **Files:** path/to/file1, path/to/file2
    Returns sorted unique list of relative paths."""
    paths = set()
    # Pattern 1: backtick-quoted paths with optional line numbers
    for match in re.finditer(r'`([^`]+\.[a-z]{2,6}(?::\d+(?:-\d+)?)?)`', text):
        raw = match.group(1)
        # Strip line numbers
        path = re.sub(r':\d+(?:-\d+)?', '', raw)
        # Normalize: remove leading ./ or src/ if it's a relative reference
        if path.startswith('./'):
            path = path[2:]
        # Only keep paths that look like real files (not URLs or commands)
        # Require a / — bare filenames like 'layout.tsx' are ambiguous
        if '/' in path:
            if not path.startswith('http') and not path.startswith('git '):
                paths.add(path)
    # Pattern 2: **Files:** lines in task extracts (unquoted, comma-separated)
    for match in re.finditer(r'\*\*Files:\*\*\s+(.+)', text):
        files_line = match.group(1)
        for part in re.split(r'[,;]\s*', files_line):
            part = part.strip()
            # Strip "(NEW)" suffix
            part = re.sub(r'\s*\(NEW\)', '', part).strip()
            if not part.startswith('http') and not part.startswith('git '):
                paths.add(part)
    return sorted(paths)



def _hash_output(text):
    """Return MD5 hex digest of text for cycle detection (F023)."""
    import hashlib
    if text is None:
        text = ""
    return hashlib.md5(text.encode("utf-8", errors="replace")).hexdigest()



def _detect_truncation(text):
    """Detect truncated coder output. Returns True if output appears truncated.

    A non-truncated output has a Report: line OR ends with terminal
    punctuation (., !, ?). None input returns False (safety); empty input
    returns True (coder crashed).
    """
    if text is None:
        return False
    if not text:
        return True
    # Check for Report: marker (case-insensitive, word boundary)
    if re.search(r'\bReport:', text, re.IGNORECASE):
        return False
    # Check if last non-whitespace character is terminal punctuation
    stripped = text.rstrip()
    if stripped and stripped[-1] in ('.', '!', '?'):
        return False
    return True



def _extract_code_context(spec_text, task_text, project_dir):
    """Extract relevant code snippets from line-range references in spec/task text.
    
    Parses patterns like:
    - "lines 4583–4594 in dokima"
    - "dokima:4583-4594"
    - "line 4584 of src/foo.py"
    
    Reads the target files and returns a code-context string for the coder prompt.
    Returns empty string if no line references found or files unreadable.
    """
    snippets = []
    # Pattern: "lines N–M" or "line N" with optional filename mention
    line_refs = re.findall(
        r'(?:lines?\s+|:)(\d{2,6})\s*(?:[–\-—]|\s*to\s*)\s*(\d{2,6})',
        spec_text + '\n' + task_text, re.IGNORECASE
    )
    if not line_refs:
        return ""
    
    # Build a set of (filename, start, end) to read — up to 5 snippets
    seen = set()
    for start, end in line_refs[:5]:
        start_i, end_i = int(start), int(end)
        if start_i > end_i:
            start_i, end_i = end_i, start_i
        # Expand context window: 3 lines before and after
        read_start = max(1, start_i - 3)
        read_end = end_i + 3
        
        # Try to find which file this refers to from task Files: fields
        files_m = re.findall(r'\*\*Files:\*\*\s*(.+)', task_text)
        target_files = []
        for fl in files_m:
            for f in re.split(r'[,;]\s*', fl):
                f = re.sub(r'\s*\(NEW\)', '', f).strip()
                if f and not f.startswith('http'):
                    target_files.append(f)
        
        for fname in target_files[:3]:
            key = (fname, read_start, read_end)
            if key in seen:
                continue
            seen.add(key)
            fpath = os.path.join(project_dir, fname)
            if not os.path.isfile(fpath):
                continue
            try:
                with open(fpath) as f:
                    lines = f.readlines()
                if read_start > len(lines):
                    continue
                actual_end = min(read_end, len(lines))
                chunk = ''.join(
                    f"{i}:{lines[i-1]}" 
                    for i in range(read_start, actual_end + 1)
                )
                if chunk.strip():
                    snippets.append(
                        f"```{fname}:{read_start}-{actual_end}\n{chunk}```"
                    )
            except Exception:
                pass
    
    if not snippets:
        return ""
    
    return (
        "\n### ⚡ Relevant Code (read ONLY these snippets — no full-file exploration)\n"
        + "\n".join(snippets)
        + "\n⚡ These are the EXACT lines to modify. Start here.\n"
    )

# ── F028: Map Enrichments ──────────────────────────



def _extract_tl_verdict(tl_output: str) -> str:
    """Extract the LAST VERDICT from TL output.

    TL may quote earlier verdicts or change its mind mid-review.
    Always use the final verdict line.
    """
    if not tl_output or not tl_output.strip():
        return "UNKNOWN"
    if "[TIMEOUT:" in tl_output and "VERDICT:" not in tl_output.upper():
        return "TIMED_OUT"

    all_verdicts = re.findall(
        r'VERDICT:\s*(APPROVED|BLOCKED|CHANGES\s+REQUESTED)',
        tl_output.upper()
    )
    if not all_verdicts:
        return "UNKNOWN"

    last = all_verdicts[-1].strip()
    if "CHANGES" in last:
        return "CHANGES REQUESTED"
    elif "BLOCKED" in last:
        return "BLOCKED"
    return "APPROVED"



def _extract_tl_blockers(tl_output: str) -> list[str]:
    """Extract structured BLOCKER findings from TL output, filtering monologue.

    Handles varied TL output formats:
    - ### BLOCKERs (must fix before merge) — flexible header matching
    - ### Blockers — case-insensitive
    - Fallback: bold-numbered items near BLOCKER mentions

    Returns clean, human-readable blocker descriptions.
    """
    if not tl_output or not tl_output.strip():
        return []

    lines = tl_output.split("\n")
    blockers = []
    noise_patterns = [
        "now let me", "however,", "let me check", "let me look",
        "let me read", "let me verify", "this coverage gap",
        "previous reviewer", "previous review", "unfixed by",
        "severity: 🔴 blocker", "- severity: 🔴",
        "severity: blocker", "blocker:", "blockers found",
        "what the coder needs", "move ", "remove ", "add tests",
    ]

    # ── Pass 1: find ### section containing "BLOCKER" (flexible) ──
    in_blockers_section = False
    section_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_blockers_section:
                section_lines.append("")  # preserve paragraph breaks
            continue

        # Section header: any ### line containing BLOCKER (case-insensitive)
        if stripped.startswith("###") and "BLOCKER" in stripped.upper():
            in_blockers_section = True
            continue

        # Next section ends it (## or ### without BLOCKER)
        if in_blockers_section:
            if stripped.startswith("###") or stripped.startswith("## "):
                in_blockers_section = False
                continue
            if not any(p in stripped.lower() for p in noise_patterns):
                section_lines.append(stripped)

    # ── Pass 2: if section found, extract numbered + detail items ──
    if section_lines:
        current = None
        for sl in section_lines:
            # Bold-numbered item: **1. Title**
            if sl.startswith("**") and len(sl) > 4 and sl[2:3].isdigit():
                if current:
                    blockers.append(current)
                current = sl
            elif sl.startswith("- ") and current:
                # Detail line under current blocker
                detail = sl.lstrip("- ").rstrip(".")
                if " — " not in current:
                    current = current + " — " + detail
                elif detail not in current:
                    current = current + "; " + detail
            elif current and sl and not sl.startswith("#"):
                # Continuation line
                if not current.endswith(sl[:30]):
                    current = current + " " + sl.rstrip(".")
        if current:
            blockers.append(current)

    # ── Pass 3: fallback — line-level heuristics (original approach, relaxed) ──
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        upper = stripped.upper()
        if "BLOCKER" not in upper and "MUST FIX" not in upper:
            continue
        if any(p in stripped.lower() for p in noise_patterns):
            continue
        if (
            stripped.startswith("**") or
            (stripped.startswith("- ") and ":" in stripped[2:40]) or
            stripped.startswith("1.") or stripped.startswith("2.") or
            stripped.startswith("3.")
        ):
            blockers.append(stripped)

    # Merge bold-numbered title + detail
    merged = []
    for b in blockers:
        if b.startswith("**") and b[2:3].isdigit():
            merged.append(b)
        elif merged and not b.startswith("**"):
            merged[-1] = merged[-1] + " — " + b.lstrip("- ").rstrip(".")
        else:
            merged.append(b)

    # Strip ** markers from final output for clean PR formatting
    merged = [m.replace("**", "") for m in merged]

    return merged[:10]




def format_blocker_cross_reference(blockers, fix_pr_url, fix_verdict):
    """Format blocker list with cross-reference to the resolution PR.

    Args:
        blockers: List of blocker description strings.
        fix_pr_url: URL of the fix PR.
        fix_verdict: TL verdict — APPROVED, BLOCKED, or UNKNOWN.

    Returns:
        Markdown string with blockers formatted per verdict.
        - APPROVED: ~~blocker~~ → resolved by <fix_pr_url>
        - BLOCKED:  blocker → unresolved
        - UNKNOWN:  blockers unchanged
        Already-resolved blockers (containing ~~) are left unchanged.
    """
    if not blockers:
        return ""

    if isinstance(blockers, str):
        blockers = [blockers]

    results = []
    for b in blockers:
        b = str(b).strip()
        if not b:
            continue
        # Skip already-resolved blockers
        if "~~" in b:
            results.append(b)
            continue

        if fix_verdict == "APPROVED":
            results.append(f"~~{b}~~ → resolved by {fix_pr_url}")
        elif fix_verdict == "BLOCKED":
            results.append(f"{b} → unresolved")
        else:  # UNKNOWN or any other
            results.append(b)

    return "\n".join(results)




def extract_should_fix_from_text(text):
    """Extract SHOULD FIX findings from any text source (TL output, PR review, nm stdout).

    Handles three formats:
    - Table: | R1 | RELIABILITY | utils.py:42 | SHOULD FIX | Naming conventions |
    - Prose: SHOULD FIX — description or SHOULD FIX: description
    - Bullet: - SHOULD FIX: description or * SHOULD FIX — description

    Returns list[dict] with keys: id, dimension, location, detail.
    Deduplicates by normalized detail text (lowercase, punctuation-stripped).
    """
    if not text or not str(text).strip():
        return []

    lines = str(text).split("\n")
    findings = []

    should_fix_pat = re.compile(r'SHOULD\s*FIX', re.IGNORECASE)

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # ── Table format: pipe-delimited row with SHOULD FIX in severity column ──
        # Split by pipe, handle escaped pipes (\\|) by not splitting on them
        # First, check if the line looks like a table row (starts with pipe or
        # has pipe characters AND contains SHOULD FIX)
        if '|' in stripped and should_fix_pat.search(stripped):
            # Split by unescaped pipe characters
            cols = []
            current = ''
            i = 0
            while i < len(stripped):
                ch = stripped[i]
                if ch == '\\' and i + 1 < len(stripped) and stripped[i + 1] == '|':
                    # Escaped pipe: keep the backslash-pipe in detail
                    current += '\\|'
                    i += 2
                    continue
                if ch == '|':
                    cols.append(current.strip())
                    current = ''
                else:
                    current += ch
                i += 1
            cols.append(current.strip())

            # Remove empty first/last columns (from leading/trailing pipes)
            cols = [c for c in cols if c]

            if not cols:
                continue

            # Find which column contains SHOULD FIX
            sf_idx = None
            for idx, col in enumerate(cols):
                if should_fix_pat.search(col):
                    sf_idx = idx
                    break

            if sf_idx is None or sf_idx == len(cols) - 1:
                # SHOULD FIX not found or is the last column (no detail)
                continue

            # Columns before SHOULD FIX: map to id, dimension, location
            before = cols[:sf_idx]
            # Columns after SHOULD FIX: detail (may include extra columns)
            after = cols[sf_idx + 1:]

            col_id = before[0] if len(before) > 0 else ""
            dimension = before[1] if len(before) > 1 else ""
            location = before[2] if len(before) > 2 else ""
            detail = after[0] if after else ""
            # Append any extra columns to detail
            for extra in after[1:]:
                detail = detail + " " + extra

            if detail:
                findings.append({
                    "id": col_id,
                    "dimension": dimension,
                    "location": location,
                    "detail": detail,
                })
            continue

        # ── Prose/bullet format: SHOULD FIX keyword followed by separator ──
        prose_re = re.compile(
            r'(?:^|[-\*])\s*'           # line start or bullet marker with space
            r'SHOULD\s*FIX\s*'          # keyword (case-insensitive via flag)
            r'(:|—|–)'
            r'\s*(.*)$',                # description
            re.IGNORECASE
        )
        p_match = prose_re.match(stripped)
        if p_match:
            detail = p_match.group(2).strip()
            if detail:
                findings.append({
                    "id": "",
                    "dimension": "",
                    "location": "",
                    "detail": detail,
                })
                continue

        # ── Prose format: SHOULD FIX keyword with em-dash (no bullet prefix) ──
        em_dash_re = re.compile(
            r'^SHOULD\s*FIX\s+(?:—|–)\s+(.+)$',
            re.IGNORECASE
        )
        em_match = em_dash_re.match(stripped)
        if em_match:
            detail = em_match.group(1).strip()
            if detail:
                findings.append({
                    "id": "",
                    "dimension": "",
                    "location": "",
                    "detail": detail,
                })
                continue

    # ── Deduplicate by normalized detail text ──
    seen = set()
    deduped = []
    for f in findings:
        normalized = f["detail"].lower().strip(".,!?;:\"' \t")
        if normalized not in seen:
            seen.add(normalized)
            deduped.append(f)

    return deduped




def _extract_nm_summary(nm_stdout):
    """Extract a structured summary from raw nm (adversarial review) output.

    Parses up to 37K chars of nm output into a compact dict suitable for
    injection into a PR body as an ### nm Review section.

    Returns dict with keys:
        risk (str): LOW/MEDIUM/HIGH/UNKNOWN
        auto_fix_count (int): number of auto-fixable patterns matched
        auto_fix_labels (list[str]): labels of matched auto-fix patterns
        key_findings (str): first ~2500 chars of substantive review content
        should_fix_items (list[dict]): from extract_should_fix_from_text()

    Returns a fully-defaulted dict if nm_stdout is empty/None.
    """
    if not nm_stdout or not str(nm_stdout).strip():
        return {
            "risk": "UNKNOWN",
            "auto_fix_count": 0,
            "auto_fix_labels": [],
            "key_findings": "",
            "should_fix_items": [],
        }

    text = str(nm_stdout)

    # ── Extract risk ──
    risk_match = re.search(r'RISK:\s*(LOW|MEDIUM|HIGH)', text, re.IGNORECASE)
    risk = risk_match.group(1).upper() if risk_match else "UNKNOWN"

    # ── Auto-fix pattern detection (mirrors pipeline.py run_phase4_nm) ──
    nm_auto_fix_patterns = [
        (r'(?i)missing\s+test', "missing test"),
        (r'(?i)uncaught\s+(panic|exception)', "uncaught exception"),
        (r'(?i)\bunwrap\b.*\b(result|option)\b', "unwrap on Result/Option"),
        (r'(?i)bundled\s+commit', "TDD violation: bundled commit"),
        (r'(?i)TDD\s+violation', "TDD violation"),
        (r'(?i)unhandled\s+error', "unhandled error"),
    ]
    auto_fix_labels = []
    for pattern, label in nm_auto_fix_patterns:
        if re.search(pattern, text):
            auto_fix_labels.append(label)

    # ── Extract key findings (first ~2500 chars of substantive review) ──
    # Skip nm script boilerplate: lines matching setup/header patterns.
    # The actual review body starts after "STAGE 1" / "You are running" and
    # continues past STAGE headers.
    lines = text.split("\n")

    # Find the content start: first line matching STAGE 1 or "You are running"
    content_start = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r'^(STAGE\s*1|You\s+are\s+running)', stripped, re.IGNORECASE):
            content_start = i
            break

    # Collect lines after boilerplate, filtering out known boilerplate markers
    boilerplate_re = re.compile(
        r'^(You\s+are\s+running|Initializ|Loading|STAGE\s*\d|RISK:\s*(LOW|MEDIUM|HIGH))',
        re.IGNORECASE
    )
    key_findings_parts = []
    char_count = 0
    max_chars = 2500
    for line in lines[content_start:]:
        stripped = line.strip()
        if boilerplate_re.match(stripped):
            continue
        if not stripped and not key_findings_parts:
            continue  # skip leading blank lines
        key_findings_parts.append(line)
        char_count += len(line) + 1  # +1 for newline
        if char_count >= max_chars:
            break

    key_findings = "\n".join(key_findings_parts).strip()

    # ── Extract SHOULD FIX items (delegate) ──
    try:
        should_fix_items = extract_should_fix_from_text(text)
    except Exception:
        should_fix_items = []

    return {
        "risk": risk,
        "auto_fix_count": len(auto_fix_labels),
        "auto_fix_labels": auto_fix_labels,
        "key_findings": key_findings,
        "should_fix_items": should_fix_items,
    }




def extract_issue_sections(issue_body):
    """Extract structured sections from a GitHub issue body.

    Parses ### What, ### Fix, ### Verify sections using regex.
    Extracts file path from ### What section via backtick-pattern matching.

    Args:
        issue_body: str — the issue body text

    Returns:
        dict with keys: what, fix, verify, file_path.
        file_path is None if no backtick path found.

    Raises:
        ValueError if issue_body is empty or ### Fix section is missing.
    """
    if not issue_body or not issue_body.strip():
        raise ValueError("Issue body is empty")

    # Match sections: ### What, ### Fix, ### Verify
    # Each section ends at the next ### heading or end of string
    section_pattern = re.compile(
        r'###\s+(What|Fix|Verify)\s*\n(.+?)(?=\n###\s+(?:What|Fix|Verify|Source)\b|\Z)',
        re.DOTALL | re.IGNORECASE
    )

    sections = {}
    for match in section_pattern.finditer(issue_body):
        heading = match.group(1).lower()
        content = match.group(2).strip()
        # Strip backtick code blocks within sections
        content = re.sub(r'```[^\n]*\n.*?\n```', '', content, flags=re.DOTALL).strip()
        sections[heading] = content

    # Fix section is required
    if "fix" not in sections or not sections["fix"].strip():
        raise ValueError("Issue body missing required ### Fix section")

    what = sections.get("what", "")
    fix = sections["fix"].strip()
    verify = sections.get("verify", "")

    # Extract file path from ### What section via backtick pattern
    file_path = None
    if what:
        # Match backtick-wrapped paths like `path/file.py` or `path/file.py:42` or `file.py:L128`
        bt_match = re.search(r'`([^`]+\.[a-z]{1,10}(?::[A-Za-z]?\d+)?)`', what)
        if bt_match:
            raw_path = bt_match.group(1)
            # Strip line number suffix (e.g., :42, :L128, :N5)
            file_path = re.sub(r':[A-Za-z]?\d+$', '', raw_path)
        else:
            # Fallback: match bare file paths like path/to/file.ext:NN
            bare_match = re.search(
                r'(?:^|\s)([\w/.-]+\.(?:py|js|ts|rs|go|md|yaml|yml|json|toml|cfg|ini|sh|bash|html|css|scss|vue|jsx|tsx|java|rb|php|c|cpp|h|hpp|swift|kt))(?::\d+)?(?:\s|$|:)',
                what
            )
            if bare_match:
                raw_path = bare_match.group(1)
                file_path = re.sub(r':\d+$', '', raw_path)

    return {
        "what": what,
        "fix": fix,
        "verify": verify,
        "file_path": file_path,
    }




def _extract_convention_rules(blocker_lines):
    """Filter TL blocker lines to pattern-violation convention rules.

    Skips file-specific one-time fixes (e.g., 'missing null check in foo.py line 42')
    and keeps generic convention patterns (e.g., 'all subprocess calls must use list args').

    Each blocker line is expected in _extract_tl_blockers output format:
    'N. Title' or 'N. Title — detail'.

    Returns a list of clean rule strings (no number prefix, no bullet markers).
    """
    if not blocker_lines:
        return []

    file_ref_pattern = re.compile(
        r'\.(?:py|js|ts|rs|go|java|rb|php|c|cpp|h|hpp|swift|kt|cs|scala|sh|bash|'
        r'vue|jsx|tsx|svelte|css|scss|html|sql|yaml|yml|json|xml|toml|cfg|ini|'
        r'md|rst|txt)\b',
        re.IGNORECASE
    )

    rules = []
    for line in blocker_lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Skip file-specific blockers: contain file extension or 'line N' pattern
        if file_ref_pattern.search(stripped):
            continue
        if re.search(r'\bline\s+\d+\b', stripped, re.IGNORECASE):
            continue
        if re.search(r'\b(?:file|path|directory):\s', stripped, re.IGNORECASE):
            continue

        # Extract rule text: after 'N. ' prefix and after ' — ' separator
        # Format: "1. Title" or "1. Title — detail"
        # Strip number prefix first
        rule = re.sub(r'^\d+\.\s*', '', stripped)

        # If no ' — ' separator, skip — malformed blocker line
        if ' — ' not in rule:
            continue

        # Take the detail part (after last " — ")
        parts = rule.rsplit(' — ', 1)
        detail = parts[-1].strip()
        if detail:
            rule = detail
        else:
            rule = parts[0].strip()

        if rule and not rule.startswith('—'):
            rules.append(rule)

    return rules




def _append_convention_rules(project_dir, rules):
    """Append convention rules to specs/conventions.md under ## Cross-Run Learning.

    Creates the ## Cross-Run Learning section if absent. Each new rule gets a
    <!-- auto: YYYY-MM-DD --> provenance comment. Rules are deduplicated
    case-insensitively against existing rules in the section.

    Args:
        project_dir: Path to the project root (must contain specs/ subdirectory).
        rules: List of rule strings to append.

    Returns:
        int: Number of newly appended rules (0 if all were duplicates).
    """
    if not rules:
        return 0

    conventions_path = os.path.join(project_dir, "specs", "conventions.md")

    # Read existing content
    existing_content = ""
    if os.path.exists(conventions_path):
        with open(conventions_path) as f:
            existing_content = f.read()

    # Collect existing rules for dedup (case-insensitive)
    existing_rules = set()
    section_header = "## Cross-Run Learning"
    if section_header in existing_content:
        # Extract rules from the section — bullet points under the header
        section_start = existing_content.index(section_header)
        section_text = existing_content[section_start:]
        # Match "- rule text" lines
        for m in re.finditer(r'^-\s+(.+)$', section_text, re.MULTILINE):
            existing_rules.add(m.group(1).strip().casefold())

    # Determine which rules are new
    today = datetime.date.today().isoformat()
    append_lines = []
    new_count = 0

    for rule in rules:
        rule = rule.strip()
        if not rule:
            continue
        if rule.casefold() in existing_rules:
            continue
        # Mark as seen for this batch too (prevents internal duplicates in one call)
        existing_rules.add(rule.casefold())
        append_lines.append(f"<!-- auto: {today} -->")
        append_lines.append(f"- {rule}")
        new_count += 1

    if new_count == 0:
        return 0

    # Build new content
    result = existing_content.rstrip('\n')

    if section_header not in result:
        # Add section header
        if result:
            result += "\n\n"
        result += f"{section_header}\n"

    # Append new rules
    for line in append_lines:
        result += f"\n{line}"

    result += "\n"

    # Write back
    specs_dir = os.path.dirname(conventions_path)
    if not os.path.exists(specs_dir):
        os.makedirs(specs_dir, exist_ok=True)
    with open(conventions_path, "w") as f:
        f.write(result)

    return new_count


# ── Profile configuration defaults (F012) ──
_PROFILE_CONFIGS = {
    "strategist": {
        "model.default": "deepseek-v4-pro",
        "model.provider": "deepseek",
        "agent.max_turns": "150",
        "agent.reasoning_effort": "high",
        "terminal.env_passthrough": "[GH_TOKEN, GITHUB_TOKEN, GLAB_TOKEN, GITLAB_TOKEN, HERMES_HOME, HOME]",
    },
    "coder": {
        "model.default": "deepseek-v4-pro",
        "model.provider": "deepseek",
        "agent.max_turns": "150",
        "terminal.env_passthrough": "[GH_TOKEN, GITHUB_TOKEN, GLAB_TOKEN, GITLAB_TOKEN, HERMES_HOME, HOME]",
    },
    "tech-lead": {
        "model.default": "deepseek-v4-pro",
        "model.provider": "deepseek",
        "agent.max_turns": "150",
        "terminal.env_passthrough": "[GH_TOKEN, GITHUB_TOKEN, GLAB_TOKEN, GITLAB_TOKEN, HERMES_HOME, HOME]",
    },
    "nm": {
        "model.default": "deepseek-v4-pro",
        "model.provider": "deepseek",
        "agent.max_turns": "150",
        "terminal.env_passthrough": "[GH_TOKEN, GITHUB_TOKEN, GLAB_TOKEN, GITLAB_TOKEN, HERMES_HOME, HOME]",
    },
}
_PROFILE_ORDER = ["strategist", "coder", "tech-lead", "nm"]




