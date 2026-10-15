from __future__ import annotations

import json
import uuid

from app.database import NOW, db, rows_to_dicts
from app.extraction import extract_entities_relations
from app.jnana import JnanaState, transition
from app.padartha import GraphAssertion, PadarthaSlice, RelationKind, create_assertion, list_assertions
from app.pramana import EvidenceRecord, add_evidence, assertion_has_accepted_support

_GRAPH_TO_PADARTHA = {
    "MENTIONS": RelationKind.ASSOCIATION,
    "RELATES_TO": RelationKind.ASSOCIATION,
    "SUPPORTS": RelationKind.ASSOCIATION,
    "CONTRADICTS": RelationKind.ASSOCIATION,
    "PART_OF": RelationKind.COMPOSITION,
    "DERIVED_FROM": RelationKind.ASSOCIATION,
}


async def project_epistemic_from_knowledge(knowledge_id: str, text: str, title: str) -> dict:
    """
    Sprint 1: Document admission (knowledge accepted) → proposed Padārtha assertions
    → source-linked Pramāṇa records → Jñāna savikalpa. Idempotent per knowledge_id.
    """
    existing = list_assertions(knowledge_id=knowledge_id)
    if existing:
        return {
            "knowledge_id": knowledge_id,
            "idempotent": True,
            "assertions": len(existing),
            "assertion_ids": [a["id"] for a in existing],
        }

    extracted = await extract_entities_relations(title, text)
    assertion_ids: list[str] = []

    for rel in extracted.get("relations", []):
        rk = _GRAPH_TO_PADARTHA.get(rel.get("type", "RELATES_TO"), RelationKind.ASSOCIATION)
        payload = GraphAssertion(
            subject=rel["from"],
            predicate=rel.get("type", "relates_to").lower(),
            object=rel["to"],
            relation_kind=rk,
            padartha=PadarthaSlice(
                dravya=rel["from"],
                samanya=["extracted_entity"],
                vishesha=f"entity_{_slug(rel['from'])}",
            ),
            epistemic_status="proposed",
            source_ids=[knowledge_id],
            knowledge_id=knowledge_id,
        )
        created = create_assertion(payload)
        assertion_ids.append(created["id"])
        _attach_source_evidence(created["id"], knowledge_id, text, rel)
        _init_jnana(created["id"])

    if not assertion_ids:
        for entity in extracted.get("entities", []):
            payload = GraphAssertion(
                subject=entity["name"],
                predicate="mentioned_in_document",
                object=title[:200],
                relation_kind=RelationKind.ASSOCIATION,
                padartha=PadarthaSlice(
                    dravya=entity["name"] if entity.get("type") in ("Concept", "Domain") else None,
                    samanya=[entity.get("type", "Concept").lower()],
                    vishesha=f"entity_{_slug(entity['name'])}",
                ),
                epistemic_status="proposed",
                source_ids=[knowledge_id],
                knowledge_id=knowledge_id,
            )
            created = create_assertion(payload)
            assertion_ids.append(created["id"])
            _attach_source_evidence(created["id"], knowledge_id, text, entity)
            _init_jnana(created["id"])

    with db() as connection:
        connection.execute(
            "INSERT INTO audit_events VALUES (%s, 'epistemic_projected', %s, %s, %s)",
            (
                str(uuid.uuid4()),
                knowledge_id,
                json.dumps({"assertions": len(assertion_ids), "document_admission_only": True}),
                NOW(),
            ),
        )

    return {
        "knowledge_id": knowledge_id,
        "document_admission": True,
        "assertion_validation": "pending",
        "assertions_created": len(assertion_ids),
        "assertion_ids": assertion_ids,
    }


def _slug(name: str) -> str:
    return name.strip().lower().replace(" ", "_")[:80]


def _attach_source_evidence(assertion_id: str, knowledge_id: str, text: str, ref: dict) -> None:
    snippet = text[:500]
    if isinstance(ref, dict) and ref.get("from") and ref.get("to"):
        snippet = f"Extracted relation: {ref['from']} → {ref['to']}"
    elif isinstance(ref, dict) and ref.get("name"):
        snippet = f"Extracted entity: {ref['name']}"
    add_evidence(
        EvidenceRecord(
            assertion_id=assertion_id,
            evidence_type="passage",
            source_id=knowledge_id,
            passage=snippet,
            supports=True,
            source_reliability=0.5,
            validation_status="proposed",
        )
    )


def _init_jnana(assertion_id: str) -> None:
    transition("assertion", assertion_id, JnanaState.NIRVIKALPA, "raw extraction")
    transition("assertion", assertion_id, JnanaState.SAVIKALPA, "structured padartha assertion")


def promote_assertion_to_prama(assertion_id: str, reviewer_note: str = "") -> dict:
    """Assertion validation — distinct from document admission. Requires accepted Pramāṇa support."""
    if not assertion_has_accepted_support(assertion_id):
        raise ValueError("Cannot promote to pramā without accepted supporting evidence in Pramāṇa ledger")
    transition("assertion", assertion_id, JnanaState.SAMSHAYA, "review for promotion")
    transition("assertion", assertion_id, JnanaState.PRAMA, reviewer_note or "validated within defined scope")
    with db() as connection:
        connection.execute(
            "UPDATE padartha_assertions SET epistemic_status = 'accepted' WHERE id = %s",
            (assertion_id,),
        )
        connection.execute(
            "INSERT INTO audit_events VALUES (%s, 'assertion_validated', %s, %s, %s)",
            (str(uuid.uuid4()), assertion_id, json.dumps({"jnana": "prama"}), NOW()),
        )
    return {"assertion_id": assertion_id, "epistemic_status": "accepted", "jnana": "prama"}


def trace_knowledge_lineage(knowledge_id: str) -> dict:
    assertions = list_assertions(knowledge_id=knowledge_id)
    lineage = []
    for a in assertions:
        with db() as connection:
            ev = rows_to_dicts(
                connection.execute(
                    "SELECT id, source_id, validation_status, passage FROM pramana_evidence WHERE assertion_id = %s",
                    (a["id"],),
                ).fetchall()
            )
            j = connection.execute(
                "SELECT state FROM jnana_states WHERE subject_type = 'assertion' AND subject_id = %s",
                (a["id"],),
            ).fetchone()
        lineage.append(
            {
                "assertion_id": a["id"],
                "subject": a["subject"],
                "predicate": a["predicate"],
                "object": a["object"],
                "epistemic_status": a["epistemic_status"],
                "jnana": j["state"] if isinstance(j, dict) else (j[0] if j else None),
                "evidence": ev,
            }
        )
    return {"knowledge_id": knowledge_id, "lineage": lineage}
