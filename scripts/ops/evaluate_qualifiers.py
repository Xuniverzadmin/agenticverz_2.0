#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci, manual
#   Execution: sync
# Role: Governance Qualifier Evaluation Engine
# Callers: preflight.py, CI workflows, Claude sessions
# Allowed Imports: L8 (stdlib only)
# Forbidden Imports: L1-L7 (must be self-contained)
# Reference: PIN-281 (L7→L2 Structural Closure), GOVERNANCE_QUALIFIERS.yaml
#
# GOVERNANCE NOTE:
# This script is the AUTHORITATIVE source for qualifier evaluation.
# It reads CAPABILITY_LIFECYCLE.yaml and produces QUALIFIER_EVALUATION.yaml.
# No human override is permitted. No "almost qualified" state exists.

"""
Governance Qualifier Evaluation Engine

Evaluates capabilities against GQ-L2-CONTRACT-READY qualification rules.

Usage:
  python scripts/ops/evaluate_qualifiers.py                    # Evaluate all, print summary
  python scripts/ops/evaluate_qualifiers.py --generate         # Generate QUALIFIER_EVALUATION.yaml
  python scripts/ops/evaluate_qualifiers.py --check LOGS_LIST  # Check specific capability
  python scripts/ops/evaluate_qualifiers.py --qualified-only   # List only QUALIFIED capabilities
  python scripts/ops/evaluate_qualifiers.py --ci               # CI mode (exit 1 if any DISQUALIFIED)

Exit codes:
  0 - All evaluated capabilities are QUALIFIED (or --generate mode)
  1 - At least one capability is DISQUALIFIED or CONDITIONALLY_QUALIFIED
  2 - Script error
"""

import argparse
import sys
import yaml
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# =============================================================================
# QUALIFIER STATES
# =============================================================================


class QualifierState(Enum):
    QUALIFIED = "QUALIFIED"
    CONDITIONALLY_QUALIFIED = "CONDITIONALLY_QUALIFIED"
    DISQUALIFIED = "DISQUALIFIED"


# =============================================================================
# EVALUATION RESULT
# =============================================================================


@dataclass
class QualificationResult:
    """Result of evaluating a capability against GQ-L2-CONTRACT-READY."""

    capability: str
    qualifier: str = "GQ-L2-CONTRACT-READY"
    state: QualifierState = QualifierState.DISQUALIFIED
    passed_gates: List[str] = field(default_factory=list)
    failed_gates: List[str] = field(default_factory=list)
    pending_gates: List[str] = field(default_factory=list)
    disqualification_reasons: List[str] = field(default_factory=list)
    evidence_source: str = "docs/governance/CAPABILITY_LIFECYCLE.yaml"

    def to_dict(self) -> dict:
        return {
            "capability": self.capability,
            "qualifier": self.qualifier,
            "state": self.state.value,
            "passed_gates": self.passed_gates,
            "failed_gates": self.failed_gates,
            "pending_gates": self.pending_gates,
            "disqualification_reasons": self.disqualification_reasons,
            "evidence_source": self.evidence_source,
        }


# =============================================================================
# GATE REQUIREMENTS
# =============================================================================

# All gates required for QUALIFIED state
REQUIRED_GATES = [
    "GATE-1",  # L2 imports L3 only
    "GATE-2",  # L3 imports L4 only
    "GATE-3",  # L4 service has explicit responsibility
    "GATE-4",  # L5 executor or bounded-read proof
    "GATE-5",  # L7 authority exists
    "GATE-6",  # BLCA passes
    "GATE-7",  # CI guards active
    "GATE-8",  # Contract tests pass
]

# Gates required for CONDITIONALLY_QUALIFIED state
CONDITIONAL_GATES = [
    "GATE-1",
    "GATE-2",
    "GATE-3",
]

# Gates that can be missing for CONDITIONALLY_QUALIFIED
OPTIONAL_FOR_CONDITIONAL = [
    "GATE-7",
    "GATE-8",
]


# =============================================================================
# EVALUATION LOGIC
# =============================================================================


