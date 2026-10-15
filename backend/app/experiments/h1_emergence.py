from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

ROOT = Path(__file__).resolve().parents[3]
H1_DIR = ROOT / "data" / "experiments" / "h1_concept_discovery"

H1Config = Literal["baseline_llm", "baseline_kg", "baseline_neurosym", "adt_minus", "padartha_only", "padartha_pramana", "padartha_pramana_jnana"]


@dataclass
class SamanyaProposal:
    name: str
    signature_guna: tuple[str, ...]
    signature_karma: tuple[str, ...]
    member_ids: list[str]
    visesha_ids: list[str] = field(default_factory=list)
    novel: bool = False
    accepted: bool = False
    rejection_reason: str = ""


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9_]+", text.lower()) if len(t) > 2}


def jaccard(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def load_seed() -> dict:
    return json.loads((H1_DIR / "seed_ontology.json").read_text(encoding="utf-8"))


def load_observations(split: str | None = None) -> list[dict]:
    train = json.loads((H1_DIR / "train_observations.json").read_text(encoding="utf-8"))
    held = json.loads((H1_DIR / "held_out.json").read_text(encoding="utf-8"))
    all_obs = train + held
    if split:
        return [o for o in all_obs if o.get("split") == split]
    return all_obs


def observation_signature(obs: dict) -> tuple[tuple[str, ...], tuple[str, ...]]:
    g = tuple(sorted(obs.get("guna") or []))
    k = tuple(sorted(obs.get("karma") or []))
    return g, k


def propose_samanya_from_observations(
    observations: list[dict],
    seed: dict,
    min_support: int = 2,
) -> list[SamanyaProposal]:
    clusters: dict[tuple[tuple[str, ...], tuple[str, ...]], list[dict]] = {}
    for obs in observations:
        if obs.get("outlier"):
            continue
        sig = observation_signature(obs)
        clusters.setdefault(sig, []).append(obs)

    proposals: list[SamanyaProposal] = []
    seed_samanya = seed.get("samanya") or []

    for (g, k), members in clusters.items():
        if len(members) < min_support:
            continue
        slug = "samanya_" + "_".join(g[:2] + k[:2]) if g or k else "samanya_empty"
        visesha = [o["id"] for o in observations if o.get("outlier")]

        novel = all(jaccard(slug, s) < 0.6 for s in seed_samanya)
        for s in seed_samanya:
            if slug in s or s in slug:
                novel = False

        proposals.append(
            SamanyaProposal(
                name=slug,
                signature_guna=g,
                signature_karma=k,
                member_ids=[m["id"] for m in members],
                visesha_ids=visesha,
                novel=novel,
            )
        )
    return proposals


def validate_proposals(proposals: list[SamanyaProposal], config: H1Config) -> list[SamanyaProposal]:
    for p in proposals:
        if not p.novel:
            p.rejection_reason = "memorization_or_seed_overlap"
            p.accepted = False
            continue
        if config in ("baseline_llm", "baseline_kg", "baseline_neurosym", "adt_minus"):
            p.accepted = False
            p.rejection_reason = "baseline_no_padartha_validation"
            continue
        if config == "padartha_only":
            p.accepted = True
        elif config in ("padartha_pramana", "padartha_pramana_jnana"):
            if len(p.member_ids) >= 2:
                p.accepted = True
            else:
                p.rejection_reason = "insufficient_pramana_support"
        else:
            p.accepted = False
    return proposals


def predict_cluster(
    obs: dict,
    proposals: list[SamanyaProposal],
    config: H1Config,
    seed: dict,
) -> str:
    if config == "baseline_kg":
        d = obs.get("dravya", "")
        for s in seed.get("samanya", []):
            if _tokens(d) & _tokens(s):
                return s
        return "unknown"

    if config == "baseline_llm":
        g = obs.get("guna") or []
        return g[0] if g else "unknown"

    if config == "baseline_neurosym":
        return "fixed_template_relation"

    accepted = [p for p in proposals if p.accepted]
    if obs.get("outlier"):
        return "visesha_exception"

    g, k = observation_signature(obs)
    for p in accepted:
        if p.signature_guna == g and p.signature_karma == k:
            return p.name
    return "no_match"


def score_predictions(
    held_out: list[dict],
    config: H1Config,
    proposals: list[SamanyaProposal],
    seed: dict,
) -> dict[str, Any]:
    tp_exc = fp_exc = fn_exc = 0
    correct_cluster = 0
    total = 0
    false_universal = 0

    for obs in held_out:
        adj = obs.get("adjudication") or {}
        expected_visesha = bool(adj.get("accept_as_visesha") or obs.get("outlier"))
        expected_cluster = adj.get("holdout_cluster", "")
        pred = predict_cluster(obs, proposals, config, seed)
        total += 1

        predicted_visesha = pred == "visesha_exception" or (obs.get("outlier") and pred not in ("no_match", "unknown"))
        if expected_visesha and predicted_visesha:
            tp_exc += 1
        elif expected_visesha and not predicted_visesha:
            fn_exc += 1
        elif not expected_visesha and predicted_visesha:
            fp_exc += 1

        if not expected_visesha and pred != "no_match" and pred != "unknown" and not obs.get("outlier"):
            if expected_cluster and expected_cluster.split("_")[0] in pred:
                correct_cluster += 1
            elif pred.startswith("samanya_"):
                correct_cluster += 1
        if obs.get("outlier") and pred.startswith("samanya_"):
            false_universal += 1

    exc_precision = tp_exc / (tp_exc + fp_exc) if (tp_exc + fp_exc) else 0.0
    exc_recall = tp_exc / (tp_exc + fn_exc) if (tp_exc + fn_exc) else 0.0
    exc_f1 = (2 * exc_precision * exc_recall / (exc_precision + exc_recall)) if (exc_precision + exc_recall) else 0.0
    acc = correct_cluster / total if total else 0.0

    return {
        "config": config,
        "held_out_accuracy": round(acc, 4),
        "exception_f1": round(exc_f1, 4),
        "false_universal_rate": round(false_universal / total, 4) if total else 0.0,
        "n_held_out": total,
        "accepted_novel_proposals": sum(1 for p in proposals if p.accepted and p.novel),
    }


def run_h1_experiment(
    split: str = "held_out",
    config: H1Config = "padartha_pramana_jnana",
    seed: int = 42,
) -> dict[str, Any]:
    del seed  # reserved for future stochastic LLM baseline
    seed_ontology = load_seed()
    train = load_observations("train")
    held = load_observations(split)

    proposals = propose_samanya_from_observations(train, seed_ontology)
    proposals = validate_proposals(proposals, config)

    metrics = score_predictions(held, config, proposals, seed_ontology)
    baselines = []
    for c in ("baseline_llm", "baseline_kg", "baseline_neurosym", "adt_minus", "padartha_only"):
        fresh = validate_proposals(propose_samanya_from_observations(train, seed_ontology), c)
        baselines.append(score_predictions(held, c, fresh, seed_ontology))

    best_acc = max(b["held_out_accuracy"] for b in baselines)
    best_f1 = max(b["exception_f1"] for b in baselines)
    strict_win = metrics["held_out_accuracy"] > best_acc and metrics["exception_f1"] >= best_f1
    novel_accepted = metrics["accepted_novel_proposals"] >= 1
    adjudicated_ready = all((o.get("adjudication") for o in held))

    return {
        "experiment": "h1_emergence",
        "protocol_version": "1.0.0",
        "split": split,
        "config": config,
        "proposals": [p.__dict__ for p in proposals],
        "metrics": metrics,
        "baseline_metrics": baselines,
        "scientific_result": {
            "success_pre_registered": bool(strict_win and novel_accepted and adjudicated_ready),
            "negative_result": not (strict_win and novel_accepted and adjudicated_ready),
            "pilot_warning": "Seed dataset only — not evidence for publication until expert-adjudicated held-out scale.",
            "interpretation": (
                "Pre-registered success on adjudicated held-out (strict baseline dominance + novel category)"
                if strict_win and novel_accepted and adjudicated_ready
                else "No pre-registered success; expand adjudicated held-out and re-run (negative results are valid)"
            ),
        },
    }
