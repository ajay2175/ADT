from __future__ import annotations

import json
import uuid
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from app.database import NOW, db, rows_to_dicts


class RelationKind(str, Enum):
    """Graph edge semantics — Samavāya is inherence only, not a generic edge label."""

    SAMAVAYA = "samavaya"  # inseparable inherence (e.g. quality in substance)
    SAMYOGA = "samyoga"  # conjunction / contact
    SAMYUKTASAMAVAYA = "samyuktasamavaya"
    ASAMYOGA = "asamyoga"  # disjunction
    CAUSATION = "causation"
    COMPOSITION = "composition"
    ASSOCIATION = "association"  # ordinary relational link (default GraphRAG MENTIONS/RELATES_TO)


class PadarthaSlice(BaseModel):
    dravya: str | None = None
    guna: list[str] = Field(default_factory=list)
    karma: list[str] = Field(default_factory=list)
    samanya: list[str] = Field(default_factory=list)
    vishesha: str | None = None
    samavaya: list[str] = Field(default_factory=list)  # inherence targets only
    abhava: list[str] = Field(default_factory=list)  # typed absence, not "not found"


class GraphAssertion(BaseModel):
    subject: str = Field(min_length=1, max_length=500)
    predicate: str = Field(min_length=1, max_length=240)
    object: str = Field(min_length=1, max_length=500)
    relation_kind: RelationKind = RelationKind.ASSOCIATION
    padartha: PadarthaSlice = Field(default_factory=PadarthaSlice)
    epistemic_status: Literal["proposed", "accepted", "rejected", "superseded"] = "proposed"
    source_ids: list[str] = Field(default_factory=list)
    constitutional: bool = False
    knowledge_id: str | None = None


def create_assertion(payload: GraphAssertion) -> dict:
    if payload.constitutional:
        raise ValueError("Padārtha assertions cannot be marked constitutional; use amendment workflow.")
    aid = str(uuid.uuid4())
    with db() as connection:
        connection.execute(
            """
            INSERT INTO padartha_assertions
            (id, subject, predicate, object, relation_kind, padartha_json, epistemic_status,
             source_ids, constitutional, knowledge_id, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                aid,
                payload.subject,
                payload.predicate,
                payload.object,
                payload.relation_kind.value,
                payload.padartha.model_dump_json(),
                payload.epistemic_status,
                json.dumps(payload.source_ids),
                0,
                payload.knowledge_id,
                NOW(),
            ),
        )
    return {"id": aid, **payload.model_dump(), "relation_kind": payload.relation_kind.value}


def list_assertions(
    epistemic_status: str | None = None,
    knowledge_id: str | None = None,
    limit: int = 50,
) -> list[dict]:
    clauses = []
    params: list = []
    if epistemic_status:
        clauses.append("epistemic_status = %s")
        params.append(epistemic_status)
    if knowledge_id:
        clauses.append("knowledge_id = %s")
        params.append(knowledge_id)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    with db() as connection:
        cur = connection.execute(
            f"SELECT * FROM padartha_assertions {where} ORDER BY created_at DESC LIMIT %s",
            tuple(params),
        )
        rows = rows_to_dicts(cur.fetchall())
    for row in rows:
        row["padartha"] = json.loads(row.pop("padartha_json", "{}"))
        row["source_ids"] = json.loads(row.get("source_ids") or "[]")
        row["constitutional"] = bool(row.get("constitutional"))
    return rows
