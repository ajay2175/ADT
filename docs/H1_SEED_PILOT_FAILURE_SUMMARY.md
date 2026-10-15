# H1 seed pilot — failure anatomy summary

**Anatomy report:** `python -m app.experiments.run_h1_failure_anatomy`  
**Full JSON:** `data/experiments/h1_concept_discovery/reports/h1_failure_anatomy_<commit>.json`

## Seed pilot (legacy micro-set)

| Outcome | Value |
|---------|--------|
| Pre-registered success | **No** (negative) |
| Interpretation | Did not meet strict dominance + adjudicated ground truth |

**Read diagnostics separately:**

| Bucket | Where to look |
|--------|----------------|
| Concept generation / novelty / validation | `proposal_diagnostics[].failure_kinds` |
| Transfer / baselines | `per_case[].failure_kinds` |
| Inconclusive (not failure) | `adjudication_not_ready` on pilot v1 `test` split |

## Pilot v1 (40 confirmatory cases)

Until `ground_truth_ready` and authentic observations: status **inconclusive**, not ADT success/failure.

## Next scientific milestone

1. **Calibrate** on `pilot_v1/calibration/ayurveda_10_cases.jsonl` (not confirmatory).  
2. **Curate** remaining `test` split with verified sources.  
3. **Blinded** panel + frozen automated comparison.  
4. Publish **H1 report** (positive, negative, or inconclusive).
