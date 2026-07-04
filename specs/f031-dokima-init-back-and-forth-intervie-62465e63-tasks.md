# Task Breakdown: F031: dokima init back-and-forth interview mode — strategist asks clarifying questions about users, goals, anti-goals, and constraints before producing constitution docs. Loops until confidence is High, then writes specs/mission.md, specs/tech-stack.md, specs/roadmap.md, specs/conventions.md.

### Task 1: Add interview detection helpers to utils.py
**Files:** utils.py
**Dependencies:** [none]
**Description:** Add interview detection helpers to utils.py

### Task 2: Extract interview answer loop into shared helper
**Files:** utils.py
**Dependencies:** 1
**Description:** Extract interview answer loop into shared helper

### Task 3: Refactor pipeline.py to use shared interview helper
**Files:** pipeline.py
**Dependencies:** 2
**Description:** Refactor pipeline.py to use shared interview helper

### Task 4: Enhance init strategist prompt for interview mode
**Files:** roadmap.py
**Dependencies:** [none]
**Description:** Enhance init strategist prompt for interview mode

### Task 5: Add interview loop to run_init() — core loop
**Files:** roadmap.py
**Dependencies:** 2, 4
**Description:** Add interview loop to run_init() — core loop

### Task 6: Add --answers flag support to init
**Files:** roadmap.py, utils.py
**Dependencies:** 5
**Description:** Add --answers flag support to init

### Task 7: Add max_turns restore on all exit paths
**Files:** roadmap.py
**Dependencies:** 5
**Description:** Add max_turns restore on all exit paths

### Task 8: Write tests for init interview loop
**Files:** tests/test_f031_init_interview.py
**Dependencies:** 5, 6
**Description:** Write tests for init interview loop

### Task 9: Write tests for interview utility helpers
**Files:** tests/test_f031_utils_helpers.py
**Dependencies:** 1
**Description:** Write tests for interview utility helpers

### Task 10: Write tests for collect_interview_answers
**Files:** tests/test_f031_collect_answers.py
**Dependencies:** 2
**Description:** Write tests for collect_interview_answers

### Task 11: Write tests for pipeline refactor
**Files:** tests/test_f031_pipeline_refactor.py
**Dependencies:** 3
**Description:** Write tests for pipeline refactor

### Task 12: Write tests for init loop structure
**Files:** tests/test_f031_init_loop.py
**Dependencies:** 5
**Description:** Write tests for init loop structure
