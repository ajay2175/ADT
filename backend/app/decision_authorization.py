from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta

from app.action_capabilities import FinalizeKind, capabilities_for_finalize_kind
from app.database import NOW, db
from app.jnana import JnanaState, get_state
from app.padartha import list_assertions
from app.pramana import assertion_has_accepted_support, ledger_for_assertion

GRANT_TTL_MINUTES = 15

RESTRICTED_ACTION_PATTERNS = (
    "prescribe",
    "treat patient",
    "clinical recommendation",
    "deploy to production",
    "delete constitution",
    "amend constitution",
    "override dharma",
)


def link_assertions_to_decision(decision_id: str, assertion_ids: list[str]) -> None:
    with db() as connection:
        for aid in assertion_ids:
            if not aid:
                continue
            connection.execute(
                "INSERT INTO decision_assertion_links (id, decision_id, assertion_id, created_at) VALUES (%s, %s, %s, %s)",
                (str(uuid.uuid4()), decision_id, aid, NOW()),
            )
        connection.execute(
            "UPDATE decision_records SET evidence_link_version = COALESCE(evidence_link_version, 0) + 1 WHERE id = %s",
            (decision_id,),
        )


def discover_supporting_assertions(question: str, explicit_ids: list[str] | None = None) -> list[str]:
    ids = list(explicit_ids or [])
    tokens = [t for t in question.lower().split() if len(t) > 4][:5]
    for assertion in list_assertions(limit=100):
        blob = f"{assertion['subject']} {assertion['object']}".lower()
        if any(t in blob for t in tokens):
            ids.append(assertion["id"])
    return list(dict.fromkeys(ids))


def _links_for_decision(decision_id: str, connection=None) -> list[str]:
    if connection is None:
        with db() as conn:
            return _links_for_decision(decision_id, conn)
    cur = connection.execute(
        "SELECT assertion_id FROM decision_assertion_links WHERE decision_id = %s",
        (decision_id,),
    )
    return [row["assertion_id"] if isinstance(row, dict) else row[0] for row in cur.fetchall()]


def _assertion_blockers(links: list[str]) -> list[dict]:
    blockers: list[dict] = []
    for aid in links:
        assertions = [a for a in list_assertions(limit=200) if a["id"] == aid]
        if not assertions:
            blockers.append({"assertion_id": aid, "reason": "missing"})
            continue
        a = assertions[0]
        if a["epistemic_status"] == "rejected":
            blockers.append({"assertion_id": aid, "reason": "assertion_rejected"})
            continue
        reasons: list[str] = []
        if a["epistemic_status"] != "accepted":
            reasons.append(f"epistemic_status={a['epistemic_status']}")
        ledger = ledger_for_assertion(aid)
        if any(row.get("validation_status") == "rejected" for row in ledger):
            reasons.append("rejected_pramana")
        if any(not row.get("supports") and row.get("validation_status") == "accepted" for row in ledger):
            reasons.append("contradicting_pramana")
        if not assertion_has_accepted_support(aid):
            reasons.append("no_accepted_pramana")
        j = get_state("assertion", aid)
        if j and j.get("state") != JnanaState.PRAMA.value:
            reasons.append(f"jnana={j.get('state')}")
        if reasons:
            blockers.append({"assertion_id": aid, "reason": ";".join(reasons)})
    return blockers


def _phrase_risk_flags(text: str) -> list[str]:
    lower = text.lower()
    return [p for p in RESTRICTED_ACTION_PATTERNS if p in lower]


def authorization_report(
    decision_id: str,
    kind: FinalizeKind = FinalizeKind.CONSEQUENTIAL,
    final_decision_text: str = "",
    connection=None,
) -> dict:
    links = _links_for_decision(decision_id, connection)
    phrase_flags = _phrase_risk_flags(final_decision_text)

    if kind == FinalizeKind.RESEARCH_RECORD:
        return {
            "authorized": True,
            "mode": kind.value,
            "action_authorized": False,
            "capabilities": capabilities_for_finalize_kind(kind),
            "message": "Research record — no executable consequential, clinical, tool, or protected permissions.",
            "assertions": links,
            "phrase_risk_flags": phrase_flags,
        }

    if not links:
        return {
            "authorized": False,
            "mode": kind.value,
            "action_authorized": False,
            "reason": "Zero supporting assertions — consequential finalize denied.",
            "assertions": [],
            "phrase_risk_flags": phrase_flags,
        }

    blockers = _assertion_blockers(links)
    return {
        "authorized": len(blockers) == 0,
        "mode": kind.value,
        "action_authorized": len(blockers) == 0,
        "capabilities": capabilities_for_finalize_kind(kind) if len(blockers) == 0 else [],
        "assertions": links,
        "blockers": blockers,
        "phrase_risk_flags": phrase_flags,
    }


def _snapshot_payload(links: list[str], link_version: int) -> str:
    return json.dumps({"links": links, "evidence_link_version": link_version})


