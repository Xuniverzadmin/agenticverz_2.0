#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Post-Migration Audit Script
# artifact_class: CODE
"""
Post-Migration Audit Script

Checks each customer domain against its audit reports to verify:
1. No quarantined/removed files were reintroduced
2. No duplicate files exist
3. Quarantine directory matches audit expectations

Usage:
    python scripts/migration/post_migration_audit.py [domain]

    If domain is specified, only audits that domain.
    Otherwise, audits all customer domains.
"""

import os
import re
import sys
from pathlib import Path
from collections import defaultdict
from typing import Set, Dict, List, Tuple

# Paths
HOC_ROOT = Path("backend/app/hoc")
CUSTOMER_ROOT = HOC_ROOT / "customer"
DUPLICATE_ROOT = HOC_ROOT / "duplicate"

# Customer domains
CUSTOMER_DOMAINS = [
    "activity", "incidents", "policies", "logs", "analytics",
    "integrations", "api_keys", "account", "overview", "general"
]


def find_audit_reports(domain: str) -> List[Path]:
    """Find all audit report files for a domain."""
    domain_path = CUSTOMER_ROOT / domain
    reports = []

    # Look for HOC_*_audit*.md files
    for f in domain_path.glob("HOC_*_audit*.md"):
        reports.append(f)

    return reports


