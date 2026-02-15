#!/usr/bin/env python3
"""UC Operation Manifest Validator (Workstream B1)

Validates the UC Operation Manifest JSON against structural, referential,
and file-existence constraints.

Usage:
    PYTHONPATH=. python3 scripts/verification/uc_operation_manifest_check.py
    PYTHONPATH=. python3 scripts/verification/uc_operation_manifest_check.py --strict
"""
import json
import os
import sys

MANIFEST_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../app/hoc/docs/architecture/usecases/UC_OPERATION_MANIFEST_2026-02-15.json",
)
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
VALID_UC_IDS = {f"UC-{i:03d}" for i in range(1, 41)} | {"HOLD"}
REQUIRED_FIELDS = [
    "uc_id",
    "operation_name",
    "handler_file",
    "engine_or_driver_files",
    "decision_type",
]


def load_manifest():
    """Load and parse the manifest JSON. Returns (entries, error_message)."""
    resolved = os.path.abspath(MANIFEST_PATH)
    if not os.path.isfile(resolved):
        return None, f"Manifest file not found: {resolved}"
    try:
        with open(resolved, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        return None, f"Manifest is not valid JSON: {exc}"
    if not isinstance(data, list):
        return None, "Manifest root must be a JSON array"
    return data, None


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def check_required_fields(entries):
    """Every entry must contain all REQUIRED_FIELDS."""
    failures = []
    for idx, entry in enumerate(entries):
        missing = [f for f in REQUIRED_FIELDS if f not in entry]
        if missing:
            op = entry.get("operation_name", f"<entry #{idx}>")
            failures.append(f"  Entry '{op}' missing fields: {missing}")
    return failures


def check_assign_test_refs(entries):
    """ASSIGN entries must have a non-empty test_refs list."""
    failures = []
    for entry in entries:
        if entry.get("decision_type") != "ASSIGN":
            continue
        test_refs = entry.get("test_refs")
        if not test_refs or (isinstance(test_refs, list) and len(test_refs) == 0):
            failures.append(
                f"  ASSIGN entry '{entry.get('operation_name')}' has empty or missing test_refs"
            )
    return failures


def check_valid_uc_ids(entries):
    """All uc_id values must be in VALID_UC_IDS."""
    failures = []
    for entry in entries:
        uc_id = entry.get("uc_id")
        if uc_id is None:
            continue  # caught by required-fields check
        if uc_id not in VALID_UC_IDS:
            failures.append(
                f"  Entry '{entry.get('operation_name')}' has unknown uc_id: {uc_id}"
            )
    return failures


def check_no_duplicate_conflicts(entries):
    """Same operation_name mapped to different uc_ids requires SPLIT decision_type."""
    op_map = {}  # operation_name -> list of (uc_id, decision_type)
    for entry in entries:
        op = entry.get("operation_name")
        if op is None:
            continue
        op_map.setdefault(op, []).append(
            (entry.get("uc_id"), entry.get("decision_type"))
        )

    failures = []
    for op, mappings in op_map.items():
        uc_ids = {m[0] for m in mappings}
        if len(uc_ids) <= 1:
            continue
        # Multiple different uc_ids for the same operation — all must be SPLIT
        non_split = [m for m in mappings if m[1] != "SPLIT"]
        if non_split:
            failures.append(
                f"  Operation '{op}' mapped to multiple uc_ids {sorted(uc_ids)} "
                f"without SPLIT decision on all entries"
            )
    return failures


def check_handler_files_exist(entries):
    """Each handler_file must exist on disk under BACKEND_ROOT."""
    failures = []
    checked = set()
    for entry in entries:
        handler = entry.get("handler_file")
        if not handler or handler in checked:
            continue
        checked.add(handler)
        full_path = os.path.join(BACKEND_ROOT, handler)
        if not os.path.isfile(full_path):
            failures.append(f"  handler_file not found: {handler}")
    return failures


def check_hold_status_strict(entries):
    """(--strict) HOLD entries must include a hold_status field."""
    failures = []
    for entry in entries:
        if entry.get("uc_id") != "HOLD":
            continue
        if not entry.get("hold_status"):
            failures.append(
                f"  HOLD entry '{entry.get('operation_name')}' missing hold_status"
            )
    return failures


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def main():
    strict = "--strict" in sys.argv

    entries, err = load_manifest()
    if err or entries is None:
        print(f"FAIL  manifest_load — {err}")
        sys.exit(1)

    print(f"Loaded manifest: {len(entries)} entries")
    print()

    checks = [
        ("required_fields", check_required_fields),
        ("assign_test_refs", check_assign_test_refs),
        ("valid_uc_ids", check_valid_uc_ids),
        ("no_duplicate_conflicts", check_no_duplicate_conflicts),
        ("handler_files_exist", check_handler_files_exist),
    ]
    if strict:
        checks.append(("hold_status_present", check_hold_status_strict))

    total_pass = 0
    total_fail = 0

    for name, fn in checks:
        failures = fn(entries)
        if failures:
            print(f"FAIL  {name} ({len(failures)} issue(s))")
            for f in failures:
                print(f)
            total_fail += 1
        else:
            print(f"PASS  {name}")
            total_pass += 1

    print()
    print(f"Summary: {total_pass} passed, {total_fail} failed" +
          (" [strict]" if strict else ""))

    sys.exit(0 if total_fail == 0 else 1)


if __name__ == "__main__":
    main()
