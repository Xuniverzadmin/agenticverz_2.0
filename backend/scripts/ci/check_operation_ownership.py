#!/usr/bin/env python3
# Layer: L8 — CI Script
# AUDIENCE: INTERNAL
# Role: Architecture fitness — operation ownership map and boundary checks
# artifact_class: CODE

"""
Operation Ownership Checker (BA-20)

Scans L4 handler files and L5 engine files to build an operation ownership map.
Validates:
  1. Each operation maps to exactly one domain owner (no two domains claim
     the same operation name).
  2. Handler files only import from their declared domain's L5 engines
     (no cross-domain L5 imports outside the handler's owning domain).

Usage:
    PYTHONPATH=. python3 scripts/ci/check_operation_ownership.py
    PYTHONPATH=. python3 scripts/ci/check_operation_ownership.py --strict

Exit codes:
    0 — no conflicts or cross-domain import violations
    1 — ownership collision or cross-domain import violation detected
"""

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
HANDLERS_DIR = (
    BACKEND_ROOT
    / "app"
    / "hoc"
    / "cus"
    / "hoc_spine"
    / "orchestrator"
    / "handlers"
)
CUS_ROOT = BACKEND_ROOT / "app" / "hoc" / "cus"

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Matches: registry.register("domain.operation", ...)
REGISTER_RE = re.compile(
    r'registry\.register\(\s*"([a-zA-Z_][a-zA-Z0-9_.]*)"'
)

# Matches import lines like:
#   from app.hoc.cus.<domain>.L5_engines.<module> import ...
L5_IMPORT_RE = re.compile(
    r"from\s+app\.hoc\.cus\.([a-zA-Z_][a-zA-Z0-9_]*)\.L5_engines\b"
)

# Extract the domain that a handler file is *supposed* to own based on:
#   1. The handler file name (e.g. account_handler.py -> account)
#   2. The operations it registers (first segment before the dot)
HANDLER_FILENAME_RE = re.compile(r"^(.+?)_handler\.py$")

# ---------------------------------------------------------------------------
# Cross-domain L5 import allowlist
# ---------------------------------------------------------------------------
# L4 handlers are the single orchestrator (PIN-491) and may legitimately
# import from other domains' L5/L6 for cross-domain coordination.
# Each entry: (handler_filename, imported_domain) -> rationale
CROSS_DOMAIN_ALLOWLIST: dict[tuple[str, str], str] = {
    # API keys write operations route through TenantEngine (account domain)
    # because API key CRUD is part of the tenant lifecycle boundary.
    ("api_keys_handler.py", "account"): (
        "API key creation/revocation delegates to TenantEngine (account domain). "
        "L4 owns cross-domain coordination per PIN-491."
    ),
    # Incidents write handler injects AuditLedgerService (logs domain) into
    # IncidentWriteService as a dependency — PIN-504 DI pattern.
    ("incidents_handler.py", "logs"): (
        "L4 creates AuditLedgerService (logs domain) and injects into "
        "IncidentWriteService — PIN-504 dependency injection pattern."
    ),
    # Traces handler dispatches to trace_mismatch_engine and
    # trace_mismatch_driver, which live in the logs domain.
    # 'traces' is a sub-domain of 'logs' — the operation prefix 'traces.*'
    # routes to logs-domain engines by design.
    ("traces_handler.py", "logs"): (
        "Trace mismatch operations are a sub-domain of logs. The 'traces.*' "
        "operation prefix maps to logs/L5_engines/ and logs/L6_drivers/ by design."
    ),
}


def _is_comment_line(line: str) -> bool:
    """Return True if the line is a Python comment (ignoring leading whitespace)."""
    return line.lstrip().startswith("#")


def _extract_handler_domain_from_filename(filename: str) -> str | None:
    """
    Derive the owning domain from the handler filename.

    Examples:
        account_handler.py        -> account
        integrations_handler.py   -> integrations
        analytics_config_handler.py -> analytics  (prefix before first _handler)
    """
    m = HANDLER_FILENAME_RE.match(filename)
    if not m:
        return None
    raw = m.group(1)
    # Some handlers have multi-part names like analytics_config_handler.
    # The domain is the first segment (analytics).  But single-segment names
    # like "account" stay as-is.
    return raw


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------


