# Pilot v1 — Dataset authenticity & leakage audit

Complete **before** official frozen comparison. Automated helper:  
`cd backend && PYTHONPATH=. python -m app.experiments.h1_pilot_audit`

## Authenticity (human — required)

- [ ] Each observation has traceable `source_provenance` (classical text ID, paper DOI, lab notebook ref, etc.).
- [ ] Ayurveda: classical **śabda** vs modern **interpretation** vs biomedical **observation** tagged separately.
- [ ] Materials: composition–property–behavior from documented measurements, not synthetic hashes.
- [ ] No placeholder `Dravya-{hash}` / empty `guna`/`karma` in **test** split.

## Leakage (human + script)

- [ ] No `test` case duplicates `development`/`validation` entities or verbatim observations.
- [ ] No adjudication labels from test used during development tuning.
- [ ] Seed ontology frozen; no test-derived terms added to seed before run.

## Sign-off

| Role | Name | Date | Pass |
|------|------|------|------|
| Domain (Ayurveda) | | | |
| Domain (Materials) | | | |
| Methodological reviewer | | | |
