from __future__ import annotations

import json
from pathlib import Path

CAL = Path(__file__).resolve().parents[3] / "data" / "experiments" / "h1_concept_discovery" / "pilot_v1" / "calibration"
OBS_DIR = CAL / "observation_data"
GT_DIR = CAL / "ground_truth"


def load_system_observations() -> list[dict]:
    """Calibration cases visible to experiment runners (no ground truth)."""
    rows: list[dict] = []
    if OBS_DIR.exists():
        for path in sorted(OBS_DIR.glob("*.json")):
            if path.name == "README.md":
                continue
            rows.append(json.loads(path.read_text(encoding="utf-8")))
    if rows:
        return rows
    # Fallback legacy jsonl (deprecated — may contain curator hints)
    legacy = CAL / "ayurveda_10_cases.jsonl"
    if legacy.exists():
        return [json.loads(line) for line in legacy.read_text(encoding="utf-8").splitlines() if line.strip()]
    return []


def load_ground_truth(observation_id: str) -> dict | None:
    path = GT_DIR / f"{observation_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
