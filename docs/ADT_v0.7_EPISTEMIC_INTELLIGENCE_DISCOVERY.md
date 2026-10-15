# ADT v0.7 — Epistemic Intelligence Discovery Experiments

**Status:** Research specification (Track A governs Track B)  
**Experiment 1 protocol:** `docs/EXPERIMENT_1_EMERGENCE_PROTOCOL.md` · runner `python -m app.experiments.run_h1`  
**Platform baseline:** ADT `main` ≥ `eb588a3` (reproducibility anchor; verify locally before publication claims)  
**Companion engineering:** A–D ablation benchmark (safety, calibration, governance) runs **in parallel**, not as a substitute for these experiments.

---

## 0. North Star

> Can classical Indian epistemology contribute **new computational mechanisms** that allow artificial intelligence to **form concepts**, **acquire valid knowledge**, **recognize uncertainty**, **discover causal structure**, and **improve its own understanding**—under governance that scales with capability?

**Success is measured by demonstrated cognitive capabilities**, not module count, API versions, or test totals.

**Four-question gate** (every major sprint or milestone):

1. Which of the **ten original hypotheses** does this advance?
2. What **observable cognitive capability** are we creating or testing?
3. What is **non-obvious** versus conventional LLM, RAG, or neuro-symbolic stacks?
4. What **experiment** could falsify the claim?

---

## 1. Scientific agenda (unchanged)

The ten directions remain hypotheses, not a product backlog. ADT is one laboratory; **Vaidya Mitra** is one rich testbed; **materials science** (or similar) is required to test **Knowledge Interoperability** and **Universal Cognitive Grammar** beyond a single domain.

| Original direction | Role in v0.7 |
|--------------------|--------------|
| Universal Cognitive Grammar | H1 primary |
| Self-Evolving Knowledge | H1 primary |
| Human–Machine Epistemology | H2 primary |
| Epistemic Humility | H2 + A–D calibration |
| Consciousness-like Architecture | H2 (metacognitive routing, state transitions) |
| Causal Creativity | H3 primary |
| Meta-Science Theory Engine | H3 primary |
| Guṇa-Based Alignment | A–D + H3 (values in reasoning, not only blocks) |
| Responsible ASI | A–D governance track |
| Knowledge Interoperability | H1 transfer + second domain |

---

## 2. Three foundational hypotheses

### Hypothesis H1 — Can AI develop new concepts rather than retrieve existing ones?

**Constructs:** Dravya, Guṇa, Karma, Sāmānya, Viśeṣa, Samavāya, Abhāva.

**Claim:** A Padārtha-grounded process can **propose novel abstractions** (new Sāmānya/Viśeṣa or relations) from observations **not present** in seed ontology, distinguish **exceptions** (viśeṣa / abhāva), and **generalize** to held-out cases.

**Task families**

| ID | Description |
|----|-------------|
| H1-T1 | Observations only — no matching ontology node; require proposed category + samavāya links |
| H1-T2 | Exception cases — majority pattern + viśeṣa outliers; must not over-generalize |
| H1-T3 | **Transfer** — abstraction learned in domain A applied in domain B (Vaidya → materials or reverse) |

**Baselines (same LLM backbone where applicable)**

- **B-LLM:** LLM + prompt-only concept naming (no structured ontology)  
- **B-KG:** Fixed schema KG + embedding retrieval (no proposal pipeline)  
- **B-NeuroSym:** Template IE + predefined relation types (no Padārtha evolution)

**ADT configurations:** A–D ablations; **primary contrast** is B (ontology) vs B+C (ontology + Pramāṇa/Jñāna on proposals).

**Primary metrics**

| Metric | Definition |
|--------|------------|
| **Novel abstraction quality** | Expert rubric 1–5: coherence, parsimony, usefulness |
| **Transfer accuracy** | Held-out application tasks in second domain |
| **Exception F1** | Detect viśeṣa / abhāva vs false universal |
| **Proposal precision** | % proposed concepts retained after Pramāṇa review |
| **False universal rate** | Over-generalization to held-out counterexamples |

