# H1 Pilot v1 — Ayurveda calibration set (n=10)

**Purpose:** Rubric calibration and adjudicator training — **not** the blinded confirmatory test.

| Set | n | Role |
|-----|---|------|
| `ayurveda_10_cases.jsonl` | 10 | Calibration (may inform rubric wording) |
| `pilot_v1` `test` split | 40 | Confirmatory held-out (after curation + adjudication) |
| `held_out_study_v1` | 60 | Separate replication study (deferred) |

## Data layers (required)

| Directory | Audience |
|-----------|----------|
| `observation_data/` | **Systems only** — no expected category |
| `ground_truth/` | Experts/panel only |
| `source_verification/` | Curation + AI-assisted śabda trace |
| `ayurveda_10_cases.jsonl` | Legacy index (being replaced per-id files) |

See `docs/H1_OBSERVATION_GROUND_TRUTH_SEPARATION.md`.

## Design principle (discovery, not retrieval)

Source passages ground **Viśeṣa**; systems must propose **Sāmānya** without pre-labels in observation files. Research-focus tags belong in `ground_truth/` after verification (`RESEARCH_FOCUS_SOURCING.md`).

## Workflow

1. Domain expert verifies `classical_source` citations.
2. Panel scores blinded SYS-* outputs using `adjudication_record_schema.json`.
3. If rubric or protocol changes, these 10 become **development/calibration** permanently; do not reuse as confirmatory test.
4. Remaining `test` cases stay sealed until blinded run.

## Exploratory (not confirmatory)

**Category revision:** cases `cal-ayur-008`–`010` include staged observations where an initial Guṇa-based grouping is **inadequate** and Viśeṣa under specific conditions should split the abstraction (H1→H2 link). Analyze separately; do not add to pre-registered success criteria.
