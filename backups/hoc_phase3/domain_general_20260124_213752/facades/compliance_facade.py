# Layer: L3 — Adapter (Facade)
# AUDIENCE: CUSTOMER
# Role: Compliance Facade - Thin translation layer for compliance operations
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Callers: L2 compliance.py API, SDK
# Allowed Imports: L5 (engines), L6 (drivers)
# Forbidden Imports: L1, L2
# Reference: GAP-103 (Compliance Verification API)
# NOTE: Reclassified L6→L3 (2026-01-24) - Per HOC topology, facades are L3 (adapters)


"""
Compliance Facade (L4 Domain Logic)

This facade provides the external interface for compliance verification operations.
All compliance APIs MUST use this facade instead of directly importing
internal compliance modules.

Why This Facade Exists:
- Prevents L2→L4 layer violations
- Centralizes compliance verification logic
- Provides unified access to compliance checks and reports
- Single point for audit emission

L2 API Routes (GAP-103):
- POST /api/v1/compliance/verify (run compliance verification)
- GET /api/v1/compliance/reports (list compliance reports)
- GET /api/v1/compliance/reports/{id} (get compliance report)
- GET /api/v1/compliance/rules (list compliance rules)
- GET /api/v1/compliance/status (compliance status)

Usage:
    from app.services.compliance.facade import get_compliance_facade

    facade = get_compliance_facade()

    # Run compliance verification
    result = await facade.verify_compliance(tenant_id="...", scope="all")

    # List compliance reports
    reports = await facade.list_reports(tenant_id="...")
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger("nova.services.compliance.facade")


class ComplianceScope(str, Enum):
    """Compliance verification scope."""
    ALL = "all"
    DATA = "data"  # Data handling compliance
    POLICY = "policy"  # Policy enforcement compliance
    COST = "cost"  # Cost governance compliance
    SECURITY = "security"  # Security compliance


class ComplianceStatus(str, Enum):
    """Compliance status."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    UNKNOWN = "unknown"


@dataclass
class ComplianceRule:
    """Compliance rule definition."""
    id: str
    name: str
    description: str
    scope: str
    severity: str
    enabled: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "scope": self.scope,
            "severity": self.severity,
            "enabled": self.enabled,
        }


@dataclass
class ComplianceViolation:
    """A compliance violation."""
    rule_id: str
    rule_name: str
    severity: str
    description: str
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "severity": self.severity,
            "description": self.description,
            "evidence": self.evidence,
        }


@dataclass
class ComplianceReport:
    """Compliance verification report."""
    id: str
    tenant_id: str
    scope: str
    status: str
    total_rules: int
    passed_rules: int
    failed_rules: int
    violations: List[ComplianceViolation]
    verified_at: str
    verified_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "scope": self.scope,
            "status": self.status,
            "total_rules": self.total_rules,
            "passed_rules": self.passed_rules,
            "failed_rules": self.failed_rules,
            "violations": [v.to_dict() for v in self.violations],
            "verified_at": self.verified_at,
            "verified_by": self.verified_by,
            "metadata": self.metadata,
        }


@dataclass
class ComplianceStatusInfo:
    """Overall compliance status."""
    status: str
    last_verification: Optional[str]
    rules_total: int
    rules_enabled: int
    pending_violations: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status,
            "last_verification": self.last_verification,
            "rules_total": self.rules_total,
            "rules_enabled": self.rules_enabled,
            "pending_violations": self.pending_violations,
        }


