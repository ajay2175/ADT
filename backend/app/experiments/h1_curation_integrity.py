from __future__ import annotations

import json
from pathlib import Path

AUTH_DIR = Path(__file__).resolve().parents[3] / "data" / "experiments" / "h1_concept_discovery" / "pilot_v1" / "authenticated_v1"

SPLIT_FILES = {
    "development": ("observations_development.jsonl", 60),
    "validation": ("observations_validation.jsonl", 20),
    "test": ("observations_test.jsonl", 40),
}


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def check_integrity() -> dict:
    all_rows: list[dict] = []
    split_counts: dict[str, int] = {}
    missing_files: list[str] = []

    for split, (fname, expected) in SPLIT_FILES.items():
        path = AUTH_DIR / fname
        rows = _load_jsonl(path)
        split_counts[split] = len(rows)
        if len(rows) != expected:
            missing_files.append(f"{fname}: expected {expected}, got {len(rows)}")
        for r in rows:
            r["_file_split"] = split
            all_rows.append(r)

    ids = [r.get("observation_id") or r.get("id") for r in all_rows]
    dup_ids = {x for x in ids if ids.count(x) > 1}

    clusters_by_split: dict[str, set[str]] = {}
    cluster_leakage: list[dict] = []
    for r in all_rows:
        cid = r.get("cluster_id")
        if not cid:
            continue
        spl = r["_file_split"]
        clusters_by_split.setdefault(cid, set()).add(spl)
    for cid, splits in clusters_by_split.items():
        if len(splits) > 1:
            cluster_leakage.append({"cluster_id": cid, "splits": sorted(splits)})

    schema_gaps: list[str] = []
    for r in all_rows:
        oid = r.get("observation_id") or r.get("id") or "?"
        for key in ("dravya", "guna", "karma", "source", "cluster_id"):
            if key not in r:
                schema_gaps.append(f"{oid}: missing {key}")
        src = r.get("source") or {}
        if src.get("evidence_type") not in (
            "classical_text",
            "interpretation",
            "experimental_measurement",
            "simulation",
            None,
        ):
            schema_gaps.append(f"{oid}: invalid evidence_type")

    ready = (
        not missing_files
        and not dup_ids
        and not cluster_leakage
        and not schema_gaps
        and len(all_rows) == 120
    )

    return {
        "dataset_version": "authenticated_v1",
        "total_rows": len(all_rows),
        "split_counts": split_counts,
        "quota_errors": missing_files,
        "duplicate_ids": sorted(dup_ids),
        "cluster_leakage": cluster_leakage,
        "schema_gaps": schema_gaps[:50],
        "ready_for_freeze": ready,
    }


def main() -> None:
    report = check_integrity()
    out = AUTH_DIR / "integrity_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
