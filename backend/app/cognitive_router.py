from __future__ import annotations

import json
from enum import Enum

from app.database import db, rows_to_dicts


def select_experts_for_routing(query: str, requested_domains: list[str] | None, high_risk: bool) -> list[dict]:
    from app.experts import select_experts

    return select_experts(query, requested_domains, high_risk)


class FacultyTask(str, Enum):
    EVIDENCE_RETRIEVAL = "evidence_retrieval"
    CONCEPTUAL_INTERPRETATION = "conceptual_interpretation"
    INFERENCE = "inference"
    CONTRADICTION_CHECK = "contradiction_check"
    CAUSAL_REASONING = "causal_reasoning"
    UNCERTAINTY_ASSESSMENT = "uncertainty_assessment"


EXPERT_TASK_AFFINITY: dict[str, list[FacultyTask]] = {
    "dharma_governor": [FacultyTask.INFERENCE, FacultyTask.CONTRADICTION_CHECK, FacultyTask.UNCERTAINTY_ASSESSMENT],
    "systems_strategy": [FacultyTask.INFERENCE, FacultyTask.CAUSAL_REASONING],
    "leadership": [FacultyTask.INFERENCE, FacultyTask.UNCERTAINTY_ASSESSMENT],
    "research_methods": [FacultyTask.EVIDENCE_RETRIEVAL, FacultyTask.INFERENCE, FacultyTask.CONTRADICTION_CHECK],
    "ai_agi": [FacultyTask.INFERENCE, FacultyTask.CAUSAL_REASONING, FacultyTask.CONTRADICTION_CHECK],
    "ayurveda": [FacultyTask.EVIDENCE_RETRIEVAL, FacultyTask.CONCEPTUAL_INTERPRETATION],
    "modern_medicine": [FacultyTask.EVIDENCE_RETRIEVAL, FacultyTask.UNCERTAINTY_ASSESSMENT, FacultyTask.CONTRADICTION_CHECK],
    "founder": [FacultyTask.INFERENCE, FacultyTask.CAUSAL_REASONING],
    "engineering": [FacultyTask.EVIDENCE_RETRIEVAL, FacultyTask.INFERENCE],
    "civilizational_codex": [FacultyTask.CONCEPTUAL_INTERPRETATION, FacultyTask.EVIDENCE_RETRIEVAL],
}

TASK_KEYWORDS: dict[FacultyTask, tuple[str, ...]] = {
    FacultyTask.EVIDENCE_RETRIEVAL: ("evidence", "source", "citation", "study", "data", "trial"),
    FacultyTask.CONCEPTUAL_INTERPRETATION: ("meaning", "classical", "text", "interpret", "veda", "ayurveda", "codex"),
    FacultyTask.INFERENCE: ("should", "decide", "strategy", "recommend", "option"),
    FacultyTask.CONTRADICTION_CHECK: ("contradict", "conflict", "disagree", "versus", "however"),
    FacultyTask.CAUSAL_REASONING: ("cause", "because", "intervention", "effect", "counterfactual", "aca"),
    FacultyTask.UNCERTAINTY_ASSESSMENT: ("uncertain", "risk", "unknown", "confidence", "patient", "clinical"),
}


def infer_tasks(query: str, high_risk: bool = False) -> list[FacultyTask]:
    q = query.lower()
    tasks: list[FacultyTask] = []
    for task, keywords in TASK_KEYWORDS.items():
        if any(k in q for k in keywords):
            tasks.append(task)
    if high_risk and FacultyTask.UNCERTAINTY_ASSESSMENT not in tasks:
        tasks.append(FacultyTask.UNCERTAINTY_ASSESSMENT)
    if not tasks:
        tasks = [FacultyTask.INFERENCE, FacultyTask.EVIDENCE_RETRIEVAL]
    return tasks[:4]


def route_faculty(query: str, requested_domains: list[str] | None = None, high_risk: bool = False) -> dict:
    tasks = infer_tasks(query, high_risk)
    baseline = select_experts_for_routing(query, requested_domains, high_risk)
    with db() as connection:
        cur = connection.execute("SELECT * FROM expert_profiles WHERE status = 'active'")
        all_experts = rows_to_dicts(cur.fetchall())

    scored: list[tuple[int, dict, list[str]]] = []
    for expert in all_experts:
        eid = expert["id"]
        affinities = EXPERT_TASK_AFFINITY.get(eid, [FacultyTask.INFERENCE])
        overlap = len(set(tasks) & set(affinities))
        if eid == "dharma_governor":
            overlap += 1
        if high_risk and eid in {"modern_medicine", "dharma_governor"}:
            overlap += 2
        matched_tasks = [t.value for t in tasks if t in affinities]
        scored.append((overlap, {**expert, "domains": json.loads(expert["domains"]), "matched_tasks": matched_tasks}, matched_tasks))

    ranked = [e for s, e, _ in sorted(scored, key=lambda x: x[0], reverse=True) if s > 0][:4]
    if not ranked:
        ranked = baseline

    return {
        "tasks": [t.value for t in tasks],
        "experts": ranked,
        "routing_mode": "faculty_task",
        "baseline_expert_ids": [e["id"] for e in baseline],
        "high_risk_escalation": high_risk,
    }