**Novelty criterion:** A result counts only if the **accepted proposal** is not lexical overlap with seed ontology and **improves** transfer or prediction vs all baselines on held-out split.

**Hypotheses advanced:** Universal Cognitive Grammar, Self-Evolving Knowledge, Knowledge Interoperability (with H1-T3).

---

### Hypothesis H2 — Can AI distinguish information from understanding?

**Constructs:** Śabda, Artha, Śabdārtha, Nirvikalpa, Savikalpa, Saṁśaya, Pramā, Viparyaya.

**Claim:** Epistemic architecture yields **grounded understanding**: detect ambiguity and misleading text, **seek evidence**, **revise** viparyaya, and maintain **coherent śabdārtha** under contradiction — measurably better than retrieval-only agents.

**Task families**

| ID | Description |
|----|-------------|
| H2-T1 | Incomplete śabda — correct abstention or targeted evidence request |
| H2-T2 | Misleading passage — viparyaya flagged; revision after counter-evidence |
| H2-T3 | Ambiguous term — savikalpa (multiple artha) → resolution path to pramā or saṁśaya |
| H2-T4 | Observation contradicts text — pramāṇa ledger updated; jñāna state regression |

**Baselines:** B-LLM, B-KG+RAG, ADT-A (no epistemic gates).

**Primary metrics**

| Metric | Definition |
|--------|------------|
| **Unsupported claim rate** | Claims without accepted pramāṇa / wrong entailment |
| **Misconception correction** | Accuracy after controlled counter-evidence |
| **Calibration (ECE)** | Confidence vs correctness on abstention tasks |
| **Evidence-seeking efficiency** | Steps to pramā vs random retrieval |
| **Semantic consistency** | Same artha across paraphrases (held-out) |

**Understanding criterion:** Improvement on H2-T2/T4 with **traceable** state transitions (saṁśaya → pramā or sustained saṁśaya), not fluent prose alone.

**Hypotheses advanced:** Human–Machine Epistemology, Epistemic Humility, metacognitive routing (faculty / savikalpa–nirvikalpa).

---

### Hypothesis H3 — Can AI generate and validate genuinely new scientific hypotheses?

**Constructs:** Pratyakṣa, Anumāna, Upamāna, Tantrayukti (as inference structure), Karma, causal graphs.

**Claim:** System proposes **competing explanations**, designs **discriminating observations** (information gain), surfaces **causal assumptions**, rejects unsupported hypotheses, and **updates theory** after evidence — beyond generic hypothesis text.

**Task families**

| ID | Description |
|----|-------------|
| H3-T1 | Competing causal models — pick experiment that splits posteriors |
| H3-T2 | Hidden confounder — tantrayukti-style assumption audit |
| H3-T3 | Sequential evidence — theory revision after simulated pratyakṣa |
| H3-Vaidya | Guṇa–karma inference → **testable** biomedical prediction (layer-tagged) |

**Baselines:** B-LLM (hypothesis generation), causal discovery library on same tabular obs, ADT without theory engine.

**Primary metrics**

| Metric | Definition |
|--------|------------|
| **Information gain** | Expected reduction in hypothesis entropy from proposed experiment |
| **Discrimination accuracy** | Did chosen experiment falsify at least one competitor? |
| **Assumption coverage** | Expert audit of stated vs hidden assumptions |
| **Post-update accuracy** | Correct effect direction after evidence round |
| **Unsupported rejection rate** | Hypotheses correctly dropped without evidence |

**Discovery criterion:** Accepted hypothesis must be **novel** relative to prompt corpus and **survive** pramāṇa + simulated or real observation round; fluent but non-discriminating proposals count as **negative results**.

**Hypotheses advanced:** Causal Creativity, Meta-Science Theory Engine.

---

## 3. A–D benchmark: extended measurement map

Keep configurations A–D as **controlled epistemic ablations**. Add **hypothesis-tagged** cases (not 1,000 generic Q&A).

