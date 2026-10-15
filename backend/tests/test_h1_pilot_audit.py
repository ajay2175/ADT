from app.experiments.h1_pilot_audit import audit_pilot_v1


def test_audit_pilot_structure():
    report = audit_pilot_v1()
    assert report["confirmatory_held_out"] == "test"
    assert report["confirmatory_n"] == 40
    assert report["counts_by_split"]["development"] == 60
