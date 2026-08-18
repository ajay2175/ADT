from __future__ import annotations

import json

from app.database import db, rows_to_dicts
from app.model_gateway import get_provider, parse_json_block
from app.retrieval import hybrid_graph_rag


def select_experts(query: str, requested_domains: list[str] | None = None, high_risk: bool = False) -> list[dict]:
    query_tokens = set(query.lower().replace("/", " ").replace("-", " ").split()) | set(requested_domains or [])
    with db() as connection:
        cur = connection.execute("SELECT * FROM expert_profiles WHERE status = 'active'")
        experts = rows_to_dicts(cur.fetchall() if hasattr(cur, "fetchall") else [])
    ranked = []
    for expert in experts:
        domains = json.loads(expert["domains"])
        score = len(query_tokens & set(domains))
        if expert["id"] == "dharma_governor":
            score += 1
        if high_risk and expert["id"] in {"modern_medicine", "dharma_governor"}:
            score += 3
        ranked.append((score, {**expert, "domains": domains}))
    selected = [e for s, e in sorted(ranked, key=lambda x: x[0], reverse=True) if s > 0][:4]
    if not selected:
        selected = [e for _, e in ranked if e["id"] == "dharma_governor"][:1]
    return selected


async def run_expert_view(expert: dict, question: str, constitution: list[dict], evidence: list[dict]) -> dict:
    provider = get_provider()
    constitution_text = "\n".join(f"- [{c['category']}] {c['statement']}" for c in constitution[:12])
    evidence_text = "\n".join(f"- {e.get('title', e.get('content', ''))}: {e.get('summary', e.get('content', ''))[:200]}" for e in evidence[:8])
    prompt = (
        f"You are {expert['name']}, an INDEPENDENT domain expert for ADT.\n"
        f"Protocol: {expert['protocol']}\n"
        f"Domains: {', '.join(expert['domains'])}\n\n"
        f"CONSTITUTION (read-only, do NOT rewrite):\n{constitution_text}\n\n"
        f"EVIDENCE:\n{evidence_text or 'No accepted evidence yet.'}\n\n"
        f"DECISION QUESTION:\n{question}\n\n"
        "Respond ONLY with JSON: "
        '{"finding":"...", "signal":"support"|"challenge"|"neutral", '
        '"evidence_refs":["..."], "unknowns":["..."]}\n'
        "Disagree if warranted. Never rewrite Ajay's constitutional values."
    )
    raw = await provider.generate([{"role": "user", "content": prompt}])
    parsed = parse_json_block(raw)
    return {
        "expert_id": expert["id"],
        "name": expert["name"],
        "domain": expert["protocol"],
        "finding": parsed.get("finding", raw[:500]),
        "signal": parsed.get("signal", "neutral"),
        "evidence_refs": parsed.get("evidence_refs", []),
        "unknowns": parsed.get("unknowns", []),
    }


async def run_all_experts(question: str, high_risk: bool = False, evidence: list[dict] | None = None) -> list[dict]:
    experts = select_experts(question, high_risk=high_risk)
    with db() as connection:
        cur = connection.execute("SELECT * FROM constitution_items WHERE status = 'approved' ORDER BY priority DESC")
        constitution = rows_to_dicts(cur.fetchall())
    if evidence is None:
        evidence = await hybrid_graph_rag(question, limit=10)
    views = []
    for expert in experts:
        views.append(await run_expert_view(expert, question, constitution, evidence))
    return views