def _decision_link_version(connection, decision_id: str) -> int:
    row = connection.execute(
        "SELECT COALESCE(evidence_link_version, 0) AS v FROM decision_records WHERE id = %s",
        (decision_id,),
    ).fetchone()
    if not row:
        return 0
    return int(row["v"] if isinstance(row, dict) else row[0])


def issue_authorization_grant(decision_id: str, kind: FinalizeKind, final_decision_text: str) -> dict:
    with db() as connection:
        report = authorization_report(decision_id, kind, final_decision_text, connection)
        if not report["authorized"]:
            raise PermissionError(json.dumps(report))
        links = report.get("assertions", [])
        link_version = _decision_link_version(connection, decision_id)
        grant_id = str(uuid.uuid4())
        expires = (datetime.now(UTC) + timedelta(minutes=GRANT_TTL_MINUTES)).isoformat()
        snapshot = _snapshot_payload(links, link_version)
        connection.execute(
            """
            INSERT INTO decision_authorization_grants
            (id, decision_id, kind, snapshot_json, expires_at, used_at, created_at)
            VALUES (%s, %s, %s, %s, %s, NULL, %s)
            """,
            (grant_id, decision_id, kind.value, snapshot, expires, NOW()),
        )
        connection.execute(
            "INSERT INTO audit_events VALUES (%s, 'decision_authorization_granted', %s, %s, %s)",
            (str(uuid.uuid4()), decision_id, json.dumps({**report, "grant_id": grant_id}), NOW()),
        )
    return {"grant_id": grant_id, "expires_at": expires, **report}


def finalize_decision_atomically(
    decision_id: str,
    kind: FinalizeKind,
    final_decision_text: str,
    grant_id: str | None = None,
) -> dict:
    """
    Validate authorization, consume grant, and persist final decision in one transaction.
    """
    with db() as connection:
        if connection.dialect == "sqlite":
            connection.begin_immediate()

        if not connection.execute("SELECT id FROM decision_records WHERE id = %s", (decision_id,)).fetchone():
            raise ValueError("Decision record not found")

        report = authorization_report(decision_id, kind, final_decision_text, connection)
        if not report["authorized"]:
            raise PermissionError(json.dumps(report))

        links = report.get("assertions", [])
        link_version = _decision_link_version(connection, decision_id)
        snapshot = _snapshot_payload(links, link_version)

        effective_grant_id = grant_id
        if grant_id:
            row = connection.execute(
                """
                SELECT id, kind, snapshot_json, expires_at, used_at
                FROM decision_authorization_grants
                WHERE id = %s AND decision_id = %s
                """,
                (grant_id, decision_id),
            ).fetchone()
            if not row:
                raise PermissionError("Invalid authorization grant")
            rd = dict(row) if isinstance(row, dict) else {
                "kind": row[1],
                "snapshot_json": row[2],
                "expires_at": row[3],
                "used_at": row[4],
            }
            if rd.get("used_at"):
                raise PermissionError("Authorization grant already used (replay blocked)")
            if datetime.fromisoformat(rd["expires_at"]) < datetime.now(UTC):
                raise PermissionError("Authorization grant expired (stale)")
            if FinalizeKind(rd["kind"]) != kind:
                raise PermissionError("Grant kind does not match finalize request")
            stored = json.loads(rd["snapshot_json"])
            if stored.get("links") != links or int(stored.get("evidence_link_version", -1)) != link_version:
                raise PermissionError("Evidence snapshot changed since authorization — re-authorize required")
            updated = connection.execute(
                "UPDATE decision_authorization_grants SET used_at = %s WHERE id = %s AND used_at IS NULL",
                (NOW(), grant_id),
            )
            if getattr(updated, "rowcount", 0) == 0:
                raise PermissionError("Authorization grant already used (replay blocked)")
        else:
            effective_grant_id = str(uuid.uuid4())
            expires = (datetime.now(UTC) + timedelta(minutes=GRANT_TTL_MINUTES)).isoformat()
            connection.execute(
                """
                INSERT INTO decision_authorization_grants
                (id, decision_id, kind, snapshot_json, expires_at, used_at, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (effective_grant_id, decision_id, kind.value, snapshot, expires, NOW(), NOW()),
            )

        caps_json = json.dumps(capabilities_for_finalize_kind(kind))
        connection.execute(
            """
            UPDATE decision_records
            SET final_decision = %s, finalize_kind = %s, action_capabilities_json = %s
            WHERE id = %s
            """,
            (final_decision_text, kind.value, caps_json, decision_id),
        )
        connection.execute(
            "INSERT INTO audit_events VALUES (%s, 'decision_finalized', %s, %s, %s)",
            (
                str(uuid.uuid4()),
                decision_id,
                json.dumps({**report, "grant_id": effective_grant_id, "capabilities": caps_json}),
                NOW(),
            ),
        )

    return {**report, "grant_id": effective_grant_id, "finalized": True}
