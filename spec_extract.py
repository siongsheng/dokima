"""spec_extract — Text processing and spec extraction utilities for Dokima.

Extracted from utils.py (F041: Split utils.py into domain modules).
Pure text processing — no external dependencies beyond Python stdlib.
"""
import sys
import os
import re


def _sanitize_prompt(text):
    """Strip known injection patterns from user-supplied text before it enters agent prompts.
    Strips backtick-escaped shell commands, markdown code blocks with dangerous commands,
    and SYSTEM:/OVERRIDE: prefix injection attempts. Logs a warning on any strip."""
    if not text:
        return text
    original = text
    # Strip SYSTEM: / OVERRIDE: prefix injection (case-insensitive, word-boundary)
    text = re.sub(r'\b(?:SYSTEM|OVERRIDE)\s*:\s*', '', text, count=0, flags=re.IGNORECASE)
    # Strip backtick content that looks like a shell command (has spaces, pipes,
    # redirects, or starts with $ for expansion). Single-word inline code like
    # `--help-json` or `config.yaml` is legitimate Markdown — don't strip it.
    SHELL_PATTERN = r'[\s|&;<>$]'
    text = re.sub(r'`[^`]*' + SHELL_PATTERN + r'[^`]*`', '', text)
    # Strip markdown code blocks (```cmd``` or ```\ncmd\n```) containing dangerous patterns
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    # Collapse multiple spaces
    text = re.sub(r' +', ' ', text).strip()
    if text != original:
        stripped = original[:80].strip()
        print(f"  WARNING: Sanitized prompt injection from feature text: {stripped!r}", file=sys.stderr, flush=True)
    return text


def _redact_secrets(text):
    """Strip GH_TOKEN, GITHUB_TOKEN, and API_SERVER_KEY values from text.
    Looks up current values from the environment at call time (not cached).
    Redacts with [REDACTED]. Returns the redacted text unmodified if no tokens found."""
    if not text:
        return text
    tokens = []
    for env_name in ("GH_TOKEN", "GITHUB_TOKEN", "API_SERVER_KEY", "GLAB_TOKEN", "GITLAB_TOKEN"):
        val = os.environ.get(env_name, "")
        if val:
            tokens.append(val)
    if not tokens:
        return text
    result = text
    for tok in tokens:
        result = result.replace(tok, "[REDACTED]")
    return result


def slugify(text):
    import hashlib
    base = re.sub(r'[^a-z0-9-]', '', text.lower().replace(" ", "-"))[:40]
    if len(text) > 40:
        h = hashlib.md5(text.encode()).hexdigest()[:8]
        return f"{base}-{h}"
    return base


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
