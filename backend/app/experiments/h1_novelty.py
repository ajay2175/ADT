from __future__ import annotations

from typing import Any

from app.experiments.h1_emergence import SamanyaProposal, jaccard, observation_signature, predict_cluster, score_predictions


def structural_pattern_key(proposal: SamanyaProposal) -> tuple[tuple[str, ...], tuple[str, ...]]:
    return (proposal.signature_guna, proposal.signature_karma)


def seed_structural_patterns(seed: dict) -> set[tuple[tuple[str, ...], tuple[str, ...]]]:
    """Seed ontology does not list patterns explicitly; infer from named samanya tokens as weak structural keys."""
    patterns: set[tuple[tuple[str, ...], tuple[str, ...]]] = set()
    for name in seed.get("samanya", []):
        tokens = tuple(sorted(t for t in name.split("_") if len(t) > 2))
        if tokens:
            patterns.add((tokens[: len(tokens) // 2 or 1], tokens[len(tokens) // 2 or 1 :]))
    return patterns


def assess_novelty_levels(
    proposal: SamanyaProposal,
    seed: dict,
    train_obs: list[dict],
    test_obs: list[dict],
    config: str,
) -> dict[str, Any]:
    max_lex = max((jaccard(proposal.name, s) for s in seed.get("samanya", [])), default=0.0)
    lexical_novel = max_lex < 0.6

    pattern = structural_pattern_key(proposal)
    seed_patterns = seed_structural_patterns(seed)
    structural_novel = pattern not in seed_patterns and proposal.novel

    metrics_with = score_predictions(test_obs, config, [proposal] if proposal.accepted else [], seed)
    ablated = SamanyaProposal(
        name=proposal.name,
        signature_guna=proposal.signature_guna,
        signature_karma=proposal.signature_karma,
        member_ids=proposal.member_ids,
        accepted=False,
        novel=proposal.novel,
    )
    metrics_without = score_predictions(test_obs, config, [], seed)
    utility_delta = round(metrics_with["held_out_accuracy"] - metrics_without["held_out_accuracy"], 4)
    functional_novel = proposal.accepted and utility_delta > 0

    return {
        "lexical": {"novel": lexical_novel, "max_jaccard_vs_seed": round(max_lex, 4)},
        "structural": {"novel": structural_novel, "pattern": [list(pattern[0]), list(pattern[1])]},
        "functional": {
            "novel": functional_novel,
            "utility_delta_ablation": utility_delta,
            "accuracy_with_category": metrics_with["held_out_accuracy"],
            "accuracy_without_category": metrics_without["held_out_accuracy"],
        },
        "decisive_functional_novelty": functional_novel,
    }


def per_case_prediction(
    obs: dict,
    proposals: list[SamanyaProposal],
    config: str,
    seed: dict,
) -> dict[str, Any]:
    pred = predict_cluster(obs, proposals, config, seed)
    g, k = observation_signature(obs)
    return {
        "observation_id": obs["id"],
        "domain": obs.get("domain"),
        "predicted": pred,
        "signature": {"guna": list(g), "karma": list(k)},
        "outlier": bool(obs.get("outlier")),
    }
