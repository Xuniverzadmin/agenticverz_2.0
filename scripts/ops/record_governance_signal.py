#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: cli
#   Execution: sync
# Role: Record governance signals from ops scripts to DB
# Callers: session_start.sh, layer_validator.py, lifecycle_qualifier_guard.py
# Allowed Imports: L6 (db)
# Forbidden Imports: L1-L5
# Reference: PIN-284 (Platform Monitoring System)
#
# PURPOSE:
# This CLI allows ops scripts (L7/L8) to write governance signals to L6.
# Platform Health Service (L4) then reads these signals.
#
# Usage:
#   python scripts/ops/record_governance_signal.py \
#     --type BLCA_STATUS \
#     --scope SYSTEM \
#     --decision CLEAN \
#     --recorded-by BLCA \
#     --reason "0 violations in 815 files"
#

"""
Record Governance Signal CLI

Allows ops scripts to write governance signals to the database.
These signals are consumed by PlatformHealthService (L4).

Signal Types:
- BLCA_STATUS: Layer validator output (CLEAN, BLOCKED, WARN)
- CI_STATUS: CI pipeline status
- LIFECYCLE_QUALIFIER_COHERENCE: Lifecycle/qualifier coherence
- QUALIFIER_STATUS: Capability qualifier state (QUALIFIED, DISQUALIFIED)
- LIFECYCLE_STATUS: Capability lifecycle state (COMPLETE, PARTIAL)

Scopes:
- SYSTEM: System-wide signal
- {CAPABILITY_NAME}: Capability-specific signal

Decisions:
- CLEAN: No issues
- BLOCKED: Critical - system/capability blocked
- WARN: Warning - degraded but functional
- PENDING: Awaiting evaluation
"""

import argparse
import os
import sys
from datetime import datetime, timezone

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.models.governance import GovernanceSignal  # noqa: E402


def get_db_url() -> str:
    """Get database URL from environment."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("ERROR: DATABASE_URL environment variable not set", file=sys.stderr)
        sys.exit(2)
    return url


def record_signal(
    signal_type: str,
    scope: str,
    decision: str,
    recorded_by: str,
    reason: str | None = None,
    constraints: dict | None = None,
) -> None:
    """Record a governance signal to the database."""
    db_url = get_db_url()
    engine = create_engine(db_url)

    with Session(engine) as session:
        now = datetime.now(timezone.utc)

        # Supersede existing signals for this scope/type
        existing = (
            session.query(GovernanceSignal)
            .filter(
                GovernanceSignal.scope == scope,
                GovernanceSignal.signal_type == signal_type,
                GovernanceSignal.superseded_at.is_(None),
            )
            .all()
        )

        for sig in existing:
            sig.superseded_at = now

        # Create new signal
        signal = GovernanceSignal(
            signal_type=signal_type,
            scope=scope,
            decision=decision,
            recorded_by=recorded_by,
            reason=reason,
            constraints=constraints,
            recorded_at=now,
        )

        session.add(signal)
        session.commit()

        print(f"Recorded: {signal_type} / {scope} = {decision}")
        if reason:
            print(f"  Reason: {reason}")


def main():
    parser = argparse.ArgumentParser(
        description="Record governance signal to database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Signal Types:
  BLCA_STATUS              Layer validator output
  CI_STATUS                CI pipeline status
  LIFECYCLE_QUALIFIER_COHERENCE  Lifecycle/qualifier coherence
  QUALIFIER_STATUS         Capability qualifier state
  LIFECYCLE_STATUS         Capability lifecycle state

Scopes:
  SYSTEM                   System-wide signal
  {CAPABILITY_NAME}        e.g., LOGS_LIST, INCIDENTS_DETAIL

Decisions:
  CLEAN                    No issues
  BLOCKED                  Critical failure
  WARN                     Warning/degraded
  PENDING                  Awaiting evaluation

Examples:
  # Record BLCA clean
  %(prog)s --type BLCA_STATUS --scope SYSTEM --decision CLEAN \\
           --recorded-by BLCA --reason "0 violations"

  # Record lifecycle coherence
  %(prog)s --type LIFECYCLE_QUALIFIER_COHERENCE --scope SYSTEM \\
           --decision COHERENT --recorded-by LIFECYCLE_GUARD

  # Record capability disqualified
  %(prog)s --type QUALIFIER_STATUS --scope KILLSWITCH_STATUS \\
           --decision DISQUALIFIED --recorded-by QUALIFIER_EVAL
        """,
    )

    parser.add_argument(
        "--type", "-t", required=True, help="Signal type (BLCA_STATUS, CI_STATUS, etc.)"
    )
    parser.add_argument(
        "--scope", "-s", required=True, help="Signal scope (SYSTEM or capability name)"
    )
    parser.add_argument(
        "--decision",
        "-d",
        required=True,
        choices=[
            "CLEAN",
            "BLOCKED",
            "WARN",
            "PENDING",
            "COHERENT",
            "INCOHERENT",
            "QUALIFIED",
            "DISQUALIFIED",
            "COMPLETE",
            "PARTIAL",
            "HEALTHY",
            "DEGRADED",
        ],
        help="Signal decision",
    )
    parser.add_argument(
        "--recorded-by",
        "-r",
        required=True,
        help="Who recorded this signal (BLCA, CI, LIFECYCLE_GUARD, etc.)",
    )
    parser.add_argument("--reason", help="Human-readable reason")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress output")

    args = parser.parse_args()

    try:
        record_signal(
            signal_type=args.type,
            scope=args.scope,
            decision=args.decision,
            recorded_by=args.recorded_by,
            reason=args.reason,
        )
    except Exception as e:
        if not args.quiet:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
