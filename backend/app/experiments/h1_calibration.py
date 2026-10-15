from __future__ import annotations

import json
from pathlib import Path

CAL_DIR = Path(__file__).resolve().parents[3] / "data" / "experiments" / "h1_concept_discovery" / "pilot_v1" / "calibration"
SCHEMA = json.loads((CAL_DIR / "adjudication_record_schema.json").read_text(encoding="utf-8"))


def load_calibration_cases() -> list[dict]:
    path = CAL_DIR / "ayurveda_10_cases.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def validate_calibration_file() -> dict:
    cases = load_calibration_cases()
    errors: list[str] = []
    for case in cases:
        if case.get("split") != "calibration":
            errors.append(f"{case.get('observation_id')}: split must be calibration")
        for field in ("observation_id", "classical_source", "dravya", "guna", "karma", "seed_ontology_status"):
            if field not in case:
                errors.append(f"{case.get('observation_id')}: missing {field}")
        if case.get("seed_ontology_status", {}).get("named_samanya_in_seed"):
            errors.append(f"{case.get('observation_id')}: must target discovery (samanya not in seed)")
    return {
        "n_cases": len(cases),
        "expected_n": 10,
        "valid": len(cases) == 10 and not errors,
        "errors": errors,
        "confirmatory_separation": "calibration cases must not be copied into test split without new protocol version",
    }


def main() -> None:
    print(json.dumps(validate_calibration_file(), indent=2))


if __name__ == "__main__":
    main()
