#!/usr/bin/env python3
"""
AURORA L2 Semantic Validator CLI
Runs two-phase semantic validation on all intents.

Phase A: Intent Guardrails (design-time)
    - INT-001 to INT-008 checks
    - Validates intent structure BEFORE SDSR or APIs

Phase B: Semantic Reality (proof-time)
    - SEM-001 to SEM-004 checks
    - Validates that capabilities and signals are real

Usage:
    python aurora_semantic_validator.py --phase-a          # Run Phase A only
    python aurora_semantic_validator.py --phase-b          # Run Phase B only
    python aurora_semantic_validator.py --all              # Run both phases
    python aurora_semantic_validator.py --panel <id>       # Single panel
"""

import argparse
import json
import sys
import yaml
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

# Paths
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent.parent.parent
DESIGN_DIR = ROOT_DIR / "design" / "l2_1"
INTENTS_DIR = DESIGN_DIR / "intents"
CAPABILITY_DIR = ROOT_DIR / "backend" / "AURORA_L2_CAPABILITY_REGISTRY"
REGISTRY_FILE = DESIGN_DIR / "AURORA_L2_INTENT_REGISTRY.yaml"

# Add backend to path for imports
sys.path.insert(0, str(ROOT_DIR / "backend"))


def load_all_intents() -> List[Dict[str, Any]]:
    """Load all intent YAML files."""
    intents = []
    for intent_file in INTENTS_DIR.glob("AURORA_L2_INTENT_*.yaml"):
        try:
            with open(intent_file) as f:
                intent = yaml.safe_load(f)
                if intent:
                    intents.append(intent)
        except Exception as e:
            print(f"  ⚠️  Error loading {intent_file.name}: {e}")
    return intents


def load_registry() -> Set[str]:
    """Load registered panel IDs from intent registry."""
    registered = set()
    if REGISTRY_FILE.exists():
        with open(REGISTRY_FILE) as f:
            registry = yaml.safe_load(f) or {}
            # Registry uses "intents" key, not "panels"
            for panel_id in registry.get("intents", {}):
                registered.add(panel_id)
    return registered


def load_capabilities() -> Tuple[Set[str], Dict[str, str]]:
    """Load capability IDs and their statuses from capability registry."""
    capabilities = set()
    statuses = {}

    for cap_file in CAPABILITY_DIR.glob("AURORA_L2_CAPABILITY_*.yaml"):
        try:
            with open(cap_file) as f:
                cap = yaml.safe_load(f)
                if cap:
                    cap_id = cap.get("capability_id", "")
                    if cap_id:
                        capabilities.add(cap_id)
                        statuses[cap_id] = cap.get("status", "DECLARED")
        except Exception as e:
            print(f"  ⚠️  Error loading {cap_file.name}: {e}")

    return capabilities, statuses


