# Layer: L4 — HOC Spine (Coordinator)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: L4 coordinator — evidence capture orchestration
# Callers: Execution, incident, policy flows
# Allowed Imports: hoc_spine, hoc.cus.logs.L6_drivers (lazy)
# Forbidden Imports: L1, L2
# Reference: PIN-513 Batch 3B1 Wiring
# artifact_class: CODE

"""
Evidence Coordinator (PIN-513 Batch 3B1 Wiring)

L4 coordinator that owns evidence capture operations.

Wires from logs/L6_drivers/capture_driver.py:
- capture_environment_evidence(session, ctx, ...)
- capture_activity_evidence(session, ctx, ...)
- capture_provider_evidence(session, ctx, ...)
- capture_policy_decision_evidence(session, ctx, ...)
- capture_integrity_evidence(session, run_id, ...)
- compute_integrity(run_id)
- hash_prompt(prompt)
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nova.hoc_spine.coordinators.evidence")


class EvidenceCoordinator:
    """L4 coordinator: evidence capture orchestration.

    All evidence capture flows route through this coordinator.
    """

    def capture_environment(
        self,
        session: Any,
        ctx: Any,
        *,
        sdk_mode: str,
        execution_environment: Optional[str] = None,
        sdk_version: Optional[str] = None,
        telemetry_delivery_status: Optional[str] = None,
        capture_confidence_score: Optional[float] = None,
        telemetry_enabled: bool = True,
        debug_mode: bool = False,
        dry_run: bool = False,
    ) -> Optional[str]:
        """Capture environment evidence."""
        from app.hoc.cus.logs.L6_drivers.capture_driver import (
            capture_environment_evidence,
        )

        return capture_environment_evidence(
            session=session,
            ctx=ctx,
            sdk_mode=sdk_mode,
            execution_environment=execution_environment,
            sdk_version=sdk_version,
            telemetry_delivery_status=telemetry_delivery_status,
            capture_confidence_score=capture_confidence_score,
            telemetry_enabled=telemetry_enabled,
            debug_mode=debug_mode,
            dry_run=dry_run,
        )

    def capture_activity(
        self,
        session: Any,
        ctx: Any,
        *,
        skill_id: str,
        model_name: str,
        prompt_fingerprint: str,
        prompt_token_length: int,
        response_fingerprint: Optional[str] = None,
        response_token_length: Optional[int] = None,
        prompt_template_id: Optional[str] = None,
        prompt_template_version: Optional[str] = None,
        completion_type: Optional[str] = None,
        sensitivity_class: Optional[str] = None,
        redaction_status: Optional[str] = None,
    ) -> Optional[str]:
        """Capture activity evidence."""
        from app.hoc.cus.logs.L6_drivers.capture_driver import (
            capture_activity_evidence,
        )

        return capture_activity_evidence(
            session=session,
            ctx=ctx,
            skill_id=skill_id,
            model_name=model_name,
            prompt_fingerprint=prompt_fingerprint,
            prompt_token_length=prompt_token_length,
            response_fingerprint=response_fingerprint,
            response_token_length=response_token_length,
            prompt_template_id=prompt_template_id,
            prompt_template_version=prompt_template_version,
            completion_type=completion_type,
            sensitivity_class=sensitivity_class,
            redaction_status=redaction_status,
        )

    def capture_provider(
        self,
        session: Any,
        ctx: Any,
        *,
        provider_name: str,
        model_name: str,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
        provider_latency_ms: Optional[int] = None,
        provider_request_id: Optional[str] = None,
        model_version: Optional[str] = None,
        api_version: Optional[str] = None,
        provider_http_status: Optional[int] = None,
        provider_error_code: Optional[str] = None,
        provider_retry_count: int = 0,
        cache_read_tokens: int = 0,
        cache_creation_tokens: int = 0,
    ) -> Optional[str]:
        """Capture provider evidence."""
        from app.hoc.cus.logs.L6_drivers.capture_driver import (
            capture_provider_evidence,
        )

        return capture_provider_evidence(
            session=session,
            ctx=ctx,
            provider_name=provider_name,
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            provider_latency_ms=provider_latency_ms,
            provider_request_id=provider_request_id,
            model_version=model_version,
            api_version=api_version,
            provider_http_status=provider_http_status,
            provider_error_code=provider_error_code,
            provider_retry_count=provider_retry_count,
            cache_read_tokens=cache_read_tokens,
            cache_creation_tokens=cache_creation_tokens,
        )

    def capture_policy_decision(
        self,
        session: Any,
        ctx: Any,
        *,
        policy_type: str,
        decision: str,
        policies_evaluated: Optional[List[str]] = None,
        policy_results: Optional[str] = None,
        decision_reason: Optional[str] = None,
        decision_confidence: Optional[float] = None,
        thresholds_used: Optional[Dict[str, Any]] = None,
        policy_rule_id: Optional[str] = None,
        policy_version: Optional[int] = None,
        customer_guardrail_result: Optional[Dict[str, Any]] = None,
        provider_moderation_result: Optional[Dict[str, Any]] = None,
        decision_reason_codes: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Capture policy decision evidence."""
        from app.hoc.cus.logs.L6_drivers.capture_driver import (
            capture_policy_decision_evidence,
        )

        return capture_policy_decision_evidence(
            session=session,
            ctx=ctx,
            policy_type=policy_type,
            decision=decision,
            policies_evaluated=policies_evaluated,
            policy_results=policy_results,
            decision_reason=decision_reason,
            decision_confidence=decision_confidence,
            thresholds_used=thresholds_used,
            policy_rule_id=policy_rule_id,
            policy_version=policy_version,
            customer_guardrail_result=customer_guardrail_result,
            provider_moderation_result=provider_moderation_result,
            decision_reason_codes=decision_reason_codes,
        )

    def capture_integrity(
        self,
        session: Any,
        run_id: str,
        *,
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
    ) -> Optional[str]:
        """Capture integrity evidence."""
        from app.hoc.cus.logs.L6_drivers.capture_driver import (
            capture_integrity_evidence,
        )

        return capture_integrity_evidence(
            session=session,
            run_id=run_id,
            is_synthetic=is_synthetic,
            synthetic_scenario_id=synthetic_scenario_id,
        )

    def compute_integrity(self, run_id: str) -> Dict[str, Any]:
        """Compute integrity hash for a run."""
        from app.hoc.cus.logs.L6_drivers.capture_driver import compute_integrity

        return compute_integrity(run_id=run_id)

    def hash_prompt(self, prompt: str) -> str:
        """Hash a prompt for fingerprinting."""
        from app.hoc.cus.logs.L6_drivers.capture_driver import hash_prompt

        return hash_prompt(prompt=prompt)
