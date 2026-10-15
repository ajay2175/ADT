from __future__ import annotations

import argparse
import json

from app.experiments.h1_failure_anatomy import run_failure_anatomy, write_failure_anatomy_report
from app.experiments.h1_held_out_study import freeze_held_out_study


def main() -> None:
    parser = argparse.ArgumentParser(description="H1 Failure Anatomy and Blind Adjudication prep")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--freeze-held-out-study", action="store_true")
    args = parser.parse_args()

    if args.freeze_held_out_study:
        info = freeze_held_out_study(seed=args.seed)
        print(json.dumps({"held_out_study": info}, indent=2))

    report = run_failure_anatomy(seed=args.seed)
    path = write_failure_anatomy_report(report)
    print(
        json.dumps(
            {
                "failure_anatomy_path": str(path),
                "failure_category_counts": report["failure_category_counts"],
                "interpretation": report["interpretation"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
