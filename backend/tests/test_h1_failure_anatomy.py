from app.experiments.h1_failure_anatomy import run_failure_anatomy, write_failure_anatomy_report
from app.experiments.h1_held_out_study import freeze_held_out_study
from app.experiments.h1_novelty import assess_novelty_levels
from app.experiments.h1_emergence import (
    load_observations,
    load_seed,
    propose_samanya_from_observations,
    validate_proposals,
)


def test_failure_anatomy_report_structure():
    report = run_failure_anatomy(seed=42)
    assert report["report_type"] == "h1_failure_anatomy"
    assert "failure_category_counts" in report
    assert "interpretation" in report
    path = write_failure_anatomy_report(report)
    assert path.exists()


def test_held_out_study_sixty_cases():
    info = freeze_held_out_study(seed=7)
    assert info["count"] == 60


def test_novelty_levels_include_functional_ablation():
    seed = load_seed()
    train = load_observations("train")
    props = validate_proposals(propose_samanya_from_observations(train, seed), "padartha_pramana_jnana")
    if props:
        levels = assess_novelty_levels(
            props[0], seed, train, load_observations("held_out"), "padartha_pramana_jnana"
        )
        assert "functional" in levels
        assert "lexical" in levels
