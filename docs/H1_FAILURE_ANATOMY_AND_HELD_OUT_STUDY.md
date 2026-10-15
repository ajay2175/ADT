# H1 Failure Anatomy & 60-case held-out study

**Protocol 1.2.0** · Next milestone: **H1 Failure Anatomy and Blind Adjudication Report** (not an ADT software release)

## 1. Seed pilot result (15fefcb era)

Pre-registered outcome on seed data: **negative**. This does not generalize to “Padārtha fails”; it localizes **where** the pipeline failed.

Generate anatomy:

```bash
cd backend && PYTHONPATH=. python -m app.experiments.run_h1_failure_anatomy --seed 42
```

Output: `data/experiments/h1_concept_discovery/reports/h1_failure_anatomy_<commit>.json`

## 2. Failure categories (per-case + per-proposal)

| Category | Question |
|----------|----------|
| `concept_generation` | Were viable clusters / Sāmānya proposed? |
| `novelty_filtering` | Were useful concepts rejected as non-novel? |
| `validation` | Did Pramāṇa / H2 contradictions reject valid candidates? |
| `generalization` | Did accepted concepts fail on unseen signatures? |
| `baseline_strength` | Did baselines already match the case? |
| `adjudication_not_ready` | Missing ground truth (inconclusive, not success) |

Separate **generation/validation** failures from **transfer** failures in the JSON (`proposal_diagnostics` vs `per_case`).

## 3. Novelty levels (1.2.0)

| Level | Criterion |
|-------|-----------|
| Lexical | Jaccard vs seed `samanya` |
| Structural | New Guṇa–Karma pattern vs seed |
| **Functional (decisive)** | Held-out accuracy **with** category minus **without** (ablation) |

Protocol refinements are versioned; confirmatory criteria from 1.1.0 remain primary; functional novelty is required for scientific “usefulness.”

## 4. Held-out study v1 (60 cases)

```bash
PYTHONPATH=. python -m app.experiments.run_h1_failure_anatomy --freeze-held-out-study --seed 42
```

- `held_out_study_v1/cases.jsonl` — 30 Ayurveda + 30 materials (curate `guna`/`karma`/provenance before official run)
- No ID overlap with `pilot_v1` development/validation
- Freeze `FROZEN.json` model slots before confirmatory run

## 5. Confirmatory vs exploratory

- **Confirmatory:** Unchanged strict dominance + accepted novel category on adjudicated test set.
- **Exploratory:** Lexical/structural novelty, utility deltas, exception handling—report separately; replicate before new claims.
