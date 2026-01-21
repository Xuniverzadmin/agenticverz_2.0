# Layer: L4 — Domain Engines
# Product: system-wide
# Reference: GAP-027 (Evidence PDF Completeness)
"""
Export Services (GAP-027)

Provides services for evidence export completeness validation
before PDF generation for SOC2 compliance.

This module provides:
    - EvidenceCompletenessChecker: Validates evidence bundle completeness
    - EvidenceCompletenessError: Raised on incomplete evidence
    - CompletenessResult: Result of completeness check
    - Helper functions for quick validation
"""

from app.services.export.completeness_checker import (
    CompletenessCheckResponse,
    CompletenessCheckResult,
    EvidenceCompletenessChecker,
    EvidenceCompletenessError,
    REQUIRED_EVIDENCE_FIELDS,
    SOC2_REQUIRED_FIELDS,
    check_evidence_completeness,
    ensure_evidence_completeness,
)

__all__ = [
    "CompletenessCheckResponse",
    "CompletenessCheckResult",
    "EvidenceCompletenessChecker",
    "EvidenceCompletenessError",
    "REQUIRED_EVIDENCE_FIELDS",
    "SOC2_REQUIRED_FIELDS",
    "check_evidence_completeness",
    "ensure_evidence_completeness",
]
