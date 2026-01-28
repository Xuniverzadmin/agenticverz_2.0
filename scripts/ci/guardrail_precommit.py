#!/usr/bin/env python3
"""
GUARDRAIL PRE-COMMIT - Runs guardrails only on staged files.

This is lightweight - only checks files about to be committed.
Install as git pre-commit hook for automatic pre-diagnosis.

Usage:
    python guardrail_precommit.py           # Check staged files
    python guardrail_precommit.py --install # Install git hook
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set

# REDUNDANT PATHS — scheduled for deletion, skip guardrails entirely.
# app/api/* and app/services/* are legacy layers being replaced by hoc/.
# See PIN-470 (HOC Layer Inventory) and PIN-483 (HOC Migration Complete).
REDUNDANT_PATHS: List[str] = [
    'api/',
    'services/',
]

# Map file patterns to relevant guardrails (same as watcher)
FILE_TO_GUARDRAILS: Dict[str, List[str]] = {
    # Legacy app/api/ and app/services/ excluded — REDUNDANT, pending deletion
    # 'api/*.py': ['DOMAIN-001', 'DATA-002', 'API-001', 'API-002'],
    # 'api/aos_accounts.py': ['DOMAIN-002'],
    # 'api/overview.py': ['DOMAIN-003'],
    # 'services/*.py': ['DOMAIN-001', 'CROSS-001', 'API-001'],
    # 'services/limit*.py': ['LIMITS-001', 'LIMITS-002', 'LIMITS-003'],
    # 'services/policy*.py': ['LIMITS-003', 'AUDIT-001'],
    # 'services/incident*.py': ['CROSS-001', 'AUDIT-001'],
    'models/*.py': ['DATA-001', 'LIMITS-001'],
    'worker/*.py': ['LIMITS-002', 'DOMAIN-001'],
    'AURORA_L2_CAPABILITY_REGISTRY/*.yaml': ['CAP-001', 'CAP-002', 'CAP-003'],
    'intents/*.yaml': ['CAP-002'],
}

GUARDRAIL_SCRIPTS = {
    'DOMAIN-001': 'check_domain_writes.py',
    'DOMAIN-002': 'check_account_boundaries.py',
    'DOMAIN-003': 'check_overview_readonly.py',
    'DATA-001': 'check_foreign_keys.py',
    'DATA-002': 'check_tenant_queries.py',
    'CROSS-001': 'check_cross_domain_propagation.py',
    'CROSS-002': 'check_bidirectional_queries.py',
    'LIMITS-001': 'check_limit_tables.py',
    'LIMITS-002': 'check_limit_enforcement.py',
    'LIMITS-003': 'check_limit_audit.py',
    'AUDIT-001': 'check_governance_audit.py',
    'AUDIT-002': 'check_audit_completeness.py',
    'CAP-001': 'check_capability_endpoints.py',
    'CAP-002': 'check_console_boundaries.py',
    'CAP-003': 'check_capability_status.py',
    'API-001': 'check_facade_usage.py',
    'API-002': 'check_response_envelopes.py',
}


def get_staged_files() -> List[str]:
    """Get list of staged files from git."""
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return []
    return [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]


def matches_pattern(path: str, pattern: str) -> bool:
    """Simple pattern matching."""
    import fnmatch
    parts = pattern.split('/')
    path_parts = path.split('/')

    for i in range(len(path_parts) - len(parts) + 1):
        match = True
        for j, p in enumerate(parts):
            if not fnmatch.fnmatch(path_parts[i + j], p):
                match = False
                break
        if match:
            return True
    return False


def is_redundant(file_path: str) -> bool:
    """Check if file is in a redundant path (pending deletion)."""
    for prefix in REDUNDANT_PATHS:
        if f"app/{prefix}" in file_path or file_path.startswith(prefix):
            return True
    return False


def get_guardrails_for_files(files: List[str]) -> Set[str]:
    """Determine which guardrails apply to the staged files."""
    guardrails = set()

    for file_path in files:
        if is_redundant(file_path):
            continue
        for pattern, rules in FILE_TO_GUARDRAILS.items():
            if matches_pattern(file_path, pattern):
                guardrails.update(rules)

    return guardrails


def run_guardrail(rule_id: str, script_dir: Path) -> tuple:
    """Run a single guardrail and return (passed, output)."""
    script = GUARDRAIL_SCRIPTS.get(rule_id)
    if not script:
        return True, ""

    script_path = script_dir / script
    if not script_path.exists():
        return True, f"Script not found: {script}"

    try:
        result = subprocess.run(
            ['python3', str(script_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    except Exception as e:
        return False, str(e)


def install_hook():
    """Install as git pre-commit hook."""
    git_dir = Path('.git')
    if not git_dir.exists():
        print("Error: Not a git repository")
        sys.exit(1)

    hooks_dir = git_dir / 'hooks'
    hooks_dir.mkdir(exist_ok=True)

    hook_path = hooks_dir / 'pre-commit'
    script_path = Path(__file__).resolve()

    hook_content = f'''#!/bin/bash
# Guardrail pre-commit hook
python3 {script_path}
exit $?
'''

    with open(hook_path, 'w') as f:
        f.write(hook_content)

    hook_path.chmod(0o755)
    print(f"✅ Installed pre-commit hook: {hook_path}")
    print("   Guardrails will run automatically before each commit.")


def main():
    if '--install' in sys.argv:
        install_hook()
        return

    # Get staged files
    staged_files = get_staged_files()

    if not staged_files:
        # No files staged, nothing to check
        sys.exit(0)

    # Filter to relevant files
    relevant_files = [f for f in staged_files if f.endswith(('.py', '.yaml', '.yml'))]

    if not relevant_files:
        sys.exit(0)

    # Get applicable guardrails
    guardrails = get_guardrails_for_files(relevant_files)

    if not guardrails:
        sys.exit(0)

    # Find script directory
    script_dir = Path(__file__).parent

    # Print header
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║           GUARDRAIL PRE-COMMIT CHECK                     ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print(f"║  Staged files: {len(relevant_files):<42} ║")
    print(f"║  Guardrails to run: {len(guardrails):<37} ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    # Run guardrails
    failures = []
    for rule_id in sorted(guardrails):
        print(f"  {rule_id}...", end=" ", flush=True)
        passed, output = run_guardrail(rule_id, script_dir)

        if passed:
            print("✅")
        else:
            print("❌")
            failures.append((rule_id, output))

    print()

    # Summary
    if failures:
        print("╔══════════════════════════════════════════════════════════╗")
        print("║  ❌ COMMIT BLOCKED - GUARDRAIL VIOLATIONS                ║")
        print("╚══════════════════════════════════════════════════════════╝")
        print()

        for rule_id, output in failures[:3]:
            print(f"  [{rule_id}]")
            lines = output.strip().split('\n')
            for line in lines[-10:]:  # Last 10 lines
                print(f"    {line}")
            print()

        print("  Fix violations before committing.")
        print("  To bypass (NOT recommended): git commit --no-verify")
        print()
        sys.exit(1)
    else:
        print("╔══════════════════════════════════════════════════════════╗")
        print("║  ✅ ALL GUARDRAILS PASSED - COMMIT ALLOWED               ║")
        print("╚══════════════════════════════════════════════════════════╝")
        print()
        sys.exit(0)


if __name__ == "__main__":
    main()
