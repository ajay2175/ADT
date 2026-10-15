from app.experiments.h1_curation_integrity import check_integrity


def test_authenticated_v1_not_ready_until_populated():
    report = check_integrity()
    assert report["total_rows"] == 0
    assert report["ready_for_freeze"] is False
