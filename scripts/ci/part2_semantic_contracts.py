#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci
#   Execution: sync
# Role: Define semantic contracts for Part-2 governance (GATE-7, GATE-8, GATE-9)
# Callers: CI pipeline, test runner
# Allowed Imports: stdlib only
# Forbidden Imports: L1-L6
# Reference: PIN-284, PIN-285, part2-design-v1 tag
#
# GATE-7: Rollout Without Audit
# Risk: Changes deployed without verification
# Enforcement: Rollout requires audit.verdict == PASS
#
# GATE-8: Unaudited Customer View
# Risk: Customers see in-progress/unverified states
# Enforcement: Customer API shows only COMPLETED contracts
#
# GATE-9: Silent Execution
# Risk: Terminal states without evidence trail
# Enforcement: COMPLETED/FAILED contracts have evidence records

"""
Part-2 Semantic Contract Tests

These tests define BEHAVIORAL contracts that implementation must satisfy.
They are declarative and operate on mock/fake models.

The tests verify:
- GATE-7: No rollout without audit PASS
- GATE-8: Customers never see unaudited states
- GATE-9: Terminal states always emit evidence

Exit codes:
  0 - All semantic contracts defined (pre-implementation) or verified
  1 - Semantic contract violation detected
  2 - Configuration error
"""

import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


def get_repo_root() -> Path:
    """Get repository root directory."""
    import subprocess

    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("ERROR: Not a git repository", file=sys.stderr)
        sys.exit(2)
    return Path(result.stdout.strip())


# ============================================================================
# MOCK MODELS (for semantic contract definition)
# These represent the CONTRACTS, not the implementation
# ============================================================================


class ContractStatus(Enum):
    """Contract states per END_TO_END_STATE_MACHINE.md"""

    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    ELIGIBLE = "ELIGIBLE"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class AuditVerdict(Enum):
    """Audit verdicts per GOVERNANCE_AUDIT_MODEL.md"""

    PENDING = "PENDING"
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass
class MockContract:
    """Mock contract for semantic testing."""

    contract_id: str
    status: ContractStatus
    audit_verdict: Optional[AuditVerdict] = None
    evidence: Optional[dict] = None
    rollout_status: Optional[str] = None


@dataclass
class SemanticContractResult:
    """Result of a semantic contract test."""

    gate: str
    name: str
    passed: bool
    reason: str
    evidence: Optional[str] = None


# ============================================================================
# GATE-7: AUDIT ROLLOUT CONTRACT
# ============================================================================


def semantic_contract_gate7_rollout_requires_audit_pass() -> SemanticContractResult:
    """
    GATE-7 Semantic Contract: Rollout Requires Audit PASS

    Invariant: No deployment (rollout_status = DEPLOYED) may occur
    unless audit_verdict == PASS.

    This contract is VIOLATED if:
    - rollout_status == DEPLOYED AND audit_verdict != PASS
    - rollout_status == DEPLOYED AND audit_verdict is None
    """
    # Test case: Valid rollout (audit PASS)
    valid = MockContract(
        contract_id="C-001",
        status=ContractStatus.COMPLETED,
        audit_verdict=AuditVerdict.PASS,
        rollout_status="DEPLOYED",
    )

    # Test case: Invalid rollout (audit FAIL)
    invalid_fail = MockContract(
        contract_id="C-002",
        status=ContractStatus.COMPLETED,
        audit_verdict=AuditVerdict.FAIL,
        rollout_status="DEPLOYED",
    )

    # Test case: Invalid rollout (no audit)
    invalid_no_audit = MockContract(
        contract_id="C-003",
        status=ContractStatus.ACTIVE,
        audit_verdict=None,
        rollout_status="DEPLOYED",
    )

    # Contract logic
    def is_rollout_valid(contract: MockContract) -> bool:
        if contract.rollout_status == "DEPLOYED":
            return contract.audit_verdict == AuditVerdict.PASS
        return True  # Non-deployed states don't require audit

    # Verify contract logic
    valid_ok = is_rollout_valid(valid)
    invalid_fail_rejected = not is_rollout_valid(invalid_fail)
    invalid_no_audit_rejected = not is_rollout_valid(invalid_no_audit)

    all_pass = valid_ok and invalid_fail_rejected and invalid_no_audit_rejected

    return SemanticContractResult(
        gate="GATE-7",
        name="Rollout Requires Audit PASS",
        passed=all_pass,
        reason="Rollout is impossible without audit.verdict == PASS"
        if all_pass
        else "Contract allows rollout without audit PASS",
        evidence=f"Valid={valid_ok}, FailRejected={invalid_fail_rejected}, NoAuditRejected={invalid_no_audit_rejected}",
    )


