import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("ADT_DATABASE_URL", "")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr("app.database.SQLITE_PATH", tmp_path / "t.db")
    monkeypatch.setattr("app.database.DATA_DIR", tmp_path)
    from app.database import setup_database
    from app.main import app

    setup_database()
    with TestClient(app) as c:
        yield c


def test_constitution_sql_mutation_blocked(client: TestClient):
    from app.persistence_guard import guard_sql_mutation

    with pytest.raises(PermissionError):
        guard_sql_mutation("UPDATE constitution_items SET statement='hacked' WHERE id='x'")


def test_finalize_blocked_without_valid_assertions(client: TestClient):
    r = client.post(
        "/v1/decisions/analyze",
        json={"question": "Should we launch a consequential clinical program next quarter?", "context": {}},
    ).json()
    fin = client.post(f"/v1/decisions/{r['id']}/finalize", json={"final_decision": "Proceed"})
    assert fin.status_code == 403


def test_finalize_exploratory_allowed(client: TestClient):
    r = client.post(
        "/v1/decisions/analyze",
        json={"question": "Should we explore ACA staging as a research hypothesis only?", "context": {}},
    ).json()
    fin = client.post(
        f"/v1/decisions/{r['id']}/finalize?exploratory=true",
        json={"final_decision": "Explore only"},
    )
    assert fin.status_code == 200


def test_counterfactual_labeled_simulation(client: TestClient):
    cf = client.post("/v1/causal/counterfactual?intervention=x&target_effect=y").json()
    assert cf.get("epistemic_label") == "simulation_hypothesis"
