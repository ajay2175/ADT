from __future__ import annotations

import json

from app.database import db, rows_to_dicts
from app.model_gateway import get_provider, parse_json_block
from app.seeds import DRIFT_CHECKS


async def run_drift_check(question: str = "", context: dict | None = None) -> dict:
    context = context or {}
    with db() as connection:
        cur = connection.execute("SELECT category, statement FROM constitution_items WHERE status = 'approved' ORDER BY priority DESC")
        constitution = rows_to_dicts(cur.fetchall())
        cur = connection.execute("SELECT question, recommendation, final_decision FROM decision_records ORDER BY created_at DESC LIMIT 5")
        recent = rows_to_dicts(cur.fetchall())

    if not question and not context:
        return {
            "protocol": ["mirror", "re-anchor", "alternative", "action"],
            "checks": DRIFT_CHECKS,
            "current_status": "Provide question and/or context for live drift inference.",
            "constitutional_integrity": "approved Constitution is separated from uploads, claims, decisions and web knowledge.",
            "drift_detected": False,
        }

    constitution_text = "\n".join(f"[{c['category']}] {c['statement']}" for c in constitution[:12])
    recent_text = "\n".join(f"- Q: {r['question'][:100]} → {r.get('final_decision') or r['recommendation']}" for r in recent)

    provider = get_provider()
    prompt = (
        "You are ADT drift-governance engine. Analyze whether Ajay's current decision context shows drift "
        "from constitutional True North. Never rewrite constitutional values.\n"
        "Respond ONLY with JSON:\n"
        '{"drift_detected": true|false, "flags":["..."], "mirror":"...", "re_anchor":"...", '
        '"alternative":"...", "action":"...", "confidence":0.0-1.0}\n\n'
        f"DRIFT CHECKS: {', '.join(DRIFT_CHECKS)}\n\n"
        f"CONSTITUTION:\n{constitution_text}\n\n"
        f"RECENT DECISIONS:\n{recent_text}\n\n"
        f"CURRENT QUESTION:\n{question}\n\nCONTEXT:\n{json.dumps(context)}"
    )
    raw = await provider.generate([{"role": "user", "content": prompt}])
    parsed = parse_json_block(raw)

    return {
        "protocol": ["mirror", "re-anchor", "alternative", "action"],
        "checks": DRIFT_CHECKS,
        "constitutional_integrity": "approved Constitution is separated from uploads, claims, decisions and web knowledge.",
        "drift_detected": parsed.get("drift_detected", False),
        "flags": parsed.get("flags", []),
        "mirror": parsed.get("mirror", ""),
        "re_anchor": parsed.get("re_anchor", ""),
        "alternative": parsed.get("alternative", ""),
        "action": parsed.get("action", ""),
        "confidence": parsed.get("confidence", 0.0),
        "llm_provider": provider.__class__.__name__,
        "inference": parsed,
    }
