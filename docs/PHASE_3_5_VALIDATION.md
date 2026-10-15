# ADT v0.5.0 — Epistemic Validation and Constitutional Assurance

## Scope (narrower than v0.4.0)

| Work package | Outcome |
| --- | --- |
| Decision authorization | Consequential finalize requires validated assertions (`prama` + accepted Pramāṇa); exploratory mode explicit |
| Constitutional integrity | SQL guard on `constitution_items` mutations via `persistence_guard.py` |
| Benchmark | Frozen manifest `data/benchmark/manifest.json`, ablation metadata on runs |
| Causal labeling | Counterfactuals tagged `simulation_hypothesis` |

## APIs

- `GET /v1/decisions/{id}/authorization?exploratory=`
- `POST /v1/decisions/{id}/finalize?exploratory=true|false`
- `GET /v1/evaluation/manifest`
- `POST /v1/evaluation/ablation-suite`

## Acceptance targets (proposed — measure, do not assume)

| Metric | Target |
| --- | --- |
| Unauthorized constitutional changes | 0 in test suite |
| Evidence-gate bypasses (consequential finalize) | 0 |
| Invalid Jñāna transitions | 0 |
| Benchmark reproducibility (deterministic cases) | 100% |

## Not in v0.5.0

- Vaidya Mitra domain pack (v0.6+)
- 1k-case frozen publication dataset
- Full authN/Z on all agent paths