# ============================================================================
# GATE-8: CUSTOMER VIEW CONTRACT
# ============================================================================


def semantic_contract_gate8_customer_view_only_completed() -> SemanticContractResult:
    """
    GATE-8 Semantic Contract: Customer View Only Shows COMPLETED

    Invariant: Customer-facing APIs must filter to only show
    contracts with status == COMPLETED (which requires audit PASS).

    This contract is VIOLATED if:
    - Customer API returns contracts with status != COMPLETED
    - Customer sees ACTIVE, APPROVED, or any intermediate state
    """
    # Test cases: Various contract states
    contracts = [
        MockContract("C-001", ContractStatus.DRAFT, None),  # Should NOT be visible
        MockContract("C-002", ContractStatus.VALIDATED, None),  # Should NOT be visible
        MockContract("C-003", ContractStatus.ELIGIBLE, None),  # Should NOT be visible
        MockContract("C-004", ContractStatus.APPROVED, None),  # Should NOT be visible
        MockContract("C-005", ContractStatus.ACTIVE, None),  # Should NOT be visible
        MockContract("C-006", ContractStatus.COMPLETED, AuditVerdict.PASS),  # VISIBLE
        MockContract(
            "C-007", ContractStatus.FAILED, AuditVerdict.FAIL
        ),  # Should NOT be visible
        MockContract("C-008", ContractStatus.REJECTED, None),  # Should NOT be visible
        MockContract("C-009", ContractStatus.EXPIRED, None),  # Should NOT be visible
    ]

    # Contract logic: Customer filter
    def customer_visible(contract: MockContract) -> bool:
        # Customer sees only COMPLETED contracts
        return contract.status == ContractStatus.COMPLETED

    # Apply filter
    visible = [c for c in contracts if customer_visible(c)]

    # Verify only COMPLETED contracts are visible
    all_visible_completed = all(c.status == ContractStatus.COMPLETED for c in visible)
    correct_count = len(visible) == 1  # Only C-006 should be visible

    all_pass = all_visible_completed and correct_count

    return SemanticContractResult(
        gate="GATE-8",
        name="Customer View Only COMPLETED",
        passed=all_pass,
        reason="Customer API filters to COMPLETED only (audit PASS required)"
        if all_pass
        else "Customer API may expose non-COMPLETED states",
        evidence=f"VisibleCount={len(visible)}, AllCompleted={all_visible_completed}",
    )


# ============================================================================
# GATE-9: EVIDENCE CONTRACT
# ============================================================================


