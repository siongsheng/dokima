"""Task 3 tests: Verify ctx parameter added to pipeline.py phase functions.

Uses source-code inspection (not import) since PipelineContext dataclass
is defined in Task 1, which is a parallel workstream.
"""
import os
import re


PIPELINE_PATH = os.path.join(os.path.dirname(__file__), "..", "pipeline.py")

# 11 functions from the spec that must receive ctx as a parameter
TARGET_FUNCTIONS = [
    "run_pipeline",
    "run_phase1_strategist",
    "run_phase2_coder",
    "run_phase3_vet",
    "run_phase4_nm",
    "run_phase5_tech_lead",
    "run_post_pipeline",
    "run_fix_mode",
    "run_fix_mode_issue",
    "discover_blocked_pr",
    "extract_blockers_from_pr",
]


def _parse_signatures(source):
    """Parse function signatures from source code.

    Returns dict: {func_name: {'params': [param_names], 'line': N}}.
    Handles multi-line signatures (continued with backslash or paren nesting).
    """
    signatures = {}
    # Match 'def func_name(' ... '):' — handles multi-line via paren balancing
    pattern = re.compile(r'^def\s+(\w+)\s*\(', re.MULTILINE)
    for m in pattern.finditer(source):
        name = m.group(1)
        if name not in TARGET_FUNCTIONS:
            continue
        start = m.end() - 1  # position of opening '('
        # Find matching '):' by balancing parentheses
        depth = 1
        pos = start + 1
        while pos < len(source) and depth > 0:
            if source[pos] == '(':
                depth += 1
            elif source[pos] == ')':
                depth -= 1
            pos += 1
        # pos is now after the closing ')', check for ':'
        if pos < len(source) and source[pos] == ':':
            sig_text = source[start + 1:pos - 1]  # content between ( )
            # Split params respecting nested parens in default values
            params = []
            current = ""
            pdepth = 0
            for ch in sig_text + ',':
                if ch == '(':
                    pdepth += 1
                    current += ch
                elif ch == ')':
                    pdepth -= 1
                    current += ch
                elif ch == ',' and pdepth == 0:
                    params.append(current.strip())
                    current = ""
                else:
                    current += ch
            params = [p for p in params if p]  # remove empty strings
            line_num = source[:m.start()].count('\n') + 1
            signatures[name] = {"params": params, "line": line_num}
    return signatures


def _read_pipeline():
    with open(PIPELINE_PATH) as f:
        return f.read()


def _has_ctx_param(params):
    """Check if 'ctx' is among the parameter names (ignoring defaults)."""
    return any(p.split('=')[0].strip() == 'ctx' for p in params)


class TestPipelineContextSignatures:
    """Verify all 11 pipeline functions have ctx parameter."""

    def test_all_11_functions_found(self):
        """All 11 target functions exist in pipeline.py."""
        source = _read_pipeline()
        sigs = _parse_signatures(source)
        found = set(sigs.keys())
        expected = set(TARGET_FUNCTIONS)
        missing = expected - found
        assert not missing, (
            f"Missing functions in pipeline.py: {sorted(missing)}"
        )

    def test_run_pipeline_has_ctx(self):
        sigs = _parse_signatures(_read_pipeline())
        assert "run_pipeline" in sigs
        params = sigs["run_pipeline"]["params"]
        assert _has_ctx_param(params), (
            f"run_pipeline should have 'ctx' param. Full: {params}"
        )

    def test_run_phase1_strategist_has_ctx(self):
        sigs = _parse_signatures(_read_pipeline())
        assert "run_phase1_strategist" in sigs
        params = sigs["run_phase1_strategist"]["params"]
        assert _has_ctx_param(params), f"Full: {params}"

    def test_run_phase2_coder_has_ctx(self):
        sigs = _parse_signatures(_read_pipeline())
        assert "run_phase2_coder" in sigs
        params = sigs["run_phase2_coder"]["params"]
        assert _has_ctx_param(params), f"Full: {params}"

    def test_run_phase3_vet_has_ctx(self):
        sigs = _parse_signatures(_read_pipeline())
        assert "run_phase3_vet" in sigs
        params = sigs["run_phase3_vet"]["params"]
        assert _has_ctx_param(params), f"Full: {params}"

    def test_run_phase4_nm_has_ctx(self):
        sigs = _parse_signatures(_read_pipeline())
        assert "run_phase4_nm" in sigs
        params = sigs["run_phase4_nm"]["params"]
        assert _has_ctx_param(params), f"Full: {params}"

    def test_run_phase5_tech_lead_has_ctx(self):
        sigs = _parse_signatures(_read_pipeline())
        assert "run_phase5_tech_lead" in sigs
        params = sigs["run_phase5_tech_lead"]["params"]
        assert _has_ctx_param(params), f"Full: {params}"

    def test_run_post_pipeline_has_ctx(self):
        sigs = _parse_signatures(_read_pipeline())
        assert "run_post_pipeline" in sigs
        params = sigs["run_post_pipeline"]["params"]
        assert _has_ctx_param(params), f"Full: {params}"

    def test_run_fix_mode_has_ctx(self):
        sigs = _parse_signatures(_read_pipeline())
        assert "run_fix_mode" in sigs
        params = sigs["run_fix_mode"]["params"]
        assert _has_ctx_param(params), f"Full: {params}"

    def test_run_fix_mode_issue_has_ctx(self):
        sigs = _parse_signatures(_read_pipeline())
        assert "run_fix_mode_issue" in sigs
        params = sigs["run_fix_mode_issue"]["params"]
        assert _has_ctx_param(params), f"Full: {params}"

    def test_discover_blocked_pr_has_ctx(self):
        sigs = _parse_signatures(_read_pipeline())
        assert "discover_blocked_pr" in sigs
        params = sigs["discover_blocked_pr"]["params"]
        assert _has_ctx_param(params), f"Full: {params}"

    def test_extract_blockers_from_pr_has_ctx(self):
        sigs = _parse_signatures(_read_pipeline())
        assert "extract_blockers_from_pr" in sigs
        params = sigs["extract_blockers_from_pr"]["params"]
        assert _has_ctx_param(params), f"Full: {params}"
