# Layer: L6 — Platform Substrate
# Product: system-wide
# Role: Evidence capture module
# Reference: Evidence Architecture v1.1

"""
Evidence Capture Module (v1.1)

Provides ctx-aware taxonomy evidence capture for Classes B-J.

Architecture (v1.1):
- capture.py: Evidence capture functions
- integrity.py: Split integrity computation (Assembler/Evaluator)

Key Changes (v1.1):
- Category B1: Activity evidence taxonomy rule (documented)
- Category B2: Separated IntegrityState/IntegrityGrade from execution status
- Category C2: Split compute_integrity into IntegrityAssembler/IntegrityEvaluator
- Category C3: Formalized failure resolution semantics
- Phase-1 Closure: No Context → No Evidence (EvidenceContextError)
"""

from app.evidence.capture import (
    CaptureFailureReason,
    EvidenceContextError,
    FailureResolution,
    capture_activity_evidence,
    capture_environment_evidence,
    capture_integrity_evidence,
    capture_policy_decision_evidence,
    capture_provider_evidence,
    compute_integrity,
    hash_prompt,
)

# v1.1: Split integrity computation
from app.evidence.integrity import (
    EvidenceClass,
    FailureResolution as IntegrityFailureResolution,
    IntegrityAssembler,
    IntegrityEvaluator,
    IntegrityEvaluation,
    IntegrityFacts,
    IntegrityGrade,
    IntegrityState,
    compute_integrity_v2,
)

__all__ = [
    # Capture functions
    "CaptureFailureReason",
    "EvidenceContextError",
    "FailureResolution",
    "capture_activity_evidence",
    "capture_environment_evidence",
    "capture_integrity_evidence",
    "capture_policy_decision_evidence",
    "capture_provider_evidence",
    "compute_integrity",
    "hash_prompt",
    # v1.1: Split integrity
    "EvidenceClass",
    "IntegrityAssembler",
    "IntegrityEvaluator",
    "IntegrityEvaluation",
    "IntegrityFacts",
    "IntegrityGrade",
    "IntegrityState",
    "compute_integrity_v2",
]
