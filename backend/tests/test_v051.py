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


def _analyze(client: TestClient, question: str) -> str:
    return client.post(
        "/v1/decisions/analyze",
        json={"question": question, "context": {}},
    ).json()["id"]


def test_research_record_finalize_without_full_epistemic_chain(client: TestClient):
    decision_id = _analyze(client, "Should we explore ACA staging as a research hypothesis only?")
    fin = client.post(
        f"/v1/decisions/{decision_id}/finalize",
        json={"final_decision": "Record hypothesis for lab review only", "kind": "research_record"},
    )
    assert fin.status_code == 200
    body = fin.json()
    assert body["authorization"]["action_authorized"] is False
    assert body["capabilities"] == ["record_research"]


def test_research_record_capability_blocks_execution_not_phrases(client: TestClient):
    decision_id = _analyze(client, "Should we explore herb mechanisms as a research hypothesis only?")
    fin = client.post(
        f"/v1/decisions/{decision_id}/finalize",
        json={
            "final_decision": "Issue clinical recommendation to treat patient with Guduchi",
            "kind": "research_record",
        },
    )
    assert fin.status_code == 200
    assert fin.json()["authorization"].get("phrase_risk_flags")
    exec_r = client.post(
        f"/v1/decisions/{decision_id}/actions/execute",
        json={"action_type": "consequential_workflow", "payload": {}},
    )
    assert exec_r.status_code == 403
    clinical = client.post(
        f"/v1/decisions/{decision_id}/actions/execute",
        json={"action_type": "clinical", "payload": {}},
    )
    assert clinical.status_code == 403


def test_grant_replay_blocked(client: TestClient):
    decision_id = _analyze(client, "Should we explore staging gates as a research hypothesis only?")
    auth = client.post(
        f"/v1/decisions/{decision_id}/authorize",
        json={"final_decision": "Research note only", "kind": "research_record"},
    )
    assert auth.status_code == 200
    grant_id = auth.json()["grant_id"]
    first = client.post(
        f"/v1/decisions/{decision_id}/finalize",
        json={"final_decision": "Research note only", "kind": "research_record", "grant_id": grant_id},
    )
    assert first.status_code == 200
    replay = client.post(
        f"/v1/decisions/{decision_id}/finalize",
        json={"final_decision": "Research note only", "kind": "research_record", "grant_id": grant_id},
    )
    assert replay.status_code == 403


def test_stale_grant_after_evidence_link_change(client: TestClient):
    decision_id = _analyze(client, "Should we explore staging gates as a research hypothesis only?")
    auth = client.post(
        f"/v1/decisions/{decision_id}/authorize",
        json={"final_decision": "Research note only", "kind": "research_record"},
    )
    grant_id = auth.json()["grant_id"]
    from app.decision_authorization import link_assertions_to_decision

    link_assertions_to_decision(decision_id, ["synthetic-assertion-id"])
    fin = client.post(
        f"/v1/decisions/{decision_id}/finalize",
        json={"final_decision": "Research note only", "kind": "research_record", "grant_id": grant_id},
    )
    assert fin.status_code == 403


def test_entailment_endpoint(client: TestClient):
    r = client.post(
        "/v1/epistemic/pramana/entailment",
        json={
            "claim": "Guduchi supports immune modulation",
            "passage": "Guduchi supports immune modulation in classical texts",
        },
    )
    assert r.status_code == 200
    assert r.json()["relation"] == "supports"


def test_vaidya_benchmark_pack(client: TestClient):
    cases = client.get("/v1/domain/vaidya-mitra/benchmark").json()
    assert len(cases) >= 3
    assert cases[0]["entity"] == "Guduchi"
