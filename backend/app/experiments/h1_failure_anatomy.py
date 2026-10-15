from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from app.experiments.h1_emergence import (
    H1Config,
    load_observations,
    load_seed,
    propose_samanya_from_observations,
    run_h1_experiment,
    validate_proposals,
)
from app.experiments.h1_novelty import assess_novelty_levels, per_case_prediction
from app.experiments.h1_pilot_dataset import load_pilot_observations, load_pilot_seed
from app.experiments.h1_pilot_run import ADT_ABLATION_MAP, SYSTEM_CONFIGS, run_condition
from app.experiments.h1_proposals import samanya_to_candidate

ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "data" / "experiments" / "h1_concept_discovery" / "reports"

FailureKind = Literal[
    "concept_generation",
    "novelty_filtering",
    "validation",
    "generalization",
    "baseline_strength",
    "adjudication_not_ready",
    "none",
]


def _git_commit() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL)
            .decode()
            .strip()
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def classify_proposal_failures(
    raw_proposals: list,
    candidates: list[dict],
    config: H1Config,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for p, c in zip(raw_proposals, candidates, strict=False):
        kinds: list[FailureKind] = []
        if not p.member_ids:
            kinds.append("concept_generation")
        if not p.novel:
            kinds.append("novelty_filtering")
        if p.novel and not p.accepted:
            if c["h2_flags"].get("contradictions"):
                kinds.append("validation")
            elif p.rejection_reason:
                kinds.append("validation" if "pramana" in p.rejection_reason else "novelty_filtering")
        rows.append(
            {
                "samanya_label": p.name,
                "failure_kinds": kinds or ["none"],
                "accepted": p.accepted,
                "rejection_reason": p.rejection_reason,
                "novelty_levels": c.get("novelty_levels"),
            }
        )
    return rows


def diagnose_condition(
    name: str,
    config: H1Config,
    train_obs: list[dict],
    test_obs: list[dict],
    seed: dict,
) -> dict[str, Any]:
    raw = propose_samanya_from_observations(train_obs, seed)
    validated = validate_proposals(raw, config)
    candidates = []
    for p in validated:
        c = samanya_to_candidate(p, train_obs + test_obs, seed).to_dict()
        c["novelty_levels"] = assess_novelty_levels(p, seed, train_obs, test_obs, config)
        candidates.append(c)

    per_case = [per_case_prediction(o, validated, config, seed) for o in test_obs]
    proposal_diag = classify_proposal_failures(validated, candidates, config)

    # Per-case generalization vs baseline strength (ADT+ focus)
    baseline_configs: list[H1Config] = ("baseline_llm", "baseline_kg", "baseline_neurosym")
    case_failures: list[dict[str, Any]] = []
    for obs in test_obs:
        pred = per_case_prediction(obs, validated, config, seed)
        base_preds = {}
        for bc in baseline_configs:
            bp = validate_proposals(propose_samanya_from_observations(train_obs, seed), bc)
            base_preds[bc] = per_case_prediction(obs, bp, bc, seed)
        kinds: list[FailureKind] = []
        if not any(p.accepted and p.novel for p in validated):
            kinds.append("concept_generation")
        adj = obs.get("adjudication") or {}
        if not adj.get("ground_truth_ready"):
            kinds.append("adjudication_not_ready")
        elif pred["predicted"] in ("no_match", "unknown"):
            kinds.append("generalization")
        if any(bp["predicted"] == pred["predicted"] for bp in base_preds.values()):
            kinds.append("baseline_strength")
        case_failures.append(
            {
                "observation_id": obs["id"],
                "failure_kinds": kinds or ["none"],
                "prediction": pred,
                "baseline_predictions": base_preds,
            }
        )

    from app.experiments.h1_emergence import score_predictions

    metrics = score_predictions(test_obs, config, validated, seed)
    return {
        "condition_name": name,
        "config": config,
        "metrics": metrics,
        "proposal_diagnostics": proposal_diag,
        "per_case": case_failures,
        "candidates": candidates,
    }


def aggregate_failure_counts(diagnostics: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for d in diagnostics:
        for row in d.get("proposal_diagnostics", []):
            for k in row.get("failure_kinds", []):
                counts[k] = counts.get(k, 0) + 1
        for row in d.get("per_case", []):
            for k in row.get("failure_kinds", []):
                counts[k] = counts.get(k, 0) + 1
    return counts


def run_failure_anatomy(seed: int = 42) -> dict[str, Any]:
    """Seed pilot + pilot_v1 test split diagnostics for H1 Failure Anatomy Report."""
    seed_ontology_legacy = load_seed()
    train_legacy = load_observations("train")
    held_legacy = load_observations("held_out")

    legacy_report = run_h1_experiment(split="held_out", config="padartha_pramana_jnana", seed=seed)
    legacy_diag = diagnose_condition(
        "seed_pilot_legacy",
        "padartha_pramana_jnana",
        train_legacy,
        held_legacy,
        seed_ontology_legacy,
    )

    pilot_seed = load_pilot_seed()
    all_pilot = load_pilot_observations()
    train_pilot = [o for o in all_pilot if o["split"] in ("development", "validation")]
    test_pilot = [o for o in all_pilot if o["split"] == "test"]

    pilot_conditions = []
    for code, cfg in SYSTEM_CONFIGS:
        if cfg in ("padartha_pramana_jnana", "adt_minus", "baseline_llm", "baseline_kg", "baseline_neurosym"):
            pilot_conditions.append(
                diagnose_condition(code, cfg, train_pilot, test_pilot, pilot_seed)
            )

    adt_plus = next(c for c in pilot_conditions if c["config"] == "padartha_pramana_jnana")
    counts = aggregate_failure_counts([legacy_diag, adt_plus])

    interpretation = _interpret_failures(counts, legacy_report, adt_plus)

    return {
        "report_type": "h1_failure_anatomy",
        "protocol_version": "1.2.0",
        "git_commit": _git_commit(),
        "generated_at": datetime.now(UTC).isoformat(),
        "random_seed": seed,
        "seed_pilot_legacy": {
            "scientific_result": legacy_report["scientific_result"],
            "diagnostics": legacy_diag,
        },
        "pilot_v1_test_split": {
            "n_test": len(test_pilot),
            "conditions_sample": pilot_conditions,
            "adt_plus_summary": adt_plus["metrics"],
        },
        "failure_category_counts": counts,
        "interpretation": interpretation,
        "exploratory_note": (
            "Secondary findings (novelty levels, per-case traces) are exploratory unless pre-registered in protocol 1.2+"
        ),
        "next_step": "held_out_study_v1 (60 adjudicated cases) before confirmatory claims",
    }


def _interpret_failures(counts: dict[str, int], legacy: dict, adt_plus: dict) -> dict[str, str]:
    primary = []
    if counts.get("adjudication_not_ready", 0) > 0:
        primary.append(
            "Adjudication not ready: aggregate metrics are inconclusive; failure anatomy on labels is partial."
        )
    if counts.get("concept_generation", 0) > counts.get("validation", 0):
        primary.append(
            "Dominant risk: concept generation (clusters/support) rather than validation rejection."
        )
    elif counts.get("validation", 0) > 0:
        primary.append("Useful concepts may be proposed but rejected by Pramāṇa/H2 contradiction checks.")
    if counts.get("generalization", 0) > 0:
        primary.append("Accepted or proposed categories fail to transfer on unseen signatures.")
    if counts.get("baseline_strength", 0) > 0:
        primary.append("Baselines match predictions on cases — task may be too easy or metrics too coarse.")
    if not primary:
        primary.append("Review per-case JSON; no dominant bucket auto-detected.")
    return {
        "headline": legacy["scientific_result"].get("interpretation", ""),
        "failure_analysis": " ".join(primary),
        "distinction": (
            "Check proposal_diagnostics (generation/novelty/validation) separately from per_case (generalization/baseline)."
        ),
    }


def write_failure_anatomy_report(report: dict[str, Any]) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"h1_failure_anatomy_{report['git_commit'][:8]}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path
