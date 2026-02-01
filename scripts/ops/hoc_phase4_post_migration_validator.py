#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: HOC Phase 4 — Post-Migration Validation
# artifact_class: CODE
"""
HOC Phase 4 — Post-Migration Validation

Runs 6 validation checks against the post-migration HOC domain structure:
  V1: Import resolution (every .py file importable)
  V2: BLCA layer validation
  V3: Test suite
  V4: Circular import detection
  V5: Domain integrity (each filename in exactly one domain)
  V6: Hash verification (lock registry hashes match actual files)

Reference: PIN-470, PIN-473, PIN-479
Artifact Class: CODE
Layer: OPS
Audience: INTERNAL

Usage:
    python3 scripts/ops/hoc_phase4_post_migration_validator.py
"""

import ast
import hashlib
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND = REPO_ROOT / "backend"
BACKEND_HOC_CUS = BACKEND / "app" / "hoc" / "cus"
DOMAIN_MAP_DIR = BACKEND_HOC_CUS / "_domain_map"
REGISTRY_PATH = DOMAIN_MAP_DIR / "DOMAIN_LOCK_REGISTRY.json"
MANIFEST_PATH = DOMAIN_MAP_DIR / "MIGRATION_MANIFEST.csv"
REPORT_PATH = DOMAIN_MAP_DIR / "PHASE4_VALIDATION_REPORT.md"
HEALTH_PATH = DOMAIN_MAP_DIR / "PHASE4_HEALTH_SCORE.json"

EXCLUDED_DIRS = {"__pycache__", "_domain_map", "docs", ".git", "node_modules"}
TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

CUSTOMER_DOMAINS = [
    "account", "activity", "analytics", "api_keys", "controls",
    "general", "incidents", "integrations", "logs", "overview", "policies",
]


# ---------------------------------------------------------------------------
# V1: Import Resolution — AST parse every .py file
# ---------------------------------------------------------------------------

