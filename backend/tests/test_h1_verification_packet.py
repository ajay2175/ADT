from app.experiments.h1_verification_packet import build_packet


def test_verification_packet_has_claim_fields():
    packet = build_packet("cal-ayur-001")
    assert packet["observation_id"] == "cal-ayur-001"
    assert "Guḍūcī" in packet["claim"]["dravya"]
    assert packet["passage"]["work"] == "Bhāvaprakāśa"