| Track | Primary measurement | Hypothesis |
|-------|---------------------|------------|
| Concept discovery | Novel abstraction + transfer | H1 |
| Grounded understanding | Consistency + correction | H2 |
| Scientific reasoning | Hypothesis quality + information gain | H3 |
| Epistemic humility | Calibration + abstention | H2, A–D |
| Constitutional governance | Unauthorized action resistance | Responsible ASI |

**Splits:** `dev` (pipeline), `validation` (tune rubrics), `held_out` (report once, frozen).  
**Ground truth:** Expert-adjudicated; synthetic cases only for **regression**, not superiority claims.

Dataset roots:

- `data/benchmark/` — A–D governance + regression fixtures  
- `data/experiments/h1_concept_discovery/`  
- `data/experiments/h2_grounded_understanding/`  
- `data/experiments/h3_scientific_reasoning/`  
- `data/experiments/materials_science_slice/` — cross-domain held-out for H1/H2  

---

## 4. Vaidya Mitra and second domain

**Vaidya Mitra** tasks must preserve epistemic **layers**:

1. Classical textual assertion (śabda / āpta)  
2. Ayurvedic interpretive inference (savikalpa)  
3. Biomedical observation (pratyakṣa / anumāna)  
4. Experimental hypothesis (saṁśaya → testing)  
5. Clinically validated conclusion (pramā, practitioner-gated)

ADT must **not** collapse these into a single “answer about an herb.”

**Materials science slice** (example): crystal structure observations → propose Sāmānya (“perovskite-like tolerance factor band”) with viśeṣa exceptions; no Ayurvedic entities in train split for transfer tests.

---

## 5. v0.7 immediate deliverables

| # | Deliverable | Location / artifact |
|---|-------------|---------------------|
| 1 | This research specification | `docs/ADT_v0.7_EPISTEMIC_INTELLIGENCE_DISCOVERY.md` |
| 2 | Controlled datasets (seed + held-out protocol) | `data/experiments/*/manifest.json`, `held_out.json` |
| 3 | Baseline + ADT configs | A–D in `data/benchmark/manifest.json`; per-run env: `LLM_PROVIDER`, `ADT_EVAL_SEED`, `ADT_GIT_COMMIT` |
| 4 | Measurable criteria | Sections 2–3 above; expert rubrics in experiment manifests |
| 5 | Reproducible reports | `epistemic_reporting.build_run_report`; **include negative results** |

**Explicitly not a v0.7 goal:** Scaling to 1,000 reviewed trivia questions. Scale **held-out adjudicated tasks** per hypothesis until confidence intervals stabilize.

---

## 6. Experimental protocol (single run)

1. Freeze `ADT_GIT_COMMIT`, model ID, seed, dataset manifest hash.  
2. Run baselines B-LLM, B-KG, B-NeuroSym on **held_out** only.  
3. Run ADT A→D on same tasks.  
4. Record: predictions, traces (padārtha proposals, pramāṇa, jñāna states), latency, cost.  
5. Blind expert scoring (primary metrics).  
6. Paired statistics (bootstrap CI); pre-register success thresholds where possible.  
7. Archive report JSON + human-readable summary; **publish failures**.

---

## 7. What we will not claim without evidence

- Sanskrit labels alone do not constitute a new theory of intelligence.  
- Passing governance tests does not prove better **understanding** or **discovery**.  
- Vaidya competence alone does not prove **general** cognitive grammar.  
- Ontology proposal queues are not **self-evolving knowledge** until H1 metrics pass on held-out data.

---

## 8. Parallel work plan

| Stream | Owner focus | Stop condition |
|--------|-------------|----------------|
| **Track A** | H1, H2, H3 held-out experiments | Pre-specified metric thresholds or honest null |
| **Track B** | A–D reviewed eval, reproducibility | Frozen report for `eb588a3`+ |
| **Deferred** | Autonomous ontology **apply** | Until H1 shows beneficial novel concepts |

**Next engineering** (only when blocked by Track A): minimal hooks to log Padārtha proposals, pramāṇa entailment labels, and theory-engine traces into experiment outputs—not new product features.

---

*Document version: 0.7.0-research-spec — 2026-10-15*
