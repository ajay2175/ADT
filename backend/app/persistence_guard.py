from __future__ import annotations

import contextvars
import re

from contextlib import contextmanager

from app.dharma_guard import GuardAction, assert_constitution_unchanged, authorize, constitution_snapshot

_amendment: contextvars.ContextVar[dict | None] = contextvars.ContextVar("adt_amendment", default=None)
_guard_enabled: contextvars.ContextVar[bool] = contextvars.ContextVar("sql_guard_enabled", default=True)


def sql_guard_enabled() -> bool:
    return _guard_enabled.get()


def disable_sql_guard() -> None:
    _guard_enabled.set(False)


def enable_sql_guard() -> None:
    _guard_enabled.set(True)

PROTECTED_TABLES = ("constitution_items",)
PROTECTED_GRAPH_MUTATIONS = re.compile(r"\b(UPDATE|DELETE|INSERT)\b.*\bgraph_nodes\b", re.I)


def set_amendment_context(explicit_ajay_approval: bool, amendment_id: str) -> contextvars.Token:
    return _amendment.set({"explicit_ajay_approval": explicit_ajay_approval, "amendment_id": amendment_id})


def reset_amendment_context(token: contextvars.Token) -> None:
    _amendment.reset(token)


def guard_sql_mutation(sql: str) -> None:
    """Raise if SQL would mutate protected constitution without explicit amendment context."""
    lower = sql.lower()
    if "constitution_items" in lower and any(k in lower for k in ("insert", "update", "delete")):
        ctx = _amendment.get()
        result = authorize(GuardAction.CONSTITUTION_WRITE, ctx or {})
        if not result.get("allowed"):
            raise PermissionError(result.get("reason", "constitution write denied"))


@contextmanager
def guarded_transaction(before_snapshot: list[dict] | None = None):
    """Verify constitution unchanged after block."""
    before = before_snapshot or constitution_snapshot()
    yield
    after = constitution_snapshot()
    assert_constitution_unchanged(before, after)
