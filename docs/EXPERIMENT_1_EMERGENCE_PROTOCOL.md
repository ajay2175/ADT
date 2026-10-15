# Experiment 1 — Emergence of New Knowledge (H1)

**Track A milestone (primary)** · Protocol version **1.0.0**  
**Hypotheses:** Universal Cognitive Grammar · Self-Evolving Knowledge · Knowledge Interoperability  
**Platform:** ADT ≥ `eb588a3`; run via `python -m app.experiments.run_h1`

---

## 1. Research hypothesis

A system with **explicit Padārtha-based abstraction** (Sāmānya / Viśeṣa / Abhāva over Guṇa–Karma structure) plus **optional epistemic validation** (Pramāṇa / Jñāna) discovers **useful novel categories** and **generalizes** to held-out instances more effectively than otherwise equivalent systems **without** those mechanisms.

**Falsification:** On held-out tasks, Padārtha-on does **not** beat all baselines on transfer accuracy and exception F1, or proposed “novel” categories are lexical duplicates of seed ontology (memorization).

---

## 2. Formal Padārtha mechanism (experiment scope)

### 2.1 Seed ontology (fixed for a run)

- Finite sets: `dravya`, `guna`, `karma`, `samanya` (named abstractions), `samavaya` rules (optional).
- **Excluded target:** The latent Sāmānya that explains training Viśeṣa is **not** listed in `seed_ontology.samanya`.
- Novelty is measured against this seed only (not against the whole internet).

### 2.2 Observations (Viśeṣa instances)

Each observation `o` is a record:

```json
{
  "id": "obs-001",
  "domain": "vaidya_mitra | materials_science",
  "dravya": "entity label",
  "guna": ["..."],
  "karma": ["..."],
  "labels": { "holdout_cluster": "optional for eval only" }
}
```

Observations are **not** assertions in the KG until ingested for a baseline; ADT proposes structure from the multiset of observations.

### 2.3 Abstraction operator 𝒜 (Sāmānya proposal)

Given training observations `O_train` and seed `Σ`:

1. **Signature:** `sig(o) = (sorted(guna), sorted(karma))` — experiment v1 uses co-occurring Guṇa–Karma pattern.
2. **Cluster:** Group by `sig` with count ≥ `min_support` (default 2).
3. **Candidate Sāmānya:** For cluster `C` with signature `s`, propose `μ = (name( s ), members(C), visesha_exceptions, abhava_flags)`.
4. **Name:** `name(s)` is a deterministic slug from Guṇa–Karma tokens (not LLM-freeform in v1) to aid reproducibility; expert rubric renames for publication.
5. **Viśeṣa:** Members of `C` that share Guṇa but diverge on Karma (or flagged `outlier: true`) attach as **viśeṣa** exceptions, not a new universal.
6. **Abhāva:** Observations with explicit `abhava: [...]` in data must not be absorbed into Sāmānya without recording typed absence.

### 2.4 Novelty predicate 𝒩(μ, Σ)

`𝒩(μ, Σ) = true` iff:

- Normalized label of `μ` has **Jaccard similarity < 0.6** to every `σ ∈ Σ.samanya` (token sets), **and**
- `μ` is not a substring rename of any seed dravya/guna/karma token alone.

Memorization failure: high overlap with seed → category discarded from “discovery” metrics (still logged).

### 2.5 Validation operator 𝒱 (epistemic)

| Mode | Behavior |
|------|----------|
| `padartha_only` | Accept 𝒜 output if 𝒩 holds |
| `padartha_pramana` | Require ≥1 synthetic/support observation in cluster as evidence record; entailment `supports` |
| `padartha_pramana_jnana` | Promote to `prama` state before use in transfer |

Rejected proposals remain in audit log; they do not enter transfer stage.

### 2.6 Transfer task

Given held-out observation `o*` in domain `D'` (possibly `D' ≠ D_train`):

- **Predict** cluster / Sāmānya membership using accepted abstractions only.
- **Score:** accuracy vs adjudicated `holdout_cluster`; **false universal** if model assigns universal when `outlier: true`.

Cross-domain: train abstractions on Vaidya `O_train`, test on materials `O*_held` with **isomorphic signature** (documented in case file, not leaked labels in production runs).

---

## 3. Baselines (same information, comparable access)

| ID | Mechanism |
|----|-----------|
| **B-LLM** | Majority co-occurring Guṇa token per dravya (simulates label-free LLM naming without structure) |
| **B-KG** | Lookup dravya in seed only; else `unknown` (no 𝒜) |
| **B-NeuroSym** | Fixed relation templates; no new Sāmānya nodes |
| **ADT−** | 𝒜 with Padārtha encoding disabled (signature clustering only, no 𝒩/𝒱) |
| **ADT+** | Full 𝒜 + 𝒩 + 𝒱 per config |

**Fairness:** All conditions receive identical `O_train` and `O_held` files; same random seed; LLM calls (if added later) use same model ID in env.

---

## 4. Measurements

| Metric | Definition | Primary |
|--------|------------|---------|
| Novel category validity | Expert rubric 1–5 (blind) | Yes |
| Held-out predictive accuracy | Correct Sāmānya / cluster on `held_out` | Yes |
| Exception F1 | Viśeṣa / outlier detection | Yes |
| Cross-domain transfer | Accuracy on materials slice after Vaidya train | Yes |
| False universal rate | Universal assigned to outliers | Yes |
| Proposal precision | Accepted / proposed after 𝒱 | Secondary |
| Cost | Wall time, tokens (if LLM) | Secondary |

**Success (pre-registered for protocol v1):**  
`ADT+` exceeds **every** baseline on **held-out predictive accuracy** and **exception F1** with **≥1** accepted novel `𝒩(μ,Σ)`, on **both** domain slices OR clear cross-domain transfer above B-KG.

**Failure (valuable):** No accepted novel category, or no metric dominance → Padārtha adds representation only.

---

## 5. Datasets

| File | Role |
|------|------|
| `data/experiments/h1_concept_discovery/seed_ontology.json` | Frozen Σ |
| `data/experiments/h1_concept_discovery/train_observations.json` | `O_train` (dev + train splits in records) |
| `data/experiments/h1_concept_discovery/held_out.json` | `O_held` (no labels in runner input; labels in `adjudication` block for scoring) |
| `data/experiments/h1_concept_discovery/manifest.json` | Version hash, metrics, rubric |

**Splits:** Runner accepts `--split held_out` only for official numbers; `dev` for debugging.

**Expert adjudication:** Fields `ground_truth_adjudication: pending_expert` until human fill; runner outputs machine-scorable columns where `adjudication` present.

---

## 6. Procedure (reproducible run)

```bash
cd backend
PYTHONPATH=. python -m app.experiments.run_h1 --split held_out --config padartha_pramana_jnana --seed 42
```

Outputs: `data/experiments/h1_concept_discovery/runs/<timestamp>_h1_report.json` with git commit, seed, proposals, metrics per baseline, **negative result flag**.

---

## 7. Ethics and domain note

Vaidya cases are **computational epistemology** exercises, not clinical advice. Materials cases test transfer only. No autonomous ontology **apply** to production constitution or clinical pathways.

---

## 8. Relation to Experiments 2 and 3

- **H2** protocol will reuse 𝒱 and entailment on misleading śabda; prepare in parallel, do not block H1 run.
- **H3** will consume **accepted** Sāmānya as variables in causal hypotheses; H1 must complete first per research sequence.

---

*Protocol 1.0.0 — 2026-10-15*
