#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: pipeline (post-compiler, pre-publish)
#   Execution: sync
# Role: Projection Diff Guard - prevent silent UI drift
# Reference: PIN-417 (HIL v1 Phase 3)
#
# PURPOSE:
# Answer ONE question only:
# "Did the compiled projection change in any way we did not explicitly allow?"
#
# PLACEMENT IN PIPELINE:
# 1. SDSR observation applied
# 2. Compiler generates new projection
# 3. >>> PROJECTION DIFF GUARD <<< (this script)
# 4. If PASS → copy to public/projection/
# 5. If FAIL → block publish, capability does not advance
#
# OUTPUT:
# Machine-readable JSON. No logs. No prose. Just truth.

"""
Projection Diff Guard

Enforces 5 rules to prevent silent UI drift:
- PDG-001: No silent panel creation/deletion
- PDG-002: No domain/subdomain drift
- PDG-003: Binding status changes are explicit
- PDG-004: panel_class is immutable post-declaration
- PDG-005: Provenance cannot be removed from interpretation panels
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any


# =============================================================================
# Rule Definitions
# =============================================================================

ALLOWED_BINDING_TRANSITIONS = {
    # From → To (allowed)
    ("DRAFT", "BOUND"),
    ("DECLARED", "DRAFT"),
    ("DECLARED", "OBSERVED"),
    ("OBSERVED", "BOUND"),
    ("DRAFT", "OBSERVED"),
    # INFO can transition to DRAFT or stay INFO
    ("INFO", "DRAFT"),
    ("INFO", "INFO"),
}

FORBIDDEN_BINDING_TRANSITIONS = {
    # These are always blocked
    ("UNBOUND", "BOUND"),
    ("BOUND", "UNBOUND"),
    ("BOUND", "DRAFT"),  # Can't downgrade
}


# =============================================================================
# Violation Data Structure
# =============================================================================

class Violation:
    def __init__(self, rule: str, panel_id: str, field: str, old: Any, new: Any, message: str):
        self.rule = rule
        self.panel_id = panel_id
        self.field = field
        self.old = old
        self.new = new
        self.message = message

    def to_dict(self) -> dict:
        return {
            "rule": self.rule,
            "panel_id": self.panel_id,
            "field": self.field,
            "old": self.old,
            "new": self.new,
            "message": self.message,
        }


# =============================================================================
# Guard Implementation
# =============================================================================

class ProjectionDiffGuard:
    def __init__(self, allowlist: dict | None = None):
        self.allowlist = allowlist or {}
        self.violations: list[Violation] = []

    def check(self, old_projection: dict, new_projection: dict) -> bool:
        """Run all checks. Returns True if passed, False if violations found."""
        self.violations = []

        old_panels = self._extract_panels(old_projection)
        new_panels = self._extract_panels(new_projection)

        self._check_pdg001_panel_creation_deletion(old_panels, new_panels)
        self._check_pdg002_domain_subdomain_drift(old_panels, new_panels)
        self._check_pdg003_binding_status_transitions(old_panels, new_panels)
        self._check_pdg004_panel_class_immutability(old_panels, new_panels)
        self._check_pdg005_provenance_preservation(old_panels, new_panels)

        return len(self.violations) == 0

    def _extract_panels(self, projection: dict) -> dict[str, dict]:
        """Extract panel_id → panel mapping from projection."""
        panels = {}
        for domain in projection.get("domains", []):
            for panel in domain.get("panels", []):
                panel_id = panel.get("panel_id")
                if panel_id:
                    panels[panel_id] = {
                        **panel,
                        "_domain": domain.get("domain"),
                    }
        return panels

    def _is_allowlisted(self, panel_id: str, rule: str) -> bool:
        """Check if panel is allowlisted for a specific rule."""
        allowlisted_panels = self.allowlist.get("panels", [])
        allowlisted_rules = self.allowlist.get("rules", {})

        # Check if panel is globally allowlisted
        if panel_id in allowlisted_panels:
            return True

        # Check if panel is allowlisted for specific rule
        rule_allowlist = allowlisted_rules.get(rule, [])
        return panel_id in rule_allowlist

    # -------------------------------------------------------------------------
    # PDG-001: No Silent Panel Creation/Deletion
    # -------------------------------------------------------------------------

    def _check_pdg001_panel_creation_deletion(
        self, old_panels: dict, new_panels: dict
    ):
        """Any added or removed panel_id → BLOCK (unless allowlisted)."""
        old_ids = set(old_panels.keys())
        new_ids = set(new_panels.keys())

        # Check for deletions
        deleted = old_ids - new_ids
        for panel_id in deleted:
            if not self._is_allowlisted(panel_id, "PDG-001"):
                self.violations.append(Violation(
                    rule="PDG-001",
                    panel_id=panel_id,
                    field="panel_id",
                    old=panel_id,
                    new=None,
                    message=f"Panel '{panel_id}' was deleted without allowlist",
                ))

        # Check for additions
        added = new_ids - old_ids
        for panel_id in added:
            if not self._is_allowlisted(panel_id, "PDG-001"):
                self.violations.append(Violation(
                    rule="PDG-001",
                    panel_id=panel_id,
                    field="panel_id",
                    old=None,
                    new=panel_id,
                    message=f"Panel '{panel_id}' was added without allowlist",
                ))

    # -------------------------------------------------------------------------
    # PDG-002: No Domain/Subdomain Drift
    # -------------------------------------------------------------------------

    def _check_pdg002_domain_subdomain_drift(
        self, old_panels: dict, new_panels: dict
    ):
        """Domain, subdomain, topic changes → BLOCK."""
        common_ids = set(old_panels.keys()) & set(new_panels.keys())

        for panel_id in common_ids:
            old = old_panels[panel_id]
            new = new_panels[panel_id]

            # Check domain
            if old.get("_domain") != new.get("_domain"):
                self.violations.append(Violation(
                    rule="PDG-002",
                    panel_id=panel_id,
                    field="domain",
                    old=old.get("_domain"),
                    new=new.get("_domain"),
                    message=f"Panel '{panel_id}' domain changed",
                ))

            # Check subdomain
            if old.get("subdomain") != new.get("subdomain"):
                self.violations.append(Violation(
                    rule="PDG-002",
                    panel_id=panel_id,
                    field="subdomain",
                    old=old.get("subdomain"),
                    new=new.get("subdomain"),
                    message=f"Panel '{panel_id}' subdomain changed",
                ))

            # Check topic
            if old.get("topic") != new.get("topic"):
                self.violations.append(Violation(
                    rule="PDG-002",
                    panel_id=panel_id,
                    field="topic",
                    old=old.get("topic"),
                    new=new.get("topic"),
                    message=f"Panel '{panel_id}' topic changed",
                ))

    # -------------------------------------------------------------------------
    # PDG-003: Binding Status Changes Are Explicit
    # -------------------------------------------------------------------------

    def _check_pdg003_binding_status_transitions(
        self, old_panels: dict, new_panels: dict
    ):
        """Only allowed binding transitions; forbidden ones → BLOCK."""
        common_ids = set(old_panels.keys()) & set(new_panels.keys())

        for panel_id in common_ids:
            old_status = old_panels[panel_id].get("binding_status", "INFO")
            new_status = new_panels[panel_id].get("binding_status", "INFO")

            if old_status == new_status:
                continue

            transition = (old_status, new_status)

            # Check forbidden transitions first
            if transition in FORBIDDEN_BINDING_TRANSITIONS:
                self.violations.append(Violation(
                    rule="PDG-003",
                    panel_id=panel_id,
                    field="binding_status",
                    old=old_status,
                    new=new_status,
                    message=f"Forbidden binding transition: {old_status} → {new_status}",
                ))
            # Check if transition is allowed
            elif transition not in ALLOWED_BINDING_TRANSITIONS:
                # Unknown transition - warn but don't block by default
                # Could make this stricter
                pass

    # -------------------------------------------------------------------------
    # PDG-004: panel_class Is Immutable Post-Declaration
    # -------------------------------------------------------------------------

    def _check_pdg004_panel_class_immutability(
        self, old_panels: dict, new_panels: dict
    ):
        """Execution ↔ interpretation flip → BLOCK."""
        common_ids = set(old_panels.keys()) & set(new_panels.keys())

        for panel_id in common_ids:
            old_class = old_panels[panel_id].get("panel_class", "execution")
            new_class = new_panels[panel_id].get("panel_class", "execution")

            if old_class != new_class:
                self.violations.append(Violation(
                    rule="PDG-004",
                    panel_id=panel_id,
                    field="panel_class",
                    old=old_class,
                    new=new_class,
                    message=f"Panel class changed from '{old_class}' to '{new_class}' (immutable)",
                ))

    # -------------------------------------------------------------------------
    # PDG-005: Provenance Cannot Be Removed
    # -------------------------------------------------------------------------

    def _check_pdg005_provenance_preservation(
        self, old_panels: dict, new_panels: dict
    ):
        """Interpretation panel losing derived_from → BLOCK."""
        common_ids = set(old_panels.keys()) & set(new_panels.keys())

        for panel_id in common_ids:
            old = old_panels[panel_id]
            new = new_panels[panel_id]

            # Only check interpretation panels
            if old.get("panel_class") != "interpretation":
                continue

            old_provenance = old.get("provenance", {})
            new_provenance = new.get("provenance", {})

            old_derived = old_provenance.get("derived_from", [])
            new_derived = new_provenance.get("derived_from", [])

            # Check if derived_from was removed entirely
            if old_derived and not new_derived:
                self.violations.append(Violation(
                    rule="PDG-005",
                    panel_id=panel_id,
                    field="provenance.derived_from",
                    old=old_derived,
                    new=new_derived,
                    message=f"Interpretation panel lost provenance",
                ))

            # Check if provenance was removed entirely
            if old_provenance and not new_provenance:
                self.violations.append(Violation(
                    rule="PDG-005",
                    panel_id=panel_id,
                    field="provenance",
                    old="present",
                    new="missing",
                    message=f"Interpretation panel lost provenance object",
                ))

    # -------------------------------------------------------------------------
    # Output
    # -------------------------------------------------------------------------

    def get_result(self) -> dict:
        """Get machine-readable result."""
        return {
            "status": "PASSED" if len(self.violations) == 0 else "FAILED",
            "violation_count": len(self.violations),
            "violations": [v.to_dict() for v in self.violations],
        }


# =============================================================================
# CLI Interface
# =============================================================================

def load_allowlist(path: str | None) -> dict:
    """Load allowlist config if provided."""
    if not path:
        return {}

    allowlist_path = Path(path)
    if not allowlist_path.exists():
        return {}

    with open(allowlist_path) as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Projection Diff Guard - prevent silent UI drift"
    )
    parser.add_argument(
        "--old",
        required=True,
        help="Path to previous projection JSON",
    )
    parser.add_argument(
        "--new",
        required=True,
        help="Path to new projection JSON",
    )
    parser.add_argument(
        "--allowlist",
        help="Path to allowlist config JSON",
    )
    parser.add_argument(
        "--output",
        help="Output file for results (default: stdout)",
    )

    args = parser.parse_args()

    # Load projections
    with open(args.old) as f:
        old_projection = json.load(f)

    with open(args.new) as f:
        new_projection = json.load(f)

    # Load allowlist
    allowlist = load_allowlist(args.allowlist)

    # Run guard
    guard = ProjectionDiffGuard(allowlist=allowlist)
    guard.check(old_projection, new_projection)
    result = guard.get_result()

    # Output
    output = json.dumps(result, indent=2)
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
    else:
        print(output)

    # Exit with appropriate code
    sys.exit(0 if result["status"] == "PASSED" else 1)


if __name__ == "__main__":
    main()
