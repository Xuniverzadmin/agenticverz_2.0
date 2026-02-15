#!/usr/bin/env python3
# Layer: L0 — CI/Verification
# AUDIENCE: INTERNAL
# Role: Verify UC-MON storage contract (migrations, table fields)
# Product: system-wide
# Temporal:
#   Trigger: CI / manual
#   Execution: sync
# Callers: CI, manual verification, uc_mon_validation.py
# Reference: UC-MON Monitoring, UC_MONITORING_IMPLEMENTATION_METHODS.md
# artifact_class: CODE

"""
UC-MON Storage Contract Verifier

Verifies:
1. All 5 UC-MON migrations exist (128-132).
2. Each migration has correct revision chain.
3. Required columns/tables are defined in each migration.
4. Migration chain is contiguous (no gaps).

Exit codes:
  0 = all checks pass
  1 = one or more checks failed
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
VERSIONS_DIR = BACKEND_ROOT / "alembic" / "versions"


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
# MIGRATION DEFINITIONS
# =============================================================================

MIGRATIONS = [
    {
        "file": "128_monitoring_activity_feedback_contracts.py",
        "prev": "127_create_sdk_attestations",
        "required_tokens": [
            "signal_feedback",
            "ttl_seconds",
            "expires_at",
            "bulk_action_id",
            "target_set_hash",
            "target_count",
            "feedback_state",
            "as_of",
            "signal_fingerprint",
        ],
        "table_action": "create_table",
    },
    {
        "file": "129_monitoring_incident_resolution_recurrence.py",
        "prev": "128_monitoring_activity_feedback_contracts",
        "required_tokens": [
            "incidents",
            "resolution_type",
            "resolution_summary",
            "postmortem_artifact_id",
            "recurrence_signature",
            "signature_version",
        ],
        "table_action": "add_column",
    },
    {
        "file": "130_monitoring_controls_binding_fields.py",
        "prev": "129_monitoring_incident_resolution_recurrence",
        "required_tokens": [
            "controls_evaluation_evidence",
            "control_set_version",
            "override_ids_applied",
            "resolver_version",
            "decision",
        ],
        "table_action": "create_table",
    },
    {
        "file": "131_monitoring_analytics_reproducibility_fields.py",
        "prev": "130_monitoring_controls_binding_fields",
        "required_tokens": [
            "analytics_artifacts",
            "dataset_version",
            "input_window_hash",
            "compute_code_version",
        ],
        "table_action": "create_table",
    },
    {
        "file": "132_monitoring_logs_replay_mode_fields.py",
        "prev": "131_monitoring_analytics_reproducibility_fields",
        "required_tokens": [
            "aos_traces",
            "replay_mode",
            "replay_attempt_id",
            "replay_artifact_version",
            "trace_completeness_status",
        ],
        "table_action": "add_column",
    },
]


def check_migration_exists() -> list[CheckResult]:
    results: list[CheckResult] = []
    for mig in MIGRATIONS:
        path = VERSIONS_DIR / mig["file"]
        ok = path.exists()
        results.append(CheckResult(
            f"storage.migration_exists.{mig['file']}",
            ok,
            f"{'exists' if ok else 'MISSING'}: {path}",
        ))
    return results


def check_revision_chain() -> list[CheckResult]:
    results: list[CheckResult] = []
    for mig in MIGRATIONS:
        path = VERSIONS_DIR / mig["file"]
        if not path.exists():
            results.append(CheckResult(
                f"storage.revision_chain.{mig['file']}",
                False,
                f"SKIP (file missing): {path}",
            ))
            continue
        txt = read_text(path)
        prev = mig["prev"]
        has_prev = f'down_revision = "{prev}"' in txt
        results.append(CheckResult(
            f"storage.revision_chain.{mig['file']}",
            has_prev,
            f"{'OK' if has_prev else 'WRONG'}: down_revision should be {prev}",
        ))
    return results


def check_required_tokens() -> list[CheckResult]:
    results: list[CheckResult] = []
    for mig in MIGRATIONS:
        path = VERSIONS_DIR / mig["file"]
        if not path.exists():
            continue
        txt = read_text(path)
        for token in mig["required_tokens"]:
            found = token in txt
            results.append(CheckResult(
                f"storage.field.{mig['file']}.{token}",
                found,
                f"{'present' if found else 'MISSING'}: {token} in {mig['file']}",
            ))
    return results


def check_table_actions() -> list[CheckResult]:
    results: list[CheckResult] = []
    for mig in MIGRATIONS:
        path = VERSIONS_DIR / mig["file"]
        if not path.exists():
            continue
        txt = read_text(path)
        action = mig["table_action"]
        has_action = action in txt
        results.append(CheckResult(
            f"storage.action.{mig['file']}",
            has_action,
            f"{'OK' if has_action else 'MISSING'}: {action} in {mig['file']}",
        ))
    return results


def check_upgrade_downgrade_symmetry() -> list[CheckResult]:
    results: list[CheckResult] = []
    for mig in MIGRATIONS:
        path = VERSIONS_DIR / mig["file"]
        if not path.exists():
            continue
        txt = read_text(path)
        has_upgrade = "def upgrade()" in txt
        has_downgrade = "def downgrade()" in txt
        results.append(CheckResult(
            f"storage.symmetry.{mig['file']}",
            has_upgrade and has_downgrade,
            f"upgrade={'OK' if has_upgrade else 'MISSING'}, downgrade={'OK' if has_downgrade else 'MISSING'}",
        ))
    return results


def check_as_of_in_feedback_migration() -> list[CheckResult]:
    """Determinism check A: as_of column exists in signal_feedback table."""
    results: list[CheckResult] = []
    path = VERSIONS_DIR / "128_monitoring_activity_feedback_contracts.py"
    if not path.exists():
        results.append(CheckResult("storage.determinism.as_of_feedback", False, "migration 128 missing"))
        return results
    txt = read_text(path)
    has_as_of = '"as_of"' in txt and "DateTime" in txt
    results.append(CheckResult(
        "storage.determinism.as_of_feedback",
        has_as_of,
        f"{'OK' if has_as_of else 'MISSING'}: as_of DateTime column in signal_feedback",
    ))
    return results


def check_ttl_determinism_fields() -> list[CheckResult]:
    """Determinism check B: TTL/expiry fields exist for feedback."""
    results: list[CheckResult] = []
    path = VERSIONS_DIR / "128_monitoring_activity_feedback_contracts.py"
    if not path.exists():
        results.append(CheckResult("storage.determinism.ttl_fields", False, "migration 128 missing"))
        return results
    txt = read_text(path)
    has_ttl = "ttl_seconds" in txt
    has_expires = "expires_at" in txt
    ok = has_ttl and has_expires
    results.append(CheckResult(
        "storage.determinism.ttl_fields",
        ok,
        f"ttl_seconds={'OK' if has_ttl else 'MISSING'}, expires_at={'OK' if has_expires else 'MISSING'}",
    ))
    return results


def check_replay_determinism_fields() -> list[CheckResult]:
    """Determinism check C: Replay mode fields exist."""
    results: list[CheckResult] = []
    path = VERSIONS_DIR / "132_monitoring_logs_replay_mode_fields.py"
    if not path.exists():
        results.append(CheckResult("storage.determinism.replay_fields", False, "migration 132 missing"))
        return results
    txt = read_text(path)
    required = ["replay_mode", "replay_attempt_id", "replay_artifact_version"]
    all_ok = all(f in txt for f in required)
    results.append(CheckResult(
        "storage.determinism.replay_fields",
        all_ok,
        f"{'ALL PRESENT' if all_ok else 'INCOMPLETE'}: {', '.join(required)}",
    ))
    return results


def check_reproducibility_fields() -> list[CheckResult]:
    """Determinism check D: Reproducibility fields exist."""
    results: list[CheckResult] = []
    path = VERSIONS_DIR / "131_monitoring_analytics_reproducibility_fields.py"
    if not path.exists():
        results.append(CheckResult("storage.determinism.reproducibility_fields", False, "migration 131 missing"))
        return results
    txt = read_text(path)
    required = ["dataset_version", "input_window_hash", "compute_code_version"]
    all_ok = all(f in txt for f in required)
    results.append(CheckResult(
        "storage.determinism.reproducibility_fields",
        all_ok,
        f"{'ALL PRESENT' if all_ok else 'INCOMPLETE'}: {', '.join(required)}",
    ))
    return results


def check_replay_runtime_wiring() -> list[CheckResult]:
    """Determinism check E: Replay columns are wired in L6 driver INSERT/SELECT."""
    results: list[CheckResult] = []
    pg_store = BACKEND_ROOT / "app" / "hoc" / "cus" / "logs" / "L6_drivers" / "pg_store.py"
    if not pg_store.exists():
        results.append(CheckResult("storage.replay_wiring.pg_store", False, "pg_store.py missing"))
        return results
    txt = read_text(pg_store)
    # Check INSERT writes replay columns
    replay_cols_in_insert = all(col in txt for col in [
        "replay_mode", "replay_attempt_id", "replay_artifact_version", "trace_completeness_status",
    ])
    results.append(CheckResult(
        "storage.replay_wiring.insert",
        replay_cols_in_insert,
        f"{'ALL replay columns in INSERT' if replay_cols_in_insert else 'replay columns MISSING from INSERT'}",
    ))
    # Check SELECT reads replay columns
    replay_in_get = "replay_mode" in txt and "replay_attempt_id" in txt
    results.append(CheckResult(
        "storage.replay_wiring.select",
        replay_in_get,
        f"{'replay columns readable' if replay_in_get else 'replay columns NOT readable'}",
    ))
    return results


def check_feedback_l6_wiring() -> list[CheckResult]:
    """Check signal_feedback L6 driver exists and has required operations."""
    results: list[CheckResult] = []
    driver = BACKEND_ROOT / "app" / "hoc" / "cus" / "activity" / "L6_drivers" / "signal_feedback_driver.py"
    if not driver.exists():
        results.append(CheckResult("storage.feedback_driver.exists", False, "signal_feedback_driver.py missing"))
        return results
    txt = read_text(driver)
    required_ops = ["insert_feedback", "query_feedback", "mark_expired_as_evaluated"]
    for op in required_ops:
        found = op in txt
        results.append(CheckResult(
            f"storage.feedback_driver.{op}",
            found,
            f"{'present' if found else 'MISSING'} in signal_feedback_driver.py",
        ))
    return results


def check_evaluation_evidence_l6_wiring() -> list[CheckResult]:
    """Check controls evaluation evidence L6 driver exists and has required operations."""
    results: list[CheckResult] = []
    driver = BACKEND_ROOT / "app" / "hoc" / "cus" / "controls" / "L6_drivers" / "evaluation_evidence_driver.py"
    if not driver.exists():
        results.append(CheckResult("storage.eval_evidence_driver.exists", False, "evaluation_evidence_driver.py missing"))
        return results
    txt = read_text(driver)
    required_ops = ["record_evidence", "query_evidence"]
    for op in required_ops:
        found = op in txt
        results.append(CheckResult(
            f"storage.eval_evidence_driver.{op}",
            found,
            f"{'present' if found else 'MISSING'} in evaluation_evidence_driver.py",
        ))
    # Check version binding fields are referenced
    binding_fields = ["control_set_version", "override_ids_applied", "resolver_version", "decision"]
    for field in binding_fields:
        found = field in txt
        results.append(CheckResult(
            f"storage.eval_evidence_driver.field.{field}",
            found,
            f"{'present' if found else 'MISSING'} in evaluation_evidence_driver.py",
        ))
    return results


def check_incident_resolution_l6_wiring() -> list[CheckResult]:
    """Check incident write driver has resolution lifecycle fields (migration 129)."""
    results: list[CheckResult] = []
    driver = BACKEND_ROOT / "app" / "hoc" / "cus" / "incidents" / "L6_drivers" / "incident_write_driver.py"
    if not driver.exists():
        results.append(CheckResult("storage.incident_driver.exists", False, "incident_write_driver.py missing"))
        return results
    txt = read_text(driver)
    # Resolution fields
    resolution_fields = ["resolution_type", "resolution_summary", "postmortem_artifact_id"]
    for field in resolution_fields:
        found = field in txt
        results.append(CheckResult(
            f"storage.incident_driver.field.{field}",
            found,
            f"{'present' if found else 'MISSING'} in incident_write_driver.py",
        ))
    # Recurrence fields
    recurrence_fields = ["recurrence_signature", "signature_version"]
    for field in recurrence_fields:
        found = field in txt
        results.append(CheckResult(
            f"storage.incident_driver.field.{field}",
            found,
            f"{'present' if found else 'MISSING'} in incident_write_driver.py",
        ))
    # Recurrence group query
    has_recurrence_query = "fetch_recurrence_group" in txt
    results.append(CheckResult(
        "storage.incident_driver.recurrence_query",
        has_recurrence_query,
        f"{'present' if has_recurrence_query else 'MISSING'}: fetch_recurrence_group",
    ))
    # Postmortem stub
    has_postmortem = "create_postmortem_stub" in txt
    results.append(CheckResult(
        "storage.incident_driver.postmortem_stub",
        has_postmortem,
        f"{'present' if has_postmortem else 'MISSING'}: create_postmortem_stub",
    ))
    return results


def check_analytics_artifacts_l6_wiring() -> list[CheckResult]:
    """Check analytics artifacts L6 driver exists and has required operations."""
    results: list[CheckResult] = []
    driver = BACKEND_ROOT / "app" / "hoc" / "cus" / "analytics" / "L6_drivers" / "analytics_artifacts_driver.py"
    if not driver.exists():
        results.append(CheckResult("storage.analytics_artifacts_driver.exists", False, "analytics_artifacts_driver.py missing"))
        return results
    txt = read_text(driver)
    required_ops = ["save_artifact", "get_artifact", "list_artifacts"]
    for op in required_ops:
        found = op in txt
        results.append(CheckResult(
            f"storage.analytics_artifacts_driver.{op}",
            found,
            f"{'present' if found else 'MISSING'} in analytics_artifacts_driver.py",
        ))
    # Check reproducibility fields are referenced
    repro_fields = ["dataset_version", "input_window_hash", "compute_code_version", "as_of"]
    for field in repro_fields:
        found = field in txt
        results.append(CheckResult(
            f"storage.analytics_artifacts_driver.field.{field}",
            found,
            f"{'present' if found else 'MISSING'} in analytics_artifacts_driver.py",
        ))
    return results


def main() -> int:
    print("UC-MON Storage Contract Verifier")
    print("=" * 50)

    all_results: list[CheckResult] = []
    all_results.extend(check_migration_exists())
    all_results.extend(check_revision_chain())
    all_results.extend(check_required_tokens())
    all_results.extend(check_table_actions())
    all_results.extend(check_upgrade_downgrade_symmetry())
    all_results.extend(check_as_of_in_feedback_migration())
    all_results.extend(check_ttl_determinism_fields())
    all_results.extend(check_replay_determinism_fields())
    all_results.extend(check_reproducibility_fields())
    all_results.extend(check_replay_runtime_wiring())
    all_results.extend(check_feedback_l6_wiring())
    all_results.extend(check_evaluation_evidence_l6_wiring())
    all_results.extend(check_incident_resolution_l6_wiring())
    all_results.extend(check_analytics_artifacts_l6_wiring())

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
