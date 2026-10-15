from __future__ import annotations

import json
import uuid
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from app.database import NOW, db, rows_to_dicts

HypothesisStatus = Literal[
    "proposed",
    "evidence_gathering",
    "tested",
    "supported",
    "refuted",
    "inconclusive",
    "revised",
]

ALLOWED_HYPOTHESIS_TRANSITIONS: dict[str, set[str]] = {
    "proposed": {"evidence_gathering", "revised"},
    "evidence_gathering": {"tested", "revised", "inconclusive"},
    "tested": {"supported", "refuted", "inconclusive", "revised"},
    "supported": {"revised"},
    "refuted": {"revised"},
    "inconclusive": {"evidence_gathering", "revised"},
    "revised": {"proposed"},
}


class HypothesisCreate(BaseModel):
    title: str = Field(min_length=4, max_length=400)
    statement: str = Field(min_length=10, max_length=4000)
    program_id: str = "aca_faculty_dissociation"
    assumptions: list[str] = Field(default_factory=list)


def create_hypothesis(payload: HypothesisCreate) -> dict:
    hid = str(uuid.uuid4())
    with db() as connection:
        connection.execute(
            """
            INSERT INTO theory_hypotheses
            (id, program_id, title, statement, status, assumptions_json, outcome_json, created_at, updated_at)
            VALUES (%s, %s, %s, %s, 'proposed', %s, %s, %s, %s)
            """,
            (
                hid,
                payload.program_id,
                payload.title,
                payload.statement,
                json.dumps(payload.assumptions),
                "{}",
                NOW(),
                NOW(),
            ),
        )
        connection.execute(
            "INSERT INTO audit_events VALUES (%s, 'hypothesis_created', %s, %s, %s)",
            (str(uuid.uuid4()), hid, payload.model_dump_json(), NOW()),
        )
    return {"id": hid, "status": "proposed", **payload.model_dump()}


def transition_hypothesis(hypothesis_id: str, new_status: HypothesisStatus, note: str = "") -> dict:
    with db() as connection:
        row = connection.execute("SELECT status FROM theory_hypotheses WHERE id = %s", (hypothesis_id,)).fetchone()
        if not row:
            raise ValueError("Hypothesis not found")
        current = row["status"] if isinstance(row, dict) else row[0]
        if new_status not in ALLOWED_HYPOTHESIS_TRANSITIONS.get(current, set()):
            raise ValueError(f"Invalid hypothesis transition {current} → {new_status}")
        connection.execute(
            "UPDATE theory_hypotheses SET status = %s, updated_at = %s WHERE id = %s",
            (new_status, NOW(), hypothesis_id),
        )
        connection.execute(
            "INSERT INTO audit_events VALUES (%s, 'hypothesis_transition', %s, %s, %s)",
            (str(uuid.uuid4()), hypothesis_id, json.dumps({"from": current, "to": new_status, "note": note}), NOW()),
        )
    return {"id": hypothesis_id, "status": new_status, "note": note}


def record_hypothesis_outcome(hypothesis_id: str, outcome: dict) -> dict:
    with db() as connection:
        connection.execute(
            "UPDATE theory_hypotheses SET outcome_json = %s, updated_at = %s WHERE id = %s",
            (json.dumps(outcome), NOW(), hypothesis_id),
        )
    return {"id": hypothesis_id, "outcome": outcome}


def list_hypotheses(program_id: str | None = None, limit: int = 50) -> list[dict]:
    params: list = []
    where = ""
    if program_id:
        where = "WHERE program_id = %s"
        params.append(program_id)
    params.append(limit)
    with db() as connection:
        cur = connection.execute(
            f"SELECT * FROM theory_hypotheses {where} ORDER BY updated_at DESC LIMIT %s",
            tuple(params),
        )
        rows = rows_to_dicts(cur.fetchall())
    for row in rows:
        row["assumptions"] = json.loads(row.pop("assumptions_json", "[]"))
        row["outcome"] = json.loads(row.pop("outcome_json", "{}"))
    return rows
