# ADT Vault — Phase 1 prototype

A local interactive prototype for the first usable Ajay Digital Twin flow:

`Constitution → upload → retrieval → independent expert views → decision → memory → recall`

## Run

```bash
npm install
npm run dev
```

The prototype is deliberately local-only. Its sample data is held in browser state; it models the product workflow and guardrails before a backend/provider integration.

## Phase-1 local API

The first persistent backend scaffold now lives in `backend/app/main.py`. It seeds the approved Constitution, expert registry, ACA research program, and reviewable web references in local SQLite. It exposes Constitution/amendment governance, provenance-bearing knowledge and claims, independent expert routing, decision/reasoning records, research, recall, and drift-governance endpoints.

The local database is intentionally ignored by Git. Remove `data/adt_vault.db` only when you explicitly want to reset this local development vault.

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

See `docs/PHASE_1_ARCHITECTURE.md` for the proposed production architecture, API contract, schemas, and milestones.