def evaluate_capability(
    capability_name: str, capability_data: dict
) -> QualificationResult:
    """Evaluate a single capability against GQ-L2-CONTRACT-READY."""
    result = QualificationResult(capability=capability_name)

    gates = capability_data.get("gates", {})

    # Categorize gates
    for gate in REQUIRED_GATES:
        gate_status = gates.get(gate, "PENDING")
        if gate_status == "PASS":
            result.passed_gates.append(gate)
        elif gate_status == "FAIL":
            result.failed_gates.append(gate)
            result.disqualification_reasons.append(f"{gate} failed")
        elif gate_status == "N/A":
            # N/A is acceptable for some gates (e.g., GATE-4 for read-only)
            result.passed_gates.append(f"{gate} (N/A)")
        else:
            result.pending_gates.append(gate)
            result.disqualification_reasons.append(f"{gate} pending")

    # Determine state
    all_passed = len(result.failed_gates) == 0 and len(result.pending_gates) == 0

    if all_passed:
        result.state = QualifierState.QUALIFIED
        result.disqualification_reasons = []  # Clear reasons if qualified
    else:
        # Check for CONDITIONALLY_QUALIFIED
        conditional_met = True
        for gate in CONDITIONAL_GATES:
            if gate not in [g.split(" ")[0] for g in result.passed_gates]:
                conditional_met = False
                break

        # Check that only optional gates are missing
        missing_required = [
            g
            for g in result.failed_gates + result.pending_gates
            if g not in OPTIONAL_FOR_CONDITIONAL
        ]

        if conditional_met and len(missing_required) == 0:
            result.state = QualifierState.CONDITIONALLY_QUALIFIED
        else:
            result.state = QualifierState.DISQUALIFIED

    return result


def load_capability_lifecycle(repo_root: Path) -> dict:
    """Load CAPABILITY_LIFECYCLE.yaml."""
    lifecycle_path = repo_root / "docs" / "governance" / "CAPABILITY_LIFECYCLE.yaml"
    if not lifecycle_path.exists():
        raise FileNotFoundError(
            f"CAPABILITY_LIFECYCLE.yaml not found at {lifecycle_path}"
        )

    with open(lifecycle_path, "r") as f:
        return yaml.safe_load(f)


def evaluate_all_capabilities(repo_root: Path) -> Dict[str, QualificationResult]:
    """Evaluate all capabilities in CAPABILITY_LIFECYCLE.yaml."""
    lifecycle = load_capability_lifecycle(repo_root)
    capabilities = lifecycle.get("capabilities", {})

    results = {}
    for name, data in capabilities.items():
        results[name] = evaluate_capability(name, data)

    return results


# =============================================================================
# YAML GENERATION
# =============================================================================


def generate_qualifier_evaluation(
    repo_root: Path, results: Dict[str, QualificationResult]
) -> str:
    """Generate QUALIFIER_EVALUATION.yaml content."""
    output = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator": "scripts/ops/evaluate_qualifiers.py",
        "qualifier": "GQ-L2-CONTRACT-READY",
        "source": "docs/governance/CAPABILITY_LIFECYCLE.yaml",
        "summary": {
            "total": len(results),
            "qualified": sum(
                1 for r in results.values() if r.state == QualifierState.QUALIFIED
            ),
            "conditionally_qualified": sum(
                1
                for r in results.values()
                if r.state == QualifierState.CONDITIONALLY_QUALIFIED
            ),
            "disqualified": sum(
                1 for r in results.values() if r.state == QualifierState.DISQUALIFIED
            ),
        },
        "capabilities": {},
    }

    for name, result in sorted(results.items()):
        output["capabilities"][name] = {
            "state": result.state.value,
            "passed_gates": result.passed_gates,
            "failed_gates": result.failed_gates,
            "pending_gates": result.pending_gates,
            "disqualification_reasons": result.disqualification_reasons
            if result.disqualification_reasons
            else None,
        }

    # Clean up None values
    for cap_data in output["capabilities"].values():
        if cap_data["disqualification_reasons"] is None:
            del cap_data["disqualification_reasons"]
        if not cap_data["failed_gates"]:
            del cap_data["failed_gates"]
        if not cap_data["pending_gates"]:
            del cap_data["pending_gates"]

    return yaml.dump(
        output, default_flow_style=False, sort_keys=False, allow_unicode=True
    )


def write_qualifier_evaluation(
    repo_root: Path, results: Dict[str, QualificationResult]
):
    """Write QUALIFIER_EVALUATION.yaml to disk."""
    content = generate_qualifier_evaluation(repo_root, results)
    output_path = repo_root / "docs" / "governance" / "QUALIFIER_EVALUATION.yaml"
    with open(output_path, "w") as f:
        f.write(content)
    return output_path


# =============================================================================
# CLI OUTPUT
# =============================================================================


