# capability_id: CAP-009
# Layer: L5 — Domain Schema
# AUDIENCE: CUSTOMER
# Product: ai-console
# Role: Threshold signal types — pure enum and result dataclass
# Callers: threshold_engine.py (L5), threshold_driver.py (L6), signal_coordinator.py (L4)
# Reference: PIN-507 (Law 1 remediation — extracted from threshold_engine.py)
# artifact_class: CODE

"""
Threshold Signal Types (L5 Schema)

Pure types for threshold signal operations.
Extracted from controls/L5_engines/threshold_engine.py (PIN-507 Law 1)
so L6 drivers can import types without reaching up to L5 engines.

These are contracts (types), not policy (logic).
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ThresholdSignal(str, Enum):
    """
    Signals emitted when runs breach thresholds.
    These appear in Activity → LLM Runs → Signal panels.
    """

    EXECUTION_TIME_EXCEEDED = "EXECUTION_TIME_EXCEEDED"
    TOKEN_LIMIT_EXCEEDED = "TOKEN_LIMIT_EXCEEDED"
    COST_LIMIT_EXCEEDED = "COST_LIMIT_EXCEEDED"
    RUN_FAILED = "RUN_FAILED"


@dataclass(frozen=True)
class ThresholdEvaluationResult:
    """Result of threshold evaluation."""

    run_id: str
    signals: list[ThresholdSignal]
    params_used: dict
    evaluated_at: datetime


__all__ = [
    "ThresholdSignal",
    "ThresholdEvaluationResult",
]
