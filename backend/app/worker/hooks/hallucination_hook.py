# Layer: L5 — Execution & Workers
# AUDIENCE: INTERNAL
# PHASE: W0
# Product: system-wide
# Wiring Type: runner-hook
# Parent Gap: GAP-023 (HallucinationDetector)
# Reference: GAP-138
# Temporal:
#   Trigger: worker (after LLM response)
#   Execution: async
# Role: Wire HallucinationDetector to runner output annotation
# Callers: app/worker/runner.py (after LLM response)
# Allowed Imports: L4 (HallucinationDetector), L6
# Forbidden Imports: L1, L2, L3

"""
Module: hallucination_hook
Purpose: Wire HallucinationDetector to runner output annotation.

Wires:
    - Source: app/services/hallucination/hallucination_detector.py
    - Target: app/worker/runner.py (after LLM response)

Design: Non-blocking per INV-002 (HALLU-INV-001)
    - Detection runs async
    - Results annotate response
    - High confidence triggers alert (does not block)

CRITICAL INVARIANT (INV-002 / HALLU-INV-001):
    This hook MUST be non-blocking by default.
    Hallucination detection is PROBABILISTIC, not DETERMINISTIC.
    False positives on blocking destroy customer trust.

Acceptance Criteria:
    - AC-138-01: LLM responses are checked
    - AC-138-02: Non-blocking per INV-002
    - AC-138-03: Annotations added to response
    - AC-138-04: High confidence triggers alert
    - AC-138-05: Hook is imported in runner.py
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.hoc.cus.incidents.L5_engines.hallucination_detector import (
    HallucinationDetector,
    HallucinationResult,
    HallucinationSeverity,
    create_detector_for_tenant,
)
from app.core.execution_context import ExecutionContext

logger = logging.getLogger("nova.worker.hooks.hallucination_hook")


@dataclass
class HallucinationAnnotation:
    """
    Annotation added to LLM responses.

    This annotation is attached to step results to provide
    hallucination detection metadata for observability.
    """

    checked: bool = False
    detected: bool = False
    confidence: float = 0.0
    flagged: bool = False  # True if high confidence hallucination
    severity: Optional[str] = None
    indicator_count: int = 0
    content_hash: Optional[str] = None
    checked_at: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "checked": self.checked,
            "detected": self.detected,
            "confidence": self.confidence,
            "flagged": self.flagged,
            "severity": self.severity,
            "indicator_count": self.indicator_count,
            "content_hash": self.content_hash,
            "checked_at": self.checked_at,
        }

    @classmethod
    def unchecked(cls) -> "HallucinationAnnotation":
        """Create an unchecked annotation (detection skipped or failed)."""
        return cls(checked=False)

    @classmethod
    def from_result(
        cls,
        result: HallucinationResult,
        high_confidence_threshold: float = 0.8,
    ) -> "HallucinationAnnotation":
        """Create annotation from detection result."""
        # Determine if flagged (high confidence hallucination)
        flagged = result.detected and result.overall_confidence >= high_confidence_threshold

        # Extract severity if detected
        severity = None
        if result.detected and result.indicators:
            # Get highest severity from indicators
            severity_order = {
                HallucinationSeverity.CRITICAL: 4,
                HallucinationSeverity.HIGH: 3,
                HallucinationSeverity.MEDIUM: 2,
                HallucinationSeverity.LOW: 1,
            }
            max_indicator = max(
                result.indicators,
                key=lambda i: severity_order.get(i.severity, 0)
            )
            severity = max_indicator.severity.value

        return cls(
            checked=True,
            detected=result.detected,
            confidence=result.overall_confidence,
            flagged=flagged,
            severity=severity,
            indicator_count=len(result.indicators),
            content_hash=result.content_hash,
            checked_at=result.checked_at.isoformat(),
            details={
                "indicators": [i.to_dict() for i in result.indicators],
                "blocking_recommended": result.blocking_recommended,
            } if result.detected else None,
        )


class HallucinationHook:
    """
    Runner hook for hallucination detection on LLM outputs.

    INV-002 / HALLU-INV-001: Non-blocking — detection does not halt execution.

    This hook:
    1. Checks LLM responses for potential hallucinations
    2. Annotates responses with detection metadata
    3. Emits alerts for high-confidence detections
    4. NEVER blocks execution (unless customer explicitly opted in)

    Usage in runner:
        hook = get_hallucination_hook()

        # After LLM response in step execution
        annotation = await hook.after_llm_response(
            execution_context=cursor.context,
            prompt=prompt,
            response=llm_response,
            context={"skill": skill_name},
        )

        # Annotate the step result
        step_result["hallucination_check"] = annotation.to_dict()
    """

    # Alert threshold (high confidence)
    ALERT_CONFIDENCE_THRESHOLD = 0.8

    def __init__(
        self,
        detector: Optional[HallucinationDetector] = None,
        tenant_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize HallucinationHook.

        Args:
            detector: HallucinationDetector instance (creates one if None)
            tenant_config: Optional tenant configuration for detector
        """
        self._detector = detector
        self._tenant_config = tenant_config

    @property
    def detector(self) -> HallucinationDetector:
        """Get detector (lazy initialization)."""
        if self._detector is None:
            self._detector = create_detector_for_tenant(self._tenant_config)
        return self._detector

    async def after_llm_response(
        self,
        prompt: str,
        response: str,
        execution_context: Optional[ExecutionContext] = None,
        context: Optional[Dict[str, Any]] = None,
        customer_blocking_opted_in: bool = False,
    ) -> HallucinationAnnotation:
        """
        Check LLM response for hallucinations.

        Non-blocking: Returns annotation, does not raise.

        Args:
            prompt: The prompt sent to the LLM
            response: The LLM response to check
            execution_context: Optional execution context for metadata
            context: Optional additional context (skill name, etc.)
            customer_blocking_opted_in: Whether customer opted into blocking

        Returns:
            HallucinationAnnotation with detection results
        """
        run_id = execution_context.run_id if execution_context else "unknown"
        step_index = execution_context.step_index if execution_context else 0

        logger.debug(
            "hallucination_hook.checking",
            extra={
                "run_id": run_id,
                "step_index": step_index,
                "response_length": len(response),
            },
        )

        try:
            # Build detection context
            detection_context = context or {}
            if execution_context:
                detection_context.update({
                    "run_id": execution_context.run_id,
                    "step_index": execution_context.step_index,
                    "trace_id": execution_context.trace_id,
                    "is_synthetic": execution_context.is_synthetic,
                })
            detection_context["prompt"] = prompt[:1000]  # Truncate for storage

            # Run detection (synchronous - detector is not async)
            result = self.detector.detect(
                content=response,
                context=detection_context,
                customer_blocking_opted_in=customer_blocking_opted_in,
            )

            annotation = HallucinationAnnotation.from_result(
                result,
                high_confidence_threshold=self.ALERT_CONFIDENCE_THRESHOLD,
            )

            # Log detection outcome
            if result.detected:
                logger.info(
                    "hallucination_hook.detected",
                    extra={
                        "run_id": run_id,
                        "step_index": step_index,
                        "confidence": result.overall_confidence,
                        "indicator_count": len(result.indicators),
                        "flagged": annotation.flagged,
                    },
                )

                # Emit alert if high confidence hallucination
                if annotation.flagged:
                    await self._emit_hallucination_alert(
                        run_id=run_id,
                        step_index=step_index,
                        result=result,
                        execution_context=execution_context,
                    )
            else:
                logger.debug(
                    "hallucination_hook.clean",
                    extra={
                        "run_id": run_id,
                        "step_index": step_index,
                    },
                )

            return annotation

        except Exception as e:
            # Non-blocking: log and return unchecked annotation
            logger.warning(
                "hallucination_hook.check_failed",
                extra={
                    "run_id": run_id,
                    "step_index": step_index,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            return HallucinationAnnotation.unchecked()

    async def _emit_hallucination_alert(
        self,
        run_id: str,
        step_index: int,
        result: HallucinationResult,
        execution_context: Optional[ExecutionContext] = None,
    ) -> None:
        """
        Emit alert for high-confidence hallucination.

        This alert goes to the observability system for review.
        It does NOT block execution (INV-002 compliance).
        """
        try:
            from app.events import get_publisher

            publisher = get_publisher()
            if publisher is None:
                logger.warning(
                    "hallucination_hook.no_publisher",
                    extra={"run_id": run_id},
                )
                return

            # Build alert payload
            payload = {
                "run_id": run_id,
                "step_index": step_index,
                "confidence": result.overall_confidence,
                "indicator_count": len(result.indicators),
                "content_hash": result.content_hash,
                "blocking_recommended": result.blocking_recommended,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Add execution context if available
            if execution_context:
                payload.update({
                    "tenant_id": execution_context.tenant_id,
                    "trace_id": execution_context.trace_id,
                    "is_synthetic": execution_context.is_synthetic,
                })

            # Add indicator summaries
            if result.indicators:
                payload["indicators"] = [
                    {
                        "type": i.indicator_type.value,
                        "confidence": i.confidence,
                        "severity": i.severity.value,
                    }
                    for i in result.indicators[:5]  # Limit to top 5
                ]

            await publisher.publish("hallucination.detected", payload)

            logger.info(
                "hallucination_hook.alert_emitted",
                extra={
                    "run_id": run_id,
                    "step_index": step_index,
                    "confidence": result.overall_confidence,
                },
            )

        except Exception as e:
            # Don't fail on alert emission - just log
            logger.error(
                "hallucination_hook.alert_emission_failed",
                extra={
                    "run_id": run_id,
                    "step_index": step_index,
                    "error": str(e),
                },
            )


# =========================
# Singleton Management
# =========================

_hallucination_hook: Optional[HallucinationHook] = None


def get_hallucination_hook() -> HallucinationHook:
    """
    Get or create the singleton HallucinationHook.

    Returns:
        HallucinationHook instance
    """
    global _hallucination_hook

    if _hallucination_hook is None:
        _hallucination_hook = HallucinationHook()
        logger.info("hallucination_hook.created")

    return _hallucination_hook


def configure_hallucination_hook(
    detector: Optional[HallucinationDetector] = None,
    tenant_config: Optional[Dict[str, Any]] = None,
) -> HallucinationHook:
    """
    Configure the singleton HallucinationHook with dependencies.

    Args:
        detector: HallucinationDetector instance to use
        tenant_config: Tenant-specific configuration

    Returns:
        Configured HallucinationHook
    """
    global _hallucination_hook

    _hallucination_hook = HallucinationHook(
        detector=detector,
        tenant_config=tenant_config,
    )

    logger.info(
        "hallucination_hook.configured",
        extra={
            "has_detector": detector is not None,
            "has_tenant_config": tenant_config is not None,
        },
    )

    return _hallucination_hook


def reset_hallucination_hook() -> None:
    """Reset the singleton (for testing)."""
    global _hallucination_hook
    _hallucination_hook = None
