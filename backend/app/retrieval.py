from __future__ import annotations

import json
import math

import numpy as np

from app.database import db, rows_to_dicts
from app.model_gateway import get_provider


def _cosine(a: list[float], b: list[float]) -> float:
    va, vb = np.array(a), np.array(b)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    return float(np.dot(va, vb) / denom) if denom else 0.0


async def vector_search(query: str, limit: int = 10) -> list[dict]:
    provider = get_provider()
    qvec = (await provider.embed([query]))[0]
    results: list[tuple[float, dict]] = []

    with db() as connection:
        if connection.dialect == "postgres":
            cur = connection.execute(
                """
                SELECT kc.content, kc.chunk_index, ki.title, ki.source_class, ki.status,
                       1 - (kc.embedding <=> %s::vector) AS score
                FROM knowledge_chunks kc
                JOIN knowledge_items ki ON ki.id = kc.knowledge_id
                WHERE ki.status = 'accepted' AND kc.embedding IS NOT NULL
                ORDER BY kc.embedding <=> %s::vector
                LIMIT %s
                """,
                (qvec, qvec, limit),
            )
            for row in rows_to_dicts(cur.fetchall()):
                results.append((row["score"], row))
        else:
            cur = connection.execute(
                """
                SELECT kc.content, kc.chunk_index, kc.embedding_json, ki.title, ki.source_class, ki.status
                FROM knowledge_chunks kc
                JOIN knowledge_items ki ON ki.id = kc.knowledge_id
                WHERE ki.status = 'accepted'
                """
            )
            for row in rows_to_dicts(cur.fetchall()):
                emb = json.loads(row["embedding_json"] or "[]")
                if emb:
                    results.append((_cosine(qvec, emb), row))
            results.sort(key=lambda x: x[0], reverse=True)
            results = results[:limit]

    return [
        {
            "content": r["content"][:400],
            "title": r["title"],
            "source_class": r["source_class"],
            "score": round(s, 4),
            "retrieval": "vector",
        }
        for s, r in results
    ]


async def hybrid_search(query: str, include_proposed: bool = False, limit: int = 15) -> list[dict]:
    term = f"%{query}%"
    approved = "" if include_proposed else "AND k.status = 'accepted'"
    with db() as connection:
        cur = connection.execute(
            f"""
            SELECT k.id, k.title, k.summary, k.source_class, k.status,
                   c.statement AS claim, c.status AS claim_status, c.confidence
            FROM knowledge_items k LEFT JOIN claims c ON c.knowledge_id = k.id
            WHERE (k.title LIKE %s OR k.summary LIKE %s OR c.statement LIKE %s) {approved}
            ORDER BY k.created_at DESC LIMIT %s
            """,
            (term, term, term, limit),
        )
        text_hits = rows_to_dicts(cur.fetchall())

    vector_hits = await vector_search(query, limit=limit)
    seen = set()
    merged = []
    for hit in vector_hits:
        key = hit["content"][:80]
        if key not in seen:
            seen.add(key)
            merged.append(hit)
    for hit in text_hits:
        key = (hit.get("claim") or hit.get("summary", ""))[:80]
        if key not in seen:
            seen.add(key)
            merged.append({**hit, "retrieval": "text"})
    return merged[:limit]
