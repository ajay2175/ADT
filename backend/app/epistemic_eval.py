from __future__ import annotations

import json
import time
import uuid
from enum import Enum
from pathlib import Path

from app.dharma_guard import assert_constitution_unchanged, constitution_snapshot
from app.database import NOW, db, row_to_dict

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "data" / "benchmark" / "fixtures.json"
MANIFEST = ROOT / "data" / "benchmark" / "manifest.json"


class EvalConfig(str, Enum):
    A_BASELINE = "A"  # ADT + GraphRAG behavior (no epistemic gates in scoring)
    B_ONTOLOGY = "B"  # + Padārtha lineage checks
    C_EPISTEMIC = "C"  # + Pramāṇa / Jñāna promotion rules
    D_GOVERNED = "D"  # + Dharma Guard adversarial expectations


def load_fixtures() -> list[dict]:
    if not FIXTURES.exists():
        return []
    return json.loads(FIXTURES.read_text(encoding="utf-8"))


def load_manifest() -> dict:
    if not MANIFEST.exists():
        return {"dataset_id": "unknown", "version": "0.0.0"}
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def run_ablation_suite(client) -> dict:
    """Run A–D configs and return comparative metrics (deterministic components)."""
    manifest = load_manifest()
    reports = {}
    for cfg in EvalConfig:
        reports[cfg.value] = run_benchmark(cfg, client)
    return {"manifest": manifest, "configs": reports}


def run_benchmark(config: EvalConfig, client) -> dict:
    """Run benchmark cases through FastAPI TestClient. Persists evaluation_runs row."""
    cases = load_fixtures()
    started = time.perf_counter()
    results: list[dict] = []
    constitution_before = constitution_snapshot()

    for case in cases:
        if config.value not in case.get("configs", ["A", "B", "C", "D"]):
            continue
        outcome = _run_case(client, case, config)
        results.append(outcome)

    constitution_after = constitution_snapshot()
    constitutional_violations = 0
    try:
        assert_constitution_unchanged(constitution_before, constitution_after)
    except AssertionError:
        constitutional_violations = 1

    manifest = load_manifest()
    passed = sum(1 for r in results if r.get("passed"))
    total = len(results)
    metrics = {
        "config": config.value,
        "dataset_id": manifest.get("dataset_id"),
        "dataset_version": manifest.get("version"),
        "ablation": manifest.get("ablations", {}).get(config.value, {}),
        "cases_total": total,
        "cases_passed": passed,
        "pass_rate": round(passed / total, 4) if total else 0.0,
        "constitutional_violations": constitutional_violations,
        "duration_ms": int((time.perf_counter() - started) * 1000),
    }
    run_id = str(uuid.uuid4())
    with db() as connection:
        connection.execute(
            """
            INSERT INTO evaluation_runs (id, config, metrics_json, results_json, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (run_id, config.value, json.dumps(metrics), json.dumps(results), NOW()),
        )
    return {"run_id": run_id, "metrics": metrics, "results": results}


def _run_case(client, case: dict, config: EvalConfig) -> dict:
    kind = case["type"]
    passed = False
    detail = ""

    try:
        if kind == "constitution_attack":
            kid = client.post("/v1/inbox", json=case["inbox"]).json()["id"]
            client.post(f"/v1/inbox/{kid}/review?action=accepted")
            passed = True
            if config == EvalConfig.D_GOVERNED:
                r = client.post(
                    "/v1/epistemic/padartha/assertions",
                    json={**case.get("bad_assertion", {}), "constitutional": True},
                )
                passed = r.status_code == 400
        elif kind == "lineage":
            kid = client.post("/v1/inbox", json=case["inbox"]).json()["id"]
            client.post(f"/v1/inbox/{kid}/review?action=accepted")
            lineage = client.get(f"/v1/epistemic/lineage/{kid}").json()
            passed = len(lineage.get("lineage", [])) > 0
            if config in {EvalConfig.C_EPISTEMIC, EvalConfig.D_GOVERNED}:
                passed = passed and all(r["epistemic_status"] == "proposed" for r in lineage["lineage"])
        elif kind == "faculty_route":
            r = client.post("/v1/experts/route-faculty", json=case["route"]).json()
            passed = len(r.get("experts", [])) > 0 and len(r.get("tasks", [])) > 0
        elif kind == "hypothesis":
            h = client.post("/v1/theory/hypotheses", json=case["hypothesis"]).json()
            passed = h.get("status") == "proposed"
        else:
            passed = False
            detail = f"unknown case type {kind}"
    except Exception as exc:  # noqa: BLE001
        detail = str(exc)
        passed = False

    return {"case_id": case.get("id"), "type": kind, "passed": passed, "detail": detail}


def list_evaluation_runs(limit: int = 20) -> list[dict]:
    with db() as connection:
        cur = connection.execute(
            "SELECT id, config, metrics_json, created_at FROM evaluation_runs ORDER BY created_at DESC LIMIT %s",
            (limit,),
        )
        rows = cur.fetchall()
    out: list[dict] = []
    for row in rows:
        rd = row_to_dict(row)
        rd["metrics"] = json.loads(rd.pop("metrics_json", "{}"))
        out.append(rd)
    return out
