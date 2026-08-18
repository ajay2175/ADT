# ADT Vault — Ajay Digital Twin

Dharma-governed meta-intelligence with a **persistent SQLite backend** and React UI.

Flow: `Constitution → upload → retrieval → independent expert routing → decision → memory → recall`

## Run (two terminals)

**Backend** (persistent vault — required):

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend**:

```bash
npm install
npm run dev
```

Open http://localhost:5173 — sidebar shows **Backend connected** when live.

API docs: http://127.0.0.1:8000/docs

## What the backend holds

- **17 approved constitutional items** — True North, persona, roles, leadership, wealth, parenting, epistemology, guardrails
- **10 expert profiles** with inspectable independent routing
- **Knowledge inbox** with provenance, claim status, review lifecycle
- **Decision + reasoning records** — evidence, assumptions, experts, disagreements, ACA risks, values, uncertainty
- **ACA research program** registry
- **Governance / drift-check** endpoint
- **3 web references** seeded as *proposed* (NIST AI RMF, HL7 FHIR, clinical AI decision-support review)

Constitutional identity cannot be changed by uploads or web findings — only via explicit amendment approval.

## Reset local vault

```bash
rm -f data/adt_vault.db
```

Restart the backend to re-seed.

See `docs/PHASE_1_ARCHITECTURE.md` for production architecture milestones.