def print_summary(results: Dict[str, QualificationResult], verbose: bool = False):
    """Print evaluation summary to console."""
    qualified = [r for r in results.values() if r.state == QualifierState.QUALIFIED]
    conditional = [
        r for r in results.values() if r.state == QualifierState.CONDITIONALLY_QUALIFIED
    ]
    disqualified = [
        r for r in results.values() if r.state == QualifierState.DISQUALIFIED
    ]

    print("=" * 70)
    print("GOVERNANCE QUALIFIER EVALUATION: GQ-L2-CONTRACT-READY")
    print("=" * 70)
    print()

    # Summary
    print(f"Total capabilities: {len(results)}")
    print(f"  QUALIFIED:                {len(qualified)}")
    print(f"  CONDITIONALLY_QUALIFIED:  {len(conditional)}")
    print(f"  DISQUALIFIED:             {len(disqualified)}")
    print()

    # QUALIFIED
    if qualified:
        print("-" * 70)
        print("QUALIFIED (L2 testing and claims PERMITTED):")
        print("-" * 70)
        for r in sorted(qualified, key=lambda x: x.capability):
            print(f"  ✓ {r.capability}")
        print()

    # CONDITIONALLY_QUALIFIED
    if conditional:
        print("-" * 70)
        print("CONDITIONALLY_QUALIFIED (Structural work only, NO testing):")
        print("-" * 70)
        for r in sorted(conditional, key=lambda x: x.capability):
            missing = ", ".join(r.failed_gates + r.pending_gates)
            print(f"  ◐ {r.capability}")
            if verbose and missing:
                print(f"      Missing: {missing}")
        print()

    # DISQUALIFIED
    if disqualified:
        print("-" * 70)
        print("DISQUALIFIED (All product claims FORBIDDEN):")
        print("-" * 70)
        for r in sorted(disqualified, key=lambda x: x.capability):
            print(f"  ✗ {r.capability}")
            if verbose and r.disqualification_reasons:
                for reason in r.disqualification_reasons:
                    print(f"      - {reason}")
        print()

    # Final verdict
    print("=" * 70)
    if len(disqualified) == 0 and len(conditional) == 0:
        print("VERDICT: ALL QUALIFIED")
        print("L2 testing and product claims are PERMITTED for all capabilities.")
    elif len(disqualified) == 0:
        print(f"VERDICT: {len(qualified)} QUALIFIED, {len(conditional)} CONDITIONAL")
        print("Some capabilities require additional gates before L2 testing.")
    else:
        print(f"VERDICT: {len(disqualified)} DISQUALIFIED")
        print("Structural repair required before any product claims.")
    print("=" * 70)


def print_capability(result: QualificationResult):
    """Print detailed info for a single capability."""
    print(f"Capability: {result.capability}")
    print(f"Qualifier:  {result.qualifier}")
    print(f"State:      {result.state.value}")
    print()
    print("Gates:")
    for gate in result.passed_gates:
        print(f"  ✓ {gate}")
    for gate in result.failed_gates:
        print(f"  ✗ {gate}")
    for gate in result.pending_gates:
        print(f"  ○ {gate} (pending)")
    print()
    if result.disqualification_reasons:
        print("Disqualification Reasons:")
        for reason in result.disqualification_reasons:
            print(f"  - {reason}")
    else:
        print("No disqualification reasons.")


# =============================================================================
# PUBLIC API (for import by other scripts)
# =============================================================================


def get_qualified_capabilities(repo_root: Optional[Path] = None) -> List[str]:
    """Return list of QUALIFIED capability names."""
    if repo_root is None:
        repo_root = Path(__file__).parent.parent.parent
    results = evaluate_all_capabilities(repo_root)
    return [
        r.capability for r in results.values() if r.state == QualifierState.QUALIFIED
    ]


def is_capability_qualified(capability: str, repo_root: Optional[Path] = None) -> bool:
    """Check if a specific capability is QUALIFIED."""
    if repo_root is None:
        repo_root = Path(__file__).parent.parent.parent
    results = evaluate_all_capabilities(repo_root)
    if capability not in results:
        return False
    return results[capability].state == QualifierState.QUALIFIED


def check_all_qualified(
    capabilities: List[str], repo_root: Optional[Path] = None
) -> Tuple[bool, List[str]]:
    """Check if all specified capabilities are QUALIFIED.

    Returns (all_qualified, list_of_unqualified).
    """
    if repo_root is None:
        repo_root = Path(__file__).parent.parent.parent
    results = evaluate_all_capabilities(repo_root)

    unqualified = []
    for cap in capabilities:
        if cap not in results:
            unqualified.append(f"{cap} (unknown)")
        elif results[cap].state != QualifierState.QUALIFIED:
            unqualified.append(f"{cap} ({results[cap].state.value})")

    return len(unqualified) == 0, unqualified


