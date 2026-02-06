# Layer: L4 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Replay determinism validation for LLM calls — CANONICAL DEFINITIONS
# Callers: logs_facade.py, evidence services, other domains (read-only)
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Governance: INV-LOGS-003 — Determinism definitions live here exclusively
# Reference: HOC_logs_analysis_v1.md

"""Replay Determinism Service - Defines and Enforces Determinism Semantics

Watchpoint #2: Replay Determinism Across Model Versions

This service addresses the fundamental tension between:
- "Logical Determinism": Same policy decision given same context
- "Byte-for-byte Determinism": Exact same output bytes

Key Insight: As upstream LLM models drift (model updates, temperature changes),
we cannot guarantee byte-for-byte determinism. However, we CAN guarantee:

1. Policy decisions are deterministic (same rules -> same enforcement)
2. Replay validates logical equivalence, not exact match
3. Version tracking allows audit trail of what ran when

Determinism Levels:
- STRICT: Byte-for-byte match required (only for local/cached responses)
- LOGICAL: Policy decision match required (default for LLM calls)
- SEMANTIC: Meaning-equivalent match (for content validation)

Usage:
    from app.houseofcards.customer.logs.engines.replay_determinism import (
        ReplayValidator,
        DeterminismLevel,
        ReplayResult
    )

    validator = ReplayValidator()
    result = validator.validate_replay(
        original_call=original,
        replayed_call=replayed,
        level=DeterminismLevel.LOGICAL
    )
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ============== DETERMINISM LEVELS ==============


class DeterminismLevel(str, Enum):
    """
    Levels of determinism for replay validation.

    STRICT: Byte-for-byte exact match
        - Use for: Cached responses, local transformations
        - Fails if: Any byte differs

    LOGICAL: Policy decision equivalence
        - Use for: LLM calls with policy enforcement
        - Passes if: Same policy triggered, same action taken
        - Fails if: Different policy decision

    SEMANTIC: Meaning-equivalent match
        - Use for: Content validation, safety checks
        - Passes if: Semantic meaning preserved
        - Fails if: Meaning fundamentally changed
    """

    STRICT = "strict"
    LOGICAL = "logical"
    SEMANTIC = "semantic"


# ============== VERSION TRACKING ==============


@dataclass
class ModelVersion:
    """Track the model version used for a call."""

    provider: str  # "openai", "anthropic", etc.
    model_id: str  # "gpt-4o-mini", "claude-sonnet-4-20250514"
    model_version: Optional[str] = None  # Snapshot version if available
    temperature: Optional[float] = None
    seed: Optional[int] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model_id": self.model_id,
            "model_version": self.model_version,
            "temperature": self.temperature,
            "seed": self.seed,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelVersion":
        return cls(
            provider=data.get("provider", "unknown"),
            model_id=data.get("model_id", "unknown"),
            model_version=data.get("model_version"),
            temperature=data.get("temperature"),
            seed=data.get("seed"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(timezone.utc),
        )


@dataclass
class PolicyDecision:
    """Record of a policy enforcement decision."""

    guardrail_id: str
    guardrail_name: str
    passed: bool
    action: Optional[str] = None  # "block", "warn", "throttle", etc.
    reason: Optional[str] = None
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "guardrail_id": self.guardrail_id,
            "guardrail_name": self.guardrail_name,
            "passed": self.passed,
            "action": self.action,
            "reason": self.reason,
            "confidence": self.confidence,
        }


# ============== REPLAY RESULT ==============


class ReplayMatch(str, Enum):
    """Result of replay comparison."""

    EXACT = "exact"  # Byte-for-byte match
    LOGICAL = "logical"  # Policy decisions match
    SEMANTIC = "semantic"  # Meaning equivalent
    MISMATCH = "mismatch"  # Failed to match


@dataclass
class ReplayResult:
    """Result of replay validation."""

    match_level: ReplayMatch
    passed: bool
    level_required: DeterminismLevel
    details: Dict[str, Any] = field(default_factory=dict)

    # Comparison details
    original_model: Optional[ModelVersion] = None
    replay_model: Optional[ModelVersion] = None
    model_drift_detected: bool = False

    # Policy comparison
    original_policies: List[PolicyDecision] = field(default_factory=list)
    replay_policies: List[PolicyDecision] = field(default_factory=list)
    policy_match: bool = True

    # Content comparison
    content_hash_original: Optional[str] = None
    content_hash_replay: Optional[str] = None
    content_match: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "match_level": self.match_level.value,
            "passed": self.passed,
            "level_required": self.level_required.value,
            "details": self.details,
            "original_model": self.original_model.to_dict() if self.original_model else None,
            "replay_model": self.replay_model.to_dict() if self.replay_model else None,
            "model_drift_detected": self.model_drift_detected,
            "policy_match": self.policy_match,
            "content_match": self.content_match,
        }


# ============== CALL RECORD FOR REPLAY ==============


@dataclass
class CallRecord:
    """Record of a call for replay validation."""

    call_id: str
    request_hash: str  # Hash of request for matching
    response_hash: str  # Hash of response for comparison

    # Model info
    model_version: ModelVersion

    # Policy decisions
    policy_decisions: List[PolicyDecision] = field(default_factory=list)

    # Content (for semantic comparison)
    request_content: Optional[str] = None
    response_content: Optional[str] = None

    # Metadata
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: Optional[int] = None
    tokens_used: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "call_id": self.call_id,
            "request_hash": self.request_hash,
            "response_hash": self.response_hash,
            "model_version": self.model_version.to_dict(),
            "policy_decisions": [p.to_dict() for p in self.policy_decisions],
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "tokens_used": self.tokens_used,
        }


# ============== REPLAY VALIDATOR ==============


class ReplayValidator:
    """
    Validates replay determinism at configurable levels.

    The key insight is that LLM outputs will drift over time as models
    are updated. We don't try to fight this - instead we:

    1. Track model versions explicitly
    2. Define determinism in terms of POLICY DECISIONS, not raw output
    3. Provide clear audit trails when drift is detected
    4. Allow operators to choose their determinism level
    """

    def __init__(self):
        self._semantic_cache: Dict[str, str] = {}

    def validate_replay(
        self,
        original: CallRecord,
        replay: CallRecord,
        level: DeterminismLevel = DeterminismLevel.LOGICAL,
    ) -> ReplayResult:
        """
        Validate a replay against the original call.

        Args:
            original: The original call record
            replay: The replayed call record
            level: Required determinism level

        Returns:
            ReplayResult with match status and details
        """
        result = ReplayResult(
            match_level=ReplayMatch.MISMATCH,
            passed=False,
            level_required=level,
            original_model=original.model_version,
            replay_model=replay.model_version,
        )

        # Check model drift
        result.model_drift_detected = self._detect_model_drift(original.model_version, replay.model_version)

        # Compare content hashes
        result.content_hash_original = original.response_hash
        result.content_hash_replay = replay.response_hash
        result.content_match = original.response_hash == replay.response_hash

        # Compare policy decisions
        result.original_policies = original.policy_decisions
        result.replay_policies = replay.policy_decisions
        result.policy_match = self._compare_policies(original.policy_decisions, replay.policy_decisions)

        # Determine match level achieved
        if result.content_match:
            result.match_level = ReplayMatch.EXACT
        elif result.policy_match:
            result.match_level = ReplayMatch.LOGICAL
        elif self._semantic_equivalent(original, replay):
            result.match_level = ReplayMatch.SEMANTIC
        else:
            result.match_level = ReplayMatch.MISMATCH

        # Check if achieved level meets required level
        result.passed = self._level_meets_requirement(result.match_level, level)

        # Add details
        result.details = {
            "content_match": result.content_match,
            "policy_match": result.policy_match,
            "model_drift": result.model_drift_detected,
            "achieved_level": result.match_level.value,
            "required_level": level.value,
        }

        if result.model_drift_detected:
            result.details["model_drift_details"] = {
                "original": f"{original.model_version.model_id}@{original.model_version.model_version}",
                "replay": f"{replay.model_version.model_id}@{replay.model_version.model_version}",
            }

        return result

    def _detect_model_drift(self, original: ModelVersion, replay: ModelVersion) -> bool:
        """Detect if the model has drifted between original and replay."""
        # Different provider = definitely drift
        if original.provider != replay.provider:
            return True

        # Different model ID = definitely drift
        if original.model_id != replay.model_id:
            return True

        # Different version (if available) = drift
        if original.model_version and replay.model_version and original.model_version != replay.model_version:
            return True

        # Different temperature might cause different output
        if (
            original.temperature is not None
            and replay.temperature is not None
            and abs(original.temperature - replay.temperature) > 0.01
        ):
            return True

        return False

    def _compare_policies(self, original: List[PolicyDecision], replay: List[PolicyDecision]) -> bool:
        """Compare policy decisions for logical equivalence."""
        if len(original) != len(replay):
            return False

        # Build lookup by guardrail_id
        original_map = {p.guardrail_id: p for p in original}
        replay_map = {p.guardrail_id: p for p in replay}

        if set(original_map.keys()) != set(replay_map.keys()):
            return False

        for guardrail_id, orig_decision in original_map.items():
            replay_decision = replay_map[guardrail_id]

            # Must have same pass/fail result
            if orig_decision.passed != replay_decision.passed:
                return False

            # If failed, must have same action
            if not orig_decision.passed:
                if orig_decision.action != replay_decision.action:
                    return False

        return True

    def _semantic_equivalent(self, original: CallRecord, replay: CallRecord) -> bool:
        """
        Check if two responses are semantically equivalent.

        Note: This is a simplified implementation. In production,
        you might use embedding similarity or another LLM to judge.
        """
        if not original.response_content or not replay.response_content:
            return False

        # Simple heuristic: similar length and no major structural changes
        len_ratio = len(replay.response_content) / max(len(original.response_content), 1)

        # Allow 20% length variation
        if len_ratio < 0.8 or len_ratio > 1.2:
            return False

        # Check for structural similarity (JSON structure if applicable)
        try:
            orig_json = json.loads(original.response_content)
            replay_json = json.loads(replay.response_content)

            # Same keys = structurally equivalent
            if isinstance(orig_json, dict) and isinstance(replay_json, dict):
                return set(orig_json.keys()) == set(replay_json.keys())

        except (json.JSONDecodeError, TypeError):
            pass

        # Default to False for safety
        return False

    def _level_meets_requirement(self, achieved: ReplayMatch, required: DeterminismLevel) -> bool:
        """Check if achieved match level meets the required determinism level."""
        # Level hierarchy: EXACT > LOGICAL > SEMANTIC
        level_order = {
            ReplayMatch.EXACT: 3,
            ReplayMatch.LOGICAL: 2,
            ReplayMatch.SEMANTIC: 1,
            ReplayMatch.MISMATCH: 0,
        }

        required_order = {
            DeterminismLevel.STRICT: 3,  # Requires EXACT
            DeterminismLevel.LOGICAL: 2,  # Requires LOGICAL or EXACT
            DeterminismLevel.SEMANTIC: 1,  # Requires SEMANTIC or better
        }

        return level_order[achieved] >= required_order[required]

    def hash_content(self, content: str) -> str:
        """Create a deterministic hash of content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


