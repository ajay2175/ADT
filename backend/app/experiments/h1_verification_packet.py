from __future__ import annotations

import argparse
import json
from pathlib import Path

CAL_DIR = Path(__file__).resolve().parents[3] / "data" / "experiments" / "h1_concept_discovery" / "pilot_v1" / "calibration"
VERIFY_DIR = CAL_DIR / "source_verification"
SCHEMA = json.loads((VERIFY_DIR / "verification_schema.json").read_text(encoding="utf-8"))


def load_case(observation_id: str) -> dict:
    for line in (CAL_DIR / "ayurveda_10_cases.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("observation_id") == observation_id:
            return row
    raise KeyError(f"Unknown observation_id: {observation_id}")


def build_packet(observation_id: str) -> dict:
    case = load_case(observation_id)
    packet = json.loads(json.dumps(SCHEMA))
    packet["observation_id"] = observation_id
    packet["claim"]["dravya"] = case.get("dravya", "")
    packet["claim"]["guna"] = case.get("guna", [])
    packet["claim"]["karma"] = case.get("karma", [])
    packet["claim"]["context"] = case.get("observation", "")
    packet["claim"]["epistemic_layer"] = case.get("epistemic_layer", "")
    src = case.get("classical_source") or {}
    packet["passage"]["work"] = src.get("work", "")
    packet["passage"]["chapter_section"] = src.get("section", "")
    packet["passage"]["verse_or_page"] = src.get("reference_note", "")
    packet["_research_prompt_for_ai_assistant"] = (
        "Retrieve primary passage for this claim. Separate explicit śabda from commentary inference. "
        "Do not assert modern clinical efficacy unless separate experimental sources are cited."
    )
    packet["_case_discovery_target"] = case.get("discovery_target", "")
    packet["_revision_pair_id"] = case.get("revision_pair_id")
    return packet


def write_packet(observation_id: str) -> Path:
    VERIFY_DIR.mkdir(parents=True, exist_ok=True)
    path = VERIFY_DIR / f"{observation_id}.json"
    if not path.exists():
        path.write_text(json.dumps(build_packet(observation_id), indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Create/update source verification packet for a calibration case")
    parser.add_argument("--case", help="e.g. cal-ayur-001")
    parser.add_argument("--all", action="store_true", help="Initialize packets for all 10 cases if missing")
    args = parser.parse_args()
    if args.all:
        for line in (CAL_DIR / "ayurveda_10_cases.jsonl").read_text(encoding="utf-8").splitlines():
            if line.strip():
                oid = json.loads(line)["observation_id"]
                write_packet(oid)
        print(json.dumps({"initialized_dir": str(VERIFY_DIR)}, indent=2))
    else:
        path = write_packet(args.case)
        print(json.dumps({"packet_path": str(path)}, indent=2))


if __name__ == "__main__":
    main()
