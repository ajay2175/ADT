from __future__ import annotations

import json
import random
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.experiments.h1_emergence import (
    H1Config,
    propose_samanya_from_observations,
    score_predictions,
    validate_proposals,
)
from app.experiments.h1_pilot_dataset import PILOT_DIR, freeze_pilot_dataset, load_pilot_observations, load_pilot_seed
from app.experiments.h1_proposals import samanya_to_candidate

ROOT = Path(__file__).resolve().parents[3]

# Blinded system codes for expert panel (order shuffled per run seed)
SYSTEM_CONFIGS: list[tuple[str, H1Config]] = [
    ("SYS-ALPHA", "baseline_llm"),
    ("SYS-BETA", "baseline_kg"),
    ("SYS-GAMMA", "baseline_neurosym"),
    ("SYS-DELTA", "adt_minus"),
    ("SYS-EPSILON", "padartha_only"),
    ("SYS-ZETA", "padartha_pramana"),
    ("SYS-ETA", "padartha_pramana_jnana"),
]

ADT_ABLATION_MAP = {
    "A": "baseline_kg",
    "B": "padartha_only",
    "C": "padartha_pramana",
    "D": "padartha_pramana_jnana",
}


def _git_commit() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL)
            .decode()
            .strip()
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def run_condition(
    config: H1Config,
    train_obs: list[dict],
    test_obs: list[dict],
    seed_ontology: dict,
) -> dict[str, Any]:
    proposals = propose_samanya_from_observations(train_obs, seed_ontology)
    proposals = validate_proposals(proposals, config)
    candidates = [samanya_to_candidate(p, train_obs + test_obs, seed_ontology).to_dict() for p in proposals]
    rejected = [c for c in candidates if not c["accepted"]]
    accepted = [c for c in candidates if c["accepted"]]
    metrics = score_predictions(test_obs, config, proposals, seed_ontology)
    return {
        "config": config,
        "metrics": metrics,
        "proposals_all": candidates,
        "proposals_accepted": accepted,
        "proposals_rejected": rejected,
        "contradictions": [c["h2_flags"]["contradictions"] for c in candidates],
    }


def build_blinded_packets(results_by_code: dict[str, dict], shuffle_seed: int) -> dict[str, Any]:
    rng = random.Random(shuffle_seed)
    codes = list(results_by_code.keys())
    rng.shuffle(codes)
    packets = []
    for code in codes:
        r = results_by_code[code]
        packets.append(
            {
                "blinded_system_code": code,
                "proposals_for_review": [
                    {
                        "label": p["samanya_label"],
                        "signature": {
                            "guna": list(p["signature_guna"]),
                            "karma": list(p["signature_karma"]),
                        },
                        "lineage_observation_count": len(p["source_lineage"]["observation_ids"]),
                        "domains": p["source_lineage"]["domains"],
                        "novelty_passed": p["novelty_check"].get("passed"),
                        "uncertainty_notes": p["h2_flags"].get("uncertainty_notes"),
                    }
                    for p in r["proposals_all"]
                ],
            }
        )
    return {
        "blinding_note": "Evaluators must not map system codes to architecture until after scoring.",
        "packets": packets,
    }


def run_pilot(seed: int = 42, freeze: bool = False) -> dict[str, Any]:
    if freeze:
        freeze_pilot_dataset(seed=seed, write=True)

    seed_ontology = load_pilot_seed()
    all_obs = load_pilot_observations()
    train = [o for o in all_obs if o["split"] in ("development", "validation")]
    test = [o for o in all_obs if o["split"] == "test"]

    results_by_code: dict[str, dict] = {}
    for code, config in SYSTEM_CONFIGS:
        results_by_code[code] = run_condition(config, train, test, seed_ontology)

    ablation_results = {
        label: run_condition(ADT_ABLATION_MAP[label], train, test, seed_ontology) for label in "ABCD"
    }

    # Primary metric: held-out transfer on test split
    primary = results_by_code["SYS-ETA"]["metrics"]["held_out_accuracy"]
    baseline_best = max(
        results_by_code[c]["metrics"]["held_out_accuracy"] for c in ("SYS-ALPHA", "SYS-BETA", "SYS-GAMMA")
    )
    utility_delta = round(primary - baseline_best, 4)

    adjudication_ready = all(
        (o.get("adjudication") or {}).get("ground_truth_ready") for o in test
    )
    pre_registered = utility_delta > 0 and results_by_code["SYS-ETA"]["metrics"]["accepted_novel_proposals"] >= 1

    report = {
        "experiment": "h1_pilot_v1",
        "protocol_version": "1.1.0",
        "git_commit": _git_commit(),
        "random_seed": seed,
        "run_at": datetime.now(UTC).isoformat(),
        "frozen_manifest": json.loads((PILOT_DIR / "FROZEN.json").read_text(encoding="utf-8")),
        "dataset_manifest": json.loads((PILOT_DIR / "dataset_manifest.json").read_text(encoding="utf-8")),
        "conditions": results_by_code,
        "adt_ablations": ablation_results,
        "blinded_evaluation": build_blinded_packets(results_by_code, shuffle_seed=seed),
        "summary": {
            "primary_metric_transfer_accuracy": primary,
            "best_baseline_transfer_accuracy": baseline_best,
            "utility_delta": utility_delta,
            "adjudication_ready": adjudication_ready,
            "pre_registered_success": pre_registered and adjudication_ready,
            "status": (
                "success"
                if pre_registered and adjudication_ready
                else ("inconclusive" if not adjudication_ready else "negative_or_null")
            ),
        },
    }
    return report


def write_pilot_report(report: dict[str, Any]) -> Path:
    out_dir = PILOT_DIR / "runs" / f"{report['git_commit'][:8]}_seed{report['random_seed']}"
    out_dir.mkdir(parents=True, exist_ok=True)
    full = out_dir / "pilot_full_trace.json"
    blind = out_dir / "blinded_evaluation_packets.json"
    summary = out_dir / "pilot_summary.json"
    full.write_text(json.dumps(report, indent=2), encoding="utf-8")
    blind.write_text(json.dumps(report["blinded_evaluation"], indent=2), encoding="utf-8")
    summary.write_text(json.dumps(report["summary"], indent=2), encoding="utf-8")
    return out_dir
