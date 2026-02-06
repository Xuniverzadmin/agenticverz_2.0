# Layer: L6 — Domain Driver
# NOTE: Renamed capture.py → capture_driver.py (2026-01-31)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: activity_evidence, policy_decisions, integrity_evidence (via session.execute, NO COMMIT)
# Database:
#   Scope: domain (policies)
#   Models: ActivityEvidence, PolicyDecision, IntegrityEvidence
# Role: Taxonomy evidence capture service (ctx-aware) — L6 DOES NOT COMMIT
# Callers: L5 engines (must provide session, must own transaction boundary)
# Allowed Imports: L6, L7 (models)
# Forbidden: session.commit(), conn.commit() — L4 owns commit authority
# Migration Note: Orphan during HOC migration. Authority enforcement applies regardless.
# Reference: PIN-470, Evidence Architecture v1.1, ExecutionContext Specification v1.1, TRANSACTION_BYPASS_REMEDIATION_CHECKLIST.md

"""
Taxonomy Evidence Capture Service (v1.1)

Single entry point for all governance taxonomy evidence writes (Classes B-J).

Transaction Boundary: L6 drivers DO NOT commit.
The caller (L5 engine or L4 coordinator) owns the transaction.
All functions receive session from caller and only call session.execute().

Rules:
- All taxonomy writes go through this file
- All functions require ExecutionContext (except integrity)
- All functions require Session (caller owns transaction)
- No context → No evidence (hard failure, not best-effort)
- No business logic - thin DB writes only
- No inference - fields must be provided explicitly
- Best-effort semantics for DB writes - failures logged, not blocking

Architecture:
- Layer 1 (Operational): contracts.decision_records, routing_decisions, etc.
- Layer 2 (Governance): activity_evidence, policy_decisions, provider_evidence, etc.
- Layer 3 (Integrity): integrity_evidence (terminal-only seal)

This file serves Layer 2 and Layer 3.

v1.1 Changes:
- compute_integrity() now delegates to compute_integrity_v2() (split architecture)
- IntegrityAssembler gathers facts, IntegrityEvaluator applies policy
- Backward compatible: returns same dict structure with extra fields

v1.2 Changes (HOC Authority Enforcement):
- All functions now require session parameter (caller owns transaction)
- Removed all conn.commit() / session.commit() calls
- Removed create_engine usage (session provided by caller)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session

from app.core.execution_context import ExecutionContext

logger = logging.getLogger("nova.evidence.capture")


# =============================================================================
# Evidence Context Error (Phase-1 Closure: No Context → No Evidence)
# =============================================================================


class EvidenceContextError(Exception):
    """
    Hard failure when evidence capture is attempted without ExecutionContext.

    Phase-1 Closure Guardrail (PIN-405):
    - Evidence capture REQUIRES execution context
    - No context = no evidence (by force, not convention)
    - This closes the evidence forgery vector permanently

    This is a blocking exception - callers must handle it explicitly.
    It is NOT a best-effort failure that gets logged and ignored.
    """

    def __init__(self, evidence_type: str, message: str = None):
        self.evidence_type = evidence_type
        self.message = message or f"Evidence capture ({evidence_type}) requires ExecutionContext"
        super().__init__(self.message)


def _assert_context_exists(ctx: ExecutionContext, evidence_type: str) -> None:
    """
    Hard guard: Fail fast if context is None.

    Phase-1 Closure (PIN-405):
    This guard closes the evidence forgery vector by ensuring no evidence
    can be captured without valid execution context.

    Raises:
        EvidenceContextError: If ctx is None (blocks execution)
    """
    if ctx is None:
        logger.error(
            "evidence_context_violation",
            extra={
                "evidence_type": evidence_type,
                "violation": "NO_CONTEXT",
                "severity": "CRITICAL",
            },
        )
        raise EvidenceContextError(
            evidence_type=evidence_type,
            message=f"Evidence capture ({evidence_type}) blocked: ExecutionContext is None. "
            f"No context → No evidence. This is a hard failure, not best-effort."
        )

# NOTE: Session is now provided by caller (L5 engine or L4 coordinator)
# This file no longer creates its own database connections


# =============================================================================
# Evidence Capture Failure Tracking (Watch-out #3, Category C3)
# =============================================================================

# Failure reasons for integrity reporting
class CaptureFailureReason:
    """
    Standard failure reasons for integrity evidence.

    Resolution Semantics (Category C3):
    - TRANSIENT: Temporary failure, may recover (network blip, retry possible)
    - PERMANENT: Unrecoverable failure (schema mismatch, invalid data)
    - SUPERSEDED: Later capture succeeded, this failure can be ignored

    Mapping to default resolution:
    - capture_failed → transient
    - provider_timeout → transient
    - pre_attach → permanent (context doesn't exist yet)
    - network_partition → transient
    - database_error → transient
    - context_invalid → permanent
    """

    CAPTURE_FAILED = "capture_failed"
    PROVIDER_TIMEOUT = "provider_timeout"
    PRE_ATTACH = "pre_attach"
    NETWORK_PARTITION = "network_partition"
    DATABASE_ERROR = "database_error"
    CONTEXT_INVALID = "context_invalid"


class FailureResolution:
    """Resolution semantics for capture failures."""
    TRANSIENT = "transient"
    PERMANENT = "permanent"
    SUPERSEDED = "superseded"


# Default resolution mapping
_FAILURE_RESOLUTION_MAP = {
    CaptureFailureReason.CAPTURE_FAILED: FailureResolution.TRANSIENT,
    CaptureFailureReason.PROVIDER_TIMEOUT: FailureResolution.TRANSIENT,
    CaptureFailureReason.PRE_ATTACH: FailureResolution.PERMANENT,
    CaptureFailureReason.NETWORK_PARTITION: FailureResolution.TRANSIENT,
    CaptureFailureReason.DATABASE_ERROR: FailureResolution.TRANSIENT,
    CaptureFailureReason.CONTEXT_INVALID: FailureResolution.PERMANENT,
}


def _record_capture_failure(
    session: Session,
    run_id: str,
    evidence_type: str,
    failure_reason: str,
    error_message: Optional[str] = None,
    resolution: Optional[str] = None,
) -> None:
    """
    Record an evidence capture failure for later integrity reporting.

    Watch-out #3: Best-effort evidence failures must surface in integrity.

    Category C3: Failures have resolution semantics:
    - transient: May recover with retry
    - permanent: Cannot recover
    - superseded: Later capture succeeded

    Args:
        session: SQLModel session (REQUIRED — caller owns transaction)
        run_id: Run identifier (scope)
        evidence_type: Evidence class (B/D/G/H/I scope)
        failure_reason: Why capture failed
        error_message: Detailed error for debugging
        resolution: Override default resolution (transient/permanent/superseded)

    This is a fire-and-forget operation - failures here are logged but don't
    propagate.
    """
    try:
        # Determine resolution
        if resolution is None:
            resolution = _FAILURE_RESOLUTION_MAP.get(
                failure_reason, FailureResolution.TRANSIENT
            )

        session.execute(
            text("""
                INSERT INTO evidence_capture_failures (
                    id, run_id, evidence_type, failure_reason,
                    error_message, resolution, created_at
                ) VALUES (
                    :id, :run_id, :evidence_type, :failure_reason,
                    :error_message, :resolution, :created_at
                )
                ON CONFLICT DO NOTHING
            """),
            {
                "id": f"ecf-{run_id}-{evidence_type}-{uuid4().hex[:8]}",
                "run_id": run_id,
                "evidence_type": evidence_type,
                "failure_reason": failure_reason,
                "error_message": error_message[:500] if error_message else None,
                "resolution": resolution,
                "created_at": datetime.now(timezone.utc),
            },
        )
        # NO COMMIT — L4 coordinator owns transaction boundary
    except Exception as e:
        # Silent fail - this is best-effort tracking
        logger.debug(f"Failed to record capture failure: {e}")


# NOTE: _get_connection() removed in v1.2
# Session is now provided by caller (L5 engine or L4 coordinator)
# All functions accept session parameter directly


def _hash_content(content: str) -> str:
    """Generate SHA256 fingerprint of content."""
    return hashlib.sha256(content.encode()).hexdigest()


# =============================================================================
# H - Environment Evidence (Once per run, at creation)
# =============================================================================


def capture_environment_evidence(
    session: Session,
    ctx: ExecutionContext,
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
    """
    Capture environment evidence (Class H) at run creation.

    Called once per run, immediately after run is persisted.

    Args:
        session: SQLModel session (REQUIRED — caller owns transaction)
        ctx: ExecutionContext (required)
        sdk_mode: SDK invocation mode (inline, async, degraded, offline)
        execution_environment: Environment context (prod, staging, dev, sandbox)
        sdk_version: SDK version string
        telemetry_delivery_status: Telemetry status (sent, dropped, buffered, unknown)
        capture_confidence_score: Confidence in evidence capture (0.0-1.0)

    Returns:
        Evidence ID if successful, None on failure

    Raises:
        EvidenceContextError: If ctx is None (Phase-1 guardrail)
    """
    # Phase-1 Closure: No Context → No Evidence (hard guard)
    _assert_context_exists(ctx, "environment_evidence")
    ctx.assert_valid_for_evidence()

    evidence_id = f"ee-{ctx.run_id}"

    try:
        session.execute(
            text("""
                INSERT INTO environment_evidence (
                    id, run_id, sdk_mode, sdk_version, environment,
                    telemetry_enabled, telemetry_delivery_status,
                    capture_confidence_score, debug_mode, dry_run,
                    is_synthetic, synthetic_scenario_id, created_at
                ) VALUES (
                    :id, :run_id, :sdk_mode, :sdk_version, :environment,
                    :telemetry_enabled, :telemetry_delivery_status,
                    :capture_confidence_score, :debug_mode, :dry_run,
                    :is_synthetic, :synthetic_scenario_id, :created_at
                )
                ON CONFLICT (run_id) DO NOTHING
            """),
            {
                "id": evidence_id,
                "run_id": ctx.run_id,
                "sdk_mode": sdk_mode,
                "sdk_version": sdk_version,
                "environment": execution_environment,
                "telemetry_enabled": telemetry_enabled,
                "telemetry_delivery_status": telemetry_delivery_status,
                "capture_confidence_score": capture_confidence_score,
                "debug_mode": debug_mode,
                "dry_run": dry_run,
                "is_synthetic": ctx.is_synthetic,
                "synthetic_scenario_id": ctx.synthetic_scenario_id,
                "created_at": datetime.now(timezone.utc),
            },
        )
        # NO COMMIT — L4 coordinator owns transaction boundary

        logger.info(
            "environment_evidence_captured",
            extra={"run_id": ctx.run_id, "evidence_id": evidence_id},
        )
        return evidence_id

    except SQLAlchemyError as e:
        logger.warning(
            "environment_evidence_capture_failed",
            extra={"run_id": ctx.run_id, "error": str(e)},
        )
        # Watch-out #3: Record failure for integrity
        _record_capture_failure(
            session=session,
            run_id=ctx.run_id,
            evidence_type="environment_evidence",
            failure_reason=CaptureFailureReason.DATABASE_ERROR,
            error_message=str(e),
        )
        return None


# =============================================================================
# B - Activity Evidence (Live, per LLM/tool call)
# =============================================================================

# -----------------------------------------------------------------------------
# TAXONOMY RULE (Category B1):
#
# Activity evidence is required ONLY for externally consequential actions.
# Not every skill produces activity evidence - this is by design.
#
# Evidence Required:
#   - llm_invoke: YES (decision-bearing, external LLM call)
#   - http_call: YES (external HTTP effects)
#   - tool_call: YES (external tool invocation)
#
# Evidence NOT Required:
#   - json_transform: NO (pure transform, no external effect)
#   - data_filter: NO (pure transform)
#   - internal_compute: NO (no decision, no external call)
#
# This distinction matters because:
#   1. Not all skills are "decision-bearing"
#   2. Pure transforms don't need audit trails
#   3. Integrity should not penalize missing activity evidence for transforms
# -----------------------------------------------------------------------------


def capture_activity_evidence(
    session: Session,
    ctx: ExecutionContext,
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
    """
    Capture activity evidence (Class B) before/after LLM calls.

    TAXONOMY RULE: Activity evidence is only for externally consequential
    actions (LLM calls, HTTP calls, tool invocations). Pure transforms
    do not require activity evidence.

    Called BEFORE each LLM/tool invocation (with prompt info),
    and optionally updated AFTER with response info.

    Args:
        session: SQLModel session (REQUIRED — caller owns transaction)
        ctx: ExecutionContext (required)
        skill_id: Skill identifier
        model_name: LLM model name
        prompt_fingerprint: SHA256 hash of canonical prompt
        prompt_token_length: Token count of prompt
        response_fingerprint: SHA256 hash of response (optional, after call)
        response_token_length: Token count of response (optional)

    Returns:
        Evidence ID if successful, None on failure

    Raises:
        EvidenceContextError: If ctx is None (Phase-1 guardrail)
    """
    # Phase-1 Closure: No Context → No Evidence (hard guard)
    _assert_context_exists(ctx, "activity_evidence")
    ctx.assert_valid_for_evidence()

    evidence_id = f"ae-{ctx.run_id}-{ctx.step_index}"

    try:
        session.execute(
            text("""
                INSERT INTO activity_evidence (
                    id, run_id, step_index, skill_id, model_name,
                    prompt_fingerprint, prompt_token_length,
                    prompt_template_id, prompt_template_version,
                    response_fingerprint, response_token_length,
                    completion_type, sensitivity_class, redaction_status,
                    evidence_source, is_synthetic, synthetic_scenario_id, created_at
                ) VALUES (
                    :id, :run_id, :step_index, :skill_id, :model_name,
                    :prompt_fingerprint, :prompt_token_length,
                    :prompt_template_id, :prompt_template_version,
                    :response_fingerprint, :response_token_length,
                    :completion_type, :sensitivity_class, :redaction_status,
                    :evidence_source, :is_synthetic, :synthetic_scenario_id, :created_at
                )
                ON CONFLICT (run_id, step_index) DO UPDATE SET
                    response_fingerprint = COALESCE(EXCLUDED.response_fingerprint, activity_evidence.response_fingerprint),
                    response_token_length = COALESCE(EXCLUDED.response_token_length, activity_evidence.response_token_length),
                    completion_type = COALESCE(EXCLUDED.completion_type, activity_evidence.completion_type)
            """),
            {
                "id": evidence_id,
                "run_id": ctx.run_id,
                "step_index": ctx.step_index,
                "skill_id": skill_id,
                "model_name": model_name,
                "prompt_fingerprint": prompt_fingerprint,
                "prompt_token_length": prompt_token_length,
                "prompt_template_id": prompt_template_id,
                "prompt_template_version": prompt_template_version,
                "response_fingerprint": response_fingerprint,
                "response_token_length": response_token_length,
                "completion_type": completion_type,
                "sensitivity_class": sensitivity_class,
                "redaction_status": redaction_status,
                "evidence_source": ctx.source.value,
                "is_synthetic": ctx.is_synthetic,
                "synthetic_scenario_id": ctx.synthetic_scenario_id,
                "created_at": datetime.now(timezone.utc),
            },
        )
        # NO COMMIT — L4 coordinator owns transaction boundary

        logger.debug(
            "activity_evidence_captured",
            extra={
                "run_id": ctx.run_id,
                "step_index": ctx.step_index,
                "evidence_id": evidence_id,
            },
        )
        return evidence_id

    except SQLAlchemyError as e:
        logger.warning(
            "activity_evidence_capture_failed",
            extra={"run_id": ctx.run_id, "step_index": ctx.step_index, "error": str(e)},
        )
        # Watch-out #3: Record failure for integrity
        _record_capture_failure(
            session=session,
            run_id=ctx.run_id,
            evidence_type="activity_evidence",
            failure_reason=CaptureFailureReason.DATABASE_ERROR,
            error_message=str(e),
        )
        return None


# =============================================================================
# G - Provider Evidence (Live, per provider call)
# =============================================================================


def capture_provider_evidence(
    session: Session,
    ctx: ExecutionContext,
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
    """
    Capture provider evidence (Class G) after LLM provider response.

    Called AFTER each provider interaction.

    Args:
        session: SQLModel session (REQUIRED — caller owns transaction)
        ctx: ExecutionContext (required)
        provider_name: Provider identifier (anthropic, openai, etc.)
        model_name: Model name used
        input_tokens: Input token count
        output_tokens: Output token count
        provider_latency_ms: Provider response latency in milliseconds

    Returns:
        Evidence ID if successful, None on failure

    Raises:
        EvidenceContextError: If ctx is None (Phase-1 guardrail)
    """
    # Phase-1 Closure: No Context → No Evidence (hard guard)
    _assert_context_exists(ctx, "provider_evidence")
    ctx.assert_valid_for_evidence()

    evidence_id = f"pe-{ctx.run_id}-{ctx.step_index}"
    now = datetime.now(timezone.utc)

    try:
        session.execute(
            text("""
                INSERT INTO provider_evidence (
                    id, run_id, step_index, provider_name, provider_request_id,
                    model_name, model_version, input_tokens, output_tokens,
                    cache_read_tokens, cache_creation_tokens, total_tokens,
                    api_version, provider_latency_ms, provider_http_status,
                    provider_error_code, provider_retry_count,
                    requested_at, responded_at,
                    is_synthetic, synthetic_scenario_id, created_at
                ) VALUES (
                    :id, :run_id, :step_index, :provider_name, :provider_request_id,
                    :model_name, :model_version, :input_tokens, :output_tokens,
                    :cache_read_tokens, :cache_creation_tokens, :total_tokens,
                    :api_version, :provider_latency_ms, :provider_http_status,
                    :provider_error_code, :provider_retry_count,
                    :requested_at, :responded_at,
                    :is_synthetic, :synthetic_scenario_id, :created_at
                )
                ON CONFLICT (run_id, step_index) DO NOTHING
            """),
            {
                "id": evidence_id,
                "run_id": ctx.run_id,
                "step_index": ctx.step_index,
                "provider_name": provider_name,
                "provider_request_id": provider_request_id,
                "model_name": model_name,
                "model_version": model_version,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cache_read_tokens": cache_read_tokens,
                "cache_creation_tokens": cache_creation_tokens,
                "total_tokens": total_tokens or ((input_tokens or 0) + (output_tokens or 0)),
                "api_version": api_version,
                "provider_latency_ms": provider_latency_ms,
                "provider_http_status": provider_http_status,
                "provider_error_code": provider_error_code,
                "provider_retry_count": provider_retry_count,
                "requested_at": now,
                "responded_at": now,
                "is_synthetic": ctx.is_synthetic,
                "synthetic_scenario_id": ctx.synthetic_scenario_id,
                "created_at": now,
            },
        )
        # NO COMMIT — L4 coordinator owns transaction boundary

        logger.debug(
            "provider_evidence_captured",
            extra={
                "run_id": ctx.run_id,
                "step_index": ctx.step_index,
                "provider": provider_name,
                "evidence_id": evidence_id,
            },
        )
        return evidence_id

    except SQLAlchemyError as e:
        logger.warning(
            "provider_evidence_capture_failed",
            extra={"run_id": ctx.run_id, "step_index": ctx.step_index, "error": str(e)},
        )
        # Watch-out #3: Record failure for integrity
        _record_capture_failure(
            session=session,
            run_id=ctx.run_id,
            evidence_type="provider_evidence",
            failure_reason=CaptureFailureReason.DATABASE_ERROR,
            error_message=str(e),
        )
        return None


# =============================================================================
# D - Policy Decision Evidence (Bridge from operational to governance)
# =============================================================================


def capture_policy_decision_evidence(
    session: Session,
    ctx: ExecutionContext,
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
    """
    Capture policy decision evidence (Class D) during policy evaluation.

    This bridges operational decision records to governance taxonomy.
    Called whenever a policy/guardrail is evaluated.

    Args:
        session: SQLModel session (REQUIRED — caller owns transaction)
        ctx: ExecutionContext (required)
        policy_type: Type of policy (budget, rate_limit, capability, permission)
        decision: Decision outcome (GRANTED, DENIED, PENDING_APPROVAL)
        policies_evaluated: List of policy IDs evaluated
        policy_results: Aggregated result (pass, warn, fail, skip)

    Returns:
        Evidence ID if successful, None on failure

    Raises:
        EvidenceContextError: If ctx is None (Phase-1 guardrail)
    """
    # Phase-1 Closure: No Context → No Evidence (hard guard)
    _assert_context_exists(ctx, "policy_decision")
    ctx.assert_valid_for_evidence()

    evidence_id = f"pd-{ctx.run_id}-{policy_type}-{uuid4().hex[:8]}"

    try:
        session.execute(
            text("""
                INSERT INTO policy_decisions (
                    id, run_id, policy_type, policy_rule_id, policy_version,
                    decision, decision_reason, decision_confidence,
                    policies_evaluated, policy_results, thresholds_used,
                    customer_guardrail_result, provider_moderation_result,
                    decision_reason_codes, evaluated_at,
                    is_synthetic, synthetic_scenario_id, created_at
                ) VALUES (
                    :id, :run_id, :policy_type, :policy_rule_id, :policy_version,
                    :decision, :decision_reason, :decision_confidence,
                    :policies_evaluated, :policy_results, :thresholds_used,
                    :customer_guardrail_result, :provider_moderation_result,
                    :decision_reason_codes, :evaluated_at,
                    :is_synthetic, :synthetic_scenario_id, :created_at
                )
            """),
            {
                "id": evidence_id,
                "run_id": ctx.run_id,
                "policy_type": policy_type,
                "policy_rule_id": policy_rule_id,
                "policy_version": policy_version,
                "decision": decision,
                "decision_reason": decision_reason,
                "decision_confidence": decision_confidence,
                "policies_evaluated": policies_evaluated,
                "policy_results": policy_results,
                "thresholds_used": thresholds_used,
                "customer_guardrail_result": customer_guardrail_result,
                "provider_moderation_result": provider_moderation_result,
                "decision_reason_codes": decision_reason_codes,
                "evaluated_at": datetime.now(timezone.utc),
                "is_synthetic": ctx.is_synthetic,
                "synthetic_scenario_id": ctx.synthetic_scenario_id,
                "created_at": datetime.now(timezone.utc),
            },
        )
        # NO COMMIT — L4 coordinator owns transaction boundary

        logger.debug(
            "policy_decision_evidence_captured",
            extra={
                "run_id": ctx.run_id,
                "policy_type": policy_type,
                "decision": decision,
                "evidence_id": evidence_id,
            },
        )
        return evidence_id

    except SQLAlchemyError as e:
        logger.warning(
            "policy_decision_evidence_capture_failed",
            extra={"run_id": ctx.run_id, "policy_type": policy_type, "error": str(e)},
        )
        # Watch-out #3: Record failure for integrity
        _record_capture_failure(
            session=session,
            run_id=ctx.run_id,
            evidence_type="policy_decisions",
            failure_reason=CaptureFailureReason.DATABASE_ERROR,
            error_message=str(e),
        )
        return None


# =============================================================================
# J - Integrity Evidence (Terminal only, exactly once)
# =============================================================================


def compute_integrity(run_id: str) -> Dict[str, Any]:
    """
    Compute integrity payload by examining evidence tables.

    v1.1: Delegates to compute_integrity_v2 which uses the split architecture
    (IntegrityAssembler + IntegrityEvaluator).

    Watch-out #3: Checks for recorded capture failures and includes them
    in missing_reasons with specific failure codes.

    Returns dictionary with expected/observed/missing artifacts and integrity score.
    Backward compatible - same dict structure as v1.0, with optional extra fields.
    """
    # v1.1: Delegate to the split architecture implementation
    from app.evidence.integrity import compute_integrity_v2

    logger.debug(
        "compute_integrity_delegating_to_v2",
        extra={"run_id": run_id},
    )

    return compute_integrity_v2(run_id)


def capture_integrity_evidence(
    session: Session,
    run_id: str,
    *,
    is_synthetic: bool = False,
    synthetic_scenario_id: Optional[str] = None,
) -> Optional[str]:
    """
    Capture integrity evidence (Class J) at terminal state.

    Called EXACTLY ONCE when run reaches terminal state.
    This is the truth seal - computed from all observed evidence.

    NOTE: This function does NOT require ExecutionContext by design.
    Integrity is computed from run_id after execution ends.

    Args:
        session: SQLModel session (REQUIRED — caller owns transaction)
        run_id: Run identifier
        is_synthetic: Whether this is SDSR execution
        synthetic_scenario_id: SDSR scenario ID if synthetic

    Returns:
        Evidence ID if successful, None on failure
    """
    evidence_id = f"ie-{run_id}"

    # Compute integrity from evidence tables
    integrity_payload = compute_integrity(run_id)

    # Watch-out #3: Include capture failures in missing_reasons for storage
    missing_reasons_with_failures = integrity_payload["missing_reasons"].copy()
    if integrity_payload.get("capture_failures"):
        missing_reasons_with_failures["_capture_failures"] = integrity_payload["capture_failures"]

    try:
        session.execute(
            text("""
                INSERT INTO integrity_evidence (
                    id, run_id, expected_artifacts, observed_artifacts,
                    missing_artifacts, missing_reasons, integrity_score,
                    integrity_status, verification_method, verification_timestamp,
                    is_synthetic, synthetic_scenario_id, created_at
                ) VALUES (
                    :id, :run_id, :expected_artifacts, :observed_artifacts,
                    :missing_artifacts, :missing_reasons, :integrity_score,
                    :integrity_status, :verification_method, :verification_timestamp,
                    :is_synthetic, :synthetic_scenario_id, :created_at
                )
                ON CONFLICT (run_id) DO NOTHING
            """),
            {
                "id": evidence_id,
                "run_id": run_id,
                "expected_artifacts": integrity_payload["expected_artifacts"],
                "observed_artifacts": integrity_payload["observed_artifacts"],
                "missing_artifacts": integrity_payload["missing_artifacts"],
                "missing_reasons": json.dumps(missing_reasons_with_failures),  # JSONB needs JSON string
                "integrity_score": integrity_payload["integrity_score"],
                "integrity_status": integrity_payload["integrity_status"],
                "verification_method": "evidence_table_scan",
                "verification_timestamp": datetime.now(timezone.utc),
                "is_synthetic": is_synthetic,
                "synthetic_scenario_id": synthetic_scenario_id,
                "created_at": datetime.now(timezone.utc),
            },
        )
        # NO COMMIT — L4 coordinator owns transaction boundary

        logger.info(
            "integrity_evidence_captured",
            extra={
                "run_id": run_id,
                "evidence_id": evidence_id,
                "integrity_score": integrity_payload["integrity_score"],
                "integrity_status": integrity_payload["integrity_status"],
            },
        )
        return evidence_id

    except SQLAlchemyError as e:
        logger.warning(
            "integrity_evidence_capture_failed",
            extra={"run_id": run_id, "error": str(e)},
        )
        return None


# =============================================================================
# Utility: Hash prompt for fingerprinting
# =============================================================================


def hash_prompt(prompt: str) -> str:
    """Generate SHA256 fingerprint of prompt content."""
    return _hash_content(prompt)
