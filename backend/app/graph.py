from __future__ import annotations

import json
import logging
import uuid

from app.config import settings
from app.database import NOW, db, rows_to_dicts
from app.extraction import extract_entities_relations

logger = logging.getLogger(__name__)

_driver = None
_last_error: str | None = None

RELATION_TYPES = frozenset({"MENTIONS", "RELATES_TO", "SUPPORTS", "CONTRADICTS", "PART_OF", "DERIVED_FROM"})


def _get_driver():
    global _driver, _last_error
    if not settings.use_neo4j:
        return None
    if _driver is not None:
        return _driver
    try:
        from neo4j import GraphDatabase

        _driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        _driver.verify_connectivity()
        _last_error = None
        return _driver
    except Exception as exc:  # noqa: BLE001
        _last_error = str(exc)
        logger.warning("Neo4j unavailable: %s", exc)
        _driver = None
        return None


def graph_status() -> dict:
    driver = _get_driver()
    if not settings.use_neo4j:
        return {"enabled": False, "connected": False, "reason": "NEO4J_URI not configured"}
    if not driver:
        return {"enabled": True, "connected": False, "reason": _last_error or "connection failed"}
    try:
        with driver.session(database=settings.neo4j_database) as session:
            stats = session.run(
                "MATCH (n) RETURN count(n) AS nodes, count{(n)-[]->()} AS edges"
            ).single()
            return {
                "enabled": True,
                "connected": True,
                "nodes": stats["nodes"] if stats else 0,
                "edges": stats["edges"] if stats else 0,
            }
    except Exception as exc:  # noqa: BLE001
        return {"enabled": True, "connected": False, "reason": str(exc)}


def ensure_schema() -> None:
    driver = _get_driver()
    if not driver:
        return
    stmts = [
        "CREATE CONSTRAINT constitution_id IF NOT EXISTS FOR (n:Constitutional) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT knowledge_id IF NOT EXISTS FOR (n:KnowledgeItem) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT entity_key IF NOT EXISTS FOR (n:Entity) REQUIRE n.key IS UNIQUE",
        "CREATE CONSTRAINT expert_id IF NOT EXISTS FOR (n:Expert) REQUIRE n.id IS UNIQUE",
        "CREATE INDEX entity_name IF NOT EXISTS FOR (n:Entity) ON (n.name)",
    ]
    with driver.session(database=settings.neo4j_database) as session:
        for stmt in stmts:
            session.run(stmt)


def seed_vault_graph() -> dict:
    """Seed constitution, experts, and research program nodes (idempotent)."""
    driver = _get_driver()
    if not driver:
        return {"seeded": False, "reason": "neo4j unavailable"}

    ensure_schema()
    counts = {"constitutional": 0, "experts": 0, "research": 0}

    with db() as connection:
        constitution = rows_to_dicts(
            connection.execute("SELECT * FROM constitution_items WHERE status = 'approved'").fetchall()
        )
        experts = rows_to_dicts(connection.execute("SELECT * FROM expert_profiles").fetchall())
        research = rows_to_dicts(connection.execute("SELECT * FROM research_programs").fetchall())

    with driver.session(database=settings.neo4j_database) as session:
        for item in constitution:
            session.run(
                """
                MERGE (c:Constitutional {id: $id})
                SET c.category = $category, c.statement = $statement,
                    c.priority = $priority, c.status = 'approved', c.protected = true
                """,
                id=item["id"],
                category=item["category"],
                statement=item["statement"],
                priority=item["priority"],
            )
            counts["constitutional"] += 1

        for expert in experts:
            domains = json.loads(expert["domains"]) if isinstance(expert["domains"], str) else expert["domains"]
            session.run(
                """
                MERGE (e:Expert {id: $id})
                SET e.name = $name, e.protocol = $protocol, e.domains = $domains, e.status = $status
                """,
                id=expert["id"],
                name=expert["name"],
                protocol=expert["protocol"],
                domains=domains,
                status=expert["status"],
            )
            counts["experts"] += 1

        for prog in research:
            session.run(
                """
                MERGE (r:ResearchProgram {id: $id})
                SET r.title = $title, r.hypothesis = $hypothesis, r.status = $status
                """,
                id=prog["id"],
                title=prog["title"],
                hypothesis=prog["hypothesis"],
                status=prog["status"],
            )
            counts["research"] += 1

    return {"seeded": True, **counts}


