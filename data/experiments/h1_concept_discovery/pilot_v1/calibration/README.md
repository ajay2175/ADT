# H1 Pilot v1 — Ayurveda calibration set (n=10)

**Purpose:** Rubric calibration and adjudicator training — **not** the blinded confirmatory test.

| Set | n | Role |
|-----|---|------|
| `ayurveda_10_cases.jsonl` | 10 | Calibration (may inform rubric wording) |
| `pilot_v1` `test` split | 40 | Confirmatory held-out (after curation + adjudication) |
| `held_out_study_v1` | 60 | Separate replication study (deferred) |

## Design principle (discovery, not retrieval)

Cases are chosen so the **latent Guṇa–Karma–prabhāva pattern is not named** in `seed_ontology.json` `samanya`. Classical sources are cited for **Viśeṣa** grounding; the system must propose **Sāmānya**, not retrieve an existing ontology node.

## Workflow

1. Domain expert verifies `classical_source` citations.
2. Panel scores blinded SYS-* outputs using `adjudication_record_schema.json`.
3. If rubric or protocol changes, these 10 become **development/calibration** permanently; do not reuse as confirmatory test.
4. Remaining `test` cases stay sealed until blinded run.

## Exploratory (not confirmatory)

**Category revision:** cases `cal-ayur-008`–`010` include staged observations where an initial Guṇa-based grouping is **inadequate** and Viśeṣa under specific conditions should split the abstraction (H1→H2 link). Analyze separately; do not add to pre-registered success criteria.
