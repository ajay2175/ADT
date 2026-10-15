from __future__ import annotations

import argparse
import json

from app.experiments.h1_pilot_run import run_pilot, write_pilot_report


def main() -> None:
    parser = argparse.ArgumentParser(description="H1 pilot v1 — 120 cases, blinded packets, full traces")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--freeze-dataset", action="store_true", help="Regenerate frozen observations.jsonl")
    args = parser.parse_args()

    report = run_pilot(seed=args.seed, freeze=args.freeze_dataset)
    out_dir = write_pilot_report(report)
    print(
        json.dumps(
            {
                "output_dir": str(out_dir),
                "status": report["summary"]["status"],
                "utility_delta": report["summary"]["utility_delta"],
                "adjudication_ready": report["summary"]["adjudication_ready"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