async def index_accepted_knowledge(knowledge_id: str) -> dict:
    """Extract entities/relations on accept and write to Neo4j + knowledge_edges."""
    with db() as connection:
        row = connection.execute("SELECT * FROM knowledge_items WHERE id = %s", (knowledge_id,)).fetchone()
        if not row:
            return {"indexed": False, "reason": "not found"}
        item = dict(row) if not isinstance(row, dict) else row
        chunks = rows_to_dicts(
            connection.execute(
                "SELECT content, chunk_index FROM knowledge_chunks WHERE knowledge_id = %s ORDER BY chunk_index",
                (knowledge_id,),
            ).fetchall()
        )

    text = item.get("summary") or ""
    if chunks:
        text = "\n\n".join(c["content"] for c in chunks[:20])
    elif not text:
        return {"indexed": False, "reason": "empty content"}

    extracted = await extract_entities_relations(item["title"], text)
    driver = _get_driver()
    if not driver:
        _mirror_edges_sql(knowledge_id, extracted)
        return {"indexed": False, "graph": "offline", "extraction": extracted, "entities": len(extracted["entities"])}

    ensure_schema()
    with driver.session(database=settings.neo4j_database) as session:
        session.run(
            """
            MERGE (k:KnowledgeItem {id: $id})
            SET k.title = $title, k.status = 'accepted', k.source_class = $source_class,
                k.content_type = $content_type, k.updated_at = $updated_at
            """,
            id=knowledge_id,
            title=item["title"],
            source_class=item.get("source_class", "ajay"),
            content_type=item.get("content_type", "text"),
            updated_at=NOW(),
        )

        for entity in extracted["entities"]:
            key = _entity_key(entity["name"])
            session.run(
                """
                MERGE (e:Entity {key: $key})
                SET e.name = $name, e.type = $type, e.confidence = $confidence, e.status = 'accepted'
                WITH e
                MATCH (k:KnowledgeItem {id: $kid})
                MERGE (k)-[r:MENTIONS]->(e)
                SET r.confidence = $confidence, r.status = 'accepted'
                """,
                key=key,
                name=entity["name"],
                type=entity["type"],
                confidence=entity["confidence"],
                kid=knowledge_id,
            )

        for rel in extracted["relations"]:
            rtype = rel["type"] if rel["type"] in RELATION_TYPES else "RELATES_TO"
            session.run(
                f"""
                MATCH (a:Entity {{key: $from_key}}), (b:Entity {{key: $to_key}})
                MERGE (a)-[r:{rtype}]->(b)
                SET r.confidence = $confidence, r.status = 'accepted', r.source_knowledge_id = $kid
                """,
                from_key=_entity_key(rel["from"]),
                to_key=_entity_key(rel["to"]),
                confidence=rel["confidence"],
                kid=knowledge_id,
            )

    _mirror_edges_sql(knowledge_id, extracted)
    with db() as connection:
        connection.execute(
            "INSERT INTO audit_events VALUES (%s, 'knowledge_graph_indexed', %s, %s, %s)",
            (
                str(uuid.uuid4()),
                knowledge_id,
                json.dumps({"entities": len(extracted["entities"]), "relations": len(extracted["relations"])}),
                NOW(),
            ),
        )

    return {
        "indexed": True,
        "knowledge_id": knowledge_id,
        "entities": len(extracted["entities"]),
        "relations": len(extracted["relations"]),
    }


def _mirror_edges_sql(knowledge_id: str, extracted: dict) -> None:
    with db() as connection:
        for rel in extracted.get("relations", []):
            edge_id = str(uuid.uuid4())
            connection.execute(
                "INSERT INTO knowledge_edges VALUES (%s, %s, %s, %s, %s)",
                (edge_id, knowledge_id, _entity_key(rel["to"]), rel["type"], rel["confidence"]),
            )


def _entity_key(name: str) -> str:
    return name.strip().lower().replace(" ", "_")[:120]


