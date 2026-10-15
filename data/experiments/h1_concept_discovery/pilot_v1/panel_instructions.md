# H1 Pilot v1 — Blinded expert panel instructions

**Protocol:** 1.1.0 (Pilot v1) · **Confirmatory held-out:** 40 cases (`test` split) · **Commit anchor:** see repository `FROZEN.json`  
**Replication study (separate):** `held_out_study_v1` (60 cases) is **not** part of Pilot v1 pre-registration; do not retroactively merge designs.

---

## 1. Research question

> Can an epistemologically structured system (**Padārtha abstraction** with **Pramāṇa-governed validation**) discover a **useful conceptual category** that was **not supplied** in the seed ontology, **defend** it against counterexamples, and **apply** it to unfamiliar observations—more effectively than equivalent baselines?

**Not in scope:** Whether ADT can add an ontology node, use Sanskrit labels, or produce fluent prose.

### What counts as a valid new concept (for panel judgment)

1. **Not supplied:** Not already named in the frozen seed ontology (lexical + structural checks are automated; panel confirms structural/definitional novelty).
2. **Defensible:** Supported by the observation lineage shown in the packet; survives stated counterexamples (Viśeṣa / contradictions in trace).
3. **Useful (panel dimension):** Would improve prediction or support a defensible inference on held-out cases—scored independently from automated accuracy (see §6).

---

## 2. Materials you will receive

- `blinded_evaluation_packets.json` — proposals per **SYS-*** code only (no architecture names).
- Optional: per-proposal lineage counts, uncertainty notes, novelty flags (automated).
- **You will not receive** held-out accuracy tables or “winner” labels during scoring.

**Rubric:** `expert_rubric.json` (v1.1).

---

## 3. Blinding rules

1. Use only **SYS-ALPHA**, **SYS-BETA**, … codes. Do not ask which system is ADT.
2. Do **not** use Sanskrit or English terminology as a proxy for quality; score **structure and defensibility**.
3. Architecture mapping is opened **only after** all scores and dissent forms are submitted to the methodological reviewer.
4. If you believe you can identify a system (e.g., distinctive formatting), **note suspicion** on the dissent log but **still score blind**.

---

## 4. Evaluator roles (three independent)

| Role | You score (1–5) |
|------|------------------|
| **Domain adjudicator** (Ayurveda and/or materials as assigned) | `domain_validity`, `held_out_utility` (judgment of *would* help, not measured accuracy) |
| **Ontology / AI adjudicator** | `conceptual_novelty`, `exception_handling` |
| **Methodological reviewer** | `methodology_integrity`, spot-check `held_out_utility` for consistency |

The project lead may serve as **Ayurveda domain adjudicator** but must **not** be the sole scorer of architecture/novelty quality.

---

## 5. Novelty levels (panel guidance)

| Level | Meaning | Who weighs most |
|-------|---------|-----------------|
| **Lexical** | New name vs seed | Ontology adjudicator |
| **Structural** | New Guṇa–Karma or composition–property pattern | Ontology adjudicator |
| **Functional** | Improves held-out performance when category is removed (ablation) | **Automated metric** + domain utility judgment |

**Functional novelty is decisive for scientific “usefulness,”** but the panel’s utility score is **subjective** and must remain **separate** from automated baseline comparisons (§6).

---

## 6. Separation of panel judgment vs automated performance

| Activity | Owner |
|----------|--------|
| Whether a concept is valid / novel / handles exceptions | **Panel** (blinded) |
| Whether SYS-* **outperformed** baselines on held-out accuracy / exception F1 | **Frozen script** (`run_h1_pilot`) — **not** decided by panel vote |
| Confirmatory success | Pre-registered rule: strict dominance + accepted novel category on **adjudicated** 40-case test split |

Evaluators must **not** decide “which system won” from impressions. They score **proposal quality** only.

---

## 7. Scoring procedure

1. Review each packet in random order (provided by methodological reviewer).
2. For each proposed category, score rubric dimensions 1–5 using anchors in `expert_rubric.json`.
3. Record **dissent** when any score differs by ≥2 points between reviewers (`dissent_log_template.json`).
4. Majority rule: median per dimension; unresolved disputes documented in final report, not overridden by project lead alone.

---

## 8. Conflicts of interest

Declare before scoring:

- Involvement in ADT implementation or funding.
- Authorship of the protocol or dataset.
- Domain advocacy (e.g., institutional stake in Ayurveda or materials program).

Methodological reviewer records COI statements; conflicted reviewers abstain from affected dimensions.

---

## 9. Negative and inconclusive findings

- **Negative** (automated confirmatory failure): Report fully; do not reinterpret as success.
- **Inconclusive** (e.g., `ground_truth_ready: false`): No confirmatory claim; panel scores may still inform H2/H1 refinement.
- **Exploratory** gains (partial novelty, no strict dominance): Label clearly; require independent replication (e.g., `held_out_study_v1`).

---

## 10. Calibration set (10 Ayurveda — not confirmatory)

Use `calibration/ayurveda_10_cases.jsonl` to align rubric interpretation **before** scoring the 40-case `test` split. If protocol or rubric changes after calibration, those 10 remain **calibration/development** only. Record scores using `calibration/adjudication_record_schema.json`.

Cases `cal-ayur-008` / `009` support **exploratory** category-revision analysis (H1/H2); not a new confirmatory criterion.

## 11. Pilot v1 evaluation plan (frozen)

| Item | Value |
|------|--------|
| Total observations | 120 |
| Train / tune | 60 development + 20 validation |
| **Confirmatory held-out** | **40 test** (adjudicate these for official Pilot v1) |
| Success criteria | Unchanged from `FROZEN.json` pre-registration |
| Ontology auto-apply | **Prohibited** — proposals are research records only |

---

## 11. Submission

Return to methodological reviewer:

1. Completed rubric scores per SYS-* / proposal.
2. `dissent_log_template.json` (if needed).
3. Signed COI declaration.
4. No architecture guesses until unlock.

---

*Panel instructions v1.0 — Pilot v1 — 2026-10-15*
