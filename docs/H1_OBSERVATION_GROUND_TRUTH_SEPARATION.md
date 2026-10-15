# H1 — Observation vs ground truth vs discovery

**Rule:** Runners and ADT inputs may load **only** `observation_data/`.  
**Never** feed `ground_truth/` or `candidate_discovery/` into training or proposal generation.

| Layer | Path | Contents |
|-------|------|----------|
| Observation data | `observation_data/` | Dravya, Guṇa, Karma, context, source citation metadata (no expected category) |
| Expert ground truth | `ground_truth/` | Adjudicator labels, research focus tags, holdout clusters — **post-hoc** |
| Candidate discovery | `runs/*/candidate_discovery/` | Per-architecture proposals (generated at experiment time) |
| Functional evaluation | Automated metrics + panel utility scores | Held-out utility, ablation |

Pre-labeling the “correct” Sāmānya in observation files risks **supervised classification**. Research-focus tags (Guṇa–Karma, Prabhāva, etc.) live in **ground_truth** for panel planning only, not in system inputs.

**First curation standard:** complete `observation_data/cal-ayur-001.json` + `source_verification/cal-ayur-001.json` with expert sign-off, then replicate pattern for 002–010 and authenticated v1 splits.
