from __future__ import annotations

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from app.experiments.h1_emergence import H1_DIR, run_h1_experiment

ROOT = Path(__file__).resolve().parents[3]
RUNS_DIR = H1_DIR / "runs"


def _git_commit() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL)
            .decode()
            .strip()
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description="Experiment 1 — Emergence of New Knowledge (H1)")
    parser.add_argument("--split", default="held_out")
    parser.add_argument(
        "--config",
        default="padartha_pramana_jnana",
        choices=[
            "baseline_llm",
            "baseline_kg",
            "baseline_neurosym",
            "adt_minus",
            "padartha_only",
            "padartha_pramana",
            "padartha_pramana_jnana",
        ],
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    report = run_h1_experiment(split=args.split, config=args.config, seed=args.seed)
    report["git_commit"] = _git_commit()
    report["run_at"] = datetime.now(UTC).isoformat()
    report["random_seed"] = args.seed

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    out = RUNS_DIR / f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_h1_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"report_path": str(out), "scientific_result": report["scientific_result"]}, indent=2))


if __name__ == "__main__":
    main()
