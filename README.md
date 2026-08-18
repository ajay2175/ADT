# ADT — Ajay Digital Twin

Dharma-governed meta-intelligence with persistent backend, model-agnostic LLM gateway, vector retrieval, and constitutional governance.

## Quick start (SQLite — zero config)

```bash
# Terminal 1 — backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
npm install && npm run dev
```

Open http://localhost:5173 · API docs http://127.0.0.1:8000/docs

## Production stack (Postgres + pgvector)

```bash
cp .env.example .env
# Set LLM_PROVIDER=openai and OPENAI_API_KEY=sk-... for real reasoning

docker compose up --build
```

Set in `.env`:
```bash
ADT_DATABASE_URL=postgresql://adt:adt@localhost:5432/adt
LLM_PROVIDER=openai   # or anthropic | local | mock
```

## Phase 2 capabilities (now implemented)

| Feature | Status |
| --- | --- |
| Model-agnostic LLM gateway | OpenAI, Anthropic, local/Ollama, mock fallback |
| Independent LLM expert views | Each routed expert gets its own prompt + JSON response |
| LLM decision synthesis | Recommendation, scores, next steps, uncertainty — not hardcoded |
| PDF / DOCX / MD / TXT ingestion | PyMuPDF + python-docx, chunk + embed |
| Vector retrieval | pgvector (Postgres) or cosine on SQLite embeddings |
| Hybrid search | Text + vector merge |
| Live drift-check | LLM inference: mirror → re-anchor → alternative → action |
| Postgres + pgvector | Docker Compose production path |
| GraphRAG (minimal) | Neo4j Docker + extraction on accept + 1-hop graph retrieval |
| Persistent UI | All tabs wired to backend across sessions |

## GraphRAG (Neo4j — optional, free locally)

```bash
docker compose up neo4j -d
cp .env.example .env   # NEO4J_URI=bolt://localhost:7687, password adtgraph
```

Restart backend. **Accept** an inbox item → entities extracted → Neo4j indexed. Browse: http://localhost:7474

## Constitutional invariant

**Knowledge can expand; constitutional identity cannot silently change.**

Uploads → proposed knowledge. Amendments → audit event only until Ajay approves.

## Reset local vault

```bash
rm -f data/adt_vault.db
```

Restart backend to re-seed.

## GitHub

https://github.com/ajay2175/ADT
