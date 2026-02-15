# Layer: L5 — Engine
# AUDIENCE: FOUNDER
# Role: Filesystem-based read engine for stagetest evidence artifacts
# artifact_class: CODE
"""
Stagetest Read Engine

Reads stagetest artifacts from the filesystem. No DB/ORM access.
Artifacts live under: backend/artifacts/stagetest/<run_id>/

This engine is called by L2 (stagetest router) and returns
normalized dicts that the router maps to response schemas.
"""

import json
from pathlib import Path

ARTIFACTS_ROOT = Path(__file__).resolve().parents[4] / "artifacts" / "stagetest"


def list_runs() -> list[dict]:
    """List all stagetest runs (most recent first)."""
    if not ARTIFACTS_ROOT.exists():
        return []

    runs = []
    for run_dir in sorted(ARTIFACTS_ROOT.iterdir(), key=lambda d: d.name, reverse=True):
        if not run_dir.is_dir():
            continue
        summary_file = run_dir / "run_summary.json"
        if summary_file.exists():
            try:
                data = json.loads(summary_file.read_text())
                runs.append(data)
            except (json.JSONDecodeError, OSError):
                continue
    return runs


def get_run(run_id: str) -> dict | None:
    """Get a specific run summary."""
    summary_file = ARTIFACTS_ROOT / run_id / "run_summary.json"
    if not summary_file.exists():
        return None
    try:
        return json.loads(summary_file.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def list_cases(run_id: str) -> list[dict]:
    """List all cases for a run."""
    cases_dir = ARTIFACTS_ROOT / run_id / "cases"
    if not cases_dir.exists():
        return []

    cases = []
    for case_file in sorted(cases_dir.glob("*.json")):
        try:
            data = json.loads(case_file.read_text())
            cases.append({
                "case_id": data.get("case_id", case_file.stem),
                "uc_id": data.get("uc_id", ""),
                "stage": data.get("stage", ""),
                "operation_name": data.get("operation_name", ""),
                "status": data.get("status", ""),
                "determinism_hash": data.get("determinism_hash", ""),
            })
        except (json.JSONDecodeError, OSError):
            continue
    return cases


def get_case(run_id: str, case_id: str) -> dict | None:
    """Get a specific case detail."""
    case_file = ARTIFACTS_ROOT / run_id / "cases" / f"{case_id}.json"
    if not case_file.exists():
        return None
    try:
        return json.loads(case_file.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def get_apis_snapshot(run_id: str | None = None) -> dict | None:
    """Get API snapshot. If run_id is None, use latest run."""
    resolved_id: str
    if run_id is None:
        # Find latest
        runs = list_runs()
        if not runs:
            return None
        resolved_id = runs[0].get("run_id", "")
    else:
        resolved_id = run_id

    apis_file = ARTIFACTS_ROOT / resolved_id / "apis_snapshot.json"
    if not apis_file.exists():
        return None
    try:
        return json.loads(apis_file.read_text())
    except (json.JSONDecodeError, OSError):
        return None
