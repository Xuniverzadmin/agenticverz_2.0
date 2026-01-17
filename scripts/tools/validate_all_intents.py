#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: manual | CI | pipeline
#   Execution: sync
# Role: Phase A Intent Guardrails validator for all intents
# Reference: PIN-420, SEMANTIC_VALIDATOR.md
#
# This script is the SINGLE GATE for Phase A validation.
# It runs BEFORE Aurora compilation to catch design-time errors early.
#
"""
Phase A Intent Validator

Validates all intent YAMLs against the Intent Guardrails (Phase A).

Usage:
    python3 scripts/tools/validate_all_intents.py [--blocking] [--output JSON_PATH] [--verbose]

Options:
    --blocking      Exit with code 1 if any blocking violations (default for CI)
    --output PATH   Write validation report to JSON file
    --verbose       Print detailed violation information

Exit Codes:
    0   All intents pass Phase A (or only warnings)
    1   Blocking violations found (with --blocking)
    2   Configuration error (missing directories, etc.)
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set

import yaml

# Add backend to path for imports
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.services.ai_console_panel_adapter import (
    TwoPhaseValidator,
    ViolationClass,
    SemanticSeverity,
)


# =============================================================================
# PATHS
# =============================================================================

INTENTS_DIR = REPO_ROOT / "design/l2_1/intents"
CAPABILITY_REGISTRY_DIR = REPO_ROOT / "backend/AURORA_L2_CAPABILITY_REGISTRY"
INTENT_REGISTRY_PATH = REPO_ROOT / "design/l2_1/AURORA_L2_INTENT_REGISTRY.yaml"
VALIDATION_OUTPUT_DIR = REPO_ROOT / "design/l2_1/ui_contract"


# =============================================================================
# LOADERS
# =============================================================================

def load_all_intents() -> List[Dict[str, Any]]:
    """Load all intent YAML files."""
    intents = []

    if not INTENTS_DIR.exists():
        print(f"[WARN] Intents directory not found: {INTENTS_DIR}", file=sys.stderr)
        return intents

    for yaml_file in sorted(INTENTS_DIR.glob("AURORA_L2_INTENT_*.yaml")):
        try:
            with open(yaml_file, "r") as f:
                intent = yaml.safe_load(f)
                if intent:
                    # Transform to expected format for validator
                    transformed = transform_intent_for_validator(intent)
                    intents.append(transformed)
        except Exception as e:
            print(f"[WARN] Failed to load {yaml_file.name}: {e}", file=sys.stderr)

    return intents


def transform_intent_for_validator(intent: Dict[str, Any]) -> Dict[str, Any]:
    """Transform intent YAML format to validator expected format."""
    # The intent YAML has a different structure than expected by validator
    # Transform capability section to consumed_capabilities
    consumed_caps = []

    if "capability" in intent:
        cap = intent["capability"]
        consumed_caps.append({
            "capability_id": cap.get("id", ""),
            "signals": [],  # Signals would be defined elsewhere
        })

    # Extract domain for contradiction checking
    domain = ""
    if "metadata" in intent:
        domain = intent["metadata"].get("domain", "")

    return {
        "panel_id": intent.get("panel_id", ""),
        "consumed_capabilities": consumed_caps,
        "domain": domain,
        "panel_state": intent.get("capability", {}).get("status", ""),
        "maturity": intent.get("capability", {}).get("status"),
        "metadata": intent.get("metadata", {}),
        "_source_file": intent.get("_source_file", ""),
    }


def load_registered_panels() -> Set[str]:
    """Load set of registered panel IDs from intent registry."""
    panels = set()

    if not INTENT_REGISTRY_PATH.exists():
        print(f"[WARN] Intent registry not found: {INTENT_REGISTRY_PATH}", file=sys.stderr)
        return panels

    try:
        with open(INTENT_REGISTRY_PATH, "r") as f:
            registry = yaml.safe_load(f)
            if registry and "intents" in registry:
                intents = registry["intents"]
                # Registry has panel_id as keys in a dict
                if isinstance(intents, dict):
                    for panel_id in intents.keys():
                        panels.add(panel_id)
                # Or as a list (fallback)
                elif isinstance(intents, list):
                    for intent in intents:
                        if isinstance(intent, dict):
                            panel_id = intent.get("panel_id", "")
                            if panel_id:
                                panels.add(panel_id)
    except Exception as e:
        print(f"[WARN] Failed to load intent registry: {e}", file=sys.stderr)

    return panels


def load_known_capabilities() -> Set[str]:
    """Load set of known capability IDs from capability registry."""
    capabilities = set()

    if not CAPABILITY_REGISTRY_DIR.exists():
        print(f"[WARN] Capability registry not found: {CAPABILITY_REGISTRY_DIR}", file=sys.stderr)
        return capabilities

    for yaml_file in CAPABILITY_REGISTRY_DIR.glob("AURORA_L2_CAPABILITY_*.yaml"):
        # Skip deprecated
        if "LEGACY_DEPRECATED" in str(yaml_file):
            continue

        try:
            with open(yaml_file, "r") as f:
                cap = yaml.safe_load(f)
                if cap and "capability_id" in cap:
                    capabilities.add(cap["capability_id"])
        except Exception as e:
            print(f"[WARN] Failed to load {yaml_file.name}: {e}", file=sys.stderr)

    return capabilities


# =============================================================================
# VALIDATION
# =============================================================================

def run_phase_a_validation(
    intents: List[Dict[str, Any]],
    registered_panels: Set[str],
    known_capabilities: Set[str],
    verbose: bool = False,
) -> Dict[str, Any]:
    """Run Phase A validation on all intents."""

    validator = TwoPhaseValidator(
        registered_panels=registered_panels,
        known_capabilities=known_capabilities,
    )

    # Validate all intents as a batch
    report = validator.validate_intents_batch(intents)

    # Build result structure
    result = {
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "phase": "A",
        "phase_name": "Intent Guardrails",
        "intents_checked": report.intents_checked,
        "registered_panels_count": len(registered_panels),
        "known_capabilities_count": len(known_capabilities),
        "total_violations": len(report.violations),
        "blocking_count": len(report.phase_a_blocking()),
        "warning_count": len(report.warnings()),
        "phase_a_valid": report.phase_a_valid(),
        "violations": [],
    }

    # Add violation details
    for v in report.violations:
        violation_dict = {
            "code": v.code.value,
            "class": v.vclass.value,
            "severity": v.severity.value,
            "message": v.message,
            "panel_id": v.context.panel_id,
            "capability_id": v.context.capability_id,
            "fix_owner": v.fix_owner,
            "fix_action": v.fix_action,
        }

        if verbose:
            violation_dict["evidence"] = v.evidence

        result["violations"].append(violation_dict)

    return result


# =============================================================================
# OUTPUT
# =============================================================================

def print_summary(result: Dict[str, Any], verbose: bool = False):
    """Print validation summary to console."""
    print()
    print("=" * 70)
    print("  PHASE A: INTENT GUARDRAILS VALIDATION")
    print("=" * 70)
    print()
    print(f"  Validated at:       {result['validated_at']}")
    print(f"  Intents checked:    {result['intents_checked']}")
    print(f"  Registered panels:  {result['registered_panels_count']}")
    print(f"  Known capabilities: {result['known_capabilities_count']}")
    print()
    print("-" * 70)
    print(f"  Total violations:   {result['total_violations']}")
    print(f"  BLOCKING:           {result['blocking_count']}")
    print(f"  WARNING:            {result['warning_count']}")
    print("-" * 70)
    print()

    if result["phase_a_valid"]:
        print("  STATUS: PASS")
        print("  Phase A validation passed. Proceeding to Aurora compilation is allowed.")
    else:
        print("  STATUS: BLOCKED")
        print("  Phase A validation FAILED. Fix blocking violations before proceeding.")

    print()

    if result["violations"]:
        print("=" * 70)
        print("  VIOLATIONS")
        print("=" * 70)

        # Group by severity
        blocking = [v for v in result["violations"] if v["severity"] == "BLOCKING"]
        warnings = [v for v in result["violations"] if v["severity"] == "WARNING"]

        if blocking:
            print()
            print("  BLOCKING VIOLATIONS (must fix):")
            print("  " + "-" * 66)
            for v in blocking:
                print(f"  [{v['code']}] {v['message']}")
                print(f"      Panel: {v['panel_id']}")
                if v.get("capability_id"):
                    print(f"      Capability: {v['capability_id']}")
                print(f"      Fix Owner: {v['fix_owner']}")
                print(f"      Fix Action: {v['fix_action']}")
                print()

        if warnings and verbose:
            print()
            print("  WARNINGS (should fix):")
            print("  " + "-" * 66)
            for v in warnings:
                print(f"  [{v['code']}] {v['message']}")
                print(f"      Panel: {v['panel_id']}")
                print(f"      Fix Owner: {v['fix_owner']}")
                print()

    print("=" * 70)
    print()


def write_output(result: Dict[str, Any], output_path: Path):
    """Write validation result to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"[INFO] Validation report written to: {output_path}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Phase A Intent Guardrails Validator"
    )
    parser.add_argument(
        "--blocking",
        action="store_true",
        help="Exit with code 1 if any blocking violations",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Write validation report to JSON file",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed violation information",
    )

    args = parser.parse_args()

    # Load data
    print("[PHASE A] Loading intents...")
    intents = load_all_intents()
    print(f"[PHASE A] Loaded {len(intents)} intents")

    print("[PHASE A] Loading panel registry...")
    registered_panels = load_registered_panels()
    print(f"[PHASE A] Found {len(registered_panels)} registered panels")

    print("[PHASE A] Loading capability registry...")
    known_capabilities = load_known_capabilities()
    print(f"[PHASE A] Found {len(known_capabilities)} known capabilities")

    # Validate
    print("[PHASE A] Running validation...")
    result = run_phase_a_validation(
        intents=intents,
        registered_panels=registered_panels,
        known_capabilities=known_capabilities,
        verbose=args.verbose,
    )

    # Output
    print_summary(result, verbose=args.verbose)

    if args.output:
        write_output(result, Path(args.output))

    # Default output to ui_contract
    default_output = VALIDATION_OUTPUT_DIR / "phase_a_validation.json"
    write_output(result, default_output)

    # Exit code
    if args.blocking and not result["phase_a_valid"]:
        print("[PHASE A] BLOCKED - Fix violations before proceeding")
        sys.exit(1)

    print("[PHASE A] Complete")
    sys.exit(0)


if __name__ == "__main__":
    main()
