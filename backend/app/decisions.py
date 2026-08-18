from __future__ import annotations

import json
import uuid

from app.database import NOW, db, rows_to_dicts
from app.experts import run_all_experts, select_experts
from app.model_gateway import get_provider, parse_json_block
from app.retrieval import hybrid_search


async def analyze_decision(question: str, context: dict | None = None) -> dict:
    context = context or {}
    high_risk = any(t in question.lower() for t in ("patient", "medical", "diagnosis", "treatment", "clinical", "invest"))
    expert_views = await run_all_experts(question, high_risk=high_risk)
    evidence = await hybrid_search(question, limit=8)

    with db() as connection:
        cur = connection.execute("SELECT * FROM constitution_items WHERE status = 'approved' ORDER BY priority DESC")
        constitution = rows_to_dicts(cur.fetchall())

    constitution_text = "\n".join(f"- {c['statement']}" for c in constitution[:15])
    expert_block = "\n".join(f"## {v['name']} ({v['signal']})\n{v['finding']}" for v in expert_views)
    evidence_block = "\n".join(f"- {e.get('content', e.get('claim', e.get('summary', '')))[:200]}" for e in evidence[:8])

    provider = get_provider()
    synthesis_prompt = (
        "You are ADT decision synthesizer. Never rewrite constitutional identity.\n"
        "Preserve disagreement and uncertainty. Respond ONLY with JSON:\n"
        '{"recommendation":"...", "confidence":0.0-1.0, "options":["..."], '
        '"next_steps":[{"step":"...","owner":"...","when":"..."}], '
        '"uncertainty":"...", "aca_risks":["..."], "scores":{"dharma_alignment":0-100, '
        '"evidence_quality":0-100, "long_term_compounding":0-100, "people_impact":0-100, '
        '"energy_efficiency":0-100}, "disagreements":["..."]}\n\n'
        f"CONSTITUTION:\n{constitution_text}\n\nEVIDENCE:\n{evidence_block}\n\n"
        f"EXPERT VIEWS (independent):\n{expert_block}\n\nQUESTION:\n{question}\n\nCONTEXT:\n{json.dumps(context)}"
    )
    raw = await provider.generate([{"role": "user", "content": synthesis_prompt}])
    parsed = parse_json_block(raw)

    recommendation = parsed.get("recommendation", "Stage with explicit stop/go gate and named owners.")
    confidence = float(parsed.get("confidence", 0.75))
    decision_id = str(uuid.uuid4())

    disagreements = parsed.get("disagreements", [v["finding"] for v in expert_views if v["signal"] == "challenge"])

    with db() as connection:
        connection.execute(
            "INSERT INTO decision_records VALUES (%s, %s, %s, %s, %s, NULL, NULL, %s)",
            (decision_id, question, json.dumps(context), recommendation, confidence, NOW()),
        )
        connection.execute(
            "INSERT INTO reasoning_records VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                decision_id,
                json.dumps(evidence[:8]),
                json.dumps(context.get("assumptions", [])),
                json.dumps([v["expert_id"] for v in expert_views]),
                json.dumps(expert_views),
                json.dumps(disagreements),
                json.dumps(parsed.get("aca_risks", ["overextension", "under-delegation"])),
                json.dumps(parsed.get("values_applied", ["dharma", "resilience"])),
                parsed.get("uncertainty", "Key unknowns remain around bandwidth and delegation."),
                raw[:8000],
            ),
        )

    return {
        "id": decision_id,
        "recommendation": recommendation,
        "confidence": confidence,
        "values_applied": parsed.get("values_applied", ["dharma", "long-term compounding", "resilience"]),
        "aca_risks": parsed.get("aca_risks", ["overextension", "under-delegation"]),
        "experts": expert_views,
        "expert_views": expert_views,
        "uncertainty": parsed.get("uncertainty", ""),
        "next_steps": parsed.get("next_steps", []),
        "options": parsed.get("options", []),
        "scores": parsed.get("scores", {}),
        "disagreements": disagreements,
        "structured_justification": {
            "synthesis": raw,
            "evidence": evidence[:8],
            "expert_views": expert_views,
        },
        "llm_provider": provider.__class__.__name__,
    }
