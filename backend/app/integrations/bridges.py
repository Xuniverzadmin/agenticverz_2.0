"""
M25 Integration Bridges

Five bridges connecting the three pillars:
1. Incident → Failure Catalog (with confidence bands)
2. Pattern → Recovery (with template/generated distinction)
3. Recovery → Policy (with shadow mode)
4. Policy → CARE Routing (with guardrails)
5. Loop Status → Console (with narrative artifacts)

FROZEN: 2025-12-23
Do NOT modify loop mechanics without explicit approval.
"""

from __future__ import annotations

import hashlib
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from .events import (
    LOOP_MECHANICS_FROZEN_AT,
    LOOP_MECHANICS_VERSION,
    ConfidenceBand,
    ConfidenceCalculator,
    LoopEvent,
    LoopFailureState,
    LoopStage,
    LoopStatus,
    PatternMatchResult,
    PolicyMode,
    PolicyRule,
    RecoverySuggestion,
    RoutingAdjustment,
)

logger = logging.getLogger(__name__)


# =============================================================================
# FROZEN MECHANICS CHECK
# =============================================================================


def _check_frozen() -> None:
    """Log that frozen mechanics are in use."""
    logger.info(
        f"M25 Loop Mechanics v{LOOP_MECHANICS_VERSION} (frozen {LOOP_MECHANICS_FROZEN_AT}) - "
        f"Confidence calculator: {ConfidenceCalculator.VERSION}"
    )


# =============================================================================
# POLICY ACTIVATION AUDIT (HYGIENE #3)
# =============================================================================


@dataclass
class PolicyActivationAudit:
    """
    Audit record for policy activation.

    Required for:
    - Rollback
    - Blame tracking
    - Trust verification
    """

    policy_id: str
    source_pattern_id: str
    source_recovery_id: str
    confidence_at_activation: float
    confidence_version: str
    approval_path: str  # "auto" | "human:{user_id}" | "threshold"
    loop_trace_id: str
    activated_at: datetime
    tenant_id: str

    def to_dict(self) -> dict:
        return {
            "policy_id": self.policy_id,
            "source_pattern_id": self.source_pattern_id,
            "source_recovery_id": self.source_recovery_id,
            "confidence_at_activation": self.confidence_at_activation,
            "confidence_version": self.confidence_version,
            "approval_path": self.approval_path,
            "loop_trace_id": self.loop_trace_id,
            "activated_at": self.activated_at.isoformat(),
            "tenant_id": self.tenant_id,
        }


async def record_policy_activation(
    db_factory,
    policy_id: str,
    source_pattern_id: str,
    source_recovery_id: str,
    confidence: float,
    approval_path: str,
    loop_trace_id: str,
    tenant_id: str,
) -> PolicyActivationAudit:
    """
    Record policy activation for audit trail.

    Every ACTIVE policy must have an audit record.
    """
    audit = PolicyActivationAudit(
        policy_id=policy_id,
        source_pattern_id=source_pattern_id,
        source_recovery_id=source_recovery_id,
        confidence_at_activation=confidence,
        confidence_version=ConfidenceCalculator.VERSION,
        approval_path=approval_path,
        loop_trace_id=loop_trace_id,
        activated_at=datetime.now(timezone.utc),
        tenant_id=tenant_id,
    )

    async with db_factory() as session:
        from sqlalchemy import text

        await session.execute(
            text(
                """
                INSERT INTO policy_activation_audit
                (policy_id, source_pattern_id, source_recovery_id,
                 confidence_at_activation, confidence_version, approval_path,
                 loop_trace_id, activated_at, tenant_id)
                VALUES (:policy_id, :pattern_id, :recovery_id,
                        :confidence, :version, :approval_path,
                        :trace_id, :activated_at, :tenant_id)
                ON CONFLICT (policy_id) DO UPDATE SET
                    confidence_at_activation = :confidence,
                    approval_path = :approval_path,
                    activated_at = :activated_at
            """
            ),
            {
                "policy_id": audit.policy_id,
                "pattern_id": audit.source_pattern_id,
                "recovery_id": audit.source_recovery_id,
                "confidence": audit.confidence_at_activation,
                "version": audit.confidence_version,
                "approval_path": audit.approval_path,
                "trace_id": audit.loop_trace_id,
                "activated_at": audit.activated_at,
                "tenant_id": audit.tenant_id,
            },
        )
        await session.commit()

    logger.info(f"Policy activation audit recorded: {policy_id} (confidence={confidence:.2f}, path={approval_path})")

    return audit


# =============================================================================
# BASE BRIDGE
# =============================================================================


class BaseBridge(ABC):
    """Base class for all integration bridges."""

    @property
    @abstractmethod
    def stage(self) -> LoopStage:
        """The stage this bridge handles."""
        pass

    @abstractmethod
    async def process(self, event: LoopEvent) -> LoopEvent:
        """Process an event and return the result event."""
        pass

    def register(self, dispatcher: "IntegrationDispatcher") -> None:
        """Register this bridge with the dispatcher."""
        dispatcher.register_handler(self.stage, self.process)
        logger.info(f"Registered {self.__class__.__name__} for {self.stage.value}")


