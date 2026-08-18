# ADT GraphRAG v1

## Scope

This activates a minimal, governance-first GraphRAG layer: typed entity extraction after explicit knowledge acceptance, a Neo4j projection, SQL audit mirror, one-hop graph retrieval, and graph inspection APIs. It is not community-detection GraphRAG or an autonomous knowledge updater.

## Ontology v1

| Node | Purpose |
| --- | --- |
| `ConstitutionItem` | Protected, approved values and guardrails. Never created or changed by ingestion. |
| `KnowledgeItem` | An accepted source item. |
| `Concept`, `Person`, `Organization`, `Source`, `Event` | Extracted, typed entities. |
| `ResearchProgram`, `Expert`, `Decision` | Reserved first-class ADT operational nodes. |

Allowed relations: `SUPPORTS`, `CONTRADICTS`, `SUPERSEDES`, `DERIVED_FROM`, `RELATES_TO`, `CONSULTED`, `APPLIES_VALUE`, `MENTIONS`, `CAUSES`, and `PART_OF`.

## Constitutional invariant

Constitution nodes are seeded with `protected=1`. Ingestion never accepts a Constitution node type, and proposed amendments use the existing explicit approval workflow. Graph projection only writes accepted `KnowledgeItem` content and extracted entities/relations; it cannot update Constitutional nodes.

## Lifecycle

`upload → parse → chunk → embed → proposed review → accepted → extract → SQL mirror + Neo4j projection → hybrid retrieval`

Extraction is scheduled only after acceptance. With the mock provider it conservatively proposes named concepts and no semantic relations; a real provider is required for reliable relation extraction.

## Run locally

Use Docker for the fully activated Neo4j projection:

```bash
cp .env.example .env
docker compose up --build
```

Neo4j Browser is available at `http://localhost:7474`. Change `NEO4J_PASSWORD` before any non-local deployment.

Without Neo4j configured, the SQL graph mirror continues to support review, inspection, and one-hop hybrid retrieval; it is deliberately not presented as an active Neo4j deployment.

## APIs

- `GET /v1/graph/status`
- `GET /v1/graph/entities?q=`
- `GET /v1/graph/neighbors/{node_id}`
- `GET /v1/graph/path?from_id=&to_id=`
- `GET /v1/knowledge/{knowledge_id}/graph`

No raw Cypher API is exposed until authenticated administrator roles exist.
