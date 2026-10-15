from app.experiments.h1_observation_loader import load_system_observations


def test_system_observation_excludes_discovery_target():
    rows = load_system_observations()
    assert rows
    first = next(r for r in rows if r["observation_id"] == "cal-ayur-001")
    assert "discovery_target" not in first
    assert "seed_ontology_status" not in first