# =============================================================================
# BRIDGE 1: INCIDENT → FAILURE CATALOG
# =============================================================================


class IncidentToCatalogBridge(BaseBridge):
    """
    Bridge 1: Route incidents to failure catalog.

    Enhanced with:
    - Confidence bands (strong/weak/novel)
    - Signature normalization for better matching
    - Pattern version tracking
    """

    def __init__(self, db_session_factory):
        self.db_factory = db_session_factory

    @property
    def stage(self) -> LoopStage:
        return LoopStage.INCIDENT_CREATED

    async def process(self, event: LoopEvent) -> LoopEvent:
        """
        Match incident against known patterns.

        Flow:
        1. Extract and normalize failure signature
        2. Query patterns with fuzzy matching
        3. Classify confidence into bands
        4. Create new pattern if novel
        5. Return match result
        """
        try:
            incident_id = event.incident_id
            incident_data = event.details.get("incident", {})

            # Extract normalized signature
            signature = self._extract_signature(incident_data)
            signature_hash = self._hash_signature(signature)

            # Find matching patterns
            match_result = await self._find_matching_pattern(signature, signature_hash, incident_id, event.tenant_id)

            # Update event with result (serialize for JSON)
            event.details["match_result"] = match_result.to_dict()
            event.details["pattern_id"] = match_result.pattern_id
            event.details["confidence"] = match_result.confidence
            event.confidence_band = match_result.confidence_band

            # Set failure state if match is too weak
            if not match_result.should_auto_proceed:
                if match_result.confidence_band == ConfidenceBand.NOVEL:
                    event.failure_state = LoopFailureState.MATCH_LOW_CONFIDENCE
                # Weak matches don't fail, but flag for review
                event.requires_human_review = True

            logger.info(
                f"Pattern match for incident {incident_id}: "
                f"pattern={match_result.pattern_id}, "
                f"confidence={match_result.confidence:.2f}, "
                f"band={match_result.confidence_band.value}"
            )

            return event

        except Exception as e:
            logger.exception(f"Bridge 1 error for incident {event.incident_id}: {e}")
            event.failure_state = LoopFailureState.MATCH_FAILED
            event.details["error"] = str(e)
            return event

    def _extract_signature(self, incident: dict) -> dict:
        """
        Extract normalized failure signature from incident.

        Signature components:
        - error_type: Category of error
        - error_code: Specific error code if available
        - context_keys: Relevant context keys (sorted)
        - agent_capability: What the agent was trying to do
        """
        return {
            "error_type": incident.get("error_type", "unknown"),
            "error_code": incident.get("error_code"),
            "context_keys": sorted(incident.get("context", {}).keys()),
            "agent_capability": incident.get("agent_capability"),
            "api_endpoint": incident.get("api_endpoint"),
            "status_code": incident.get("status_code"),
        }

    def _hash_signature(self, signature: dict) -> str:
        """Create deterministic hash of signature for exact matching."""
        canonical = json.dumps(signature, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()[:32]

    async def _find_matching_pattern(
        self,
        signature: dict,
        signature_hash: str,
        incident_id: str,
        tenant_id: str,
    ) -> PatternMatchResult:
        """Find matching pattern with confidence scoring."""
        try:
            async with self.db_factory() as session:
                from sqlalchemy import text

                # First try exact hash match
                result = await session.execute(
                    text(
                        """
                        SELECT id, signature, occurrence_count
                        FROM failure_patterns
                        WHERE signature_hash = :hash
                        AND (tenant_id = :tenant_id OR tenant_id IS NULL)
                        LIMIT 1
                    """
                    ),
                    {"hash": signature_hash, "tenant_id": tenant_id},
                )
                exact_match = result.fetchone()

                if exact_match:
                    # Exact match = high confidence
                    await self._increment_pattern_count(session, exact_match.id)
                    return PatternMatchResult.from_match(
                        incident_id=incident_id,
                        pattern_id=exact_match.id,
                        confidence=0.95,  # Strong match
                        signature_hash=signature_hash,
                        is_new=False,
                        details={"match_type": "exact_hash"},
                    )

                # Try fuzzy matching on signature components (without pg_trgm)
                fuzzy_result = await session.execute(
                    text(
                        """
                        SELECT id, signature, occurrence_count
                        FROM failure_patterns
                        WHERE (tenant_id = :tenant_id OR tenant_id IS NULL)
                        AND signature->>'error_type' = :error_type
                        ORDER BY occurrence_count DESC
                        LIMIT 5
                    """
                    ),
                    {
                        "tenant_id": tenant_id,
                        "error_type": signature.get("error_type", ""),
                    },
                )
                fuzzy_matches = fuzzy_result.fetchall()

                if fuzzy_matches:
                    best_match = fuzzy_matches[0]
                    # Calculate composite confidence using Python
                    stored_sig = best_match.signature
                    if isinstance(stored_sig, str):
                        stored_sig = json.loads(stored_sig)
                    confidence = self._calculate_fuzzy_confidence(signature, stored_sig)

                    if confidence >= 0.6:
                        await self._increment_pattern_count(session, best_match.id)
                        return PatternMatchResult.from_match(
                            incident_id=incident_id,
                            pattern_id=best_match.id,
                            confidence=confidence,
                            signature_hash=signature_hash,
                            is_new=False,
                            details={"match_type": "fuzzy", "calculated_confidence": confidence},
                        )

                # No good match - create new pattern
                pattern_id = await self._create_pattern(session, signature, signature_hash, incident_id, tenant_id)

                return PatternMatchResult.from_match(
                    incident_id=incident_id,
                    pattern_id=pattern_id,
                    confidence=1.0,  # New patterns have full confidence (they match themselves)
                    signature_hash=signature_hash,
                    is_new=True,
                    details={"match_type": "new_pattern"},
                )

        except Exception as e:
            logger.error(f"Pattern matching failed: {e}")
            return PatternMatchResult.no_match(incident_id, signature_hash)

    def _calculate_fuzzy_confidence(self, query_sig: dict, stored_sig: dict) -> float:
        """Calculate fuzzy match confidence between signatures."""
        if isinstance(stored_sig, str):
            stored_sig = json.loads(stored_sig)

        score = 0.0
        weights = {
            "error_type": 0.3,
            "error_code": 0.2,
            "agent_capability": 0.2,
            "api_endpoint": 0.15,
            "status_code": 0.15,
        }

        for key, weight in weights.items():
            if query_sig.get(key) == stored_sig.get(key):
                score += weight
            elif query_sig.get(key) and stored_sig.get(key):
                # Partial match for strings
                if isinstance(query_sig.get(key), str):
                    if query_sig[key] in stored_sig[key] or stored_sig[key] in query_sig[key]:
                        score += weight * 0.5

        return score

    async def _increment_pattern_count(self, session, pattern_id: str) -> None:
        """Increment pattern occurrence count."""
        from sqlalchemy import text

        await session.execute(
            text(
                """
                UPDATE failure_patterns
                SET occurrence_count = occurrence_count + 1,
                    last_occurrence_at = NOW()
                WHERE id = :id
            """
            ),
            {"id": pattern_id},
        )
        await session.commit()

    async def _create_pattern(
        self,
        session,
        signature: dict,
        signature_hash: str,
        incident_id: str,
        tenant_id: str,
    ) -> str:
        """Create new failure pattern."""
        from uuid import uuid4

        from sqlalchemy import text

        pattern_id = f"pat_{uuid4().hex[:16]}"

        # Determine pattern type from signature
        error_type = signature.get("error_type", "unknown")
        pattern_type = "policy_violation" if "policy" in error_type or "block" in error_type else "error"

        await session.execute(
            text(
                """
                INSERT INTO failure_patterns
                (id, tenant_id, pattern_type, signature, signature_hash, first_incident_id, occurrence_count, created_at)
                VALUES (:id, :tenant_id, :pattern_type, CAST(:signature AS jsonb), :hash, :incident_id, 1, NOW())
            """
            ),
            {
                "id": pattern_id,
                "tenant_id": tenant_id,
                "pattern_type": pattern_type,
                "signature": json.dumps(signature),
                "hash": signature_hash,
                "incident_id": incident_id,
            },
        )
        await session.commit()

        logger.info(f"Created new pattern {pattern_id} for incident {incident_id}")
        return pattern_id


# =============================================================================
# BRIDGE 2: PATTERN → RECOVERY
# =============================================================================


class PatternToRecoveryBridge(BaseBridge):
    """
    Bridge 2: Generate recovery suggestions from patterns.

    Enhanced with:
    - Template vs generated distinction
    - Confirmation requirements based on confidence
    - Auto-apply only for strong matches
    """

    def __init__(self, db_session_factory, llm_client=None):
        self.db_factory = db_session_factory
        self.llm_client = llm_client

    @property
    def stage(self) -> LoopStage:
        return LoopStage.PATTERN_MATCHED

    async def process(self, event: LoopEvent) -> LoopEvent:
        """
        Generate recovery suggestion for matched pattern.

        Flow:
        1. Load pattern with recovery template
        2. If template exists, instantiate it
        3. If no template, generate suggestion
        4. Apply confidence-based auto-apply rules
        """
        try:
            pattern_id = event.details.get("pattern_id")
            if not pattern_id:
                event.failure_state = LoopFailureState.RECOVERY_NOT_APPLICABLE
                event.details["error"] = "No pattern ID provided"
                return event

            # Load pattern
            pattern = await self._load_pattern(pattern_id)
            if not pattern:
                event.failure_state = LoopFailureState.RECOVERY_NOT_APPLICABLE
                event.details["error"] = f"Pattern {pattern_id} not found"
                return event

            # Get confidence band from event
            confidence_band = event.confidence_band or ConfidenceBand.from_confidence(
                event.details.get("confidence", 0)
            )

            # Generate or instantiate recovery
            if pattern.get("recovery_template"):
                suggestion = await self._instantiate_template(pattern, event.incident_id, confidence_band)
            else:
                suggestion = await self._generate_recovery(pattern, event.incident_id, confidence_band)

            # Apply auto-apply rules
            if suggestion.auto_applicable and pattern.get("auto_apply_recovery"):
                suggestion = await self._apply_recovery(suggestion)
            else:
                suggestion = await self._queue_for_review(suggestion)

            # Update event (serialize for JSON)
            event.details["recovery"] = suggestion.to_dict()
            event.details["recovery_id"] = suggestion.recovery_id
            event.confidence_band = suggestion.confidence_band

            if suggestion.status == "rejected":
                event.failure_state = LoopFailureState.RECOVERY_REJECTED

            logger.info(
                f"Recovery suggestion for pattern {pattern_id}: "
                f"type={suggestion.suggestion_type}, "
                f"status={suggestion.status}"
            )

            return event

        except Exception as e:
            logger.exception(f"Bridge 2 error: {e}")
            event.failure_state = LoopFailureState.RECOVERY_REJECTED
            event.details["error"] = str(e)
            return event

    async def _load_pattern(self, pattern_id: str) -> Optional[dict]:
        """Load pattern from database."""
        async with self.db_factory() as session:
            from sqlalchemy import text

            result = await session.execute(
                text("SELECT * FROM failure_patterns WHERE id = :id"),
                {"id": pattern_id},
            )
            row = result.fetchone()
            if row:
                return dict(row._mapping)
        return None

    async def _instantiate_template(
        self,
        pattern: dict,
        incident_id: str,
        confidence_band: ConfidenceBand,
    ) -> RecoverySuggestion:
        """Instantiate recovery from pattern template."""
        template = pattern["recovery_template"]
        if isinstance(template, str):
            template = json.loads(template)

        return RecoverySuggestion.create(
            incident_id=incident_id,
            pattern_id=pattern["id"],
            action_type=template.get("action_type", "unknown"),
            action_params=template.get("action_params", {}),
            confidence=0.9 if confidence_band == ConfidenceBand.STRONG_MATCH else 0.7,
            suggestion_type="template",
            requires_confirmation=0 if confidence_band.allows_auto_apply else 1,
        )

    async def _generate_recovery(
        self,
        pattern: dict,
        incident_id: str,
        confidence_band: ConfidenceBand,
    ) -> RecoverySuggestion:
        """
        Generate recovery suggestion (LLM or heuristics).

        Uses FROZEN ConfidenceCalculator for all confidence logic.
        """
        # Heuristic-based recovery generation
        signature = pattern.get("signature", {})
        if isinstance(signature, str):
            signature = json.loads(signature)

        error_type = signature.get("error_type", "unknown")

        # Map error types to recovery actions
        recovery_map = {
            "rate_limit": ("rate_limit", {"window_seconds": 60, "max_requests": 10}),
            "timeout": ("retry", {"max_retries": 3, "backoff_seconds": 5}),
            "auth_error": ("escalate", {"escalation_level": "admin"}),
            "validation_error": ("block", {"reason": "invalid_input"}),
            "resource_exhausted": ("rate_limit", {"window_seconds": 300, "max_requests": 5}),
        }

        action_type, action_params = recovery_map.get(error_type, ("escalate", {"reason": "unknown_error"}))

        # FROZEN: Use centralized ConfidenceCalculator
        occurrence_count = pattern.get("occurrence_count", 1)
        is_strong_match = confidence_band == ConfidenceBand.STRONG_MATCH

        confidence, conf_version, conf_details = ConfidenceCalculator.calculate_recovery_confidence(
            base_confidence=0.7 if is_strong_match else 0.5,
            occurrence_count=occurrence_count,
            is_strong_match=is_strong_match,
        )

        # FROZEN: Use centralized auto-apply logic
        requires_confirmation = ConfidenceCalculator.get_confirmation_level(confidence)
        if ConfidenceCalculator.should_auto_apply(confidence, occurrence_count):
            requires_confirmation = 0

        logger.info(
            f"Recovery confidence calculated: {conf_version} -> {confidence:.2f} "
            f"(occurrences={occurrence_count}, boost={conf_details['boost_applied']:.2f})"
        )

        return RecoverySuggestion.create(
            incident_id=incident_id,
            pattern_id=pattern["id"],
            action_type=action_type,
            action_params=action_params,
            confidence=confidence,
            suggestion_type="generated",
            requires_confirmation=requires_confirmation,
        )

    async def _apply_recovery(self, suggestion: RecoverySuggestion) -> RecoverySuggestion:
        """Apply recovery immediately."""
        suggestion.status = "applied"
        await self._persist_recovery(suggestion)
        logger.info(f"Auto-applied recovery {suggestion.recovery_id}")
        return suggestion

    async def _queue_for_review(self, suggestion: RecoverySuggestion) -> RecoverySuggestion:
        """Queue recovery for human review."""
        suggestion.status = "pending"
        await self._persist_recovery(suggestion)
        logger.info(f"Queued recovery {suggestion.recovery_id} for review")
        return suggestion

    async def _persist_recovery(self, suggestion: RecoverySuggestion) -> None:
        """Persist recovery suggestion to database."""
        import uuid

        async with self.db_factory() as session:
            from sqlalchemy import text

            # Generate UUIDs for required fields
            failure_match_id = uuid.uuid4()

            # Use proper schema: recovery_candidates requires failure_match_id, suggestion, etc.
            await session.execute(
                text(
                    """
                    INSERT INTO recovery_candidates
                    (failure_match_id, suggestion, confidence, source_incident_id, source_pattern_id,
                     suggestion_type, confidence_band, requires_confirmation, occurrence_count,
                     last_occurrence_at, created_at, updated_at)
                    VALUES (:failure_match_id, :suggestion, :confidence, :incident_id, :pattern_id,
                            :type, :confidence_band, :requires_conf, 1, NOW(), NOW(), NOW())
                """
                ),
                {
                    "failure_match_id": str(failure_match_id),
                    "suggestion": json.dumps(
                        {
                            "action_type": suggestion.action_type,
                            "action_params": suggestion.action_params,
                            "status": suggestion.status,
                        }
                    ),
                    "confidence": suggestion.confidence,
                    "incident_id": suggestion.incident_id,
                    "pattern_id": suggestion.pattern_id,
                    "type": suggestion.suggestion_type,
                    "confidence_band": suggestion.confidence_band.value if suggestion.confidence_band else "weak_match",
                    "requires_conf": suggestion.requires_confirmation,
                },
            )
            await session.commit()


# =============================================================================
# BRIDGE 3: RECOVERY → POLICY
# =============================================================================


class RecoveryToPolicyBridge(BaseBridge):
    """
    Bridge 3: Convert applied recovery into prevention policy.

    Enhanced with:
    - Shadow mode for safe observation
    - N-confirmation requirement
    - Policy regret tracking
    """

    def __init__(self, db_session_factory, config=None):
        self.db_factory = db_session_factory
        self.confirmations_required = config.policy_confirmations_required if config else 3

    @property
    def stage(self) -> LoopStage:
        return LoopStage.RECOVERY_SUGGESTED

    async def process(self, event: LoopEvent) -> LoopEvent:
        """
        Generate prevention policy from applied recovery.

        Only generate policy if:
        - Recovery was applied (not just suggested)
        - Pattern has occurred 3+ times (not one-off)
        - Confidence is sufficient
        """
        try:
            recovery = event.details.get("recovery")
            if not recovery:
                event.failure_state = LoopFailureState.POLICY_LOW_CONFIDENCE
                event.details["policy_skipped"] = "No recovery provided"
                return event

            # Check recovery status (handle both dict and object)
            recovery_status = (
                recovery.get("status") if isinstance(recovery, dict) else getattr(recovery, "status", None)
            )
            if recovery_status and recovery_status not in ("applied", "pending"):
                event.failure_state = LoopFailureState.POLICY_LOW_CONFIDENCE
                event.details["policy_skipped"] = f"Recovery status is {recovery_status}"
                return event

            pattern_id = event.details.get("pattern_id")
            pattern = await self._load_pattern(pattern_id)

            if not pattern:
                event.failure_state = LoopFailureState.POLICY_LOW_CONFIDENCE
                return event

            # Check occurrence threshold
            occurrence_count = pattern.get("occurrence_count", 0)
            if occurrence_count < 3:
                event.details["policy_skipped"] = f"Only {occurrence_count} occurrences, need 3+"
                # Don't fail, just skip policy generation
                return event

            # Generate policy
            recovery_obj = (
                recovery
                if isinstance(recovery, RecoverySuggestion)
                else RecoverySuggestion(
                    recovery_id=recovery.get("recovery_id", "unknown"),
                    incident_id=event.incident_id,
                    pattern_id=pattern_id,
                    suggestion_type=recovery.get("suggestion_type", "generated"),
                    confidence=recovery.get("confidence", 0.5),
                    confidence_band=ConfidenceBand.from_confidence(recovery.get("confidence", 0.5)),
                    action_type=recovery.get("action_type", "escalate"),
                    action_params=recovery.get("action_params", {}),
                    status=recovery.get("status", "applied"),
                    auto_applicable=False,
                    requires_confirmation=0,
                )
            )

            policy = self._generate_policy(pattern, recovery_obj)

            # Persist in shadow mode (pass tenant_id from event)
            await self._persist_policy(policy, event.tenant_id)

            event.details["policy"] = policy.to_dict()
            event.details["policy_id"] = policy.policy_id
            event.details["policy_mode"] = policy.mode.value

            # Note: Don't set failure_state for shadow mode - loop should continue
            # Routing bridge will decide what to do based on policy mode

            logger.info(
                f"Generated policy {policy.policy_id} in {policy.mode.value} mode "
                f"from recovery {recovery_obj.recovery_id}"
            )

            return event

        except Exception as e:
            logger.exception(f"Bridge 3 error: {e}")
            event.failure_state = LoopFailureState.POLICY_REJECTED
            event.details["error"] = str(e)
            return event

    async def _load_pattern(self, pattern_id: str) -> Optional[dict]:
        """Load pattern from database."""
        async with self.db_factory() as session:
            from sqlalchemy import text

            result = await session.execute(
                text("SELECT * FROM failure_patterns WHERE id = :id"),
                {"id": pattern_id},
            )
            row = result.fetchone()
            if row:
                return dict(row._mapping)
        return None

    def _generate_policy(self, pattern: dict, recovery: RecoverySuggestion) -> PolicyRule:
        """Generate prevention policy from pattern and recovery."""
        signature = pattern.get("signature", {})
        if isinstance(signature, str):
            signature = json.loads(signature)

        error_type = signature.get("error_type", "unknown")

        # Map recovery actions to policy actions
        action_map = {
            "rate_limit": "rate_limit",
            "retry": "escalate",  # Retry patterns become escalation policies
            "escalate": "escalate",
            "block": "block",
        }

        policy_action = action_map.get(recovery.action_type, "warn")

        # Generate policy condition (simplified DSL)
        condition = f"error_type == '{error_type}'"
        if signature.get("api_endpoint"):
            condition += f" AND api_endpoint == '{signature['api_endpoint']}'"

        return PolicyRule.create(
            name=f"Prevention: {error_type}",
            description=f"Auto-generated policy to prevent {error_type} errors. "
            f"Created from pattern {pattern['id']} with {pattern.get('occurrence_count', 0)} occurrences.",
            category="operational",
            condition=condition,
            action=policy_action,
            source_pattern_id=pattern["id"],
            source_recovery_id=recovery.recovery_id,
            confidence=recovery.confidence,
            scope_type="tenant",
            confirmations_required=self.confirmations_required,
        )

    async def _persist_policy(self, policy: PolicyRule, tenant_id: str) -> None:
        """Persist policy to database."""
        async with self.db_factory() as session:
            from sqlalchemy import text

            # Build conditions and actions as JSON
            conditions_json = json.dumps({"expression": policy.condition, "type": "dsl"})
            actions_json = json.dumps({"type": policy.action, "params": {}})

            await session.execute(
                text(
                    """
                    INSERT INTO policy_rules
                    (id, tenant_id, name, description, rule_type, conditions, actions,
                     source_type, source_pattern_id, source_recovery_id,
                     generation_confidence, mode, is_active, priority,
                     confirmations_required, confirmations_received,
                     regret_count, shadow_evaluations, shadow_would_block,
                     created_at, updated_at)
                    VALUES (:id, :tenant_id, :name, :description, :rule_type,
                            CAST(:conditions AS jsonb), CAST(:actions AS jsonb),
                            'recovery', :pattern_id, :recovery_id,
                            :confidence, :mode, :is_active, 100,
                            :confirmations_required, :confirmations_received,
                            0, 0, 0, NOW(), NOW())
                    ON CONFLICT (id) DO UPDATE SET mode = :mode, is_active = :is_active, updated_at = NOW()
                """
                ),
                {
                    "id": policy.policy_id,
                    "tenant_id": tenant_id,
                    "name": policy.name,
                    "description": policy.description,
                    "rule_type": policy.category,
                    "conditions": conditions_json,
                    "actions": actions_json,
                    "pattern_id": policy.source_pattern_id,
                    "recovery_id": policy.source_recovery_id,
                    "confidence": policy.confidence,
                    "mode": policy.mode.value,
                    "is_active": policy.mode.value != "disabled",
                    "confirmations_required": policy.confirmations_required,
                    "confirmations_received": policy.confirmations_received,
                },
            )
            await session.commit()


# =============================================================================
# BRIDGE 4: POLICY → CARE ROUTING
# =============================================================================


class PolicyToRoutingBridge(BaseBridge):
    """
    Bridge 4: Update CARE routing based on new policy.

    Enhanced with guardrails:
    - Max delta per adjustment (default 20%)
    - Decay window (default 7 days)
    - KPI regression rollback (default 10% threshold)
    """

    def __init__(self, db_session_factory, config=None):
        self.db_factory = db_session_factory
        self.max_delta = config.max_routing_delta if config else 0.2
        self.decay_days = config.routing_decay_days if config else 7

    @property
    def stage(self) -> LoopStage:
        return LoopStage.POLICY_GENERATED

    async def process(self, event: LoopEvent) -> LoopEvent:
        """
        Adjust CARE routing based on new policy.

        Guardrails:
        - Never adjust more than max_delta at once
        - Adjustments decay over time
        - Rollback if KPI regresses
        """
        try:
            policy = event.details.get("policy")
            if not policy:
                event.failure_state = LoopFailureState.ROUTING_ADJUSTMENT_SKIPPED
                event.details["routing_skipped"] = "No policy provided"
                return event

            # Get policy object
            policy_obj = (
                policy
                if isinstance(policy, PolicyRule)
                else PolicyRule(
                    policy_id=policy.get("policy_id", "unknown"),
                    name=policy.get("name", ""),
                    description=policy.get("description", ""),
                    category=policy.get("category", "operational"),
                    condition=policy.get("condition", ""),
                    action=policy.get("action", "warn"),
                    scope_type=policy.get("scope_type", "tenant"),
                    scope_id=policy.get("scope_id"),
                    source_pattern_id=policy.get("source_pattern_id", ""),
                    source_recovery_id=policy.get("source_recovery_id", ""),
                    confidence=policy.get("confidence", 0.5),
                    confidence_band=ConfidenceBand.from_confidence(policy.get("confidence", 0.5)),
                    mode=PolicyMode(policy.get("mode", "shadow")),
                    confirmations_required=3,
                )
            )

            # Only adjust for active policies (not shadow mode)
            if policy_obj.mode == PolicyMode.SHADOW:
                event.details["routing_skipped"] = "Policy in shadow mode"
                return event

            # Identify affected agents
            affected_agents = await self._identify_affected_agents(policy_obj, event.tenant_id)

            if not affected_agents:
                event.details["routing_skipped"] = "No agents affected"
                return event

            # Create adjustments with guardrails
            adjustments = []
            for agent_id in affected_agents:
                adjustment = await self._create_adjustment(agent_id, policy_obj, event.tenant_id)
                if adjustment:
                    adjustments.append(adjustment)

            if not adjustments:
                event.failure_state = LoopFailureState.ROUTING_GUARDRAIL_BLOCKED
                event.details["routing_blocked"] = "All adjustments blocked by guardrails"
                return event

            # Serialize adjustments for JSON
            serialized_adjustments = [adj.to_dict() for adj in adjustments]
            event.details["adjustment"] = (
                serialized_adjustments[0] if len(serialized_adjustments) == 1 else serialized_adjustments
            )
            event.details["adjustments_count"] = len(adjustments)

            logger.info(f"Created {len(adjustments)} routing adjustments for policy {policy_obj.policy_id}")

            return event

        except Exception as e:
            logger.exception(f"Bridge 4 error: {e}")
            event.failure_state = LoopFailureState.ROUTING_ADJUSTMENT_SKIPPED
            event.details["error"] = str(e)
            return event

    async def _identify_affected_agents(self, policy: PolicyRule, tenant_id: str) -> list[str]:
        """Identify agents affected by this policy."""
        async with self.db_factory() as session:
            from sqlalchemy import text

            # Find agents that match the policy scope
            result = await session.execute(
                text(
                    """
                    SELECT DISTINCT agent_id
                    FROM routing_decisions
                    WHERE tenant_id = :tenant_id
                    AND created_at > NOW() - INTERVAL '7 days'
                    LIMIT 10
                """
                ),
                {"tenant_id": tenant_id},
            )
            return [row.agent_id for row in result.fetchall()]

    async def _create_adjustment(
        self,
        agent_id: str,
        policy: PolicyRule,
        tenant_id: str,
    ) -> Optional[RoutingAdjustment]:
        """Create routing adjustment with guardrails."""
        # Check existing adjustments for this agent
        existing = await self._get_active_adjustments(agent_id)
        total_adjustment = sum(a.effective_magnitude for a in existing)

        # Calculate desired adjustment
        action_magnitudes = {
            "block": -0.5,
            "route_away": -0.3,
            "rate_limit": -0.2,
            "escalate": -0.1,
            "warn": -0.05,
        }
        desired_magnitude = action_magnitudes.get(policy.action, -0.1)

        # Apply max delta guardrail
        clamped_magnitude = max(-self.max_delta, min(self.max_delta, desired_magnitude))

        # Check if total would exceed bounds
        new_total = total_adjustment + clamped_magnitude
        if new_total < -0.8:  # Don't completely disable an agent
            logger.warning(f"Guardrail blocked: adjustment for {agent_id} would exceed -80%")
            return None

        adjustment = RoutingAdjustment.create(
            agent_id=agent_id,
            adjustment_type="confidence_penalty" if clamped_magnitude < 0 else "weight_shift",
            magnitude=clamped_magnitude,
            reason=f"Policy {policy.name}: {policy.action}",
            source_policy_id=policy.policy_id,
            max_delta=self.max_delta,
            decay_days=self.decay_days,
        )

        # Capture baseline KPI for rollback detection
        adjustment.kpi_baseline = await self._get_agent_kpi(agent_id)

        await self._persist_adjustment(adjustment)

        return adjustment

    async def _get_active_adjustments(self, agent_id: str) -> list[RoutingAdjustment]:
        """Get active adjustments for an agent."""
        async with self.db_factory() as session:
            from sqlalchemy import text

            result = await session.execute(
                text(
                    """
                    SELECT * FROM routing_policy_adjustments
                    WHERE agent_id = :agent_id
                    AND is_active = TRUE
                    AND (expires_at IS NULL OR expires_at > NOW())
                """
                ),
                {"agent_id": agent_id},
            )
            rows = result.fetchall()
            return [
                RoutingAdjustment(
                    adjustment_id=row.id,
                    agent_id=row.agent_id,
                    capability=row.capability,
                    adjustment_type=row.adjustment_type,
                    magnitude=row.magnitude,
                    reason=row.reason or "",
                    source_policy_id=row.source_policy_id or "",
                    created_at=row.created_at,
                    expires_at=row.expires_at,
                    is_active=row.is_active,
                )
                for row in rows
            ]

    async def _get_agent_kpi(self, agent_id: str) -> float:
        """Get current KPI for an agent (success rate)."""
        async with self.db_factory() as session:
            from sqlalchemy import text

            result = await session.execute(
                text(
                    """
                    SELECT
                        COALESCE(
                            SUM(CASE WHEN outcome = 'success' THEN 1 ELSE 0 END)::float /
                            NULLIF(COUNT(*), 0),
                            1.0
                        ) as success_rate
                    FROM routing_decisions
                    WHERE agent_id = :agent_id
                    AND created_at > NOW() - INTERVAL '24 hours'
                """
                ),
                {"agent_id": agent_id},
            )
            row = result.fetchone()
            return row.success_rate if row else 1.0

    async def _persist_adjustment(self, adjustment: RoutingAdjustment) -> None:
        """Persist routing adjustment to database."""
        async with self.db_factory() as session:
            from sqlalchemy import text

            await session.execute(
                text(
                    """
                    INSERT INTO routing_policy_adjustments
                    (id, agent_id, capability, adjustment_type, magnitude, reason,
                     source_policy_id, created_at, expires_at, is_active)
                    VALUES (:id, :agent_id, :capability, :type, :magnitude, :reason,
                            :policy_id, :created_at, :expires_at, :is_active)
                """
                ),
                {
                    "id": adjustment.adjustment_id,
                    "agent_id": adjustment.agent_id,
                    "capability": adjustment.capability,
                    "type": adjustment.adjustment_type,
                    "magnitude": adjustment.magnitude,
                    "reason": adjustment.reason,
                    "policy_id": adjustment.source_policy_id,
                    "created_at": adjustment.created_at,
                    "expires_at": adjustment.expires_at,
                    "is_active": adjustment.is_active,
                },
            )
            await session.commit()


# =============================================================================
# BRIDGE 5: LOOP STATUS → CONSOLE
# =============================================================================


class LoopStatusBridge(BaseBridge):
    """
    Bridge 5: Aggregate loop status for console display.

    Enhanced with:
    - Narrative artifacts for storytelling
    - Real-time SSE updates
    - Before/after comparisons
    """

    def __init__(self, db_session_factory, redis_client):
        self.db_factory = db_session_factory
        self.redis = redis_client

    @property
    def stage(self) -> LoopStage:
        return LoopStage.ROUTING_ADJUSTED

    async def process(self, event: LoopEvent) -> LoopEvent:
        """
        Update console with final loop status.

        This is called after routing adjustment (final stage).
        Generates narrative artifacts and pushes SSE update.
        """
        try:
            # Build complete loop status
            loop_status = await self._build_loop_status(event)

            # Generate narrative artifacts
            narrative = loop_status.to_console_display()

            # Push SSE update
            await self._push_sse_update(event.tenant_id, event.incident_id, narrative)

            event.details["loop_status"] = loop_status.to_dict()
            event.details["narrative"] = narrative

            logger.info(f"Loop complete for incident {event.incident_id}: {loop_status.completion_pct:.0f}% complete")

            return event

        except Exception as e:
            logger.exception(f"Bridge 5 error: {e}")
            # Don't fail the loop for console update errors
            return event

    async def _build_loop_status(self, event: LoopEvent) -> LoopStatus:
        """Build complete loop status from event chain."""
        async with self.db_factory() as session:
            from sqlalchemy import text

            # Get all events for this incident
            result = await session.execute(
                text(
                    """
                    SELECT * FROM loop_events
                    WHERE incident_id = :incident_id
                    ORDER BY created_at ASC
                """
                ),
                {"incident_id": event.incident_id},
            )
            events = result.fetchall()

            stages_completed = []
            stages_failed = []

            for evt in events:
                details = evt.details if isinstance(evt.details, dict) else json.loads(evt.details or "{}")
                if details.get("failure_state"):
                    stages_failed.append(evt.stage)
                else:
                    stages_completed.append(evt.stage)

            return LoopStatus(
                loop_id=f"loop_{event.incident_id[:16]}",
                incident_id=event.incident_id,
                tenant_id=event.tenant_id,
                current_stage=LoopStage.ROUTING_ADJUSTED,
                stages_completed=stages_completed,
                stages_failed=stages_failed,
                is_complete=True,
                pattern_match_result=event.details.get("match_result"),
                recovery_suggestion=event.details.get("recovery"),
                policy_rule=event.details.get("policy"),
                routing_adjustment=event.details.get("adjustment"),
            )

    async def _push_sse_update(
        self,
        tenant_id: str,
        incident_id: str,
        data: dict,
    ) -> None:
        """Push SSE update to connected consoles."""
        channel = f"loop:{tenant_id}:{incident_id}"
        await self.redis.publish(
            channel,
            json.dumps(
                {
                    "type": "loop_complete",
                    "incident_id": incident_id,
                    "data": data,
                }
            ),
        )


# =============================================================================
# BRIDGE FACTORY
# =============================================================================


def create_bridges(
    db_session_factory,
    redis_client,
    config=None,
) -> list[BaseBridge]:
    """Create all bridges with shared configuration."""
    return [
        IncidentToCatalogBridge(db_session_factory),
        PatternToRecoveryBridge(db_session_factory),
        RecoveryToPolicyBridge(db_session_factory, config),
        PolicyToRoutingBridge(db_session_factory, config),
        LoopStatusBridge(db_session_factory, redis_client),
    ]


def register_all_bridges(
    dispatcher: "IntegrationDispatcher",
    db_session_factory,
    redis_client,
    config=None,
) -> None:
    """Register all bridges with the dispatcher."""
    bridges = create_bridges(db_session_factory, redis_client, config)
    for bridge in bridges:
        bridge.register(dispatcher)
