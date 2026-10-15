from __future__ import annotations

import json
import uuid

from app.database import NOW, db, row_to_dict, rows_to_dicts
from app.jnana import JnanaState, get_state
from app.padartha import list_assertions
from app.pramana import assertion_has_accepted_support


def link_assertions_to_decision(decision_id: str, assertion_ids: list[str]) -> None:
    with db() as connection:
        for aid in assertion_ids:
            if not aid:
                continue
            connection.execute(
                "INSERT INTO decision_assertion_links (id, decision_id, assertion_id, created_at) VALUES (%s, %s, %s, %s)",
                (str(uuid.uuid4()), decision_id, aid, NOW()),
            )


def discover_supporting_assertions(question: str, explicit_ids: list[str] | None = None) -> list[str]:
    ids = list(explicit_ids or [])
    tokens = [t for t in question.lower().split() if len(t) > 4][:5]
    for assertion in list_assertions(limit=100):
        blob = f"{assertion['subject']} {assertion['object']}".lower()
        if any(t in blob for t in tokens):
            ids.append(assertion["id"])
    return list(dict.fromkeys(ids))


def authorization_report(decision_id: str, exploratory: bool = False) -> dict:
    with db() as connection:
        cur = connection.execute(
            "SELECT assertion_id FROM decision_assertion_links WHERE decision_id = %s",
            (decision_id,),
        )
        links = [row["assertion_id"] if isinstance(row, dict) else row[0] for row in cur.fetchall()]

    if exploratory:
        return {
            "authorized": True,
            "mode": "exploratory",
            "message": "Exploratory decision — not authorized for restricted clinical actions.",
            "assertions": links,
        }

    if not links:
        return {
            "authorized": False,
            "mode": "consequential",
            "reason": "No supporting assertions linked; cannot finalize consequential decision.",
            "assertions": [],
        }

    blockers: list[dict] = []
    for aid in links:
        assertions = [a for a in list_assertions(limit=200) if a["id"] == aid]
        if not assertions:
            blockers.append({"assertion_id": aid, "reason": "missing"})
            continue
        a = assertions[0]
        reasons = []
        if a["epistemic_status"] != "accepted":
            reasons.append(f"epistemic_status={a['epistemic_status']}")
        if not assertion_has_accepted_support(aid):
            reasons.append("no_accepted_pramana")
        j = get_state("assertion", aid)
        if j and j.get("state") != JnanaState.PRAMA.value:
            reasons.append(f"jnana={j.get('state')}")
        if reasons:
            blockers.append({"assertion_id": aid, "reason": ";".join(reasons)})

    return {
        "authorized": len(blockers) == 0,
        "mode": "consequential",
        "assertions": links,
        "blockers": blockers,
    }


def require_finalize_authorization(decision_id: str, exploratory: bool = False) -> dict:
    report = authorization_report(decision_id, exploratory=exploratory)
    if not report["authorized"]:
        raise PermissionError(json.dumps(report))
    with db() as connection:
        connection.execute(
            "INSERT INTO audit_events VALUES (%s, 'decision_authorized', %s, %s, %s)",
            (str(uuid.uuid4()), decision_id, json.dumps(report), NOW()),
        )
    return report
