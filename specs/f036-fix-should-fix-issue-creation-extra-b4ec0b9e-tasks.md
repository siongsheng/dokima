# Task Breakdown: F036: Fix SHOULD FIX issue creation: extract from PR review text (not just nm_stdout), handle table-format findings (R1 | RELIABILITY | ... | SHOULD FIX). Add tests for all extraction formats.

### Task 1: Add extract_should_fix_from_text() to utils.py
**Files:** utils.py
**Dependencies:** [none]
**Description:** Add extract_should_fix_from_text() to utils.py

### Task 2: Wire unified extractor into pipeline.py SHOULD FIX issue creation
**Files:** pipeline.py
**Dependencies:** 1
**Description:** Wire unified extractor into pipeline.py SHOULD FIX issue creation

### Task 3: Add tests for all SHOULD FIX extraction formats
**Files:** tests/test_f036_should_fix_extraction.py
**Dependencies:** 1
**Description:** Add tests for all SHOULD FIX extraction formats
