from __future__ import annotations

import json
import uuid
from enum import Enum

from pydantic import BaseModel, Field

from app.database import NOW, db, row_to_dict


class JnanaState(str, Enum):
    """Computational analogues — not claims of reproducing human consciousness."""

    NIRVIKALPA = "nirvikalpa"
    SAVIKALPA = "savikalpa"
    SAMSHAYA = "samshaya"
    PRAMA = "prama"
    VIPARYAYA = "viparyaya"
    SMRITI = "smriti"


ALLOWED_TRANSITIONS: dict[JnanaState, set[JnanaState]] = {
    JnanaState.NIRVIKALPA: {JnanaState.SAVIKALPA},
    JnanaState.SAVIKALPA: {JnanaState.SAMSHAYA, JnanaState.PRAMA, JnanaState.VIPARYAYA, JnanaState.SMRITI},
    JnanaState.SAMSHAYA: {JnanaState.PRAMA, JnanaState.VIPARYAYA, JnanaState.SAVIKALPA},
    JnanaState.PRAMA: {JnanaState.SMRITI, JnanaState.SAMSHAYA},
    JnanaState.VIPARYAYA: {JnanaState.SAVIKALPA, JnanaState.SAMSHAYA},
    JnanaState.SMRITI: {JnanaState.SAVIKALPA, JnanaState.SAMSHAYA},
}


class CognitiveStateRecord(BaseModel):
    subject_type: str = Field(description="assertion | decision | knowledge_item")
    subject_id: str
    state: JnanaState = JnanaState.NIRVIKALPA
    note: str = ""


def transition(subject_type: str, subject_id: str, new_state: JnanaState, note: str = "") -> dict:
    with db() as connection:
        cur = connection.execute(
            "SELECT * FROM jnana_states WHERE subject_type = %s AND subject_id = %s",
            (subject_type, subject_id),
        )
        row = cur.fetchone()
        if row:
            rd = row_to_dict(row)
            current = JnanaState(rd["state"])
            if new_state not in ALLOWED_TRANSITIONS.get(current, set()):
                raise ValueError(f"Invalid transition {current.value} → {new_state.value}")
            connection.execute(
                "UPDATE jnana_states SET state = %s, note = %s, updated_at = %s WHERE subject_type = %s AND subject_id = %s",
                (new_state.value, note, NOW(), subject_type, subject_id),
            )
        else:
            if new_state != JnanaState.NIRVIKALPA:
                raise ValueError("Initial state must be nirvikalpa")
            connection.execute(
                "INSERT INTO jnana_states (id, subject_type, subject_id, state, note, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (str(uuid.uuid4()), subject_type, subject_id, new_state.value, note, NOW(), NOW()),
            )
    return {"subject_type": subject_type, "subject_id": subject_id, "state": new_state.value, "note": note}


def get_state(subject_type: str, subject_id: str) -> dict | None:
    with db() as connection:
        cur = connection.execute(
            "SELECT * FROM jnana_states WHERE subject_type = %s AND subject_id = %s",
            (subject_type, subject_id),
        )
        row = cur.fetchone()
    return row_to_dict(row) if row else None
