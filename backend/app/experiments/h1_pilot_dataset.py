from __future__ import annotations

import hashlib
import json
from pathlib import Path

PILOT_DIR = Path(__file__).resolve().parents[3] / "data" / "experiments" / "h1_concept_discovery" / "pilot_v1"

AYUR_GUNA = ["tikta", "madhura", "kashaya", "laghu", "guru", "ushna", "snigdha", "ruksha"]
AYUR_KARMA = ["deepana", "rasayana", "medhya", "shothahara", "immune_modulation", "sleep_latency"]
MAT_GUNA = ["tolerance_high", "tolerance_low", "ionic_radius_match", "crystal_stable"]
MAT_KARMA = ["bandgap_stable", "ferroelectric", "ionic_conductivity", "phase_transition"]


def _split_for_index(i: int) -> str:
    if i < 60:
        return "development"
    if i < 80:
        return "validation"
    return "test"


def generate_pilot_observations(seed: int = 42) -> list[dict]:
    """Deterministic 120-case pilot scaffold (60 Ayurveda + 60 materials)."""
    cases: list[dict] = []
    for i in range(120):
        domain = "vaidya_mitra" if i < 60 else "materials_science"
        digest = hashlib.sha256(f"{seed}:pilot:{i}".encode()).hexdigest()
        if domain == "vaidya_mitra":
            g = [AYUR_GUNA[int(digest[0:2], 16) % len(AYUR_GUNA)]]
            g.append(AYUR_GUNA[int(digest[2:4], 16) % len(AYUR_GUNA)])
            k = [AYUR_KARMA[int(digest[4:6], 16) % len(AYUR_KARMA)]]
            if int(digest[6:8], 16) % 5 == 0:
                k.append("immune_modulation")
            dravya = f"Dravya-{digest[:6]}"
        else:
            g = [MAT_GUNA[int(digest[0:2], 16) % len(MAT_GUNA)]]
            k = [MAT_KARMA[int(digest[4:6], 16) % len(MAT_KARMA)]]
            dravya = f"Compound-{digest[:6]}"
        outlier = int(digest[8:10], 16) % 17 == 0
        cases.append(
            {
                "id": f"pilot-{i:03d}",
                "split": _split_for_index(i),
                "domain": domain,
                "dravya": dravya,
                "guna": sorted(set(g)),
                "karma": sorted(set(k)),
                "outlier": outlier,
                "adjudication": {
                    "holdout_cluster": "pending_expert",
                    "ground_truth_ready": False,
                },
            }
        )
    return cases


def freeze_pilot_dataset(seed: int = 42, write: bool = True) -> dict:
    obs = generate_pilot_observations(seed)
    seed_ontology = {
        "version": "h1-pilot-v1-seed",
        "samanya": ["classical_rasayana_dravya", "standard_deepana_herb", "perovskite_prototype_a"],
        "dravya": [],
        "guna": AYUR_GUNA + MAT_GUNA,
        "karma": AYUR_KARMA + MAT_KARMA,
    }
    manifest = {
        "counts": {
            "total": len(obs),
            "vaidya_mitra": sum(1 for o in obs if o["domain"] == "vaidya_mitra"),
            "materials_science": sum(1 for o in obs if o["domain"] == "materials_science"),
            "development": sum(1 for o in obs if o["split"] == "development"),
            "validation": sum(1 for o in obs if o["split"] == "validation"),
            "test": sum(1 for o in obs if o["split"] == "test"),
        },
        "seed": seed,
    }
    if write:
        PILOT_DIR.mkdir(parents=True, exist_ok=True)
        (PILOT_DIR / "seed_ontology.json").write_text(json.dumps(seed_ontology, indent=2), encoding="utf-8")
        with (PILOT_DIR / "observations.jsonl").open("w", encoding="utf-8") as fh:
            for row in obs:
                fh.write(json.dumps(row) + "\n")
        (PILOT_DIR / "dataset_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"manifest": manifest, "observation_count": len(obs)}


def load_pilot_observations(split: str | None = None) -> list[dict]:
    path = PILOT_DIR / "observations.jsonl"
    if not path.exists():
        freeze_pilot_dataset(write=True)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if split:
        return [r for r in rows if r.get("split") == split]
    return rows


def load_pilot_seed() -> dict:
    path = PILOT_DIR / "seed_ontology.json"
    if not path.exists():
        freeze_pilot_dataset(write=True)
    return json.loads(path.read_text(encoding="utf-8"))