def scan_handler_operations(
    handler_path: Path,
) -> list[tuple[str, int]]:
    """
    Return a list of (operation_name, line_number) tuples extracted from
    registry.register() calls in *handler_path*.
    """
    results: list[tuple[str, int]] = []
    try:
        lines = handler_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return results

    for lineno, line in enumerate(lines, start=1):
        if _is_comment_line(line):
            continue
        for m in REGISTER_RE.finditer(line):
            results.append((m.group(1), lineno))
    return results


def scan_handler_l5_imports(
    handler_path: Path,
) -> list[tuple[str, int]]:
    """
    Return a list of (imported_domain, line_number) for every L5_engines
    import found in *handler_path*.
    """
    results: list[tuple[str, int]] = []
    try:
        lines = handler_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return results

    for lineno, line in enumerate(lines, start=1):
        if _is_comment_line(line):
            continue
        for m in L5_IMPORT_RE.finditer(line):
            results.append((m.group(1), lineno))
    return results


def scan_l5_engine_operations(
    engine_path: Path,
) -> list[tuple[str, int]]:
    """
    Scan an L5 engine file for operation-name-like strings
    (e.g. "domain.verb") that might indicate implicit ownership claims.
    """
    results: list[tuple[str, int]] = []
    # L5 engines do not call registry.register() — they are *called by*
    # handlers.  We still scan for dotted operation names in string literals
    # that might indicate a domain claim (e.g. returning operation names).
    op_re = re.compile(r'"([a-z_]+\.[a-z_]+(?:\.[a-z_]+)*)"')
    try:
        lines = engine_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return results

    for lineno, line in enumerate(lines, start=1):
        if _is_comment_line(line):
            continue
        for m in op_re.finditer(line):
            candidate = m.group(1)
            # Filter out common false positives (module paths, etc.)
            # Only keep if it looks like domain.operation (2 segments)
            segments = candidate.split(".")
            if len(segments) >= 2:
                # Exclude things that look like Python import paths
                if candidate.startswith("app.") or candidate.startswith("hoc."):
                    continue
                # Exclude known non-operation patterns
                if any(
                    seg in ("py", "md", "json", "yaml", "txt", "csv", "sql")
                    for seg in segments
                ):
                    continue
                results.append((candidate, lineno))
    return results


