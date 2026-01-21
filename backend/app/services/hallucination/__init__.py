# Layer: L4 — Domain Engines
# Product: system-wide
# Reference: GAP-023, INV-002 (HALLU-INV-001)
"""
Hallucination Detection Service (GAP-023)

CRITICAL INVARIANT (INV-002 / HALLU-INV-001):
    Hallucination detection is ALWAYS non-blocking by default.
    Blocking requires explicit customer opt-in.

This module provides:
    - HallucinationDetector: Main detection service
    - HallucinationResult: Detection result dataclass
    - HallucinationIndicator: Individual indicator
    - HallucinationType: Types of hallucinations
    - HallucinationSeverity: Severity levels
    - HallucinationConfig: Configuration options
"""

from app.services.hallucination.hallucination_detector import (
    HallucinationConfig,
    HallucinationDetector,
    HallucinationIndicator,
    HallucinationResult,
    HallucinationSeverity,
    HallucinationType,
    create_detector_for_tenant,
)

__all__ = [
    "HallucinationConfig",
    "HallucinationDetector",
    "HallucinationIndicator",
    "HallucinationResult",
    "HallucinationSeverity",
    "HallucinationType",
    "create_detector_for_tenant",
]
