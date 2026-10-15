import json

from app.experiments.h1_emergence import jaccard, propose_samanya_from_observations, run_h1_experiment, validate_proposals


def test_novelty_jaccard():
    assert jaccard("tikta_deepana", "classical_rasayana_dravya") < 0.6


def test_proposes_novel_samanya_not_in_seed():
    seed = json.loads(
        '{"samanya": ["classical_rasayana_dravya"], "dravya": [], "guna": [], "karma": []}'
    )
    obs = [
        {"id": "a", "guna": ["tikta"], "karma": ["deepana", "immune_modulation"], "outlier": False},
        {"id": "b", "guna": ["tikta"], "karma": ["deepana", "immune_modulation"], "outlier": False},
    ]
    props = propose_samanya_from_observations(obs, seed, min_support=2)
    assert props
    assert any(p.novel for p in props)


def test_h1_run_produces_report_structure():
    report = run_h1_experiment(split="held_out", config="padartha_pramana_jnana", seed=42)
    assert report["experiment"] == "h1_emergence"
    assert "scientific_result" in report
    assert "baseline_metrics" in report
    assert "metrics" in report


def test_padartha_only_accepts_novel():
    seed = {"samanya": ["other"], "dravya": [], "guna": [], "karma": []}
    obs = [
        {"id": "a", "guna": ["x"], "karma": ["y"], "outlier": False},
        {"id": "b", "guna": ["x"], "karma": ["y"], "outlier": False},
    ]
    props = validate_proposals(propose_samanya_from_observations(obs, seed), "padartha_only")
    assert props[0].accepted
