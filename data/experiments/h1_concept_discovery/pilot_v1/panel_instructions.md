# H1 blind adjudication — panel instructions

## Roles

| Role | Focus |
|------|--------|
| Domain adjudicator | Classical / scientific defensibility (Ayurveda or materials) |
| Ontology / AI adjudicator | Structural coherence and genuine novelty (not relabeling) |
| Methodological reviewer | Leakage, consistency, trace completeness |

Project lead may serve as **Ayurveda domain adjudicator** but must not be sole scorer of architecture quality.

## Blinding

Evaluate `blinded_evaluation_packets.json` using system codes only (`SYS-*`). Architecture mapping is opened only after scores are submitted.

## Scoring

Use `expert_rubric.json` scales (1–5). Record dissent in `dissent_log` (separate form).

**Functional novelty (decisive):** A category counts as scientifically useful only if it would improve held-out prediction or supports a defensible new inference—panel utility score ≥4 with majority agreement.

## Outcomes

- **Confirmatory:** Pre-registered strict dominance + functional novelty (protocol 1.1+).
- **Exploratory:** Improvements in novelty, calibration, or exceptions without strict dominance—label clearly; replicate before claims.
