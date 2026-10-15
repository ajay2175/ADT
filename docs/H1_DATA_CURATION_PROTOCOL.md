# H1 Pilot v1 — Data curation protocol

**Design lock:** `6e8b8bb` · **Authenticated dataset:** `pilot_v1/authenticated_v1/`  
**Archived placeholders:** `pilot_v1/placeholder_archive/` (immutable)

---

## 1. Why a new dataset version

Replacing synthetic placeholders changes experimental inputs. **Authenticated v1** is a separately versioned, source-grounded dataset. Original placeholder runs remain traceable; official pre-registered comparison uses **only** the frozen authenticated bundle.

---

## 2. What must be curated (all splits)

| Split | n | Domain mix |
|-------|---|------------|
| development | 60 | 30 Ayurveda + 30 materials |
| validation | 20 | 10 + 10 |
| test (confirmatory) | 40 | 20 + 20 |

**Not sufficient:** curating only the 40 test cases while leaving dev/val synthetic.

---

## 3. Required fields per observation

See `authenticated_v1/observation_schema.json`:

- **observation_id**, **dravya**, **guna**, **karma**, **context**
- **source** (exact reference, evidence_type, reliability)
- **domain**, **split**, **cluster_id** (leakage control)
- **ground_truth** (adjudication_status, holdout_cluster when ready)

### Pramāṇa distinction

| Domain | Classical text | Modern claim |
|--------|----------------|--------------|
| Ayurveda | What tradition **describes** | Biomedical efficacy requires **separate** experimental evidence_type |
| Materials | — | **Measured** vs **simulated** must be tagged |

---

## 4. Bias controls

1. Select sources **before** viewing model predictions on those IDs.
2. Curators ≠ blind evaluators when feasible.
3. Record every exclusion in `exclusions.jsonl`.
4. **cluster_id:** no cluster may span development, validation, and test.
5. Do not edit `placeholder_archive/`.

---

## 5. Recommended sequence

1. **10 Ayurveda calibration** — verify citations; blind rubric calibration (`calibration/ayurveda_10_cases.jsonl`).
2. **Full 120** — dev, val, test with provenance.
3. **Integrity** — `python -m app.experiments.h1_curation_integrity` (after rows exist).
4. **Freeze** — update `authenticated_v1/FROZEN.json`, model IDs, commit hash.
5. **Blinded adjudication** — panel on SYS-* packets.
6. **Official comparison** — pre-registered baselines + ADT; publish all outcomes.

---

## 6. Success definition (unchanged)

Demonstrate—or rigorously fail to demonstrate—that Padārtha–Pramāṇa–Jñāna-style abstraction yields a **useful new conceptual distinction** with **functional utility** on held-out observations, vs equivalent baselines.

---

## 7. What not to do before freeze

- No new ADT modules or benchmark scale-up
- No ontology auto-apply
- No changing pre-registered Pilot v1 success criteria
- No treating calibration cases as hidden confirmatory test

---

*Protocol document — Track A — 2026-10-15*
