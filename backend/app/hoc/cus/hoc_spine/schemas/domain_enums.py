# capability_id: CAP-012
# Layer: L4 — Shared Schema
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: L5-safe enum mirrors for cross-domain audit constants
# Callers: L5 engines across policies, incidents, logs domains
# Allowed Imports: stdlib only
# Forbidden Imports: L1, L2, L3, L7 (app.models)
# Reference: PIN-520 Phase 3 (L5 purity — no runtime app.models imports)
# artifact_class: CODE

"""
Domain-level enum mirrors.

These mirror the canonical enums in app.models so that
L5 engines never need a runtime import of app.models.
Values MUST stay in sync with the L7 originals.

Canonical sources:
- app/models/audit_ledger.py (PIN-413): ActorType, AuditEntityType, AuditEventType
- app/models/killswitch.py: IncidentSeverity
- app/models/contract.py: AuditVerdict
"""

from enum import Enum


class ActorType(str, Enum):
    """Types of actors performing actions.

    Mirror of app.models.audit_ledger.ActorType.
    """

    HUMAN = "HUMAN"
    SYSTEM = "SYSTEM"
    AGENT = "AGENT"


class AuditEntityType(str, Enum):
    """Entity types tracked in audit ledger.

    Mirror of app.models.audit_ledger.AuditEntityType.
    """

    POLICY_RULE = "POLICY_RULE"
    POLICY_PROPOSAL = "POLICY_PROPOSAL"
    LIMIT = "LIMIT"
    INCIDENT = "INCIDENT"
    SIGNAL = "SIGNAL"


class AuditEventType(str, Enum):
    """Canonical audit events — only these create audit rows.

    Mirror of app.models.audit_ledger.AuditEventType.
    """

    # Policies > Governance
    POLICY_RULE_CREATED = "PolicyRuleCreated"
    POLICY_RULE_MODIFIED = "PolicyRuleModified"
    POLICY_RULE_RETIRED = "PolicyRuleRetired"
    POLICY_PROPOSAL_APPROVED = "PolicyProposalApproved"
    POLICY_PROPOSAL_REJECTED = "PolicyProposalRejected"
    # Policies > Limits
    LIMIT_CREATED = "LimitCreated"
    LIMIT_UPDATED = "LimitUpdated"
    LIMIT_BREACHED = "LimitBreached"
    LIMIT_OVERRIDE_GRANTED = "LimitOverrideGranted"
    LIMIT_OVERRIDE_REVOKED = "LimitOverrideRevoked"
    # Incidents
    INCIDENT_ACKNOWLEDGED = "IncidentAcknowledged"
    INCIDENT_RESOLVED = "IncidentResolved"
    INCIDENT_MANUALLY_CLOSED = "IncidentManuallyClosed"
    # System / Control
    EMERGENCY_OVERRIDE_ACTIVATED = "EmergencyOverrideActivated"
    EMERGENCY_OVERRIDE_DEACTIVATED = "EmergencyOverrideDeactivated"
    # Signal Feedback
    SIGNAL_ACKNOWLEDGED = "SignalAcknowledged"
    SIGNAL_SUPPRESSED = "SignalSuppressed"
    SIGNAL_ESCALATED = "SignalEscalated"


class IncidentSeverity(str, Enum):
    """Incident severity levels.

    Mirror of app.models.killswitch.IncidentSeverity.
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AuditVerdict(str, Enum):
    """Audit verification verdict.

    Mirror of app.models.contract.AuditVerdict.
    """

    PENDING = "PENDING"
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"
