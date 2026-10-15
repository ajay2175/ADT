from __future__ import annotations

import json
import uuid
from typing import Literal

from pydantic import BaseModel, Field

from app.database import NOW, db, rows_to_dicts
from app.padartha import RelationKind


class CausalClaimCreate(BaseModel):
    cause: str = Field(min_length=2, max_length=500)
    effect: str = Field(min_length=2, max_length=500)
    assumptions: list[str] = Field(default_factory=list)
    justification: str = Field(default="", max_length=4000)
    status: Literal["proposed", "accepted", "rejected"] = "proposed"
    hypothesis_id: str | None = None


def register_causal_claim(payload: CausalClaimCreate) -> dict:
    """Causal claims are stored separately from associative GraphRAG edges."""
    cid = str(uuid.uuid4())
    with db() as connection:
        connection.execute(
            """
            INSERT INTO causal_claims
            (id, cause, effect, assumptions_json, justification, status, hypothesis_id, relation_kind, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                cid,
                payload.cause,
                payload.effect,
                json.dumps(payload.assumptions),
                payload.justification,
                payload.status,
                payload.hypothesis_id,
                RelationKind.CAUSATION.value,
                NOW(),
            ),
        )
    return {"id": cid, "relation_kind": RelationKind.CAUSATION.value, **payload.model_dump()}


def list_causal_claims(status: str | None = None, limit: int = 50) -> list[dict]:
    params: list = []
    where = ""
    if status:
        where = "WHERE status = %s"
        params.append(status)
    params.append(limit)
    with db() as connection:
        cur = connection.execute(
            f"SELECT * FROM causal_claims {where} ORDER BY created_at DESC LIMIT %s",
            tuple(params),
        )
        rows = rows_to_dicts(cur.fetchall())
    for row in rows:
        row["assumptions"] = json.loads(row.pop("assumptions_json", "[]"))
    return rows


def counterfactual(intervention: str, target_effect: str, claims: list[dict] | None = None) -> dict:
    """
    Lightweight counterfactual scaffold: match causal claims where intervention relates to cause.
    Not a full structural causal model — requires explicit causal_claims to be registered.
    """
    claims = claims or list_causal_claims(status="accepted", limit=20)
    intervention_l = intervention.lower()
    matches = [
        c
        for c in claims
        if intervention_l in c["cause"].lower() or intervention_l in c["effect"].lower()
    ]
    if not matches:
        return {
            "intervention": intervention,
            "target_effect": target_effect,
            "result": "inconclusive",
            "epistemic_label": "simulation_hypothesis",
            "reason": "No accepted causal claims match intervention; association ≠ causation.",
            "matched_claims": [],
        }
    return {
        "intervention": intervention,
        "target_effect": target_effect,
        "result": "plausible_under_assumptions",
        "epistemic_label": "simulation_hypothesis",
        "matched_claims": matches[:5],
        "caveat": "Counterfactual output is a simulation hypothesis, not an experimentally established causal result.",
    }
