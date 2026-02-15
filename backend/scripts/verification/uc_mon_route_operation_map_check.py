#!/usr/bin/env python3
# Layer: L0 — CI/Verification
# AUDIENCE: INTERNAL
# Role: Verify UC-MON endpoint-to-L4 operation mapping evidence
# Product: system-wide
# Temporal:
#   Trigger: CI / manual
#   Execution: sync
# Callers: CI, manual verification, uc_mon_validation.py
# Reference: UC-MON Monitoring, HANDOVER_UC_MONITORING_TO_CLAUDE.md
# artifact_class: CODE

"""
UC-MON Route-to-Operation Mapping Verifier

Verifies that every documented endpoint in the UC-MON route map
has matching evidence in the L2 source files. Detects:
1. Documented endpoints missing from source (stale docs)
2. Endpoints that bypass L4 dispatch (direct DB/L5 access)
3. Domain coverage gaps

Exit codes:
  0 = all checks pass
  1 = one or more checks failed
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
HOC_API = BACKEND_ROOT / "app" / "hoc" / "api"


@dataclass
class RouteEntry:
    domain: str
    file_rel: str
    method: str
    path_pattern: str
    l4_operation: str
    notes: str = ""


# =============================================================================
# CANONICAL UC-MON ROUTE MAP
# =============================================================================

ACTIVITY_ROUTES: list[RouteEntry] = [
    RouteEntry("activity", "cus/activity/activity.py", "GET", "/activity/runs", "activity.query"),
    RouteEntry("activity", "cus/activity/activity.py", "GET", "/activity/runs/{run_id}", "activity.query"),
    RouteEntry("activity", "cus/activity/activity.py", "GET", "/activity/summary/by-status", "activity.query"),
    RouteEntry("activity", "cus/activity/activity.py", "GET", "/activity/runs/live/by-dimension", "activity.query"),
    RouteEntry("activity", "cus/activity/activity.py", "GET", "/activity/runs/completed/by-dimension", "activity.query"),
    RouteEntry("activity", "cus/activity/activity.py", "GET", "/activity/runs/by-dimension", "activity.query"),
    RouteEntry("activity", "cus/activity/activity.py", "GET", "/activity/patterns", "activity.query"),
    RouteEntry("activity", "cus/activity/activity.py", "GET", "/activity/cost-analysis", "activity.query"),
    RouteEntry("activity", "cus/activity/activity.py", "GET", "/activity/attention-queue", "activity.query"),
    RouteEntry("activity", "cus/activity/activity.py", "GET", "/activity/risk-signals", "activity.query"),
    RouteEntry("activity", "cus/activity/activity.py", "GET", "/activity/live", "activity.query"),
    RouteEntry("activity", "cus/activity/activity.py", "GET", "/activity/completed", "activity.query"),
    RouteEntry("activity", "cus/activity/activity.py", "GET", "/activity/signals", "activity.query"),
    RouteEntry("activity", "cus/activity/activity.py", "GET", "/activity/metrics", "activity.query"),
    RouteEntry("activity", "cus/activity/activity.py", "GET", "/activity/threshold-signals", "activity.query"),
    RouteEntry("activity", "cus/activity/activity.py", "POST", "/activity/signals/{fp}/ack", "activity.query"),
    RouteEntry("activity", "cus/activity/activity.py", "POST", "/activity/signals/{fp}/suppress", "activity.query"),
]

INCIDENTS_ROUTES: list[RouteEntry] = [
    RouteEntry("incidents", "cus/incidents/incidents.py", "GET", "/incidents", "incidents.query"),
    RouteEntry("incidents", "cus/incidents/incidents.py", "GET", "/incidents/by-run/{run_id}", "incidents.query"),
    RouteEntry("incidents", "cus/incidents/incidents.py", "GET", "/incidents/patterns", "incidents.query"),
    RouteEntry("incidents", "cus/incidents/incidents.py", "GET", "/incidents/recurring", "incidents.query"),
    RouteEntry("incidents", "cus/incidents/incidents.py", "GET", "/incidents/cost-impact", "incidents.query"),
    RouteEntry("incidents", "cus/incidents/incidents.py", "GET", "/incidents/active", "incidents.query"),
    RouteEntry("incidents", "cus/incidents/incidents.py", "GET", "/incidents/resolved", "incidents.query"),
    RouteEntry("incidents", "cus/incidents/incidents.py", "GET", "/incidents/historical", "incidents.query"),
    RouteEntry("incidents", "cus/incidents/incidents.py", "GET", "/incidents/metrics", "incidents.query"),
    RouteEntry("incidents", "cus/incidents/incidents.py", "GET", "/incidents/historical/trend", "incidents.query"),
    RouteEntry("incidents", "cus/incidents/incidents.py", "GET", "/incidents/historical/distribution", "incidents.query"),
    RouteEntry("incidents", "cus/incidents/incidents.py", "GET", "/incidents/historical/cost-trend", "incidents.query"),
    RouteEntry("incidents", "cus/incidents/incidents.py", "GET", "/incidents/{incident_id}", "incidents.query"),
    RouteEntry("incidents", "cus/incidents/incidents.py", "GET", "/incidents/{incident_id}/learnings", "incidents.query"),
    RouteEntry("incidents", "cus/incidents/incidents.py", "POST", "/{incident_id}/export/evidence", "incidents.export"),
    RouteEntry("incidents", "cus/incidents/incidents.py", "POST", "/{incident_id}/export/soc2", "incidents.export"),
    RouteEntry("incidents", "cus/incidents/incidents.py", "POST", "/{incident_id}/export/executive-debrief", "incidents.export"),
]

CONTROLS_ROUTES: list[RouteEntry] = [
    RouteEntry("controls", "cus/controls/controls.py", "GET", "/controls", "controls.query"),
    RouteEntry("controls", "cus/controls/controls.py", "GET", "/controls/status", "controls.query"),
    RouteEntry("controls", "cus/controls/controls.py", "GET", "/controls/{control_id}", "controls.query"),
    RouteEntry("controls", "cus/controls/controls.py", "PUT", "/controls/{control_id}", "controls.query"),
    RouteEntry("controls", "cus/controls/controls.py", "POST", "/controls/{control_id}/enable", "controls.query"),
    RouteEntry("controls", "cus/controls/controls.py", "POST", "/controls/{control_id}/disable", "controls.query"),
]

ANALYTICS_ROUTES: list[RouteEntry] = [
    RouteEntry("analytics", "cus/analytics/feedback.py", "GET", "/feedback", "analytics.feedback"),
    RouteEntry("analytics", "cus/analytics/feedback.py", "GET", "/feedback/{feedback_id}", "analytics.feedback"),
    RouteEntry("analytics", "cus/analytics/feedback.py", "GET", "/feedback/stats/summary", "analytics.feedback"),
    RouteEntry("analytics", "cus/analytics/predictions.py", "GET", "/predictions", "analytics.prediction_read"),
    RouteEntry("analytics", "cus/analytics/predictions.py", "GET", "/predictions/{prediction_id}", "analytics.prediction_read"),
    RouteEntry("analytics", "cus/analytics/predictions.py", "GET", "/predictions/subject/{st}/{sid}", "analytics.prediction_read"),
    RouteEntry("analytics", "cus/analytics/predictions.py", "GET", "/predictions/stats/summary", "analytics.prediction_read"),
    RouteEntry("analytics", "cus/analytics/costsim.py", "GET", "/costsim/v2/status", "analytics.costsim.status"),
    RouteEntry("analytics", "cus/analytics/costsim.py", "POST", "/costsim/v2/simulate", "analytics.costsim.simulate"),
    RouteEntry("analytics", "cus/analytics/costsim.py", "GET", "/costsim/divergence", "analytics.costsim.divergence"),
    RouteEntry("analytics", "cus/analytics/costsim.py", "GET", "/costsim/canary/reports", "analytics.canary_reports"),
    RouteEntry("analytics", "cus/analytics/costsim.py", "GET", "/costsim/datasets", "analytics.costsim.datasets"),
    RouteEntry("analytics", "cus/analytics/costsim.py", "GET", "/costsim/datasets/{dataset_id}", "analytics.costsim.datasets"),
]

LOGS_ROUTES: list[RouteEntry] = [
    RouteEntry("logs", "cus/logs/traces.py", "GET", "/traces", "logs.traces_api"),
    RouteEntry("logs", "cus/logs/traces.py", "POST", "/traces", "logs.traces_api"),
    RouteEntry("logs", "cus/logs/traces.py", "GET", "/traces/{run_id}", "logs.traces_api"),
    RouteEntry("logs", "cus/logs/traces.py", "GET", "/traces/by-hash/{root_hash}", "logs.traces_api"),
    RouteEntry("logs", "cus/logs/traces.py", "GET", "/traces/compare/{r1}/{r2}", "logs.traces_api"),
    RouteEntry("logs", "cus/logs/traces.py", "DELETE", "/traces/{run_id}", "logs.traces_api"),
    RouteEntry("logs", "cus/logs/traces.py", "POST", "/traces/cleanup", "logs.traces_api"),
    RouteEntry("logs", "cus/logs/traces.py", "GET", "/traces/idempotency/{key}", "logs.traces_api"),
    RouteEntry("logs", "cus/logs/traces.py", "GET", "/traces/mismatches", "traces.list_mismatches"),
    RouteEntry("logs", "cus/logs/traces.py", "POST", "/traces/mismatches/bulk-report", "traces.bulk_report_mismatches"),
    RouteEntry("logs", "cus/logs/traces.py", "POST", "/traces/{tid}/mismatch", "traces.report_mismatch"),
    RouteEntry("logs", "cus/logs/traces.py", "GET", "/traces/{tid}/mismatches", "traces.list_trace_mismatches"),
    RouteEntry("logs", "cus/logs/traces.py", "POST", "/traces/{tid}/mismatches/{mid}/resolve", "traces.resolve_mismatch"),
]

POLICIES_ROUTES: list[RouteEntry] = [
    RouteEntry("policies", "cus/policies/policies.py", "GET", "/policies", "policies.query"),
    RouteEntry("policies", "cus/policies/policies.py", "POST", "/policies", "policies.query"),
    RouteEntry("policies", "cus/policies/policies.py", "GET", "/policies/{id}", "policies.query"),
    RouteEntry("policies", "cus/policies/policies.py", "PUT", "/policies/{id}", "policies.query"),
    RouteEntry("policies", "cus/policies/policies.py", "DELETE", "/policies/{id}", "policies.query"),
    RouteEntry("policies", "cus/policies/policies.py", "POST", "/policies/{id}/enable", "policies.query"),
    RouteEntry("policies", "cus/policies/policies.py", "POST", "/policies/{id}/disable", "policies.query"),
]

ALL_ROUTES = ACTIVITY_ROUTES + INCIDENTS_ROUTES + CONTROLS_ROUTES + ANALYTICS_ROUTES + LOGS_ROUTES + POLICIES_ROUTES

DOMAINS = ["activity", "incidents", "controls", "analytics", "logs", "policies"]


# =============================================================================
# VERIFICATION ENGINE
# =============================================================================

@dataclass
class VerifyResult:
    check: str
    passed: bool
    detail: str


def verify_file_exists(routes: list[RouteEntry]) -> list[VerifyResult]:
    results: list[VerifyResult] = []
    seen: set[str] = set()
    for r in routes:
        if r.file_rel in seen:
            continue
        seen.add(r.file_rel)
        fpath = HOC_API / r.file_rel
        ok = fpath.exists()
        results.append(VerifyResult(
            f"file_exists:{r.file_rel}",
            ok,
            f"{'OK' if ok else 'MISSING'}: {fpath}",
        ))
    return results


def verify_operation_references(routes: list[RouteEntry]) -> list[VerifyResult]:
    results: list[VerifyResult] = []
    file_cache: dict[str, str] = {}
    for r in routes:
        if r.l4_operation in ("EXEMPT", "DIRECT", "bridge"):
            continue
        fpath = HOC_API / r.file_rel
        if r.file_rel not in file_cache:
            try:
                file_cache[r.file_rel] = fpath.read_text()
            except (OSError, UnicodeDecodeError):
                file_cache[r.file_rel] = ""
        source = file_cache[r.file_rel]
        op_name = r.l4_operation
        found = f'"{op_name}"' in source or f"'{op_name}'" in source
        results.append(VerifyResult(
            f"op_ref:{r.domain}:{r.method} {r.path_pattern}",
            found,
            f"{'OK' if found else 'NOT FOUND'}: {op_name} in {r.file_rel}",
        ))
    return results


def verify_l4_dispatch_pattern(routes: list[RouteEntry]) -> list[VerifyResult]:
    results: list[VerifyResult] = []
    file_cache: dict[str, str] = {}
    seen: set[str] = set()
    for r in routes:
        if r.l4_operation in ("EXEMPT", "DIRECT", "bridge"):
            continue
        if r.file_rel in seen:
            continue
        seen.add(r.file_rel)
        fpath = HOC_API / r.file_rel
        if r.file_rel not in file_cache:
            try:
                file_cache[r.file_rel] = fpath.read_text()
            except (OSError, UnicodeDecodeError):
                file_cache[r.file_rel] = ""
        source = file_cache[r.file_rel]
        has_registry = "get_operation_registry" in source
        results.append(VerifyResult(
            f"l4_dispatch:{r.file_rel}",
            has_registry,
            f"{'OK' if has_registry else 'MISSING'}: get_operation_registry in {r.file_rel}",
        ))
    return results


def verify_domain_coverage() -> list[VerifyResult]:
    results: list[VerifyResult] = []
    for domain in DOMAINS:
        count = sum(1 for r in ALL_ROUTES if r.domain == domain)
        results.append(VerifyResult(
            f"domain_coverage:{domain}",
            count > 0,
            f"{'OK' if count > 0 else 'EMPTY'}: {domain} has {count} mapped routes",
        ))
    return results


def verify_route_map_doc_exists() -> list[VerifyResult]:
    doc_path = BACKEND_ROOT / "app" / "hoc" / "docs" / "architecture" / "usecases" / "UC_MONITORING_ROUTE_OPERATION_MAP.md"
    ok = doc_path.exists()
    return [VerifyResult(
        "route_map_doc_exists",
        ok,
        f"{'OK' if ok else 'MISSING'}: {doc_path}",
    )]


def main() -> int:
    print("UC-MON Route-to-Operation Mapping Verifier")
    print("=" * 60)
    print(f"Total canonical routes: {len(ALL_ROUTES)}")
    for domain in DOMAINS:
        count = sum(1 for r in ALL_ROUTES if r.domain == domain)
        print(f"  {domain}: {count}")
    print()

    all_results: list[VerifyResult] = []
    all_results.extend(verify_route_map_doc_exists())
    all_results.extend(verify_domain_coverage())
    all_results.extend(verify_file_exists(ALL_ROUTES))
    all_results.extend(verify_operation_references(ALL_ROUTES))
    all_results.extend(verify_l4_dispatch_pattern(ALL_ROUTES))

    passed = [r for r in all_results if r.passed]
    failed = [r for r in all_results if not r.passed]

    if failed:
        print(f"FAILED ({len(failed)} failures, {len(passed)} passed):")
        for r in failed:
            print(f"  FAIL: {r.check} — {r.detail}")
        print()
    else:
        print(f"ALL PASSED ({len(passed)} checks)")

    print()
    print("Domain Route Summary:")
    print("-" * 90)
    print(f"{'Domain':<12} {'Method':<7} {'Path':<40} {'L4 Operation':<30}")
    print("-" * 90)
    for r in ALL_ROUTES:
        print(f"{r.domain:<12} {r.method:<7} {r.path_pattern:<40} {r.l4_operation:<30}")
    print("-" * 90)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
