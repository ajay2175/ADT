# Pilot v1 — Authenticated dataset v1 (curation workspace)

**Status:** `curation_in_progress_not_frozen` — official H1 run **prohibited** until `FROZEN.json` status is `frozen`.

## Scope

Curate **all 120** observations across **development (60), validation (20), and test (40)** with traceable sources. Curating only the test split would bias comparison against artificial train/val patterns.

## Files (populate during curation)

| File | Purpose |
|------|---------|
| `observations_development.jsonl` | 60 rows |
| `observations_validation.jsonl` | 20 rows |
| `observations_test.jsonl` | 40 rows (confirmatory held-out) |
| `curation_log.md` | Curator, date, decisions |
| `exclusions.jsonl` | Rejected candidates with reason |
| `integrity_report.json` | Output of integrity script after curation |

Calibration: continue in `../calibration/` (10 Ayurveda); do not merge into test without new protocol version.

## Bias controls

- Curate from sources **before** inspecting model outputs on those cases.
- Separate curators from blind evaluators where possible.
- Log all exclusions.
- Enforce `cluster_id` — no related observations across splits.

## When complete

1. Run integrity checks (see `docs/H1_DATA_CURATION_PROTOCOL.md`).
2. Set `FROZEN.json` → `status: frozen`, fill model slots, record git commit.
3. Point official runners at `authenticated_v1` (protocol update in same commit as freeze).

Placeholder archive remains at `../placeholder_archive/` for traceability.
