# H1 calibration — AI-assisted classical source verification

**Cases:** `pilot_v1/calibration/ayurveda_10_cases.jsonl`  
**Output per case:** `pilot_v1/calibration/source_verification/<observation_id>.json`  
**No ADT runtime required** — research curation workflow.

## Purpose

Convert **structured** calibration rows into **authenticated** observations with traceable śabda, explicit vs inferred artha, and expert sign-off—supporting Śabda–Artha–Śabdārtha without conflating classical description with modern biomedical efficacy.

## Workflow (per case)

| Step | Activity | Record in JSON |
|------|----------|----------------|
| 1 | **Identify classical claim** — Dravya, Guṇa, Karma, context from case file | `claim` |
| 2 | **Retrieve original passage** — edition, chapter, verse/page; Sanskrit if available | `passage` |
| 3 | **Tantrayukti interpretation** — literal, contextual, inferential layers | `tantrayukti` |
| 4 | **Compare interpretations** — agreement, contradiction, exception | `competing_readings` |
| 5 | **Expert verification** — accept / reject / uncertain | `expert_signoff` |

Use AI assistants to **draft** retrieval and translation; **domain expert** must verify before `verification_status: expert_verified`.

## AI assistance rules

- AI proposes candidate passages; human confirms edition and verse ID.
- Separate fields: `explicit_in_text` vs `inferred_by_commentary` vs `modern_biomedical` (must not be merged).
- Log model name and date in `ai_assistance_log` for reproducibility.
- Do not tune cases after viewing ADT outputs on the same IDs.

## Generate empty verification packet

```bash
cd backend
PYTHONPATH=. python -m app.experiments.h1_verification_packet --case cal-ayur-001
```

## Completion criteria (all 10)

- `expert_signoff.status` ∈ {accept, reject, uncertain} with named reviewer
- `passage.sanskrit` or `passage.not_found_documented` with reason
- Update row in `ayurveda_10_cases.jsonl`: `classical_source.verification_status: expert_verified` only when step 5 passes

## Levels 1–3 (research distinction — not results)

| Level | Target |
|-------|--------|
| L1 Recognition | Known Sāmānya from observations |
| L2 Formation | New Sāmānya not in seed |
| L3 Revision | Inadequate category revised (see 008/009) |

Calibration includes **exploratory L3** in 008/009 only; not confirmatory success criteria.