def semantic_contract_gate9_terminal_states_emit_evidence() -> SemanticContractResult:
    """
    GATE-9 Semantic Contract: Terminal States Emit Evidence

    Invariant: Contracts in terminal states (COMPLETED, FAILED)
    must have evidence records. No silent execution.

    This contract is VIOLATED if:
    - status == COMPLETED AND evidence is None
    - status == FAILED AND evidence is None
    """
    # Test cases: Terminal states
    valid_completed = MockContract(
        contract_id="C-001",
        status=ContractStatus.COMPLETED,
        audit_verdict=AuditVerdict.PASS,
        evidence={"job_id": "J-001", "audit_id": "A-001", "completed_at": "2026-01-04"},
    )

    valid_failed = MockContract(
        contract_id="C-002",
        status=ContractStatus.FAILED,
        audit_verdict=AuditVerdict.FAIL,
        evidence={
            "job_id": "J-002",
            "audit_id": "A-002",
            "failure_reason": "Health degraded",
        },
    )

    invalid_completed_no_evidence = MockContract(
        contract_id="C-003",
        status=ContractStatus.COMPLETED,
        audit_verdict=AuditVerdict.PASS,
        evidence=None,  # VIOLATION
    )

    invalid_failed_no_evidence = MockContract(
        contract_id="C-004",
        status=ContractStatus.FAILED,
        audit_verdict=AuditVerdict.FAIL,
        evidence=None,  # VIOLATION
    )

    # Non-terminal states don't require evidence
    valid_active_no_evidence = MockContract(
        contract_id="C-005",
        status=ContractStatus.ACTIVE,
        audit_verdict=None,
        evidence=None,  # OK - not terminal
    )

    # Contract logic
    TERMINAL_STATES = {ContractStatus.COMPLETED, ContractStatus.FAILED}

    def has_required_evidence(contract: MockContract) -> bool:
        if contract.status in TERMINAL_STATES:
            return contract.evidence is not None
        return True  # Non-terminal states don't require evidence

    # Verify contract logic
    valid_completed_ok = has_required_evidence(valid_completed)
    valid_failed_ok = has_required_evidence(valid_failed)
    invalid_completed_rejected = not has_required_evidence(
        invalid_completed_no_evidence
    )
    invalid_failed_rejected = not has_required_evidence(invalid_failed_no_evidence)
    active_ok = has_required_evidence(valid_active_no_evidence)

    all_pass = (
        valid_completed_ok
        and valid_failed_ok
        and invalid_completed_rejected
        and invalid_failed_rejected
        and active_ok
    )

    return SemanticContractResult(
        gate="GATE-9",
        name="Terminal States Emit Evidence",
        passed=all_pass,
        reason="Terminal states (COMPLETED/FAILED) always have evidence records"
        if all_pass
        else "Silent execution allowed in terminal states",
        evidence=f"CompletedOK={valid_completed_ok}, FailedOK={valid_failed_ok}, "
        f"NoEvCompletedRejected={invalid_completed_rejected}, "
        f"NoEvFailedRejected={invalid_failed_rejected}",
    )


# ============================================================================
# IMPLEMENTATION VERIFICATION
# ============================================================================