# ============== REPLAY CONTEXT BUILDER ==============


class ReplayContextBuilder:
    """
    Builds replay context from API calls.

    Used to capture all information needed for replay validation:
    - Request details
    - Response details
    - Model version
    - Policy decisions
    """

    def __init__(self):
        self._validator = ReplayValidator()

    def build_call_record(
        self,
        call_id: str,
        request: Dict[str, Any],
        response: Dict[str, Any],
        model_info: Dict[str, Any],
        policy_decisions: List[Dict[str, Any]],
        duration_ms: Optional[int] = None,
    ) -> CallRecord:
        """Build a CallRecord from raw API data."""
        # Hash request (deterministic)
        request_str = json.dumps(request, sort_keys=True)
        request_hash = self._validator.hash_content(request_str)

        # Hash response
        response_str = json.dumps(response, sort_keys=True)
        response_hash = self._validator.hash_content(response_str)

        # Parse model version
        model_version = ModelVersion(
            provider=model_info.get("provider", "unknown"),
            model_id=model_info.get("model", "unknown"),
            model_version=model_info.get("version"),
            temperature=model_info.get("temperature"),
            seed=model_info.get("seed"),
        )

        # Parse policy decisions
        decisions = [
            PolicyDecision(
                guardrail_id=pd.get("guardrail_id", "unknown"),
                guardrail_name=pd.get("guardrail_name", "unknown"),
                passed=pd.get("passed", True),
                action=pd.get("action"),
                reason=pd.get("reason"),
                confidence=pd.get("confidence", 1.0),
            )
            for pd in policy_decisions
        ]

        # Extract content for semantic comparison
        response_content = None
        if "choices" in response and response["choices"]:
            choice = response["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                response_content = choice["message"]["content"]

        return CallRecord(
            call_id=call_id,
            request_hash=request_hash,
            response_hash=response_hash,
            model_version=model_version,
            policy_decisions=decisions,
            request_content=request_str,
            response_content=response_content,
            duration_ms=duration_ms,
            tokens_used=response.get("usage", {}).get("total_tokens"),
        )


# ============== EXPORTS ==============

__all__ = [
    "DeterminismLevel",
    "ModelVersion",
    "PolicyDecision",
    "ReplayMatch",
    "ReplayResult",
    "CallRecord",
    "ReplayValidator",
    "ReplayContextBuilder",
]
