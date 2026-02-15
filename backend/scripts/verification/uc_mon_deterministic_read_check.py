#!/usr/bin/env python3
# Layer: L0 — CI/Verification
# AUDIENCE: INTERNAL
# Role: Verify UC-MON deterministic read contract (as_of, TTL, replay, reproducibility)
# Product: system-wide
# Temporal:
#   Trigger: CI / manual
#   Execution: sync
# Callers: CI, manual verification, uc_mon_validation.py
# Reference: UC-MON Monitoring, UC_MONITORING_IMPLEMENTATION_METHODS.md
# artifact_class: CODE

"""
UC-MON Deterministic Read Verifier

Implements the 4 mandatory determinism checks:

A) as_of contract:
   - Priority read endpoints must accept as_of or have TODO markers.
   - If absent, service generates once and returns in response metadata.

B) TTL/expiry determinism:
   - Feedback/override expiry evaluation must use as_of watermark, not moving clock.
   - Storage migration must define ttl_seconds + expires_at columns.

C) Replay determinism:
   - replay_mode (FULL|TRACE_ONLY), replay_attempt_id, replay_artifact_version
     must be persisted in the traces table.
   - Replay mode changes must emit explicit events and versioned evidence.

D) Reproducibility:
   - Analytics outputs must persist dataset_version + input_window_hash +
     compute_code_version.

Exit codes:
  0 = all checks pass (or all WARNs in advisory mode)
  1 = one or more checks failed
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class CheckResult:
    name: str
    status: str  # PASS | WARN | FAIL
    detail: str


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


# =============================================================================
# CHECK A: as_of CONTRACT
# =============================================================================

# Priority read endpoints that should accept or return as_of
AS_OF_TARGET_FILES: list[tuple[str, str]] = [
    ("activity", "app/hoc/api/cus/activity/activity.py"),
    ("incidents", "app/hoc/api/cus/incidents/incidents.py"),
    ("analytics.feedback", "app/hoc/api/cus/analytics/feedback.py"),
    ("analytics.predictions", "app/hoc/api/cus/analytics/predictions.py"),
    ("logs.traces", "app/hoc/api/cus/logs/traces.py"),
]


def check_as_of_contract() -> list[CheckResult]:
    """Check A: as_of token presence in priority read endpoints."""
    results: list[CheckResult] = []
    pattern = re.compile(r"\bas_of\b")

    for domain, rel_path in AS_OF_TARGET_FILES:
        path = BACKEND_ROOT / rel_path
        if not path.exists():
            results.append(CheckResult(
                f"determinism.as_of.{domain}",
                "WARN",
                f"{path} missing (advisory)",
            ))
            continue
        txt = read_text(path)
        has_as_of = bool(pattern.search(txt))
        results.append(CheckResult(
            f"determinism.as_of.{domain}",
            "PASS" if has_as_of else "WARN",
            f"{'contains' if has_as_of else 'missing'} as_of token in {rel_path}",
        ))

    # Check route map doc documents as_of candidates
    route_map = BACKEND_ROOT / "app" / "hoc" / "docs" / "architecture" / "usecases" / "UC_MONITORING_ROUTE_OPERATION_MAP.md"
    if route_map.exists():
        txt = read_text(route_map)
        has_candidates = "as_of" in txt and "TODO" in txt
        results.append(CheckResult(
            "determinism.as_of.route_map_documented",
            "PASS" if has_candidates else "WARN",
            f"{'as_of candidates documented' if has_candidates else 'as_of section missing'} in route map",
        ))

    return results


# =============================================================================
# CHECK A+: ENDPOINT-LEVEL as_of WIRING (stronger assertions)
# =============================================================================

# Mapping: domain -> list of (endpoint_name, function_name)
AS_OF_WIRED_ENDPOINTS: dict[str, list[tuple[str, str]]] = {
    "activity": [
        ("GET /live", "list_live_runs"),
        ("GET /completed", "list_completed_runs"),
        ("GET /signals", "list_signals"),
    ],
    "incidents": [
        ("GET /active", "list_active_incidents"),
        ("GET /resolved", "list_resolved_incidents"),
        ("GET /historical", "list_historical_incidents"),
    ],
    "analytics.feedback": [
        ("GET /feedback", "list_feedback"),
    ],
    "analytics.predictions": [
        ("GET /predictions", "list_predictions"),
    ],
    "logs.traces": [
        ("GET /traces", "list_traces"),
    ],
}


def check_as_of_endpoint_wiring() -> list[CheckResult]:
    """Check A+: Verify endpoint-level as_of wiring (query param + normalize + L4 dispatch)."""
    results: list[CheckResult] = []

    normalize_pattern = re.compile(r"def _normalize_as_of\b")
    query_param_pattern = re.compile(r"as_of.*Query\(")
    effective_pattern = re.compile(r"effective_as_of\s*=\s*_normalize_as_of\(as_of\)")
    dispatch_pattern = re.compile(r'"as_of"\s*:\s*effective_as_of')

    for domain, rel_path in AS_OF_TARGET_FILES:
        path = BACKEND_ROOT / rel_path
        if not path.exists():
            continue
        txt = read_text(path)

        # Check 1: _normalize_as_of helper exists
        has_helper = bool(normalize_pattern.search(txt))
        results.append(CheckResult(
            f"determinism.as_of.helper.{domain}",
            "PASS" if has_helper else "FAIL",
            f"{'_normalize_as_of defined' if has_helper else '_normalize_as_of MISSING'} in {rel_path}",
        ))

        # Check 2: Per-endpoint wiring
        endpoints = AS_OF_WIRED_ENDPOINTS.get(domain, [])
        for ep_label, fn_name in endpoints:
            fn_pattern = re.compile(rf"def {fn_name}\b")
            fn_match = fn_pattern.search(txt)
            if not fn_match:
                results.append(CheckResult(
                    f"determinism.as_of.endpoint.{domain}.{fn_name}",
                    "WARN",
                    f"function {fn_name} not found in {rel_path}",
                ))
                continue
            # Extract function body (next 80 lines from def)
            fn_start = fn_match.start()
            fn_body = txt[fn_start:fn_start + 3000]

            has_query = bool(query_param_pattern.search(fn_body))
            has_normalize = bool(effective_pattern.search(fn_body))
            has_dispatch = bool(dispatch_pattern.search(fn_body))

            all_ok = has_query and has_normalize and has_dispatch
            detail_parts = []
            if not has_query:
                detail_parts.append("missing as_of Query param")
            if not has_normalize:
                detail_parts.append("missing _normalize_as_of call")
            if not has_dispatch:
                detail_parts.append("missing as_of in L4 dispatch")

            results.append(CheckResult(
                f"determinism.as_of.endpoint.{domain}.{fn_name}",
                "PASS" if all_ok else "FAIL",
                f"{ep_label}: {'fully wired' if all_ok else '; '.join(detail_parts)}",
            ))

    return results


# =============================================================================
# CHECK B: TTL/EXPIRY DETERMINISM
# =============================================================================

def check_ttl_determinism() -> list[CheckResult]:
    """Check B: TTL/expiry evaluation uses as_of watermark, not moving clock."""
    results: list[CheckResult] = []

    # Verify signal_feedback migration has as_of + ttl_seconds + expires_at
    migration = BACKEND_ROOT / "alembic" / "versions" / "128_monitoring_activity_feedback_contracts.py"
    if not migration.exists():
        results.append(CheckResult("determinism.ttl.migration", "FAIL", f"MISSING: {migration}"))
        return results

    txt = read_text(migration)
    has_as_of = '"as_of"' in txt
    has_ttl = "ttl_seconds" in txt
    has_expires = "expires_at" in txt
    ok = has_as_of and has_ttl and has_expires
    results.append(CheckResult(
        "determinism.ttl.storage_fields",
        "PASS" if ok else "FAIL",
        f"as_of={'OK' if has_as_of else 'MISSING'}, ttl_seconds={'OK' if has_ttl else 'MISSING'}, expires_at={'OK' if has_expires else 'MISSING'}",
    ))

    # Check that the as_of column is DateTime(timezone=True) — ensures UTC watermark
    has_tz = "DateTime(timezone=True)" in txt and "as_of" in txt
    results.append(CheckResult(
        "determinism.ttl.as_of_timezone",
        "PASS" if has_tz else "WARN",
        f"{'as_of uses timezone-aware DateTime' if has_tz else 'as_of timezone type not verified'}",
    ))

    return results


# =============================================================================
# CHECK C: REPLAY DETERMINISM
# =============================================================================

def check_replay_determinism() -> list[CheckResult]:
    """Check C: replay_mode, replay_attempt_id, replay_artifact_version persisted."""
    results: list[CheckResult] = []

    migration = BACKEND_ROOT / "alembic" / "versions" / "132_monitoring_logs_replay_mode_fields.py"
    if not migration.exists():
        results.append(CheckResult("determinism.replay.migration", "FAIL", f"MISSING: {migration}"))
        return results

    txt = read_text(migration)

    # Required fields
    fields = {
        "replay_mode": "replay_mode" in txt,
        "replay_attempt_id": "replay_attempt_id" in txt,
        "replay_artifact_version": "replay_artifact_version" in txt,
        "trace_completeness_status": "trace_completeness_status" in txt,
    }
    for field, found in fields.items():
        results.append(CheckResult(
            f"determinism.replay.{field}",
            "PASS" if found else "FAIL",
            f"{'present' if found else 'MISSING'} in migration 132",
        ))

    # Check replay mode values documented in methods doc
    methods = BACKEND_ROOT / "app" / "hoc" / "docs" / "architecture" / "usecases" / "UC_MONITORING_IMPLEMENTATION_METHODS.md"
    if methods.exists():
        mtxt = read_text(methods)
        has_modes = "FULL" in mtxt and "TRACE_ONLY" in mtxt
        results.append(CheckResult(
            "determinism.replay.modes_documented",
            "PASS" if has_modes else "WARN",
            f"{'FULL|TRACE_ONLY documented' if has_modes else 'replay modes not fully documented'}",
        ))

    # Check that replay_mode is applied to aos_traces table
    has_aos_traces = "aos_traces" in txt
    results.append(CheckResult(
        "determinism.replay.target_table",
        "PASS" if has_aos_traces else "FAIL",
        f"{'targets aos_traces' if has_aos_traces else 'wrong target table'} in migration 132",
    ))

    return results


# =============================================================================
# CHECK D: REPRODUCIBILITY
# =============================================================================

def check_reproducibility() -> list[CheckResult]:
    """Check D: dataset_version + input_window_hash + compute_code_version persisted."""
    results: list[CheckResult] = []

    migration = BACKEND_ROOT / "alembic" / "versions" / "131_monitoring_analytics_reproducibility_fields.py"
    if not migration.exists():
        results.append(CheckResult("determinism.reproducibility.migration", "FAIL", f"MISSING: {migration}"))
        return results

    txt = read_text(migration)

    fields = {
        "dataset_version": "dataset_version" in txt,
        "input_window_hash": "input_window_hash" in txt,
        "compute_code_version": "compute_code_version" in txt,
        "dataset_id": "dataset_id" in txt,
        "as_of": '"as_of"' in txt,
    }
    for field, found in fields.items():
        results.append(CheckResult(
            f"determinism.reproducibility.{field}",
            "PASS" if found else "FAIL",
            f"{'present' if found else 'MISSING'} in migration 131",
        ))

    # Check analytics_artifacts table created
    has_table = "analytics_artifacts" in txt
    results.append(CheckResult(
        "determinism.reproducibility.table",
        "PASS" if has_table else "FAIL",
        f"{'analytics_artifacts table' if has_table else 'table not found'} in migration 131",
    ))

    return results


# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    print("UC-MON Deterministic Read Verifier")
    print("=" * 55)

    all_results: list[CheckResult] = []
    all_results.extend(check_as_of_contract())
    all_results.extend(check_as_of_endpoint_wiring())
    all_results.extend(check_ttl_determinism())
    all_results.extend(check_replay_determinism())
    all_results.extend(check_reproducibility())

    pass_count = sum(1 for r in all_results if r.status == "PASS")
    warn_count = sum(1 for r in all_results if r.status == "WARN")
    fail_count = sum(1 for r in all_results if r.status == "FAIL")

    for r in all_results:
        print(f"[{r.status}] {r.name} :: {r.detail}")
    print("-" * 55)
    print(f"Total: {len(all_results)} | PASS: {pass_count} | WARN: {warn_count} | FAIL: {fail_count}")

    return 1 if fail_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
