"""Task 13: Verify module-level globals removed from utils.py.

PipelineContext replaces the 25+ module-level globals in utils.py.
Functions inside utils.py that used `global` declarations now use `_ctx` fields.
Backward-compatible access is maintained for other modules.
"""

import pytest
import sys
import os


class TestPipelineContextInUtils:
    """PipelineContext dataclass exists and globals are removed/replaced."""

    def test_pipelinecontext_exists_in_utils(self):
        """PipelineContext dataclass can be imported from utils."""
        from utils import PipelineContext
        assert PipelineContext is not None
        ctx = PipelineContext()
        assert ctx.project_dir == ""
        assert ctx.repo == ""
        assert ctx.default_branch == "master"

    def test_pipelinecontext_has_all_required_fields(self):
        """PipelineContext has all fields that were previously module globals."""
        from utils import PipelineContext
        ctx = PipelineContext()
        # Project identity
        assert hasattr(ctx, 'project_dir')
        assert hasattr(ctx, 'repo')
        assert hasattr(ctx, 'default_branch')
        assert hasattr(ctx, 'panel_feature')
        assert hasattr(ctx, 'panel_dir')
        # Paths
        assert hasattr(ctx, 'real_home')
        assert hasattr(ctx, 'hermes_home')
        assert hasattr(ctx, 'hermes_bin')
        assert hasattr(ctx, 'profiles_dir')
        assert hasattr(ctx, 'output_log')
        # API
        assert hasattr(ctx, 'api_key')
        # Ports
        assert hasattr(ctx, 'panel_port')
        assert isinstance(ctx.panel_port, dict)
        # Flags
        assert hasattr(ctx, 'skip_autofix')
        assert hasattr(ctx, 'force_full')
        assert hasattr(ctx, 'skip_human_gate')
        assert hasattr(ctx, 'max_parallel_override')
        assert hasattr(ctx, 'resume')
        assert hasattr(ctx, 'max_continuous')
        # Commands
        assert hasattr(ctx, 'test_cmd')
        assert hasattr(ctx, 'build_cmd')
        assert hasattr(ctx, 'lint_cmd')
        # Transient state (repr=False)
        assert hasattr(ctx, '_log_file_handle')
        assert hasattr(ctx, '_lock_fd')
        assert hasattr(ctx, '_log_file')
        assert hasattr(ctx, '_stdout_orig')
        assert hasattr(ctx, '_gh_token_cache')
        # Model fallback
        assert hasattr(ctx, 'fallback_models')
        assert isinstance(ctx.fallback_models, dict)

    def test_pipelinecontext_defaults_match_old_globals(self):
        """PipelineContext defaults match the old module-level global defaults."""
        from utils import PipelineContext
        ctx = PipelineContext()
        assert ctx.default_branch == "master"
        assert ctx.project_dir == ""
        assert ctx.output_log == "/tmp/dokima-output.txt"
        assert ctx.max_continuous == 20
        assert ctx.test_cmd == "npm test"
        assert ctx.build_cmd == "npm run build"
        assert ctx.lint_cmd == "npm run lint"
        assert ctx.skip_autofix is False
        assert ctx.force_full is False
        assert ctx.skip_human_gate is False
        assert ctx.max_parallel_override is None
        assert ctx.resume is None

    def test_pipelinecontext_computed_paths(self):
        """PipelineContext computed paths (hermes_home, hermes_bin, profiles_dir)
        are derived from real_home."""
        from utils import PipelineContext
        ctx = PipelineContext(real_home="/home/testuser")
        assert ctx.hermes_home == "/home/testuser/.hermes"
        assert ctx.hermes_bin == "/home/testuser/.hermes/hermes-agent/venv/bin/hermes"
        assert ctx.profiles_dir == "/home/testuser/.hermes/profiles"

    def test_pipelinecontext_mutable_default_isolation(self):
        """PipelineContext dict fields use factories to avoid shared mutable defaults."""
        from utils import PipelineContext
        c1 = PipelineContext()
        c2 = PipelineContext()
        assert c1.panel_port is not c2.panel_port
        assert c1.fallback_models is not c2.fallback_models
        c1.panel_port["test"] = 9999
        assert "test" not in c2.panel_port
        c1.fallback_models["x"] = "y"
        assert "x" not in c2.fallback_models

    def test_no_global_declarations_in_utils_functions(self):
        """utils.py functions that previously used `global` now use _ctx fields.

        We verify by importing the module and checking the function source code
        or by calling functions and verifying they don't rely on module globals.
        """
        import utils
        import inspect

        # Functions that previously had `global` declarations
        # should now use _ctx fields instead
        global_using_funcs = ['_write_log_line', 'gh', '_cleanup_lock']

        for func_name in global_using_funcs:
            func = getattr(utils, func_name, None)
            if func is None:
                continue
            source = inspect.getsource(func)
            # After refactor, these should NOT contain 'global' statements
            # for the old module-level state variables
            for old_global in ['_LOG_FILE_HANDLE', '_GH_TOKEN_CACHE',
                               '_LOCK_FD', '_LOG_FILE', '_STDOUT_ORIG']:
                assert f'global {old_global}' not in source, \
                    f"{func_name} still has 'global {old_global}'"


class TestBackwardCompatibleAccess:
    """Old global names still work for backward compatibility."""

    def test_old_global_names_still_accessible(self):
        """PROJECT_DIR, REPO etc. are still accessible as module attributes."""
        import utils
        # These should still be accessible (via __getattr__ or direct vars)
        assert hasattr(utils, 'PROJECT_DIR')
        assert hasattr(utils, 'REPO')
        assert hasattr(utils, 'DEFAULT_BRANCH')
        assert hasattr(utils, 'OUTPUT_LOG')

    def test_old_global_names_return_correct_defaults(self):
        """Old global names return the correct default values."""
        import utils
        assert utils.DEFAULT_BRANCH == "master"
        assert isinstance(utils.PANEL_PORT, dict)
        assert "strategist" in utils.PANEL_PORT

    def test_old_global_names_are_mutable(self):
        """Old global names can still be assigned to (backward compat)."""
        import utils
        old_val = utils.PROJECT_DIR
        try:
            utils.PROJECT_DIR = "/tmp/test_project_dir"
            assert utils.PROJECT_DIR == "/tmp/test_project_dir"
        finally:
            utils.PROJECT_DIR = old_val


class TestPipelineContextRepr:
    """repr() excludes transient fields marked repr=False."""

    def test_repr_excludes_transient_fields(self):
        """repr(PipelineContext) does not include _log_file_handle etc."""
        from utils import PipelineContext
        ctx = PipelineContext(project_dir="/test")
        r = repr(ctx)
        assert "project_dir" in r
        assert "_log_file_handle" not in r
        assert "_lock_fd" not in r
        assert "_log_file" not in r
        assert "_stdout_orig" not in r
        assert "_gh_token_cache" not in r