async def graph_search(query: str, limit: int = 8) -> list[dict]:
    """1-hop graph neighborhood from entities matching query tokens."""
    driver = _get_driver()
    if not driver:
        return _sql_graph_fallback(query, limit)

    tokens = [t for t in query.lower().split() if len(t) > 3][:6]
    if not tokens:
        return []

    cypher = """
    UNWIND $tokens AS token
    MATCH (e:Entity)
    WHERE toLower(e.name) CONTAINS token AND e.status = 'accepted'
    MATCH (e)-[r]-(neighbor)
    WHERE neighbor.status IS NULL OR neighbor.status = 'accepted'
    RETURN DISTINCT
      labels(neighbor)[0] AS node_type,
      coalesce(neighbor.name, neighbor.title, neighbor.statement) AS label,
      coalesce(neighbor.id, neighbor.key) AS node_id,
      type(r) AS relation,
      r.confidence AS confidence
    LIMIT $limit
    """
    hits: list[dict] = []
    with driver.session(database=settings.neo4j_database) as session:
        rows = session.run(cypher, tokens=tokens, limit=limit)
        for row in rows:
            hits.append(
                {
                    "content": f"{row['label']} ({row['relation']})",
                    "title": row["label"],
                    "source_class": "graph",
                    "score": float(row["confidence"] or 0.5),
                    "retrieval": "graph",
                    "node_type": row["node_type"],
                    "node_id": row["node_id"],
                }
            )
    return hits


def _sql_graph_fallback(query: str, limit: int) -> list[dict]:
    term = f"%{query}%"
    with db() as connection:
        cur = connection.execute(
            """
            SELECT ke.relation, ke.weight, ki.title, ki.id
            FROM knowledge_edges ke
            JOIN knowledge_items ki ON ki.id = ke.from_id
            WHERE ki.status = 'accepted' AND (ke.to_id LIKE %s OR ki.title LIKE %s)
            LIMIT %s
            """,
            (term, term, limit),
        )
        rows = rows_to_dicts(cur.fetchall())
    return [
        {
            "content": f"{r['title']} → {r['to_id']} ({r['relation']})",
            "title": r["title"],
            "source_class": "graph",
            "score": float(r.get("weight") or 0.5),
            "retrieval": "graph_sql",
        }
        for r in rows
    ]


def get_knowledge_subgraph(knowledge_id: str) -> dict:
    driver = _get_driver()
    if not driver:
        return _sql_subgraph(knowledge_id)

    with driver.session(database=settings.neo4j_database) as session:
        center = session.run(
            "MATCH (k:KnowledgeItem {id: $id}) RETURN k.title AS title, k.status AS status",
            id=knowledge_id,
        ).single()
        if not center:
            return {"knowledge_id": knowledge_id, "nodes": [], "edges": []}

        entities = session.run(
            """
            MATCH (k:KnowledgeItem {id: $id})-[r:MENTIONS]->(e:Entity)
            RETURN e.key AS id, e.name AS label, e.type AS type, r.confidence AS confidence
            """,
            id=knowledge_id,
        )
        entity_rows = [dict(r) for r in entities]

        edges = session.run(
            """
            MATCH (k:KnowledgeItem {id: $id})-[:MENTIONS]->(e:Entity)-[r]->(n)
            WHERE n:Entity OR n:Constitutional
            RETURN e.key AS from_id, coalesce(n.key, n.id) AS to_id, type(r) AS type, r.confidence AS confidence
            LIMIT 30
            """,
            id=knowledge_id,
        )
        edge_rows = [dict(r) for r in edges]

    nodes = [{"id": knowledge_id, "label": center["title"], "type": "KnowledgeItem"}]
    nodes.extend({"id": e["id"], "label": e["label"], "type": e["type"]} for e in entity_rows)
    return {"knowledge_id": knowledge_id, "nodes": nodes, "edges": edge_rows}


