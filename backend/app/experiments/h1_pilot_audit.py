from __future__ import annotations

import json
from pathlib import Path

from app.experiments.h1_pilot_dataset import PILOT_DIR, load_pilot_observations

ROOT = Path(__file__).resolve().parents[3]


def audit_pilot_v1() -> dict:
    obs = load_pilot_observations()
    by_split: dict[str, list[dict]] = {}
    for o in obs:
        by_split.setdefault(o.get("split", "unknown"), []).append(o)

    ids = {o["id"] for o in obs}
    dravya_by_split = {s: {o["dravya"] for o in rows} for s, rows in by_split.items()}

    leakage_dravya = []
    test_dravya = dravya_by_split.get("test", set())
    for split in ("development", "validation"):
        overlap = test_dravya & dravya_by_split.get(split, set())
        if overlap:
            leakage_dravya.append({"split": split, "overlapping_dravya": sorted(overlap)})

    placeholders = []
    for o in obs:
        if o.get("split") == "test":
            if not o.get("guna") and not o.get("karma"):
                placeholders.append(o["id"])
            if str(o.get("dravya", "")).startswith(("Dravya-", "Compound-")):
                placeholders.append(o["id"])

    provenance_pending = sum(
        1 for o in obs if (o.get("source_provenance") or {}).get("status") == "pending_curation"
    )

    return {
        "pilot_id": "h1-pilot-v1",
        "protocol_version": "1.1.0",
        "confirmatory_held_out": "test",
        "confirmatory_n": len(by_split.get("test", [])),
        "counts_by_split": {k: len(v) for k, v in by_split.items()},
        "domain_counts": {
            "vaidya_mitra": sum(1 for o in obs if o["domain"] == "vaidya_mitra"),
            "materials_science": sum(1 for o in obs if o["domain"] == "materials_science"),
        },
        "leakage_dravya_overlap": leakage_dravya,
        "test_placeholder_flags": sorted(set(placeholders)),
        "authenticity_blocked": provenance_pending > 0 or bool(placeholders),
        "replication_study_note": "held_out_study_v1 (60) is separate from Pilot v1 (40 test); not required for this audit",
        "ready_for_official_run": not leakage_dravya and not placeholders and provenance_pending == 0,
    }


def main() -> None:
    report = audit_pilot_v1()
    out = PILOT_DIR / "dataset_audit_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
