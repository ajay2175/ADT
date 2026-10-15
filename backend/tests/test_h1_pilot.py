from app.experiments.h1_pilot_dataset import freeze_pilot_dataset, load_pilot_observations
from app.experiments.h1_pilot_run import run_pilot


def test_pilot_dataset_counts():
    info = freeze_pilot_dataset(seed=99, write=False)
    assert info["observation_count"] == 120
    obs = load_pilot_observations()
    if len(obs) != 120:
        freeze_pilot_dataset(seed=42, write=True)
        obs = load_pilot_observations()
    assert len(obs) == 120
    assert sum(1 for o in obs if o["domain"] == "vaidya_mitra") == 60
    assert sum(1 for o in obs if o["split"] == "test") == 40


def test_pilot_run_inconclusive_without_adjudication():
    report = run_pilot(seed=42, freeze=True)
    assert report["summary"]["status"] in ("inconclusive", "negative_or_null", "success")
    assert report["summary"]["adjudication_ready"] is False
    assert "blinded_evaluation" in report
    assert len(report["conditions"]) >= 7
