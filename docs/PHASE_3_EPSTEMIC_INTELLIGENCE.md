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
- [x] Dharma Guard injection audit + adversarial tests (v0.4.0; not every write path)
- [x] Faculty routing, theory/causal engines, benchmark harness (`data/benchmark/fixtures.json`)
- [ ] Full E2E ingestion → decision audit with epistemic gates
- [ ] Frozen 1k-case A–D benchmark publication

## Sprints 2–5 (shipped in v0.4.0)

See modules: `cognitive_router.py`, `semantic_grounding.py`, `theory_engine.py`, `causal_engine.py`, `epistemic_eval.py`, `ontology_evolution.py` (proposals only).

Run benchmarks: `POST /v1/evaluation/run/A` through `D`. Tests: `pytest backend/tests/ -q`.

Autonomous ontology modification remains **after** governance and evidence tests pass.
