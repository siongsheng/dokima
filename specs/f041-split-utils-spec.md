# F041: Split utils.py into Domain Modules

## Impact
Contributors open the right domain module instead of scrolling through 83 functions in one file. 3,351 lines → 4 focused modules.

## What Changed
- git_ops.py: git(), gh(), detect_repo(), _set_gh_token(), _detect_default_branch()
- spec_extract.py: extract_pr_sections(), extract_issue_sections(), clean_spec_content(), verify_spec_quality()
- codebase_map.py: generate_codebase_map(), _build_domain_map(), _build_impact_map()
- control_panel.py: handle_status(), handle_stop(), handle_kill(), handle_list_crons()

### Task 1: Create git_ops.py
**Files:** utils.py, git_ops.py
**Dependencies:** [none]
**Parallelizable:** no
**Description:** Move all git and gh wrapper functions from utils.py into new git_ops.py. Update imports in all files that use git()/gh(). Keep backward compat by re-exporting from utils.py.

### Task 2: Create spec_extract.py
**Files:** utils.py, spec_extract.py
**Dependencies:** [Task 1]
**Parallelizable:** no
**Description:** Move spec extraction functions (extract_pr_sections, extract_issue_sections, clean_spec_content, verify_spec_quality, extract_should_fix_from_text, _extract_nm_summary) to spec_extract.py. Update imports.

### Task 3: Create codebase_map.py and control_panel.py
**Files:** utils.py, codebase_map.py, control_panel.py
**Dependencies:** [Task 2]
**Parallelizable:** no
**Description:** Move codebase map generation to codebase_map.py. Move control panel handlers to control_panel.py. Update all imports. Verify 1029 tests pass.
