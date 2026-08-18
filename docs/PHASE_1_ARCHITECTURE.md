# ADT Phase 1: architecture and build boundary

## First usable ADT

ADT is first usable when Ajay can submit a decision with context, retrieve provenance-bearing knowledge, receive at least two independently framed expert views plus a Constitution/Dharma synthesis, save the reasoning record, and recall it later. No upload or inference may silently modify constitutional memory.

## Thin vertical slice

```text
Constitution (approved, versioned, read-only at runtime)
  → upload/inbox (proposed knowledge only)
  → retrieval (source + claim status visible)
  → expert router (independent analyses)
  → decision synthesizer (structured justification, not hidden reasoning)
  → decision memory + scheduled outcome review
  → future recall
```

## Repository shape

```text
adt-vault/
  frontend/                 # Next.js/React production client (this prototype uses Vite)
  backend/app/
    api/ constitution, inbox, retrieval, decisions, memories
    services/ ingestion, retrieval, expert_router, decision_engine, governance
    models/ constitution_item, knowledge_item, decision, reasoning_record
  schemas/                  # JSON schema / OpenAPI source
  vault/01_ADT_CONSTITUTION # signed, versioned source material
  data/raw | processed      # object storage
  docs/
```

## Minimal relational schema

| Table | Purpose | important fields |
| --- | --- | --- |
| `constitution_items` | immutable-at-runtime identity/values | `id, category, statement, status, priority, version, confirmed_by_ajay` |
| `constitution_amendments` | explicit amendment workflow | `id, item_id, rationale, status, approved_by, approved_at` |
| `knowledge_items` | uploaded source and lifecycle | `id, title, content_type, status, provenance, source_uri, created_at` |
| `claims` | epistemic records, never flatten hypotheses | `id, knowledge_item_id, statement, status, confidence, evidence_for, evidence_against` |
| `decision_records` | question, recommendation, final decision, outcome | `id, question, context, confidence, review_date, actual_outcome` |
| `reasoning_records` | auditable justification | `decision_id, facts_used, assumptions, experts, disagreements, values_applied, uncertainty` |
| `memory_links` | retrieval edges | `from_type, from_id, to_type, to_id, relation, strength` |

## Phase 1 API contract

```http
GET  /v1/constitution?status=approved
POST /v1/constitution/amendments          # always creates proposed amendment
GET  /v1/inbox
POST /v1/inbox                             # upload → received
POST /v1/inbox/{id}/review                 # accept/edit/reject/defer
POST /v1/retrieval/search                  # { query, domains, memory_types }
POST /v1/decisions/analyze                 # synchronous thin-slice synthesis
POST /v1/decisions/{id}/finalize           # records Ajay's actual choice
GET  /v1/memories/recall?q=...
POST /v1/decisions/{id}/outcome
```

`POST /v1/decisions/analyze` returns: `retrieved_claims`, `independent_expert_views`, `structured_justification`, `options`, `scores`, `uncertainty`, `next_steps`, and an unfinalized `decision_id`.

## Milestones

1. **Foundation:** Postgres + pgvector, auth, audit log, seeded approved Constitution.
2. **Ingestion:** text/Markdown/PDF upload, parsing, claim extraction, review queue; no auto-accept.
3. **Decision loop:** retrieval, two independent expert templates, scoring/sensitivity, structured record.
4. **Memory:** recall, decision outcome capture, drift audit, review reminders.
5. **Extensions:** provider gateway, GraphRAG, Vaidya Mitra interoperability, multimodal/sensor inputs.

## Non-negotiable controls

- Constitutional rows are revisioned and require Ajay approval; knowledge ingestion cannot write them.
- Every claim carries status, provenance, review date, and counter-evidence where present.
- Experts are invoked independently before synthesis; disagreement remains visible.
- Medical/high-risk queries require a safety/escalation policy before model output.
