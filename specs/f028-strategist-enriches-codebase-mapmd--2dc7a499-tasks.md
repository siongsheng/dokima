# Task Breakdown: F028: Strategist enriches codebase-map.md during normal feature planning — appends architecture decisions and agent guidance discovered during exploration. Map accumulates real-world rationale across features with zero extra LLM calls.

### Task 1: Add enrichment data functions to utils.py
**Files:** utils.py
**Dependencies:** [none]
**Description:** Add enrichment data functions to utils.py

### Task 2: Modify generate_codebase_map() to inject Agent Guidance section
**Files:** utils.py
**Dependencies:** 1
**Description:** Modify generate_codebase_map() to inject Agent Guidance section

### Task 3: Inject > MAP: hint into strategist prompt and wire extraction
**Files:** pipeline.py
**Dependencies:** 1
**Description:** Inject > MAP: hint into strategist prompt and wire extraction

### Task 4: Add tests for enrichment extraction, storage, and map injection
**Files:** tests/test_codebase_map.py
**Dependencies:** 1, 2, 3
**Description:** Add tests for enrichment extraction, storage, and map injection
