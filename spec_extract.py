"""Spec extraction functions extracted from utils.py (F041).

Contains extract_pr_sections(), clean_spec_content(), verify_spec_quality(),
extract_should_fix_from_text(), _extract_nm_summary(), extract_issue_sections().
"""

import re


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
        pos_m2 = re.search(
            r'Position:\s*(.+?)(?=\n\s*\n\s*(?:F\d{3}:|\Z))',
            spec_text, re.DOTALL | re.IGNORECASE)
        if pos_m2 and pos_m2.group(1).strip():
            text = pos_m2.group(1).strip()
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
            files_m2 = re.search(r'^\s*(?:\*\*)?Files?:?(?:\*\*)?[ \t]*(.*?)\s*$', body, re.MULTILINE)
            if files_m2:
                files = [f.strip().rstrip(',') for f in files_m2.group(1).split(',') if f.strip()]
                parallel_tasks[tid] = set(files)
    task_ids = sorted(parallel_tasks.keys(), key=int)
    for i in range(len(task_ids)):
        for j in range(i + 1, len(task_ids)):
            overlap = parallel_tasks[task_ids[i]] & parallel_tasks[task_ids[j]]
            if overlap:
                failures.append(f"Task {task_ids[i]} + Task {task_ids[j]}: file overlap on parallel tasks — {', '.join(sorted(overlap))}")

    # Check 6: PR body quality — delegate to _check_pr_body_quality
    _check_pr_body_quality(spec_text, failures)

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
