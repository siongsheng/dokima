# Task Breakdown: F044: PR body quality — `extract_pr_sections()` currently dumps the strategist's full spec into Why/Impact instead of extracting concise summaries. Fix: trim Why to first 2 sentences (max 200 chars), Impact to product-value-only (strip meta-commentary and internal thinking), strip nm Review of shell commands and reasoning noise.

### Task 1: Add _trim_to_sentences and _filter_impact_product_only helpers + wire into extract_pr_sections()
**Files:** spec_extract.py
**Dependencies:** [none]
**Description:** Add _trim_to_sentences and _filter_impact_product_only helpers + wire into extract_pr_sections()

### Task 2: Add _strip_nm_noise helper + wire into _extract_nm_summary()
**Files:** spec_extract.py
**Dependencies:** 1
**Description:** Add _strip_nm_noise helper + wire into _extract_nm_summary()

### Task 3: Add tests for trimmed PR body output and nm noise stripping
**Files:** tests/test_spec_extract.py
**Dependencies:** 2
**Description:** Add tests for trimmed PR body output and nm noise stripping