def run_phase_a(
    intents: List[Dict[str, Any]],
    registered_panels: Set[str],
    known_capabilities: Set[str],
    panel_filter: Optional[str] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Run Phase A (Intent Guardrails) validation.

    Returns dict mapping panel_id -> list of violations.
    """
    from app.services.ai_console_panel_adapter.intent_guardrails import run_intent_guardrails

    results = {}

    for intent in intents:
        panel_id = intent.get("panel_id", "")

        if panel_filter and panel_id != panel_filter:
            continue

        violations = run_intent_guardrails(
            intent=intent,
            all_intents=intents,
            registered_panels=registered_panels,
            known_capabilities=known_capabilities,
        )

        results[panel_id] = [
            {
                "code": str(v.code.value) if hasattr(v.code, 'value') else str(v.code),
                "severity": str(v.severity.value) if hasattr(v.severity, 'value') else str(v.severity),
                "message": v.message,
                "fix_owner": v.fix_owner,
                "fix_action": v.fix_action,
                "evidence": v.evidence,
            }
            for v in violations
        ]

    return results


def run_phase_b(
    intents: List[Dict[str, Any]],
    capability_statuses: Dict[str, str],
    panel_filter: Optional[str] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Run Phase B (Semantic Reality) validation.

    Returns dict mapping panel_id -> list of violations.
    """
    from app.services.ai_console_panel_adapter.validator_engine import TwoPhaseValidator

    validator = TwoPhaseValidator()
    results = {}

    for intent in intents:
        panel_id = intent.get("panel_id", "")

        if panel_filter and panel_id != panel_filter:
            continue

        # Extract capability info from intent
        capability_id = None
        cap_block = intent.get("capability", {})
        if cap_block:
            capability_id = cap_block.get("id", "")

        if not capability_id:
            results[panel_id] = [{
                "code": "SEM-000",
                "severity": "WARNING",
                "message": "No capability ID declared in intent",
                "fix_owner": "Product",
                "fix_action": "Add capability.id to intent YAML",
                "evidence": {},
            }]
            continue

        # Build panel spec from intent
        panel_spec = {
            "capability_binding": capability_id,
            "capability_ids": [capability_id],
            "signals": [],
        }

        # Get capability status
        status = capability_statuses.get(capability_id, "DECLARED")

        # Check SEM-002: Capability must be OBSERVED or TRUSTED
        violations = []

        if status not in ("OBSERVED", "TRUSTED"):
            violations.append({
                "code": "SEM-002",
                "severity": "BLOCKING",
                "message": f"Capability '{capability_id}' is {status}, not OBSERVED/TRUSTED",
                "fix_owner": "SDSR",
                "fix_action": "Run SDSR scenario to observe capability",
                "evidence": {
                    "capability_id": capability_id,
                    "status": status,
                },
            })

        results[panel_id] = violations

    return results


def print_results(phase: str, results: Dict[str, List[Dict[str, Any]]]) -> Tuple[int, int, int]:
    """Print validation results. Returns (total, blocking, warnings)."""
    total_violations = 0
    blocking_count = 0
    warning_count = 0

    print(f"\n{'=' * 70}")
    print(f"PHASE {phase} RESULTS")
    print(f"{'=' * 70}")

    # Group by status
    clean_panels = []
    violation_panels = []

    for panel_id, violations in results.items():
        if not violations:
            clean_panels.append(panel_id)
        else:
            violation_panels.append((panel_id, violations))

    # Print clean panels summary
    if clean_panels:
        print(f"\n✅ {len(clean_panels)} panels PASSED Phase {phase}")

    # Print violations
    if violation_panels:
        print(f"\n❌ {len(violation_panels)} panels have violations:\n")

        for panel_id, violations in sorted(violation_panels):
            print(f"  {panel_id}:")
            for v in violations:
                total_violations += 1
                severity = v.get("severity", "WARNING")
                code = v.get("code", "???")
                msg = v.get("message", "No message")

                if severity == "BLOCKING":
                    blocking_count += 1
                    icon = "🚫"
                else:
                    warning_count += 1
                    icon = "⚠️"

                print(f"    {icon} [{code}] {msg}")

                fix_owner = v.get("fix_owner", "")
                fix_action = v.get("fix_action", "")
                if fix_owner or fix_action:
                    print(f"       Fix: {fix_owner} - {fix_action}")
            print()

    return total_violations, blocking_count, warning_count


def main():
    parser = argparse.ArgumentParser(description="AURORA L2 Semantic Validator")
    parser.add_argument("--phase-a", action="store_true", help="Run Phase A only")
    parser.add_argument("--phase-b", action="store_true", help="Run Phase B only")
    parser.add_argument("--all", action="store_true", help="Run both phases")
    parser.add_argument("--panel", type=str, help="Single panel to validate")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    # Default to --all if no phase specified
    if not args.phase_a and not args.phase_b and not args.all:
        args.all = True

    print("=" * 70)
    print("AURORA L2 SEMANTIC VALIDATOR")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)

    # Load data
    print("\nLoading data...")
    intents = load_all_intents()
    print(f"  Loaded {len(intents)} intents")

    registered_panels = load_registry()
    print(f"  Loaded {len(registered_panels)} registered panels")

    capabilities, capability_statuses = load_capabilities()
    print(f"  Loaded {len(capabilities)} capabilities")

    total_blocking = 0
    total_warnings = 0
    all_results = {}

    # Phase A
    if args.phase_a or args.all:
        print("\n" + "=" * 70)
        print("RUNNING PHASE A: Intent Guardrails (Design-Time)")
        print("=" * 70)

        phase_a_results = run_phase_a(
            intents=intents,
            registered_panels=registered_panels,
            known_capabilities=capabilities,
            panel_filter=args.panel,
        )

        total, blocking, warnings = print_results("A", phase_a_results)
        total_blocking += blocking
        total_warnings += warnings
        all_results["phase_a"] = phase_a_results

    # Phase B
    if args.phase_b or args.all:
        print("\n" + "=" * 70)
        print("RUNNING PHASE B: Semantic Reality (Proof-Time)")
        print("=" * 70)

        phase_b_results = run_phase_b(
            intents=intents,
            capability_statuses=capability_statuses,
            panel_filter=args.panel,
        )

        total, blocking, warnings = print_results("B", phase_b_results)
        total_blocking += blocking
        total_warnings += warnings
        all_results["phase_b"] = phase_b_results

    # Summary
    print("\n" + "=" * 70)
    print("SEMANTIC VALIDATION SUMMARY")
    print("=" * 70)
    print(f"  Total panels checked: {len(intents)}")
    print(f"  🚫 Blocking violations: {total_blocking}")
    print(f"  ⚠️  Warnings: {total_warnings}")

    if total_blocking > 0:
        print(f"\n❌ SEMANTIC VALIDATION FAILED")
        print("   Pipeline should NOT proceed until blocking violations are fixed.")
        return_code = 1
    elif total_warnings > 0:
        print(f"\n⚠️  SEMANTIC VALIDATION PASSED WITH WARNINGS")
        print("   Pipeline may proceed, but warnings should be addressed.")
        return_code = 0
    else:
        print(f"\n✅ SEMANTIC VALIDATION PASSED")
        print("   Pipeline may proceed.")
        return_code = 0

    if args.json:
        print("\n" + json.dumps(all_results, indent=2))

    return return_code


if __name__ == "__main__":
    sys.exit(main())
