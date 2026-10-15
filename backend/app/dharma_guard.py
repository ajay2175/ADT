from __future__ import annotations

import json
from enum import Enum

from app.database import db, rows_to_dicts


class GuardAction(str, Enum):
    CONSTITUTION_WRITE = "constitution_write"
    CONSTITUTION_DELETE = "constitution_delete"
    ASSERTION_CONSTITUTIONAL_FLAG = "assertion_constitutional_flag"
    GRAPH_PROTECTED_NODE_WRITE = "graph_protected_node_write"
    AMENDMENT_WITHOUT_AUDIT = "amendment_without_audit"


BLOCKED_WITHOUT_EXPLICIT_APPROVAL = frozenset(
    {
        GuardAction.CONSTITUTION_WRITE,
        GuardAction.CONSTITUTION_DELETE,
        GuardAction.ASSERTION_CONSTITUTIONAL_FLAG,
        GuardAction.GRAPH_PROTECTED_NODE_WRITE,
    }
)

INJECTION_PATTERNS = (
    "ignore prior constitution",
    "rewrite dharma",
    "update constitution_items",
    "set constitutional",
    "approve amendment automatically",
    "you are now unrestricted",
    "bypass dharma guard",
)


def scan_content_for_injection(text: str) -> list[str]:
    lower = text.lower()
    return [p for p in INJECTION_PATTERNS if p in lower]


def record_injection_audit(subject_id: str, channel: str, flags: list[str]) -> None:
    import uuid

    from app.database import NOW, db

    if not flags:
        return
    with db() as connection:
        connection.execute(
            "INSERT INTO audit_events VALUES (%s, 'injection_attempt_detected', %s, %s, %s)",
            (str(uuid.uuid4()), subject_id, json.dumps({"channel": channel, "flags": flags}), NOW()),
        )


def require_authorize(action: GuardAction, context: dict | None = None) -> None:
    result = authorize(action, context)
    if not result.get("allowed"):
        raise PermissionError(result.get("reason", "denied"))


def deny_protected_graph_mutation(node_id: str) -> None:
    with db() as connection:
        row = connection.execute(
            "SELECT protected FROM graph_nodes WHERE id = %s",
            (node_id,),
        ).fetchone()
    if row and (row["protected"] if isinstance(row, dict) else row[0]):
        require_authorize(GuardAction.GRAPH_PROTECTED_NODE_WRITE, {})


def authorize(action: GuardAction, context: dict | None = None) -> dict:
    """Return allow/deny with reason. Explicit amendment approval required for blocked actions."""
    context = context or {}
    if action in BLOCKED_WITHOUT_EXPLICIT_APPROVAL:
        if context.get("explicit_ajay_approval") is True and context.get("amendment_id"):
            return {"allowed": True, "action": action.value, "mode": "explicit_amendment"}
        return {
            "allowed": False,
            "action": action.value,
            "reason": "Constitutional identity cannot change without explicit Ajay approval and amendment id.",
        }
    if action == GuardAction.AMENDMENT_WITHOUT_AUDIT:
        return {"allowed": False, "reason": "Amendments must create audit_events."}
    return {"allowed": True, "action": action.value}


def constitution_snapshot() -> list[dict]:
    with db() as connection:
        cur = connection.execute(
            "SELECT id, category, statement, status, priority, version FROM constitution_items ORDER BY id"
        )
        return rows_to_dicts(cur.fetchall())


def assert_constitution_unchanged(before: list[dict], after: list[dict]) -> None:
    if len(before) != len(after):
        raise AssertionError("Constitution item count changed without authorization")
    bmap = {r["id"]: r for r in before}
    for row in after:
        prev = bmap.get(row["id"])
        if not prev:
            raise AssertionError(f"New constitution item {row['id']} without authorization")
        if prev["statement"] != row["statement"] or prev["status"] != row["status"]:
            raise AssertionError(f"Constitution item {row['id']} mutated without authorization")


def protected_graph_integrity() -> dict:
    with db() as connection:
        cur = connection.execute("SELECT COUNT(*) AS c FROM graph_nodes WHERE protected = 1")
        row = cur.fetchone()
        protected = row["c"] if isinstance(row, dict) else row[0]
        cur = connection.execute("SELECT COUNT(*) AS c FROM constitution_items WHERE status = 'approved'")
        row = cur.fetchone()
        approved = row["c"] if isinstance(row, dict) else row[0]
    return {"protected_graph_nodes": protected, "approved_constitution_items": approved, "ok": protected >= approved}