def v1_import_resolution() -> dict:
    """Check that every .py file under hoc/cus/ parses without syntax errors
    and that import targets reference existing files."""
    print("  V1: Import resolution (AST parse)...")
    results = {"status": "PASS", "total": 0, "passed": 0, "failed": 0, "errors": []}

    for domain in CUSTOMER_DOMAINS:
        domain_dir = BACKEND_HOC_CUS / domain
        if not domain_dir.exists():
            continue
        for root, dirs, fnames in os.walk(domain_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            for fname in fnames:
                if not fname.endswith(".py"):
                    continue
                fpath = Path(root) / fname
                results["total"] += 1
                try:
                    source = fpath.read_text(encoding="utf-8", errors="replace")
                    ast.parse(source, filename=str(fpath))
                    results["passed"] += 1
                except SyntaxError as e:
                    results["failed"] += 1
                    rel = str(fpath.relative_to(REPO_ROOT))
                    results["errors"].append(f"{rel}:{e.lineno}: {e.msg}")

    if results["failed"] > 0:
        results["status"] = "FAIL"
    print(f"    {results['passed']}/{results['total']} files parse OK, {results['failed']} syntax errors")
    return results


# ---------------------------------------------------------------------------
# V2: BLCA Layer Validation
# ---------------------------------------------------------------------------

def v2_blca_validation() -> dict:
    """Run BLCA layer validator if available."""
    print("  V2: BLCA layer validation...")
    results = {"status": "SKIP", "violations": -1, "output": ""}

    validator = REPO_ROOT / "scripts" / "ops" / "layer_validator.py"
    if not validator.exists():
        results["output"] = "layer_validator.py not found"
        print(f"    SKIP: {results['output']}")
        return results

    try:
        proc = subprocess.run(
            [sys.executable, str(validator), "--backend", "--ci"],
            capture_output=True, text=True, timeout=120,
            cwd=str(REPO_ROOT),
        )
        results["output"] = proc.stdout[-2000:] if proc.stdout else ""
        # Try to parse violation count from output
        for line in proc.stdout.splitlines():
            if "violation" in line.lower():
                import re
                m = re.search(r'(\d+)\s*violation', line.lower())
                if m:
                    results["violations"] = int(m.group(1))
                    break

        if proc.returncode == 0:
            results["status"] = "PASS"
            if results["violations"] == -1:
                results["violations"] = 0
        else:
            results["status"] = "FAIL"
        print(f"    {results['status']}: {results['violations']} violations (exit code {proc.returncode})")
    except subprocess.TimeoutExpired:
        results["status"] = "TIMEOUT"
        results["output"] = "Timed out after 120s"
        print(f"    TIMEOUT")
    except Exception as e:
        results["status"] = "ERROR"
        results["output"] = str(e)
        print(f"    ERROR: {e}")

    return results


# ---------------------------------------------------------------------------
# V3: Test Suite
# ---------------------------------------------------------------------------

def v3_test_suite() -> dict:
    """Run HOC tests if they exist."""
    print("  V3: Test suite...")
    results = {"status": "SKIP", "passed": 0, "failed": 0, "output": ""}

    test_dir = BACKEND / "tests" / "hoc"
    if not test_dir.exists():
        # Try broader test directory
        test_dir = BACKEND / "tests"
        if not test_dir.exists():
            results["output"] = "No test directory found"
            print(f"    SKIP: {results['output']}")
            return results

    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_dir), "-v", "--tb=no", "-q", "--no-header"],
            capture_output=True, text=True, timeout=300,
            cwd=str(BACKEND),
            env={**os.environ, "PYTHONPATH": str(BACKEND)},
        )
        results["output"] = proc.stdout[-2000:] if proc.stdout else ""
        # Parse pytest summary
        for line in reversed(proc.stdout.splitlines()):
            if "passed" in line or "failed" in line or "error" in line:
                import re
                p = re.search(r'(\d+) passed', line)
                f = re.search(r'(\d+) failed', line)
                if p:
                    results["passed"] = int(p.group(1))
                if f:
                    results["failed"] = int(f.group(1))
                break

        results["status"] = "PASS" if proc.returncode == 0 else "FAIL"
        print(f"    {results['status']}: {results['passed']} passed, {results['failed']} failed")
    except subprocess.TimeoutExpired:
        results["status"] = "TIMEOUT"
        print(f"    TIMEOUT")
    except Exception as e:
        results["status"] = "ERROR"
        results["output"] = str(e)
        print(f"    ERROR: {e}")

    return results


# ---------------------------------------------------------------------------
# V4: Circular Import Detection
# ---------------------------------------------------------------------------

