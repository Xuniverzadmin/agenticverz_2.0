# capability_id: CAP-012
# Layer: L5 — Domain Schemas
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: CRM validator shared schema types — safe to import across domains without importing L5 engines
# Callers: account/L5_engines/crm_validator_engine.py (producer), policies/L5_engines/eligibility_engine.py (consumer)
# Reference: PIN-513 (cross-domain routing), PIN-520 (schema vs engine separation)
# artifact_class: CODE

"""
CRM Validator Types (L5 Schemas)

Schema-only types for the CRM validator and its consumers (e.g., policies
eligibility). These types are intentionally separated from L5 engine logic
to avoid cross-domain engine imports.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional
from uuid import UUID


class IssueType(str, Enum):
    """
    Issue type classification.

    Reference: VALIDATOR_LOGIC.md Issue Type Classification
    """

    CAPABILITY_REQUEST = "capability_request"  # Enable/disable/modify capability
    BUG_REPORT = "bug_report"  # Report of incorrect behavior
    CONFIGURATION_CHANGE = "configuration_change"  # Modify system configuration
    ESCALATION = "escalation"  # Requires immediate human attention
    UNKNOWN = "unknown"  # Cannot classify with sufficient confidence


class Severity(str, Enum):
    """
    Issue severity classification.

    Reference: VALIDATOR_LOGIC.md Severity Classification
    """

    CRITICAL = "critical"  # System-wide impact, immediate action
    HIGH = "high"  # Significant impact, prompt action
    MEDIUM = "medium"  # Noticeable impact, standard timeline
    LOW = "low"  # Minor impact, can be deferred


class RecommendedAction(str, Enum):
    """
    Recommended action from validator.

    Reference: VALIDATOR_LOGIC.md Recommended Action Logic
    """

    CREATE_CONTRACT = "create_contract"  # Proceed to eligibility
    DEFER = "defer"  # Needs more information
    REJECT = "reject"  # Should not proceed
    ESCALATE = "escalate"  # Requires immediate human attention


class IssueSource(str, Enum):
    """Issue source for confidence weighting."""

    OPS_ALERT = "ops_alert"  # Highest trust (0.2)
    SUPPORT_TICKET = "support_ticket"  # Medium trust (0.1)
    CRM_FEEDBACK = "crm_feedback"  # Low trust (0.05)
    MANUAL = "manual"  # Neutral (0.0)
    INTEGRATION = "integration"  # Variable


@dataclass(frozen=True)
class ValidatorInput:
    """
    Input to the validator.

    Reference: VALIDATOR_LOGIC.md Validator Input
    """

    issue_id: UUID
    source: str  # IssueSource value
    raw_payload: dict[str, Any]
    received_at: datetime
    tenant_id: Optional[UUID] = None
    affected_capabilities_hint: Optional[list[str]] = None
    priority_hint: Optional[str] = None


@dataclass(frozen=True)
class ValidatorVerdict:
    """
    Output from the validator.

    Reference: VALIDATOR_LOGIC.md Validator Output (Verdict)
    """

    issue_type: IssueType
    severity: Severity
    affected_capabilities: tuple[str, ...]  # Immutable
    recommended_action: RecommendedAction
    confidence_score: Decimal  # 0.00 - 1.00 (VAL-003)
    reason: str
    evidence: dict[str, Any]
    analyzed_at: datetime
    validator_version: str  # VAL-002: Required


class ValidatorErrorType(str, Enum):
    """Error types for validator failures."""

    PARSE_ERROR = "parse_error"
    REGISTRY_UNAVAILABLE = "registry_unavailable"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ValidatorError:
    """
    Error from validator with fallback verdict.

    Reference: VALIDATOR_LOGIC.md Error Handling
    """

    error_type: ValidatorErrorType
    message: str
    fallback_verdict: ValidatorVerdict


__all__ = [
    "IssueType",
    "Severity",
    "RecommendedAction",
    "IssueSource",
    "ValidatorInput",
    "ValidatorVerdict",
    "ValidatorErrorType",
    "ValidatorError",
]

