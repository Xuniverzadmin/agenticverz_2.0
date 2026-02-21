# Layer: L5 — Engine
# AUDIENCE: FOUNDER
# Role: Filesystem-based read engine for stagetest evidence artifacts
# artifact_class: CODE
# capability_id: CAP-005
"""
Stagetest Read Engine

Reads stagetest artifacts from the filesystem. No DB/ORM access.
Artifacts live under: backend/artifacts/stagetest/<run_id>/

This engine is called by L2 (stagetest router) and returns
normalized dicts that the router maps to response schemas.
"""

import ast
import json
import re
from pathlib import Path

ARTIFACTS_ROOT = Path(__file__).resolve().parents[5] / "artifacts" / "stagetest"
REPO_ROOT = Path(__file__).resolve().parents[6]
API_LEDGER_ROOT = REPO_ROOT / "docs" / "api"
LEDGER_FILES = {
    "all": API_LEDGER_ROOT / "HOC_API_LEDGER_ALL.json",
    "cus": API_LEDGER_ROOT / "HOC_CUS_API_LEDGER.json",
    "fdr": API_LEDGER_ROOT / "HOC_FDR_API_LEDGER.json",
}
SOURCE_ROOTS = {
    "cus": Path(__file__).resolve().parents[5] / "app" / "hoc" / "api" / "cus",
    "fdr": Path(__file__).resolve().parents[5] / "app" / "hoc" / "api" / "fdr",
}
SCOPE_PREFIXES = {
    "cus": "/hoc/api/cus",
    "fdr": "/hoc/api/fdr",
}

_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}


def _router_prefix_from_source(content: str) -> str:
    match = re.search(r'APIRouter\s*\([^)]*prefix\s*=\s*["\']([^"\']+)["\']', content, re.DOTALL)
    if match:
        return match.group(1)
    return ""


def _join_paths(prefix: str, route: str) -> str:
    if not prefix:
        return route
    if not route:
        return prefix
    if prefix.endswith("/") and route.startswith("/"):
        return prefix[:-1] + route
    if (not prefix.endswith("/")) and (not route.startswith("/")):
        return prefix + "/" + route
    return prefix + route


def _normalize_scope_path(path: str, scope: str) -> str:
    prefix = SCOPE_PREFIXES[scope]
    if path.startswith(prefix + "/"):
        return path
    if path.startswith(f"/{scope}/"):
        return "/hoc/api" + path
    return prefix + (path if path.startswith("/") else f"/{path}")


def _ordered_endpoints(endpoints: list[dict]) -> list[dict]:
    dedup: dict[tuple[str, str, str], dict] = {}
    for e in endpoints:
        method = str(e.get("method", "")).upper()
        path = str(e.get("path", ""))
        operation = str(e.get("operation", e.get("operation_id", "")))
        if not method or not path:
            continue
        dedup[(method, path, operation)] = {
            "method": method,
            "path": path,
            "operation": operation,
        }
    return sorted(dedup.values(), key=lambda x: (x["path"], x["method"], x["operation"]))


def _load_ledger_file(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    mapped = _ordered_endpoints(payload.get("endpoints", []))
    if not mapped:
        return None
    return {
        "generated_at": str(payload.get("generated_at_utc", "")),
        "endpoints": mapped,
    }


def _build_scope_ledger_from_source(scope: str) -> list[dict]:
    endpoints: list[dict] = []
    source_root = SOURCE_ROOTS[scope]
    if not source_root.exists():
        return endpoints

    for py_file in sorted(source_root.rglob("*.py")):
        if py_file.name == "__init__.py":
            continue
        try:
            content = py_file.read_text()
            tree = ast.parse(content)
        except Exception:
            continue

        router_prefix = _router_prefix_from_source(content)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                if not isinstance(decorator.func, ast.Attribute):
                    continue
                method = decorator.func.attr.lower()
                if method not in _METHODS:
                    continue
                if not decorator.args:
                    continue
                first_arg = decorator.args[0]
                if not isinstance(first_arg, ast.Constant) or not isinstance(first_arg.value, str):
                    continue

                route_path = first_arg.value
                full_path = _normalize_scope_path(_join_paths(router_prefix, route_path), scope)
                endpoints.append(
                    {
                        "method": method.upper(),
                        "path": full_path,
                        "operation": node.name,
                    }
                )

    return _ordered_endpoints(endpoints)


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


def get_apis_ledger_snapshot() -> dict:
    """
    Return a ledger-oriented API snapshot for HOC surfaces.

    Priority:
    1) docs/api/HOC_API_LEDGER_ALL.json (if present)
    2) docs/api/HOC_CUS_API_LEDGER.json + docs/api/HOC_FDR_API_LEDGER.json
    3) latest stagetest artifact snapshot (if non-empty)
    4) source-derived CUS+FDR inventory (always available in repo)
    """
    merged = _load_ledger_file(LEDGER_FILES["all"])
    if merged:
        return {"run_id": "ledger-hoc-all", "generated_at": merged["generated_at"], "endpoints": merged["endpoints"]}

    scoped_endpoints: list[dict] = []
    generated_at = ""
    scopes_found: list[str] = []
    for scope in ("cus", "fdr"):
        payload = _load_ledger_file(LEDGER_FILES[scope])
        if payload is None:
            continue
        scoped_endpoints.extend(payload["endpoints"])
        scopes_found.append(scope)
        if payload["generated_at"] and not generated_at:
            generated_at = payload["generated_at"]

    scoped_ordered = _ordered_endpoints(scoped_endpoints)
    if scoped_ordered:
        return {
            "run_id": "ledger-hoc-" + "-".join(scopes_found),
            "generated_at": generated_at,
            "endpoints": scoped_ordered,
        }

    artifact = get_apis_snapshot()
    if artifact and artifact.get("endpoints"):
        return artifact

    source_endpoints = _build_scope_ledger_from_source("cus") + _build_scope_ledger_from_source("fdr")
    return {
        "run_id": "ledger-source-hoc",
        "generated_at": "",
        "endpoints": _ordered_endpoints(source_endpoints),
    }