class ComplianceFacade:
    """
    Facade for compliance verification operations.

    This is the ONLY entry point for L2 APIs and SDK to interact with
    compliance services.

    Layer: L4 (Domain Logic)
    Callers: compliance.py (L2), aos_sdk
    """

    def __init__(self):
        """Initialize facade."""
        self._last_verification: Optional[datetime] = None

        # In-memory stores for demo (would be database in production)
        self._reports: Dict[str, ComplianceReport] = {}
        self._rules: Dict[str, ComplianceRule] = self._init_default_rules()

    def _init_default_rules(self) -> Dict[str, ComplianceRule]:
        """Initialize default compliance rules."""
        rules = [
            ComplianceRule(
                id="COMP-DATA-001",
                name="Data Retention Policy",
                description="Verify data retention policies are enforced",
                scope="data",
                severity="HIGH",
                enabled=True,
            ),
            ComplianceRule(
                id="COMP-DATA-002",
                name="PII Handling",
                description="Verify PII is properly handled and masked",
                scope="data",
                severity="CRITICAL",
                enabled=True,
            ),
            ComplianceRule(
                id="COMP-POLICY-001",
                name="Policy Enforcement",
                description="Verify all policies are actively enforced",
                scope="policy",
                severity="HIGH",
                enabled=True,
            ),
            ComplianceRule(
                id="COMP-COST-001",
                name="Budget Limits",
                description="Verify budget limits are configured",
                scope="cost",
                severity="MEDIUM",
                enabled=True,
            ),
            ComplianceRule(
                id="COMP-COST-002",
                name="Cost Attribution",
                description="Verify cost attribution is complete",
                scope="cost",
                severity="MEDIUM",
                enabled=True,
            ),
            ComplianceRule(
                id="COMP-SEC-001",
                name="API Key Rotation",
                description="Verify API keys are rotated regularly",
                scope="security",
                severity="HIGH",
                enabled=True,
            ),
            ComplianceRule(
                id="COMP-SEC-002",
                name="Audit Logging",
                description="Verify audit logging is enabled",
                scope="security",
                severity="HIGH",
                enabled=True,
            ),
        ]
        return {r.id: r for r in rules}

    # =========================================================================
    # Compliance Verification (GAP-103)
    # =========================================================================

    async def verify_compliance(
        self,
        tenant_id: str,
        scope: str = "all",
        actor: Optional[str] = None,
    ) -> ComplianceReport:
        """
        Run compliance verification.

        Args:
            tenant_id: Tenant ID
            scope: Verification scope (all, data, policy, cost, security)
            actor: Who triggered the verification

        Returns:
            ComplianceReport with verification results
        """
        logger.info(
            "facade.verify_compliance",
            extra={"tenant_id": tenant_id, "scope": scope}
        )

        now = datetime.now(timezone.utc)
        self._last_verification = now

        # Get applicable rules
        if scope == "all":
            applicable_rules = list(self._rules.values())
        else:
            applicable_rules = [
                r for r in self._rules.values()
                if r.scope == scope and r.enabled
            ]

        # Run verification (simulated for demo)
        violations = []
        passed = 0
        failed = 0

        for rule in applicable_rules:
            if rule.enabled:
                # Simulate verification - in production, would actually check
                is_compliant = self._check_rule_compliance(tenant_id, rule)
                if is_compliant:
                    passed += 1
                else:
                    failed += 1
                    violations.append(ComplianceViolation(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        severity=rule.severity,
                        description=f"Violation of {rule.name}",
                        evidence={"checked_at": now.isoformat()},
                    ))

        # Determine overall status
        if failed == 0:
            status = ComplianceStatus.COMPLIANT.value
        elif passed == 0:
            status = ComplianceStatus.NON_COMPLIANT.value
        else:
            status = ComplianceStatus.PARTIALLY_COMPLIANT.value

        report = ComplianceReport(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            scope=scope,
            status=status,
            total_rules=len(applicable_rules),
            passed_rules=passed,
            failed_rules=failed,
            violations=violations,
            verified_at=now.isoformat(),
            verified_by=actor,
        )

        self._reports[report.id] = report
        return report

    def _check_rule_compliance(
        self,
        tenant_id: str,
        rule: ComplianceRule,
    ) -> bool:
        """
        Check if tenant is compliant with a rule.

        In production, this would actually verify compliance.
        For demo, returns True (compliant).
        """
        # Simulated - in production would check actual compliance
        return True

    # =========================================================================
    # Report Operations (GAP-103)
    # =========================================================================

    async def list_reports(
        self,
        tenant_id: str,
        scope: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ComplianceReport]:
        """
        List compliance reports.

        Args:
            tenant_id: Tenant ID
            scope: Optional filter by scope
            status: Optional filter by status
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of ComplianceReport
        """
        results = []
        for report in self._reports.values():
            if report.tenant_id != tenant_id:
                continue
            if scope and report.scope != scope:
                continue
            if status and report.status != status:
                continue
            results.append(report)

        # Sort by verified_at descending
        results.sort(key=lambda r: r.verified_at, reverse=True)

        return results[offset:offset + limit]

    async def get_report(
        self,
        report_id: str,
        tenant_id: str,
    ) -> Optional[ComplianceReport]:
        """
        Get a specific compliance report.

        Args:
            report_id: Report ID
            tenant_id: Tenant ID for authorization

        Returns:
            ComplianceReport or None if not found
        """
        report = self._reports.get(report_id)
        if report and report.tenant_id == tenant_id:
            return report
        return None

    # =========================================================================
    # Rules Operations (GAP-103)
    # =========================================================================

    async def list_rules(
        self,
        scope: Optional[str] = None,
        enabled_only: bool = True,
    ) -> List[ComplianceRule]:
        """
        List compliance rules.

        Args:
            scope: Optional filter by scope
            enabled_only: Only return enabled rules

        Returns:
            List of ComplianceRule
        """
        results = []
        for rule in self._rules.values():
            if scope and rule.scope != scope:
                continue
            if enabled_only and not rule.enabled:
                continue
            results.append(rule)

        return results

    async def get_rule(self, rule_id: str) -> Optional[ComplianceRule]:
        """
        Get a specific compliance rule.

        Args:
            rule_id: Rule ID

        Returns:
            ComplianceRule or None if not found
        """
        return self._rules.get(rule_id)

    # =========================================================================
    # Status Operations (GAP-103)
    # =========================================================================

    async def get_compliance_status(
        self,
        tenant_id: str,
    ) -> ComplianceStatusInfo:
        """
        Get overall compliance status.

        Args:
            tenant_id: Tenant ID

        Returns:
            ComplianceStatusInfo with overall status
        """
        # Count pending violations
        pending_violations = 0
        for report in self._reports.values():
            if report.tenant_id == tenant_id:
                pending_violations += report.failed_rules

        # Get latest report status
        tenant_reports = [
            r for r in self._reports.values()
            if r.tenant_id == tenant_id
        ]
        if tenant_reports:
            latest = max(tenant_reports, key=lambda r: r.verified_at)
            status = latest.status
            last_verification = latest.verified_at
        else:
            status = ComplianceStatus.UNKNOWN.value
            last_verification = None

        return ComplianceStatusInfo(
            status=status,
            last_verification=last_verification,
            rules_total=len(self._rules),
            rules_enabled=len([r for r in self._rules.values() if r.enabled]),
            pending_violations=pending_violations,
        )


# =============================================================================
# Module-level singleton accessor
# =============================================================================

_facade_instance: Optional[ComplianceFacade] = None


def get_compliance_facade() -> ComplianceFacade:
    """
    Get the compliance facade instance.

    This is the recommended way to access compliance operations
    from L2 APIs and the SDK.

    Returns:
        ComplianceFacade instance
    """
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = ComplianceFacade()
    return _facade_instance
