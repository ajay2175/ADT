# Pilot v1 — Baseline equivalence audit

Confirm **before** `FROZEN.json` model slots are filled and official run executed.

## Information access

- [ ] All SYS-* conditions receive the **same** `observations.jsonl` rows per split (identical JSON inputs).
- [ ] No baseline receives extra retrieval corpus or prompt-only “hints” absent from ADT+.
- [ ] Seed ontology `seed_ontology.json` identical for all conditions.

## Computation (when LLM baselines enabled)

- [ ] Same `llm_backbone` model ID and temperature across conditions that use the model.
- [ ] Token / latency budgets documented in run report (`pilot_full_trace.json`).
- [ ] ADT+ overhead (Padārtha/Pramāṇa steps) reported separately—not hidden extra retrieval.

## Fair comparison note

Current deterministic baselines (B-LLM / B-KG / B-NeuroSym) are **structural placeholders** until LLM-backed baselines are wired with equivalent access. Official publication run must either:

1. Upgrade baselines to matched LLM+access, or  
2. Report results as **pipeline ablation only** (not LLM superiority claims).

## Sign-off

| Item | Verified by | Date |
|------|-------------|------|
| Information parity | | |
| Model config frozen in FROZEN.json | | |
| Budgets logged | | |
