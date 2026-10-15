from __future__ import annotations

from app.database import db, rows_to_dicts


def ground_term(term: str, limit: int = 8) -> list[dict]:
    """Map surface form to graph entity / assertion subjects (SQL mirror)."""
    pattern = f"%{term}%"
    with db() as connection:
        nodes = rows_to_dicts(
            connection.execute(
                """
                SELECT id, name, node_type, status FROM graph_nodes
                WHERE name LIKE %s AND protected = 0
                ORDER BY created_at DESC LIMIT %s
                """,
                (pattern, limit),
            ).fetchall()
        )
        assertions = rows_to_dicts(
            connection.execute(
                """
                SELECT id, subject AS name, 'Assertion' AS node_type, epistemic_status AS status
                FROM padartha_assertions WHERE subject LIKE %s OR object LIKE %s
                LIMIT %s
                """,
                (pattern, pattern, limit),
            ).fetchall()
        )
    return [{"binding": n["name"], "entity_id": n["id"], "type": n["node_type"], "status": n["status"]} for n in nodes + assertions]
