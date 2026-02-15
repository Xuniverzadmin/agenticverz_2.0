#!/usr/bin/env python3
# Layer: L0 — CI/Verification
# AUDIENCE: INTERNAL
# Role: Verify UC-MON event schema contract compliance
# Product: system-wide
# Temporal:
#   Trigger: CI / manual
#   Execution: sync
# Callers: CI, manual verification, uc_mon_validation.py
# Reference: UC-MON Monitoring, UC_MONITORING_IMPLEMENTATION_METHODS.md
# artifact_class: CODE

"""
UC-MON Event Contract Verifier

Verifies:
1. Base event schema contract module exists and has required exports.
2. Domain extension field definitions are documented.
3. Known authoritative emitters reference the contract.
4. Domain extension field schemas are structurally consistent.

Exit codes:
  0 = all checks pass
  1 = one or more checks failed
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


# =============================================================================
# UC-MON DOMAIN EXTENSION FIELD DEFINITIONS
# =============================================================================

# Required domain extension fields per UC-MON event category.
# These are checked against the route map doc and implementation methods doc.

DOMAIN_EXTENSION_FIELDS: dict[str, list[str]] = {
    "activity_feedback": [
        "signal_id", "feedback_state", "as_of", "ttl_seconds", "expires_at",
    ],
    "incident_lifecycle": [
        "incident_id", "incident_state",
    ],
    "controls_evaluation": [
        "run_id", "control_set_version", "resolver_version", "decision",
    ],
    "analytics_dataset": [
        "dataset_id", "dataset_version", "input_window_hash", "as_of", "compute_code_version",
    ],
    "logs_replay": [
        "run_id", "replay_attempt_id", "replay_mode", "replay_artifact_version",
    ],
}


def check_base_contract_module() -> list[CheckResult]:
    results: list[CheckResult] = []
    contract = BACKEND_ROOT / "app" / "hoc" / "cus" / "hoc_spine" / "authority" / "event_schema_contract.py"
    ok = contract.exists()
    results.append(CheckResult("event.base_contract_file", ok, f"{'exists' if ok else 'MISSING'}: {contract}"))
    if not ok:
        return results

    txt = read_text(contract)
    required_exports = [
        "REQUIRED_EVENT_FIELDS",
        "VALID_ACTOR_TYPES",
        "CURRENT_SCHEMA_VERSION",
        "EventSchemaViolation",
        "validate_event_payload",
        "is_valid_event_payload",
    ]
    for token in required_exports:
        found = token in txt
        results.append(CheckResult(
            f"event.base_export.{token}",
            found,
            f"{'present' if found else 'MISSING'} in event_schema_contract.py",
        ))

    # Check 9 required base fields
    base_fields = [
        "event_id", "event_type", "tenant_id", "project_id",
        "actor_type", "actor_id", "decision_owner", "sequence_no", "schema_version",
    ]
    for field_name in base_fields:
        found = f'"{field_name}"' in txt or f"'{field_name}'" in txt
        results.append(CheckResult(
            f"event.base_field.{field_name}",
            found,
            f"{'present' if found else 'MISSING'} in REQUIRED_EVENT_FIELDS",
        ))
    return results


def check_domain_extension_definitions() -> list[CheckResult]:
    """Verify domain extension field lists are documented in the methods doc."""
    results: list[CheckResult] = []
    methods_doc = BACKEND_ROOT / "app" / "hoc" / "docs" / "architecture" / "usecases" / "UC_MONITORING_IMPLEMENTATION_METHODS.md"
    if not methods_doc.exists():
        results.append(CheckResult("event.methods_doc", False, f"MISSING: {methods_doc}"))
        return results

    txt = read_text(methods_doc)
    for category, fields in DOMAIN_EXTENSION_FIELDS.items():
        for field_name in fields:
            found = field_name in txt
            results.append(CheckResult(
                f"event.extension.{category}.{field_name}",
                found,
                f"{'documented' if found else 'NOT FOUND'} in methods doc",
            ))
    return results


def check_known_emitters() -> list[CheckResult]:
    """Verify known authoritative emitters reference event_schema_contract."""
    results: list[CheckResult] = []
    known_emitters = [
        BACKEND_ROOT / "app" / "hoc" / "cus" / "hoc_spine" / "authority" / "lifecycle_provider.py",
        BACKEND_ROOT / "app" / "hoc" / "cus" / "hoc_spine" / "authority" / "runtime_switch.py",
        BACKEND_ROOT / "app" / "hoc" / "cus" / "hoc_spine" / "orchestrator" / "handlers" / "onboarding_handler.py",
        BACKEND_ROOT / "app" / "hoc" / "cus" / "hoc_spine" / "orchestrator" / "handlers" / "activity_handler.py",
        BACKEND_ROOT / "app" / "hoc" / "cus" / "hoc_spine" / "orchestrator" / "handlers" / "controls_handler.py",
        BACKEND_ROOT / "app" / "hoc" / "cus" / "hoc_spine" / "orchestrator" / "handlers" / "incidents_handler.py",
        BACKEND_ROOT / "app" / "hoc" / "cus" / "hoc_spine" / "orchestrator" / "handlers" / "analytics_handler.py",
    ]
    for emitter_file in known_emitters:
        if not emitter_file.exists():
            results.append(CheckResult(
                f"event.emitter.{emitter_file.name}",
                False,
                f"MISSING: {emitter_file}",
            ))
            continue
        txt = read_text(emitter_file)
        has_contract = "event_schema_contract" in txt or "validate_event_payload" in txt
        results.append(CheckResult(
            f"event.emitter.{emitter_file.name}",
            has_contract,
            f"{'references contract' if has_contract else 'NO contract reference'} in {emitter_file.name}",
        ))
    return results


def check_replay_mode_contract() -> list[CheckResult]:
    """Check replay mode determinism: replay_mode values must be FULL or TRACE_ONLY."""
    results: list[CheckResult] = []

    # Check migration defines replay_mode column
    migration = BACKEND_ROOT / "alembic" / "versions" / "132_monitoring_logs_replay_mode_fields.py"
    if not migration.exists():
        results.append(CheckResult("event.replay.migration", False, f"MISSING: {migration}"))
        return results

    txt = read_text(migration)
    has_replay_mode = "replay_mode" in txt
    has_replay_attempt = "replay_attempt_id" in txt
    has_replay_version = "replay_artifact_version" in txt
    results.append(CheckResult("event.replay.replay_mode_col", has_replay_mode, "replay_mode column in migration"))
    results.append(CheckResult("event.replay.replay_attempt_id_col", has_replay_attempt, "replay_attempt_id column in migration"))
    results.append(CheckResult("event.replay.replay_artifact_version_col", has_replay_version, "replay_artifact_version column in migration"))

    # Check methods doc documents FULL|TRACE_ONLY
    methods_doc = BACKEND_ROOT / "app" / "hoc" / "docs" / "architecture" / "usecases" / "UC_MONITORING_IMPLEMENTATION_METHODS.md"
    if methods_doc.exists():
        mtxt = read_text(methods_doc)
        has_modes = "FULL" in mtxt and "TRACE_ONLY" in mtxt
        results.append(CheckResult("event.replay.modes_documented", has_modes, "FULL|TRACE_ONLY documented in methods doc"))

    # Check runtime wiring: pg_store.py writes replay columns
    pg_store = BACKEND_ROOT / "app" / "hoc" / "cus" / "logs" / "L6_drivers" / "pg_store.py"
    if pg_store.exists():
        ptxt = read_text(pg_store)
        has_rm_write = "replay_mode" in ptxt and "replay_attempt_id" in ptxt and "replay_artifact_version" in ptxt
        results.append(CheckResult(
            "event.replay.l6_driver_wired",
            has_rm_write,
            f"{'replay columns wired' if has_rm_write else 'replay columns NOT wired'} in pg_store.py",
        ))

    # Check L5 engine forwards replay params
    trace_engine = BACKEND_ROOT / "app" / "hoc" / "cus" / "logs" / "L5_engines" / "trace_api_engine.py"
    if trace_engine.exists():
        etxt = read_text(trace_engine)
        has_rm_fwd = "replay_mode" in etxt
        results.append(CheckResult(
            "event.replay.l5_engine_wired",
            has_rm_fwd,
            f"{'replay_mode forwarded' if has_rm_fwd else 'replay_mode NOT forwarded'} in trace_api_engine.py",
        ))

    return results


def check_reproducibility_contract() -> list[CheckResult]:
    """Check analytics reproducibility: dataset_version + input_window_hash + compute_code_version."""
    results: list[CheckResult] = []

    migration = BACKEND_ROOT / "alembic" / "versions" / "131_monitoring_analytics_reproducibility_fields.py"
    if not migration.exists():
        results.append(CheckResult("event.reproducibility.migration", False, f"MISSING: {migration}"))
        return results

    txt = read_text(migration)
    required_cols = ["dataset_version", "input_window_hash", "compute_code_version"]
    for col in required_cols:
        found = col in txt
        results.append(CheckResult(
            f"event.reproducibility.{col}",
            found,
            f"{'present' if found else 'MISSING'} in migration 131",
        ))
    return results


def check_incident_lifecycle_events() -> list[CheckResult]:
    """Check incident handler emits lifecycle events with correct extension fields."""
    results: list[CheckResult] = []
    handler = BACKEND_ROOT / "app" / "hoc" / "cus" / "hoc_spine" / "orchestrator" / "handlers" / "incidents_handler.py"
    if not handler.exists():
        results.append(CheckResult("event.incident.handler_exists", False, "incidents_handler.py missing"))
        return results
    txt = read_text(handler)
    # Check emitter helper exists
    has_emitter = "_emit_incident_event" in txt
    results.append(CheckResult(
        "event.incident.emitter_helper",
        has_emitter,
        f"{'present' if has_emitter else 'MISSING'}: _emit_incident_event helper",
    ))
    # Check event types
    event_types = ["IncidentAcknowledged", "IncidentResolved", "IncidentManuallyClosed"]
    for evt in event_types:
        found = evt in txt
        results.append(CheckResult(
            f"event.incident.type.{evt}",
            found,
            f"{'emitted' if found else 'NOT EMITTED'}: incidents.{evt}",
        ))
    # Check extension fields
    for field in ["incident_id", "incident_state"]:
        found = f'"{field}"' in txt or f"'{field}'" in txt
        results.append(CheckResult(
            f"event.incident.field.{field}",
            found,
            f"{'present' if found else 'MISSING'}: {field} in incident events",
        ))
    return results


def check_analytics_artifact_events() -> list[CheckResult]:
    """Check analytics handler emits artifact events with reproducibility fields."""
    results: list[CheckResult] = []
    handler = BACKEND_ROOT / "app" / "hoc" / "cus" / "hoc_spine" / "orchestrator" / "handlers" / "analytics_handler.py"
    if not handler.exists():
        results.append(CheckResult("event.analytics.handler_exists", False, "analytics_handler.py missing"))
        return results
    txt = read_text(handler)
    # Check emitter helper exists
    has_emitter = "_emit_analytics_event" in txt
    results.append(CheckResult(
        "event.analytics.emitter_helper",
        has_emitter,
        f"{'present' if has_emitter else 'MISSING'}: _emit_analytics_event helper",
    ))
    # Check event type
    has_artifact_event = "ArtifactRecorded" in txt
    results.append(CheckResult(
        "event.analytics.type.ArtifactRecorded",
        has_artifact_event,
        f"{'emitted' if has_artifact_event else 'NOT EMITTED'}: analytics.ArtifactRecorded",
    ))
    # Check reproducibility extension fields
    for field in ["dataset_id", "dataset_version", "input_window_hash", "compute_code_version"]:
        found = f'"{field}"' in txt or f"'{field}'" in txt
        results.append(CheckResult(
            f"event.analytics.field.{field}",
            found,
            f"{'present' if found else 'MISSING'}: {field} in analytics events",
        ))
    return results


def main() -> int:
    print("UC-MON Event Contract Verifier")
    print("=" * 50)

    all_results: list[CheckResult] = []
    all_results.extend(check_base_contract_module())
    all_results.extend(check_domain_extension_definitions())
    all_results.extend(check_known_emitters())
    all_results.extend(check_replay_mode_contract())
    all_results.extend(check_reproducibility_contract())
    all_results.extend(check_incident_lifecycle_events())
    all_results.extend(check_analytics_artifact_events())

    passed = sum(1 for r in all_results if r.passed)
    failed = sum(1 for r in all_results if not r.passed)

    for r in all_results:
        mark = "PASS" if r.passed else "FAIL"
        print(f"[{mark}] {r.name} :: {r.detail}")
    print("-" * 50)
    print(f"Total: {len(all_results)} | PASS: {passed} | FAIL: {failed}")

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
