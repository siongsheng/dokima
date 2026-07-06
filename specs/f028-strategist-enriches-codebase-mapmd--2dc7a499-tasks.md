# Task Breakdown: F028: Strategist enriches codebase-map.md during normal feature planning — appends architecture decisions and agent guidance discovered during exploration. Map accumulates real-world rationale across features with zero extra LLM calls.

### Task 1: Implement enrichment preservation in generate_codebase_map
**Files:** utils.py
**Dependencies:** [none]
**Description:** Implement enrichment preservation in generate_codebase_map

### Task 2: Update strategist prompt with enrichment instructions
**Files:** pipeline.py
**Dependencies:** 1
**Description:** Update strategist prompt with enrichment instructions

### Task 3: Update _make_map_hint to mention enrichments
**Files:** pipeline.py
**Dependencies:** 1
**Description:** Update _make_map_hint to mention enrichments

### Task 4: Write enrichment preservation tests
**Files:** tests/test_codebase_map.py
**Dependencies:** 1
**Description:** Write enrichment preservation tests
