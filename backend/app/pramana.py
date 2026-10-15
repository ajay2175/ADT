from __future__ import annotations

import json
import uuid
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from app.database import NOW, db, rows_to_dicts


class AbsenceKind(str, Enum):
    """Distinguish epistemic absence from retrieval failure."""

    NOT_SEARCHED = "not_searched"
    NOT_FOUND = "not_found"  # searched, no positive evidence — not proof of nonexistence
    NOT_OBSERVED = "not_observed"
    CONTRADICTED = "contradicted"
    DEMONSTRABLY_ABSENT = "demonstrably_absent"  # justified negative knowledge only


class EvidenceRecord(BaseModel):
    assertion_id: str
    evidence_type: Literal["passage", "observation", "inference", "expert", "citation"] = "passage"
    source_id: str = ""
    passage: str = Field(default="", max_length=8000)
    supports: bool = True
    source_reliability: float = Field(default=0.5, ge=0, le=1)
    validation_status: Literal["proposed", "reviewed", "accepted", "rejected"] = "proposed"
    inference_dependencies: list[str] = Field(default_factory=list)
    absence: AbsenceKind | None = None
    reviewer_note: str = ""


def add_evidence(record: EvidenceRecord) -> dict:
    eid = str(uuid.uuid4())
    with db() as connection:
        if not connection.execute(
            "SELECT id FROM padartha_assertions WHERE id = %s", (record.assertion_id,)
        ).fetchone():
            raise ValueError("Assertion not found")
        connection.execute(
            """
            INSERT INTO pramana_evidence
            (id, assertion_id, evidence_type, source_id, passage, supports, source_reliability,
             validation_status, inference_dependencies, absence, reviewer_note, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                eid,
                record.assertion_id,
                record.evidence_type,
                record.source_id,
                record.passage,
                1 if record.supports else 0,
                record.source_reliability,
                record.validation_status,
                json.dumps(record.inference_dependencies),
                record.absence.value if record.absence else None,
                record.reviewer_note,
                NOW(),
            ),
        )
    return {"id": eid, **record.model_dump()}


def ledger_for_assertion(assertion_id: str) -> list[dict]:
    with db() as connection:
        cur = connection.execute(
            "SELECT * FROM pramana_evidence WHERE assertion_id = %s ORDER BY created_at",
            (assertion_id,),
        )
        rows = rows_to_dicts(cur.fetchall())
    for row in rows:
        row["supports"] = bool(row.get("supports"))
        row["inference_dependencies"] = json.loads(row.get("inference_dependencies") or "[]")
    return rows


def assertion_has_accepted_support(assertion_id: str) -> bool:
    with db() as connection:
        cur = connection.execute(
            """
            SELECT COUNT(*) AS c FROM pramana_evidence
            WHERE assertion_id = %s AND supports = 1 AND validation_status = 'accepted'
            """,
            (assertion_id,),
        )
        row = cur.fetchone()
        c = row["c"] if isinstance(row, dict) else row[0]
    return c > 0
