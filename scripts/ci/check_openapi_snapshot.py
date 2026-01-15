#!/usr/bin/env python3
"""
CI Guard: OpenAPI Snapshot Validity

Fails build if:
  - backend/.openapi_snapshot.json missing
  - file size == 0
  - JSON invalid
  - "paths" empty

This prevents regressions when:
  - someone deletes the snapshot
  - someone forgets to refresh after API changes
  - someone reintroduces live introspection

Usage:
    python scripts/ci/check_openapi_snapshot.py

Exit codes:
    0 = snapshot valid
    1 = snapshot missing or invalid

Reference: HISAR Phase 0 contract
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
SNAPSHOT_PATH = REPO_ROOT / "backend" / ".openapi_snapshot.json"


def main() -> int:
    print("=" * 60)
    print("CI GUARD: OpenAPI Snapshot Validity")
    print("=" * 60)
    print()

    # Check 1: File exists
    if not SNAPSHOT_PATH.exists():
        print(f"FAIL: OpenAPI snapshot missing")
        print(f"      File: {SNAPSHOT_PATH}")
        print(f"      Run:  ./scripts/tools/hisar_snapshot_backend.sh")
        return 1
    print(f"  [1/4] File exists: {SNAPSHOT_PATH.name}")

    # Check 2: File non-empty
    file_size = SNAPSHOT_PATH.stat().st_size
    if file_size == 0:
        print(f"FAIL: OpenAPI snapshot is empty (0 bytes)")
        print(f"      File: {SNAPSHOT_PATH}")
        print(f"      Run:  ./scripts/tools/hisar_snapshot_backend.sh")
        return 1
    print(f"  [2/4] File non-empty: {file_size:,} bytes")

    # Check 3: Valid JSON
    try:
        with open(SNAPSHOT_PATH) as f:
            spec = json.load(f)
    except json.JSONDecodeError as e:
        print(f"FAIL: OpenAPI snapshot is invalid JSON")
        print(f"      Error: {e}")
        print(f"      Run:  ./scripts/tools/hisar_snapshot_backend.sh")
        return 1
    print(f"  [3/4] Valid JSON")

    # Check 4: Has paths
    paths = spec.get("paths", {})
    if not isinstance(paths, dict) or len(paths) == 0:
        print(f"FAIL: OpenAPI snapshot has no paths")
        print(f"      This indicates a corrupt or incomplete snapshot")
        print(f"      Run:  ./scripts/tools/hisar_snapshot_backend.sh")
        return 1
    print(f"  [4/4] Has paths: {len(paths)} routes")

    print()
    print("=" * 60)
    print("PASS: OpenAPI snapshot is valid")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
