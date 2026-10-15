# ADT Phase 3 — Epistemic Intelligence

## Objective

Advance ADT into an **experimentally testable** cognitive architecture grounded in Padārtha–Pramāṇa–Jñāna, **without** weakening constitutional governance.

Build on existing: GraphRAG, expert router, decision synthesis, drift-check — not a new prototype.

## Phase map

| Phase | Focus |
| --- | --- |
| 3 | Epistemic Intelligence (Padārtha, Pramāṇa, Jñāna, Dharma Guard) |
| 4 | Causal discovery, controlled self-evolution |
| 5 | Independent scientific validation (benchmarks A–D) |

## P0 modules (started in v0.3.0)

| Module | Path | Role |
| --- | --- | --- |
| Padārtha Engine | `backend/app/padartha.py` | Typed assertions; `RelationKind` separates **samavāya** (inherence) from association/causation |
| Pramāṇa Ledger | `backend/app/pramana.py` | Per-assertion evidence; `AbsenceKind` distinguishes not-found vs demonstrable absence |
| Jñāna states | `backend/app/jnana.py` | Validated state machine (computational analogues) |
| Dharma Guard | `backend/app/dharma_guard.py` | Action gates + constitution snapshot checks |

## APIs

- `POST/GET /v1/epistemic/padartha/assertions`
- `POST /v1/epistemic/pramana/evidence`, `GET .../evidence/{assertion_id}`
- `POST /v1/epistemic/jnana/transition`, `GET /v1/epistemic/jnana/state`
- `POST /v1/governance/dharma-guard/authorize`, `GET .../integrity`

## Experiment A–D (design)

| Config | Stack |
| --- | --- |
| A | ADT + GraphRAG (baseline) |
| B | A + Padārtha |
| C | B + Pramāṇa + Jñāna |
| D | C + Dharma Guard |

**Governance acceptance:** zero unauthorized constitution mutations in the adversarial suite (`backend/tests/test_constitutional_integrity.py`).

## Sprint 1 exit criterion

On knowledge **accept** (document admission only):

1. `project_epistemic_from_knowledge` creates **proposed** Padārtha assertions (idempotent).
2. Each assertion gets a **proposed** Pramāṇa passage linked to `source_id=knowledge_id`.
3. Jñāna: `nirvikalpa` → `savikalpa` on each assertion.
4. Promotion to `prama` / `epistemic_status=accepted` requires `POST .../assertions/{id}/validate` with accepted evidence.

`GET /v1/epistemic/lineage/{knowledge_id}` traces document → assertions → evidence → jñāna state.

## Phase 3 completion checklist

- [x] v0.3.0 source + migrations (`padartha_assertions`, `pramana_evidence`, `jnana_states`)
- [x] Six integrity tests + Sprint 1 lineage test (`pytest tests/`)
- [x] Accepted documents → proposed Padārtha assertions (`epistemic_pipeline.py`)
- [x] Source-level Pramāṇa on each assertion (proposed; not truth-validated)
- [x] Jñāna transitions on extraction; promotion gated on Pramāṇa
- [ ] Dharma Guard on every mutation path (partial — API gates + integrity tests)
- [ ] Full E2E ingestion → decision audit
- [ ] Frozen A–D benchmark dataset and results


`cognitive_router.py`, `semantic_grounding.py`, `causal_engine.py`, `theory_engine.py`, `ontology_evolution.py`, `epistemic_eval.py` — Sprint 6–8.

Autonomous ontology modification remains **after** governance and evidence tests pass.