def _sql_subgraph(knowledge_id: str) -> dict:
    with db() as connection:
        item = connection.execute("SELECT title FROM knowledge_items WHERE id = %s", (knowledge_id,)).fetchone()
        if not item:
            return {"knowledge_id": knowledge_id, "nodes": [], "edges": []}
        title = item["title"] if isinstance(item, dict) else item[0]
        edges = rows_to_dicts(
            connection.execute(
                "SELECT from_id, to_id, relation, weight FROM knowledge_edges WHERE from_id = %s LIMIT 30",
                (knowledge_id,),
            ).fetchall()
        )
    nodes = [{"id": knowledge_id, "label": title, "type": "KnowledgeItem"}]
    for e in edges:
        nodes.append({"id": e["to_id"], "label": e["to_id"], "type": "Entity"})
    return {
        "knowledge_id": knowledge_id,
        "nodes": nodes,
        "edges": [
            {"from_id": e["from_id"], "to_id": e["to_id"], "type": e["relation"], "confidence": e["weight"]}
            for e in edges
        ],
    }


def sync_static_nodes() -> dict:
    return seed_vault_graph()


async def project_accepted_knowledge(knowledge_id: str) -> dict:
    return await index_accepted_knowledge(knowledge_id)


def knowledge_graph(knowledge_id: str) -> dict:
    return get_knowledge_subgraph(knowledge_id)


def entity_search(q: str, limit: int = 12) -> list[dict]:
    driver = _get_driver()
    if not driver:
        term = f"%{q}%"
        with db() as connection:
            cur = connection.execute(
                "SELECT to_id AS name, relation AS type, weight AS confidence FROM knowledge_edges WHERE to_id LIKE %s LIMIT %s",
                (term, limit),
            )
            return rows_to_dicts(cur.fetchall())
    tokens = [t for t in q.lower().split() if len(t) > 2][:4]
    with driver.session(database=settings.neo4j_database) as session:
        rows = session.run(
            """
            MATCH (e:Entity)
            WHERE ANY(token IN $tokens WHERE toLower(e.name) CONTAINS token)
            RETURN e.key AS id, e.name AS name, e.type AS type, e.confidence AS confidence
            LIMIT $limit
            """,
            tokens=tokens or [q.lower()[:20]],
            limit=limit,
        )
        return [dict(r) for r in rows]


def neighbors(node_id: str, limit: int = 20) -> dict:
    driver = _get_driver()
    if not driver:
        with db() as connection:
            out_edges = rows_to_dicts(
                connection.execute(
                    "SELECT to_id AS target, relation AS type, weight AS confidence FROM knowledge_edges WHERE from_id = %s LIMIT %s",
                    (node_id, limit),
                ).fetchall()
            )
        return {"node_id": node_id, "neighbors": out_edges}

    with driver.session(database=settings.neo4j_database) as session:
        rows = session.run(
            """
            MATCH (n {id: $id})-[r]-(m)
            RETURN coalesce(m.id, m.key) AS id,
                   coalesce(m.name, m.title, m.statement) AS label,
                   labels(m)[0] AS type,
                   type(r) AS relation,
                   r.confidence AS confidence
            LIMIT $limit
            UNION
            MATCH (n:Entity {key: $id})-[r]-(m)
            RETURN coalesce(m.id, m.key) AS id,
                   coalesce(m.name, m.title, m.statement) AS label,
                   labels(m)[0] AS type,
                   type(r) AS relation,
                   r.confidence AS confidence
            LIMIT $limit
            """,
            id=node_id,
            limit=limit,
        )
        return {"node_id": node_id, "neighbors": [dict(r) for r in rows]}


def shortest_path(from_id: str, to_id: str, max_hops: int = 4) -> list[dict]:
    driver = _get_driver()
    if not driver:
        return []

    with driver.session(database=settings.neo4j_database) as session:
        result = session.run(
            """
            MATCH p = shortestPath((a)-[*..%d]-(b))
            WHERE (a.id = $from_id OR a.key = $from_id)
              AND (b.id = $to_id OR b.key = $to_id)
            RETURN [r IN relationships(p) | {from: startNode(r).name, to: endNode(r).name, type: type(r)}] AS edges
            LIMIT 1
            """
            % max_hops,
            from_id=from_id,
            to_id=to_id,
        )
        row = result.single()
        return row["edges"] if row else []