# =============================================================================
# GOVERNANCE SIGNAL RECORDING
# =============================================================================


def record_governance_signals(results: Dict[str, QualificationResult], db_url: str):
    """
    Record per-capability QUALIFIER_STATUS signals to the database.

    This enables PlatformHealthService (L4) to read qualifier states.
    Signals are recorded for each capability with their qualification state.
    """
    try:
        import os
        import sys

        sys.path.insert(
            0, os.path.join(os.path.dirname(__file__), "..", "..", "backend")
        )

        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session
        from app.models.governance import GovernanceSignal

        engine = create_engine(db_url)
        now = datetime.now(timezone.utc)

        with Session(engine) as session:
            for name, result in results.items():
                # Supersede existing signals
                existing = (
                    session.query(GovernanceSignal)
                    .filter(
                        GovernanceSignal.scope == name,
                        GovernanceSignal.signal_type == "QUALIFIER_STATUS",
                        GovernanceSignal.superseded_at.is_(None),
                    )
                    .all()
                )

                for sig in existing:
                    sig.superseded_at = now

                # Create new signal
                signal = GovernanceSignal(
                    signal_type="QUALIFIER_STATUS",
                    scope=name,
                    decision=result.state.value,
                    recorded_by="QUALIFIER_EVAL",
                    reason="Evaluated against GQ-L2-CONTRACT-READY",
                    recorded_at=now,
                )
                session.add(signal)

            session.commit()

        print(f"Recorded {len(results)} QUALIFIER_STATUS signals to database")

    except Exception as e:
        print(f"WARNING: Could not record governance signals: {e}")


# =============================================================================
# MAIN
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Governance Qualifier Evaluation Engine"
    )
    parser.add_argument(
        "--generate",
        "-g",
        action="store_true",
        help="Generate QUALIFIER_EVALUATION.yaml",
    )
    parser.add_argument(
        "--record-signals",
        action="store_true",
        help="Record governance signals to database (requires DATABASE_URL)",
    )
    parser.add_argument(
        "--check",
        "-c",
        type=str,
        metavar="CAPABILITY",
        help="Check specific capability",
    )
    parser.add_argument(
        "--qualified-only",
        "-q",
        action="store_true",
        help="List only QUALIFIED capabilities",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )
    parser.add_argument(
        "--ci", action="store_true", help="CI mode (exit 1 if any not QUALIFIED)"
    )
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent.parent

    try:
        results = evaluate_all_capabilities(repo_root)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)

    # Handle specific capability check
    if args.check:
        if args.check not in results:
            print(f"ERROR: Unknown capability '{args.check}'", file=sys.stderr)
            sys.exit(2)
        print_capability(results[args.check])
        if results[args.check].state == QualifierState.QUALIFIED:
            sys.exit(0)
        else:
            sys.exit(1)

    # Handle qualified-only mode
    if args.qualified_only:
        qualified = [
            r.capability
            for r in results.values()
            if r.state == QualifierState.QUALIFIED
        ]
        for cap in sorted(qualified):
            print(cap)
        sys.exit(0)

    # Handle generate mode
    if args.generate:
        output_path = write_qualifier_evaluation(repo_root, results)
        print(f"Generated: {output_path}")
        print_summary(results, verbose=args.verbose)

        # Optionally record signals
        if args.record_signals:
            import os

            db_url = os.environ.get("DATABASE_URL")
            if db_url:
                record_governance_signals(results, db_url)
            else:
                print("WARNING: DATABASE_URL not set, skipping signal recording")

        sys.exit(0)

    # Handle record-signals only mode
    if args.record_signals:
        import os

        db_url = os.environ.get("DATABASE_URL")
        if db_url:
            record_governance_signals(results, db_url)
            print_summary(results, verbose=args.verbose)
        else:
            print("ERROR: DATABASE_URL not set", file=sys.stderr)
            sys.exit(2)
        sys.exit(0)

    # Default: print summary
    print_summary(results, verbose=args.verbose)

    # CI mode: exit 1 if any not qualified
    if args.ci:
        qualified = [r for r in results.values() if r.state == QualifierState.QUALIFIED]
        if len(qualified) < len(results):
            sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
