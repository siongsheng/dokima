# F044: PR Body Quality

## Impact
Reviewers open a PR and immediately understand what changed — one-sentence Why, product-value Impact, clean nm Review. No walls of strategist text.

### Task 1: Trim extract_pr_sections output
**Files:** spec_extract.py
**Dependencies:** [none]
**Parallelizable:** no
**Description:** In extract_pr_sections(): trim Why to first 2 sentences (max 200 chars). Trim Impact to product-value only — strip meta-commentary ("the spec was a skeleton"), strategist internal thinking ("Here is the COMPLETE corrected spec"), and verbose descriptions. Strip nm Review of shell commands, reasoning noise, and terminal output — keep only risk assessment and key findings. Add tests.