def infer_handler_domains(
    handler_path: Path,
    operations: list[tuple[str, int]],
) -> set[str]:
    """
    Determine the domain(s) that a handler file *owns* based on the
    operations it registers.  The domain is the first segment of the
    operation name (e.g. "account.query" -> "account").
    """
    domains: set[str] = set()
    for op_name, _ in operations:
        domain = op_name.split(".")[0]
        domains.add(domain)
    return domains


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check operation ownership — no two domains may claim the same operation."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Strict mode: also flag cross-domain L5 imports in handlers.",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Phase 1: Build operation ownership map from L4 handlers
    # ------------------------------------------------------------------
    # operation_name -> list of (handler_file, line_number)
    ownership_map: dict[str, list[tuple[Path, int]]] = {}
    handler_domain_map: dict[Path, set[str]] = {}

    handler_files = sorted(HANDLERS_DIR.glob("*.py"))
    handler_files = [
        f for f in handler_files if f.name != "__init__.py" and f.is_file()
    ]

    for hf in handler_files:
        ops = scan_handler_operations(hf)
        domains = infer_handler_domains(hf, ops)
        handler_domain_map[hf] = domains

        for op_name, lineno in ops:
            ownership_map.setdefault(op_name, []).append((hf, lineno))

    # ------------------------------------------------------------------
    # Phase 2: Scan L5 engine files for operation name references
    # ------------------------------------------------------------------
    l5_dirs = sorted(CUS_ROOT.glob("*/L5_engines"))
    l5_files: list[Path] = []
    for d in l5_dirs:
        if d.is_dir():
            l5_files.extend(
                sorted(
                    f
                    for f in d.glob("*.py")
                    if f.is_file() and f.name != "__init__.py"
                )
            )

    # L5 engine operation references are informational — they do not
    # constitute ownership claims (only registry.register does).  We
    # report them in strict mode as advisory.
    l5_op_refs: dict[str, list[tuple[Path, int]]] = {}
    for ef in l5_files:
        ops = scan_l5_engine_operations(ef)
        for op_name, lineno in ops:
            l5_op_refs.setdefault(op_name, []).append((ef, lineno))

    # ------------------------------------------------------------------
    # Phase 3: Detect ownership conflicts
    # ------------------------------------------------------------------
    conflicts: list[tuple[str, list[tuple[Path, int]]]] = []
    clean_ops: list[tuple[str, Path]] = []

    for op_name in sorted(ownership_map):
        claimants = ownership_map[op_name]
        # Deduplicate by file (same file registering same op on multiple
        # lines is not a conflict — it is a duplicate registration).
        unique_files = set(f for f, _ in claimants)
        if len(unique_files) > 1:
            conflicts.append((op_name, claimants))
        else:
            clean_ops.append((op_name, claimants[0][0]))

    # ------------------------------------------------------------------
    # Phase 4: Cross-domain L5 import check (strict mode)
    # ------------------------------------------------------------------
    cross_domain_violations: list[tuple[Path, int, str, set[str]]] = []

    if args.strict:
        for hf in handler_files:
            owned_domains = handler_domain_map.get(hf, set())
            if not owned_domains:
                continue  # no registered ops -> skip

            imports = scan_handler_l5_imports(hf)
            for imported_domain, lineno in imports:
                if imported_domain not in owned_domains:
                    # Check cross-domain allowlist
                    allowlist_key = (hf.name, imported_domain)
                    if allowlist_key in CROSS_DOMAIN_ALLOWLIST:
                        continue  # Documented cross-domain coordination
                    cross_domain_violations.append(
                        (hf, lineno, imported_domain, owned_domains)
                    )

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------
    total_ops = len(ownership_map)
    unique_domains: set[str] = set()
    for op_name in ownership_map:
        unique_domains.add(op_name.split(".")[0])

    # Clean operations
    for op_name, owner_file in clean_ops:
        domain = op_name.split(".")[0]
        rel = owner_file.relative_to(BACKEND_ROOT)
        print(f"[PASS] {op_name} -- owned by domain '{domain}' ({rel})")

    # Conflicts
    for op_name, claimants in conflicts:
        files_str = ", ".join(
            str(f.relative_to(BACKEND_ROOT)) + f":{ln}"
            for f, ln in claimants
        )
        print(f"[FAIL] {op_name} -- claimed by multiple domains: {files_str}")

    # Cross-domain import violations (strict)
    for hf, lineno, imported_domain, owned_domains in cross_domain_violations:
        rel = hf.relative_to(BACKEND_ROOT)
        owned_str = ", ".join(sorted(owned_domains))
        print(
            f"[FAIL] {rel}:{lineno} -- imports L5 from domain '{imported_domain}' "
            f"but handler owns domain(s): {owned_str}"
        )

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print()
    print("=" * 60)
    print("Operation Ownership Summary")
    print("=" * 60)
    print(f"  Total operations registered : {total_ops}")
    print(f"  Unique domain owners        : {len(unique_domains)}")
    print(f"  Domains                     : {', '.join(sorted(unique_domains))}")
    print(f"  Ownership conflicts         : {len(conflicts)}")
    print(f"  Handler files scanned       : {len(handler_files)}")
    print(f"  L5 engine files scanned     : {len(l5_files)}")
    if args.strict:
        print(f"  Cross-domain L5 violations  : {len(cross_domain_violations)}")
    print("=" * 60)

    # ------------------------------------------------------------------
    # Exit code
    # ------------------------------------------------------------------
    has_failures = len(conflicts) > 0
    if args.strict:
        has_failures = has_failures or len(cross_domain_violations) > 0

    if has_failures:
        print("\nRESULT: FAIL")
        return 1
    else:
        print("\nRESULT: PASS")
        return 0


if __name__ == "__main__":
    sys.exit(main())