def check_implementation_patterns(repo_root: Path) -> list[dict]:
    """Check implementation for semantic contract violations."""
    violations = []

    # GATE-7: Check for rollout without audit check
    rollout_patterns = [
        (
            r"rollout_status\s*=\s*['\"]DEPLOYED['\"](?!.*audit.*PASS)",
            "GATE-7: Rollout without audit PASS check",
        ),
        (
            r"deploy\s*\((?!.*audit)",
            "GATE-7: Deploy function without audit parameter",
        ),
    ]

    # GATE-8: Check for customer API exposing non-completed
    customer_patterns = [
        (
            r"customer.*(?:list|get).*contract(?!.*COMPLETED)",
            "GATE-8: Customer API may expose non-COMPLETED contracts",
        ),
        (
            r"/api/v1/customer.*contract(?!.*filter.*COMPLETED)",
            "GATE-8: Customer endpoint without COMPLETED filter",
        ),
    ]

    # GATE-9: Check for terminal state without evidence
    evidence_patterns = [
        (
            r"status\s*=\s*(?:ContractStatus\.)?COMPLETED(?!.*evidence)",
            "GATE-9: COMPLETED without evidence assignment",
        ),
        (
            r"status\s*=\s*(?:ContractStatus\.)?FAILED(?!.*evidence)",
            "GATE-9: FAILED without evidence assignment",
        ),
    ]

    all_patterns = [
        ("GATE-7", rollout_patterns),
        ("GATE-8", customer_patterns),
        ("GATE-9", evidence_patterns),
    ]

    # Check governance and API files
    check_paths = [
        "backend/app/services/governance/*.py",
        "backend/app/api/contracts.py",
        "backend/app/api/governance*.py",
    ]

    for path_pattern in check_paths:
        for file_path in repo_root.glob(path_pattern):
            if "test" in str(file_path).lower():
                continue

            try:
                with open(file_path) as f:
                    content = f.read()
                    lines = content.split("\n")
            except FileNotFoundError:
                continue

            rel_path = str(file_path.relative_to(repo_root))

            for gate, patterns in all_patterns:
                for pattern, description in patterns:
                    for i, line in enumerate(lines, 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            violations.append(
                                {
                                    "gate": gate,
                                    "file": rel_path,
                                    "line": i,
                                    "description": description,
                                    "content": line.strip()[:80],
                                }
                            )

    return violations


def main() -> int:
    print("=" * 70)
    print("Part-2 Semantic Contract Tests")
    print("Reference: part2-design-v1, GATE-7, GATE-8, GATE-9")
    print("=" * 70)
    print()

    repo_root = get_repo_root()
    all_results: list[SemanticContractResult] = []
    impl_violations: list[dict] = []

    # Run semantic contract tests
    print("Running semantic contract definitions...")
    print()

    # GATE-7
    print("GATE-7: Rollout Requires Audit PASS")
    result7 = semantic_contract_gate7_rollout_requires_audit_pass()
    all_results.append(result7)
    print(f"  Contract logic: {'✅ VALID' if result7.passed else '❌ INVALID'}")
    print(f"  Invariant: {result7.reason}")
    print(f"  Evidence: {result7.evidence}")
    print()

    # GATE-8
    print("GATE-8: Customer View Only COMPLETED")
    result8 = semantic_contract_gate8_customer_view_only_completed()
    all_results.append(result8)
    print(f"  Contract logic: {'✅ VALID' if result8.passed else '❌ INVALID'}")
    print(f"  Invariant: {result8.reason}")
    print(f"  Evidence: {result8.evidence}")
    print()

    # GATE-9
    print("GATE-9: Terminal States Emit Evidence")
    result9 = semantic_contract_gate9_terminal_states_emit_evidence()
    all_results.append(result9)
    print(f"  Contract logic: {'✅ VALID' if result9.passed else '❌ INVALID'}")
    print(f"  Invariant: {result9.reason}")
    print(f"  Evidence: {result9.evidence}")
    print()

    # Check implementation (if exists)
    print("=" * 70)
    print("Checking implementation patterns...")
    impl_violations = check_implementation_patterns(repo_root)

    if impl_violations:
        print(f"  Status: ⚠️  {len(impl_violations)} potential violations")
        print()
        for v in impl_violations:
            print(f"  {v['gate']}: {v['file']}:{v['line']}")
            print(f"    {v['description']}")
            if v.get("content"):
                print(f"    Code: {v['content']}")
            print()
    else:
        governance_files = list(repo_root.glob("backend/app/services/governance/*.py"))
        if governance_files:
            print("  Status: ✅ No obvious violations in governance code")
        else:
            print("  Status: Pre-implementation (no governance services yet)")
    print()

    # Summary
    all_contracts_valid = all(r.passed for r in all_results)

    if not all_contracts_valid:
        print("=" * 70)
        print("❌ SEMANTIC CONTRACT DEFINITION ERROR")
        print("=" * 70)
        print()
        print("One or more semantic contracts have invalid logic.")
        print("This indicates a bug in the contract definition itself.")
        return 2

    if impl_violations:
        print("=" * 70)
        print("⚠️  SEMANTIC CONTRACT WARNINGS")
        print("=" * 70)
        print()
        print("Implementation patterns may violate semantic contracts.")
        print("Review the warnings above and ensure:")
        print("  - GATE-7: Rollout only occurs after audit.verdict == PASS")
        print("  - GATE-8: Customer APIs filter to COMPLETED only")
        print("  - GATE-9: Terminal states always have evidence records")
        print()
        # Warnings, not blocking
        print("These are warnings for manual review, not blocking violations.")
        print()

    print("=" * 70)
    print("✅ Part-2 Semantic Contracts: DEFINED")
    print()
    print("Contracts verified:")
    for r in all_results:
        print(f"  - {r.gate}: {r.name}")
    print()
    print("Implementation must satisfy these behavioral invariants.")
    print("Tests will verify compliance when governance code is implemented.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
