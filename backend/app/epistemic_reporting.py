from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from app.epistemic_eval import load_manifest


def build_run_report(run_payload: dict) -> dict:
    """WP5 — attach reproducibility metadata to an evaluation run."""
    commit = os.environ.get("ADT_GIT_COMMIT", "")
    if not commit:
        try:
            root = Path(__file__).resolve().parents[2]
            commit = (
                subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, stderr=subprocess.DEVNULL)
                .decode()
                .strip()
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            commit = "unknown"

    manifest = load_manifest()
    return {
        "dataset": manifest,
        "git_commit": commit,
        "llm_provider": os.environ.get("LLM_PROVIDER", "mock"),
        "random_seed": int(os.environ.get("ADT_EVAL_SEED", "42")),
        "rubric_version": "0.6.0",
        "metrics": run_payload.get("metrics", {}),
        "results": run_payload.get("results", []),
    }
