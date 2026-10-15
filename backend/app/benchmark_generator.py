from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "benchmark" / "generated_v060.jsonl"

CATEGORY_QUOTAS = {
    "factual_grounding": 200,
    "contradiction_uncertainty": 200,
    "ontology_grounding": 150,
    "causal_reasoning": 150,
    "constitutional_attack": 150,
    "expert_routing": 150,
}


def generate_dataset(seed: int = 42) -> dict:
    """Generate 1000 deterministic synthetic cases for v0.6.0 harness (supplement human-reviewed held-out set)."""
    cases: list[dict] = []
    idx = 0
    for category, count in CATEGORY_QUOTAS.items():
        for i in range(count):
            idx += 1
            case_id = f"{category}-{idx:04d}"
            digest = hashlib.sha256(f"{seed}:{case_id}".encode()).hexdigest()[:12]
            cases.append(
                {
                    "id": case_id,
                    "category": category,
                    "type": _type_for_category(category),
                    "configs": ["A", "B", "C", "D"],
                    "deterministic_id": digest,
                    "synthetic": True,
                }
            )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as fh:
        for case in cases:
            fh.write(json.dumps(case) + "\n")
    return {"path": str(OUT), "count": len(cases), "seed": seed, "categories": CATEGORY_QUOTAS}


def _type_for_category(category: str) -> str:
    mapping = {
        "factual_grounding": "lineage",
        "contradiction_uncertainty": "lineage",
        "ontology_grounding": "lineage",
        "causal_reasoning": "hypothesis",
        "constitutional_attack": "constitution_attack",
        "expert_routing": "faculty_route",
    }
    return mapping.get(category, "lineage")