def extract_quarantine_files_from_audit(audit_path: Path) -> Set[str]:
    """Extract quarantined/removed file references from audit report.

    Only looks for explicitly quarantined files in specific patterns,
    excluding __init__.py and general file listings.
    """
    quarantined = set()

    try:
        content = audit_path.read_text()
    except Exception as e:
        print(f"  Warning: Could not read {audit_path}: {e}")
        return quarantined

    # Patterns to find EXPLICIT quarantine references
    patterns = [
        # Pattern: Quarantined `filename.py` (explicit action)
        r'[Qq]uarantined\s+`([^`]+\.py)`',
        # Pattern: POL-DUP-XXX | Quarantined `filename` (action table)
        r'\|\s*[A-Z]+-DUP-\d+\s*\|\s*[Qq]uarantined\s+`([^`]+)`',
        # Pattern: ✅ COMPLETE for quarantine actions
        r'[Qq]uarantined\s+`([^`]+)`[^|]*\|\s*✅',
        # Pattern: REMOVED: filename.py or DELETED: filename.py (explicit)
        r'(?:REMOVED|DELETED):\s*`([^`]+\.py)`',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            # Clean up the match
            filename = match.strip()
            if filename.endswith('.py'):
                # Add .py if not present
                pass
            elif not filename.endswith('.py'):
                filename = filename + '.py' if '.' not in filename else filename

            # Skip __init__.py - these are expected everywhere
            if filename == '__init__.py':
                continue

            if filename and filename.endswith('.py'):
                quarantined.add(filename)

    return quarantined


def get_domain_files(domain: str) -> Dict[str, List[Path]]:
    """Get all Python files in a domain, grouped by basename."""
    domain_path = CUSTOMER_ROOT / domain
    files_by_name = defaultdict(list)

    for py_file in domain_path.rglob("*.py"):
        # Skip __pycache__
        if "__pycache__" in str(py_file):
            continue
        files_by_name[py_file.name].append(py_file)

    return files_by_name


def get_quarantine_files(domain: str) -> Set[str]:
    """Get files currently in quarantine for a domain."""
    quarantine_path = DUPLICATE_ROOT / domain
    quarantined = set()

    if quarantine_path.exists():
        for py_file in quarantine_path.glob("*.py"):
            if py_file.name != "__init__.py":
                quarantined.add(py_file.name)

    return quarantined


def audit_domain(domain: str) -> Dict:
    """Audit a single domain and return findings."""
    print(f"\n{'='*60}")
    print(f"AUDITING DOMAIN: {domain}")
    print(f"{'='*60}")

    findings = {
        "domain": domain,
        "audit_reports": [],
        "quarantine_expected": set(),
        "quarantine_actual": set(),
        "reintroduced_files": [],
        "duplicate_files": [],
        "quarantine_missing": [],
        "quarantine_extra": [],
        "status": "CLEAN"
    }

    # Step 1: Find and read audit reports
    audit_reports = find_audit_reports(domain)
    findings["audit_reports"] = [str(r) for r in audit_reports]
    print(f"\n  Audit reports found: {len(audit_reports)}")
    for report in audit_reports:
        print(f"    - {report.name}")

    # Step 2: Extract expected quarantine files from audits
    for report in audit_reports:
        quarantine_refs = extract_quarantine_files_from_audit(report)
        findings["quarantine_expected"].update(quarantine_refs)

    print(f"\n  Quarantine references in audits: {len(findings['quarantine_expected'])}")
    for f in sorted(findings["quarantine_expected"]):
        print(f"    - {f}")

    # Step 3: Get actual quarantine files
    findings["quarantine_actual"] = get_quarantine_files(domain)
    print(f"\n  Files in quarantine directory: {len(findings['quarantine_actual'])}")
    for f in sorted(findings["quarantine_actual"]):
        print(f"    - {f}")

    # Step 4: Get all domain files
    domain_files = get_domain_files(domain)
    total_files = sum(len(paths) for paths in domain_files.values())
    print(f"\n  Total Python files in domain: {total_files}")

    # Step 5: Check for reintroduced quarantine files
    print(f"\n  Checking for reintroduced quarantine files...")
    for quarantine_file in findings["quarantine_expected"]:
        if quarantine_file in domain_files:
            # File with same name exists in domain
            for path in domain_files[quarantine_file]:
                # Exclude the quarantine directory itself
                if "duplicate" not in str(path):
                    findings["reintroduced_files"].append({
                        "file": quarantine_file,
                        "path": str(path),
                        "issue": "Quarantined file reintroduced"
                    })

    if findings["reintroduced_files"]:
        print(f"  ❌ REINTRODUCED FILES FOUND: {len(findings['reintroduced_files'])}")
        for item in findings["reintroduced_files"]:
            print(f"    - {item['path']}")
        findings["status"] = "ISSUES"
    else:
        print(f"  ✅ No reintroduced quarantine files")

    # Step 6: Check for duplicate files (same basename in multiple locations)
    print(f"\n  Checking for duplicate files...")
    for filename, paths in domain_files.items():
        if filename == "__init__.py":
            continue  # Init files are expected in multiple places

        # Filter out quarantine paths
        non_quarantine_paths = [p for p in paths if "duplicate" not in str(p)]

        if len(non_quarantine_paths) > 1:
            findings["duplicate_files"].append({
                "file": filename,
                "paths": [str(p) for p in non_quarantine_paths],
                "count": len(non_quarantine_paths)
            })

    if findings["duplicate_files"]:
        print(f"  ⚠️  DUPLICATE FILES FOUND: {len(findings['duplicate_files'])}")
        for item in findings["duplicate_files"]:
            print(f"    - {item['file']} ({item['count']} copies)")
            for path in item["paths"]:
                print(f"        {path}")
        findings["status"] = "ISSUES"
    else:
        print(f"  ✅ No duplicate files")

    # Step 7: Quarantine consistency check
    print(f"\n  Checking quarantine consistency...")

    # Files expected but not in quarantine
    findings["quarantine_missing"] = list(
        findings["quarantine_expected"] - findings["quarantine_actual"]
    )

    # Files in quarantine but not expected
    findings["quarantine_extra"] = list(
        findings["quarantine_actual"] - findings["quarantine_expected"]
    )

    if findings["quarantine_missing"]:
        print(f"  ⚠️  Missing from quarantine: {len(findings['quarantine_missing'])}")
        for f in findings["quarantine_missing"]:
            print(f"    - {f}")

    if findings["quarantine_extra"]:
        print(f"  ℹ️  Extra in quarantine (not in audit): {len(findings['quarantine_extra'])}")
        for f in findings["quarantine_extra"]:
            print(f"    - {f}")

    # Final status
    print(f"\n  DOMAIN STATUS: {findings['status']}")

    # Convert sets to lists for JSON serialization
    findings["quarantine_expected"] = list(findings["quarantine_expected"])
    findings["quarantine_actual"] = list(findings["quarantine_actual"])

    return findings


def print_summary(all_findings: List[Dict]):
    """Print summary of all domain audits."""
    print(f"\n{'='*60}")
    print("AUDIT SUMMARY")
    print(f"{'='*60}")

    clean_domains = []
    issue_domains = []

    for f in all_findings:
        if f["status"] == "CLEAN":
            clean_domains.append(f["domain"])
        else:
            issue_domains.append(f["domain"])

    print(f"\n  CLEAN domains: {len(clean_domains)}")
    for d in clean_domains:
        print(f"    ✅ {d}")

    if issue_domains:
        print(f"\n  ISSUES found in: {len(issue_domains)}")
        for d in issue_domains:
            print(f"    ❌ {d}")

    # Total issues
    total_reintroduced = sum(len(f["reintroduced_files"]) for f in all_findings)
    total_duplicates = sum(len(f["duplicate_files"]) for f in all_findings)

    print(f"\n  Total reintroduced files: {total_reintroduced}")
    print(f"  Total duplicate files: {total_duplicates}")

    if total_reintroduced == 0 and total_duplicates == 0:
        print(f"\n  ✅ ALL DOMAINS CLEAN - No issues found")
        return 0
    else:
        print(f"\n  ❌ ISSUES REQUIRE ATTENTION")
        return 1


def main():
    # Change to repo root
    os.chdir(Path(__file__).parent.parent.parent)

    # Check if specific domain requested
    if len(sys.argv) > 1:
        domain = sys.argv[1]
        if domain not in CUSTOMER_DOMAINS:
            print(f"Unknown domain: {domain}")
            print(f"Valid domains: {', '.join(CUSTOMER_DOMAINS)}")
            sys.exit(1)
        domains_to_audit = [domain]
    else:
        domains_to_audit = CUSTOMER_DOMAINS

    print("="*60)
    print("POST-MIGRATION AUDIT")
    print("="*60)
    print(f"\nDomains to audit: {len(domains_to_audit)}")
    print(f"HOC Root: {HOC_ROOT}")
    print(f"Quarantine Root: {DUPLICATE_ROOT}")

    all_findings = []

    for domain in domains_to_audit:
        findings = audit_domain(domain)
        all_findings.append(findings)

    exit_code = print_summary(all_findings)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
