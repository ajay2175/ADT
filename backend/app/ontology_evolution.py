from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from app.database import NOW, db


class OntologyProposal(BaseModel):
    title: str = Field(min_length=4, max_length=200)
    changes: list[dict] = Field(default_factory=list)
    rationale: str = Field(min_length=10, max_length=4000)


def propose_ontology_change(payload: OntologyProposal) -> dict:
    """Sandboxed ontology proposals — never auto-applied; does not mutate constitution."""
    pid = str(uuid.uuid4())
    with db() as connection:
        connection.execute(
            "INSERT INTO ontology_proposals (id, proposal_json, status, created_at) VALUES (%s, %s, 'proposed', %s)",
            (pid, payload.model_dump_json(), NOW()),
        )
    return {"id": pid, "status": "proposed", "message": "Ontology change recorded for review; not applied."}
