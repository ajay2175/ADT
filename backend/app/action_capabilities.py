from __future__ import annotations

import json
from enum import Enum

from app.database import db


class FinalizeKind(str, Enum):
    RESEARCH_RECORD = "research_record"
    CONSEQUENTIAL = "consequential"


class ActionCapability(str, Enum):
    """Executable permissions granted by a finalized decision (not inferred from text)."""

    RECORD_RESEARCH = "record_research"
    EXECUTE_CONSEQUENTIAL = "execute_consequential"
    CLINICAL_ACTION = "clinical_action"
    EXTERNAL_TOOL = "external_tool"
    PROTECTED_MUTATION = "protected_mutation"


RESEARCH_ONLY: frozenset[ActionCapability] = frozenset({ActionCapability.RECORD_RESEARCH})

CONSEQUENTIAL_BASE: frozenset[ActionCapability] = frozenset(
    {
        ActionCapability.RECORD_RESEARCH,
        ActionCapability.EXECUTE_CONSEQUENTIAL,
    }
)


def capabilities_for_finalize_kind(kind: FinalizeKind) -> list[str]:
    if kind == FinalizeKind.RESEARCH_RECORD:
        return sorted(c.value for c in RESEARCH_ONLY)
    return sorted(c.value for c in CONSEQUENTIAL_BASE)


def decision_capabilities(decision_id: str) -> set[str]:
    with db() as connection:
        row = connection.execute(
            "SELECT action_capabilities_json FROM decision_records WHERE id = %s",
            (decision_id,),
        ).fetchone()
    if not row:
        return set()
    raw = row["action_capabilities_json"] if isinstance(row, dict) else row[0]
    if not raw:
        return set()
    return set(json.loads(raw))


def require_decision_capability(decision_id: str, capability: ActionCapability) -> None:
    granted = decision_capabilities(decision_id)
    if capability.value not in granted:
        raise PermissionError(
            f"Decision {decision_id} lacks capability '{capability.value}' "
            f"(granted: {sorted(granted) or 'none — finalize decision first'})"
        )
