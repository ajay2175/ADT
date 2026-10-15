from __future__ import annotations

import hashlib
import json
from pathlib import Path

STUDY_DIR = Path(__file__).resolve().parents[3] / "data" / "experiments" / "h1_concept_discovery" / "held_out_study_v1"


def generate_held_out_study_cases(seed: int = 42) -> list[dict]:
    """60 serious held-out slots: 30 Ayurveda + 30 materials (expert adjudication required)."""
    cases: list[dict] = []
    for i in range(60):
        domain = "vaidya_mitra" if i < 30 else "materials_science"
        prefix = "h1-ho-ayur" if domain == "vaidya_mitra" else "h1-ho-mat"
        idx = (i % 30) + 1
        digest = hashlib.sha256(f"{seed}:heldout:{i}".encode()).hexdigest()
        cases.append(
            {
                "id": f"{prefix}-{idx:03d}",
                "split": "held_out_study",
                "domain": domain,
                "dravya": f"ENTITY-{digest[:8]}",
                "guna": [],
                "karma": [],
                "source_provenance": {
                    "status": "pending_curation",
                    "corpus_refs": [],
                    "no_overlap_with": ["pilot_v1:development", "pilot_v1:validation"],
                },
                "outlier": False,
                "adjudication": {
                    "holdout_cluster": "pending_expert",
                    "ground_truth_ready": False,
                    "domain_validity_score": None,
                    "ontology_novelty_score": None,
                    "methodology_integrity_score": None,
                },
            }
        )
    return cases


def freeze_held_out_study(seed: int = 42) -> dict:
    STUDY_DIR.mkdir(parents=True, exist_ok=True)
    cases = generate_held_out_study_cases(seed)
    frozen = {
        "study_id": "h1-held-out-study-v1",
        "protocol_version": "1.2.0",
        "n_cases": 60,
        "vaidya_mitra": 30,
        "materials_science": 30,
        "leakage_policy": "zero_id_overlap_with_pilot_v1_train_dev_val",
        "adjudication_panel": 3,
        "confirmatory_metric": "pre_registered_strict_dominance",
        "exploratory_metrics": ["lexical_novelty", "structural_novelty", "functional_utility_delta"],
    }
    (STUDY_DIR / "FROZEN.json").write_text(json.dumps(frozen, indent=2), encoding="utf-8")
    with (STUDY_DIR / "cases.jsonl").open("w", encoding="utf-8") as fh:
        for row in cases:
            fh.write(json.dumps(row) + "\n")
    return {"count": len(cases), "path": str(STUDY_DIR)}