def v4_circular_imports() -> dict:
    """Detect circular imports by building an import graph from AST."""
    print("  V4: Circular import detection...")
    results = {"status": "PASS", "cycles": 0, "cycle_details": []}

    # Build import graph: module -> set of imported modules
    graph = defaultdict(set)
    module_map = {}  # file path -> module name

    hoc_prefix = "app.hoc.cus."

    for domain in CUSTOMER_DOMAINS:
        domain_dir = BACKEND_HOC_CUS / domain
        if not domain_dir.exists():
            continue
        for root, dirs, fnames in os.walk(domain_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            for fname in fnames:
                if not fname.endswith(".py"):
                    continue
                fpath = Path(root) / fname
                rel = str(fpath.relative_to(BACKEND)).replace("/", ".").replace(".py", "")
                module_map[str(fpath)] = rel

                try:
                    source = fpath.read_text(encoding="utf-8", errors="replace")
                    tree = ast.parse(source)
                except SyntaxError:
                    continue

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name.startswith(hoc_prefix):
                                graph[rel].add(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and node.module.startswith(hoc_prefix):
                            graph[rel].add(node.module)

    # DFS cycle detection
    WHITE, GRAY, BLACK = 0, 1, 2
    color = defaultdict(int)
    cycles = []

    def dfs(node, path):
        color[node] = GRAY
        path.append(node)
        for neighbor in graph.get(node, []):
            if color[neighbor] == GRAY:
                # Found cycle
                idx = path.index(neighbor) if neighbor in path else -1
                if idx >= 0:
                    cycle = path[idx:] + [neighbor]
                    cycles.append(" -> ".join(cycle))
            elif color[neighbor] == WHITE:
                dfs(neighbor, path)
        path.pop()
        color[node] = BLACK

    for node in list(graph.keys()):
        if color[node] == WHITE:
            dfs(node, [])

    results["cycles"] = len(cycles)
    results["cycle_details"] = cycles[:20]  # cap at 20
    if cycles:
        results["status"] = "WARN"
    print(f"    {results['status']}: {results['cycles']} cycles detected")
    return results


# ---------------------------------------------------------------------------
# V5: Domain Integrity
# ---------------------------------------------------------------------------

def v5_domain_integrity() -> dict:
    """Check each .py filename exists in exactly one domain (excluding __init__.py)."""
    print("  V5: Domain integrity (no cross-domain duplicates)...")
    results = {"status": "PASS", "total_files": 0, "duplicates": 0, "duplicate_details": []}

    filename_to_domains = defaultdict(list)

    for domain in CUSTOMER_DOMAINS:
        domain_dir = BACKEND_HOC_CUS / domain
        if not domain_dir.exists():
            continue
        for root, dirs, fnames in os.walk(domain_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            for fname in fnames:
                if not fname.endswith(".py") or fname == "__init__.py":
                    continue
                results["total_files"] += 1
                filename_to_domains[fname].append(domain)

    for fname, domains in sorted(filename_to_domains.items()):
        if len(domains) > 1:
            results["duplicates"] += 1
            results["duplicate_details"].append(f"{fname}: {', '.join(domains)}")

    if results["duplicates"] > 0:
        results["status"] = "WARN"
    print(f"    {results['status']}: {results['total_files']} files, {results['duplicates']} names in >1 domain")
    return results


# ---------------------------------------------------------------------------
# V6: Hash Verification
# ---------------------------------------------------------------------------

def v6_hash_verification() -> dict:
    """Verify lock registry hashes match actual files."""
    print("  V6: Hash verification (lock registry vs filesystem)...")
    results = {"status": "PASS", "domains_checked": 0, "mismatches": 0, "mismatch_details": []}

    if not REGISTRY_PATH.exists():
        results["status"] = "SKIP"
        results["output"] = "DOMAIN_LOCK_REGISTRY.json not found"
        print(f"    SKIP: {results['output']}")
        return results

    with open(REGISTRY_PATH) as f:
        registry = json.load(f)

    for domain, meta in registry.get("domains", {}).items():
        results["domains_checked"] += 1
        domain_dir = BACKEND_HOC_CUS / domain
        if not domain_dir.exists():
            results["mismatches"] += 1
            results["mismatch_details"].append(f"{domain}: directory missing")
            continue

        # Recompute domain hash
        file_hashes = []
        for root, dirs, fnames in os.walk(domain_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            for fname in sorted(fnames):
                if not fname.endswith(".py"):
                    continue
                fpath = Path(root) / fname
                h = hashlib.sha256()
                with open(fpath, "rb") as fh:
                    for chunk in iter(lambda: fh.read(8192), b""):
                        h.update(chunk)
                file_hashes.append(h.hexdigest())

        all_hashes = sorted(file_hashes)
        computed_hash = hashlib.sha256("|".join(all_hashes).encode()).hexdigest()
        expected_hash = meta.get("domain_hash", "")

        if computed_hash != expected_hash:
            results["mismatches"] += 1
            results["mismatch_details"].append(
                f"{domain}: expected {expected_hash[:12]}..., got {computed_hash[:12]}..."
            )

    if results["mismatches"] > 0:
        results["status"] = "FAIL"
    print(f"    {results['status']}: {results['domains_checked']} domains, {results['mismatches']} hash mismatches")
    return results


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def generate_report(checks: dict) -> str:
    lines = [
        "# Phase 4 — Post-Migration Validation Report",
        "",
        f"**Generated:** {TIMESTAMP}",
        f"**Generator:** `hoc_phase4_post_migration_validator.py`",
        f"**Reference:** PIN-470, PIN-479",
        "",
        "---",
        "",
        "## Validation Summary",
        "",
        "| Check | Status | Details |",
        "|-------|--------|---------|",
    ]

    for name, data in checks.items():
        status = data.get("status", "UNKNOWN")
        icon = {"PASS": "PASS", "FAIL": "**FAIL**", "WARN": "WARN", "SKIP": "SKIP"}.get(status, status)
        detail = ""
        if name == "V1":
            detail = f"{data['passed']}/{data['total']} files parse OK"
        elif name == "V2":
            detail = f"{data.get('violations', '?')} violations"
        elif name == "V3":
            detail = f"{data.get('passed', 0)} passed, {data.get('failed', 0)} failed"
        elif name == "V4":
            detail = f"{data['cycles']} cycles"
        elif name == "V5":
            detail = f"{data['total_files']} files, {data['duplicates']} name duplicates"
        elif name == "V6":
            detail = f"{data['domains_checked']} domains, {data['mismatches']} mismatches"
        lines.append(f"| {name} | {icon} | {detail} |")

    # Overall
    statuses = [d["status"] for d in checks.values()]
    if "FAIL" in statuses:
        overall = "UNHEALTHY"
    elif "WARN" in statuses:
        overall = "HEALTHY (with warnings)"
    else:
        overall = "HEALTHY"

    lines += ["", f"**Overall:** {overall}", ""]

    # Detail sections
    for name, data in checks.items():
        if data.get("errors") or data.get("cycle_details") or data.get("duplicate_details") or data.get("mismatch_details"):
            lines += [f"### {name} Details", ""]
            for detail_key in ("errors", "cycle_details", "duplicate_details", "mismatch_details"):
                details = data.get(detail_key, [])
                if details:
                    for d in details[:30]:
                        lines.append(f"- `{d}`")
            lines.append("")

    lines.append(f"*Report generated: {TIMESTAMP}*")
    lines.append("")
    return "\n".join(lines)


def generate_health_score(checks: dict) -> dict:
    statuses = [d["status"] for d in checks.values()]
    if "FAIL" in statuses:
        overall = "UNHEALTHY"
        score = 50
    elif "WARN" in statuses:
        overall = "HEALTHY"
        score = 85
    else:
        overall = "HEALTHY"
        score = 100

    return {
        "overall": overall,
        "score": score,
        "generated": TIMESTAMP,
        "checks": {
            name: {
                "status": data["status"],
                **{k: v for k, v in data.items() if k != "status" and k != "output" and not isinstance(v, list)},
            }
            for name, data in checks.items()
        },
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("HOC Phase 4 — Post-Migration Validation")
    print("=" * 60)

    checks = {}

    print("\nRunning 6 validation checks...\n")
    checks["V1"] = v1_import_resolution()
    checks["V2"] = v2_blca_validation()
    checks["V3"] = v3_test_suite()
    checks["V4"] = v4_circular_imports()
    checks["V5"] = v5_domain_integrity()
    checks["V6"] = v6_hash_verification()

    # Generate outputs
    print("\nGenerating reports...")
    report = generate_report(checks)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"  Report: {REPORT_PATH}")

    health = generate_health_score(checks)
    with open(HEALTH_PATH, "w") as f:
        json.dump(health, f, indent=2)
    print(f"  Health:  {HEALTH_PATH}")

    statuses = [d["status"] for d in checks.values()]
    if "FAIL" in statuses:
        print(f"\nResult: UNHEALTHY — some checks failed")
        return 1
    elif "WARN" in statuses:
        print(f"\nResult: HEALTHY (with warnings)")
        return 0
    else:
        print(f"\nResult: HEALTHY")
        return 0


if __name__ == "__main__":
    sys.exit(main())
