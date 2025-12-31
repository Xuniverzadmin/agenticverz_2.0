# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Role: SBA agent evolution logic
# Callers: API routes, workers
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: M18 SBA

# M18 SBA Evolution Engine
# Self-improving agents with drift detection and boundary awareness
#
# Features:
# - Boundary violation tracking
# - Drift detection (data, domain, behavior, boundary)
# - Strategy adjustment
# - Self-updating capabilities

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger("nova.agents.sba.evolution")


# =============================================================================
# Configuration
# =============================================================================

# Drift detection thresholds
SUCCESS_RATE_DRIFT_THRESHOLD = 0.20  # 20% drop triggers drift signal
LATENCY_DRIFT_THRESHOLD = 0.50  # 50% increase triggers drift signal
VIOLATION_SPIKE_THRESHOLD = 3  # 3 violations in window triggers drift
DRIFT_WINDOW = 3600  # 1 hour window for drift detection

# Strategy adjustment thresholds
STRATEGY_ADJUSTMENT_SUCCESS_THRESHOLD = 0.60  # Below this triggers adjustment
STRATEGY_ADJUSTMENT_COOLDOWN = 1800  # 30 min between adjustments


# =============================================================================
# Enums
# =============================================================================


class DriftType(str, Enum):
    """Types of drift that can be detected."""

    DATA_DRIFT = "data_drift"  # Input distribution changed
    DOMAIN_DRIFT = "domain_drift"  # Task domain shifted
    BEHAVIOR_DRIFT = "behavior_drift"  # Agent outputs changed
    BOUNDARY_DRIFT = "boundary_drift"  # Boundaries too tight/loose


class ViolationType(str, Enum):
    """Types of boundary violations."""

    DOMAIN = "domain"  # Task outside domain
    TOOL = "tool"  # Used disallowed tool
    CONTEXT = "context"  # Wrong execution context
    RISK = "risk"  # Risk policy violation
    CAPABILITY = "capability"  # Used unavailable capability


class AdjustmentType(str, Enum):
    """Types of strategy adjustments."""

    TASK_SPLIT = "task_split"  # Split complex tasks
    STEP_REFINEMENT = "step_refinement"  # Refine execution steps
    FALLBACK_ADD = "fallback_add"  # Add fallback strategies
    BOUNDARY_EXPAND = "boundary_expand"  # Expand boundaries
    BOUNDARY_CONTRACT = "boundary_contract"  # Tighten boundaries


# =============================================================================
# Models
# =============================================================================


class BoundaryViolation(BaseModel):
    """Record of a boundary violation."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    agent_id: str
    violation_type: ViolationType
    description: str
    task_description: Optional[str] = None
    task_domain: Optional[str] = None
    severity: float = Field(default=0.5, ge=0.0, le=1.0)
    auto_reported: bool = False  # Agent self-reported vs system detected
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "violation_type": self.violation_type.value,
            "description": self.description,
            "task_description": self.task_description,
            "task_domain": self.task_domain,
            "severity": self.severity,
            "auto_reported": self.auto_reported,
            "detected_at": self.detected_at.isoformat(),
        }


class DriftSignal(BaseModel):
    """Signal indicating detected drift."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    agent_id: str
    drift_type: DriftType
    severity: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    recommendation: Optional[str] = None
    acknowledged: bool = False
    auto_adjusted: bool = False
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "drift_type": self.drift_type.value,
            "severity": self.severity,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
            "acknowledged": self.acknowledged,
            "auto_adjusted": self.auto_adjusted,
            "detected_at": self.detected_at.isoformat(),
        }


class StrategyAdjustment(BaseModel):
    """Record of a strategy adjustment."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    agent_id: str
    trigger: str  # What triggered the adjustment
    adjustment_type: AdjustmentType
    old_strategy: Dict[str, Any]
    new_strategy: Dict[str, Any]
    success_rate_before: Optional[float] = None
    success_rate_after: Optional[float] = None
    adjusted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "trigger": self.trigger,
            "adjustment_type": self.adjustment_type.value,
            "old_strategy": self.old_strategy,
            "new_strategy": self.new_strategy,
            "success_rate_before": self.success_rate_before,
            "success_rate_after": self.success_rate_after,
            "adjusted_at": self.adjusted_at.isoformat(),
        }


# =============================================================================
# Evolution Engine
# =============================================================================


class SBAEvolutionEngine:
    """
    SBA Evolution Engine for self-improving agents.

    Responsibilities:
    - Track boundary violations
    - Detect drift (data, domain, behavior, boundary)
    - Recommend and apply strategy adjustments
    - Update agent capabilities based on probes
    """

    def __init__(self, database_url: Optional[str] = None):
        self._db_url = database_url if database_url is not None else os.environ.get("DATABASE_URL")
        # In-memory stores (will be persisted to DB when available)
        self._violations: Dict[str, List[BoundaryViolation]] = {}
        self._drift_signals: Dict[str, List[DriftSignal]] = {}
        self._adjustments: Dict[str, List[StrategyAdjustment]] = {}
        self._last_adjustment: Dict[str, datetime] = {}

    # =========================================================================
    # Boundary Violations
    # =========================================================================

    def record_violation(
        self,
        agent_id: str,
        violation_type: ViolationType,
        description: str,
        task_description: Optional[str] = None,
        task_domain: Optional[str] = None,
        severity: float = 0.5,
        auto_reported: bool = False,
    ) -> BoundaryViolation:
        """
        Record a boundary violation.

        Args:
            agent_id: Agent that violated
            violation_type: Type of violation
            description: Human-readable description
            task_description: Task that caused violation
            task_domain: Domain of the task
            severity: 0.0-1.0 severity
            auto_reported: Whether agent self-reported

        Returns:
            The recorded violation
        """
        violation = BoundaryViolation(
            agent_id=agent_id,
            violation_type=violation_type,
            description=description,
            task_description=task_description,
            task_domain=task_domain,
            severity=severity,
            auto_reported=auto_reported,
        )

        if agent_id not in self._violations:
            self._violations[agent_id] = []
        self._violations[agent_id].append(violation)

        # Persist to database
        self._persist_violation(violation)

        logger.warning(
            "boundary_violation_recorded",
            extra={
                "agent_id": agent_id,
                "violation_type": violation_type.value,
                "severity": severity,
                "auto_reported": auto_reported,
            },
        )

        # Check if this triggers drift
        self._check_boundary_drift(agent_id)

        return violation

    def get_violations(
        self,
        agent_id: str,
        since: Optional[datetime] = None,
        violation_type: Optional[ViolationType] = None,
    ) -> List[BoundaryViolation]:
        """Get violations for an agent."""
        violations = self._violations.get(agent_id, [])

        if since:
            violations = [v for v in violations if v.detected_at >= since]

        if violation_type:
            violations = [v for v in violations if v.violation_type == violation_type]

        return violations

    def _persist_violation(self, violation: BoundaryViolation) -> bool:
        """Persist violation to database."""
        if not self._db_url:
            return False

        try:
            engine = create_engine(self._db_url)
            with engine.connect() as conn:
                conn.execute(
                    text(
                        """
                        INSERT INTO agents.boundary_violations (
                            id, agent_id, violation_type, description,
                            task_description, task_domain, severity,
                            auto_reported, detected_at
                        ) VALUES (
                            CAST(:id AS UUID), :agent_id, :violation_type, :description,
                            :task_description, :task_domain, :severity,
                            :auto_reported, :detected_at
                        )
                        ON CONFLICT (id) DO NOTHING
                    """
                    ),
                    {
                        "id": violation.id,
                        "agent_id": violation.agent_id,
                        "violation_type": violation.violation_type.value,
                        "description": violation.description,
                        "task_description": violation.task_description,
                        "task_domain": violation.task_domain,
                        "severity": violation.severity,
                        "auto_reported": violation.auto_reported,
                        "detected_at": violation.detected_at,
                    },
                )
                conn.commit()
            engine.dispose()
            return True
        except SQLAlchemyError as e:
            logger.debug(f"Failed to persist violation: {e}")
            return False

    # =========================================================================
    # Drift Detection
    # =========================================================================

    def detect_drift(
        self,
        agent_id: str,
        current_success_rate: float,
        historical_success_rate: float,
        current_latency: float,
        historical_latency: float,
        recent_violations: int = 0,
    ) -> List[DriftSignal]:
        """
        Detect drift based on performance metrics.

        Args:
            agent_id: Agent to check
            current_success_rate: Recent success rate
            historical_success_rate: Historical baseline
            current_latency: Recent average latency
            historical_latency: Historical baseline
            recent_violations: Violations in recent window

        Returns:
            List of detected drift signals
        """
        signals = []

        # Success rate degradation (behavior drift)
        success_drop = historical_success_rate - current_success_rate
        if success_drop >= SUCCESS_RATE_DRIFT_THRESHOLD:
            signal = DriftSignal(
                agent_id=agent_id,
                drift_type=DriftType.BEHAVIOR_DRIFT,
                severity=min(1.0, success_drop / 0.5),  # Severity scales with drop
                evidence={
                    "current_success_rate": current_success_rate,
                    "historical_success_rate": historical_success_rate,
                    "drop": success_drop,
                },
                recommendation="Consider adjusting How-to-Win strategy or expanding boundaries",
            )
            signals.append(signal)
            self._record_drift_signal(signal)

        # Latency increase (data or domain drift)
        if historical_latency > 0:
            latency_increase = (current_latency - historical_latency) / historical_latency
            if latency_increase >= LATENCY_DRIFT_THRESHOLD:
                signal = DriftSignal(
                    agent_id=agent_id,
                    drift_type=DriftType.DATA_DRIFT,
                    severity=min(1.0, latency_increase),
                    evidence={
                        "current_latency": current_latency,
                        "historical_latency": historical_latency,
                        "increase_pct": latency_increase,
                    },
                    recommendation="Check for data distribution changes or dependency issues",
                )
                signals.append(signal)
                self._record_drift_signal(signal)

        # Violation spike (boundary drift)
        if recent_violations >= VIOLATION_SPIKE_THRESHOLD:
            signal = DriftSignal(
                agent_id=agent_id,
                drift_type=DriftType.BOUNDARY_DRIFT,
                severity=min(1.0, recent_violations / 10),
                evidence={
                    "recent_violations": recent_violations,
                    "threshold": VIOLATION_SPIKE_THRESHOLD,
                },
                recommendation="Boundaries may be too tight - consider expanding Where-to-Play",
            )
            signals.append(signal)
            self._record_drift_signal(signal)

        return signals

    def _check_boundary_drift(self, agent_id: str) -> Optional[DriftSignal]:
        """Check if recent violations indicate boundary drift."""
        window_start = datetime.now(timezone.utc) - timedelta(seconds=DRIFT_WINDOW)
        recent = self.get_violations(agent_id, since=window_start)

        if len(recent) >= VIOLATION_SPIKE_THRESHOLD:
            signal = DriftSignal(
                agent_id=agent_id,
                drift_type=DriftType.BOUNDARY_DRIFT,
                severity=min(1.0, len(recent) / 10),
                evidence={
                    "recent_violations": len(recent),
                    "window_seconds": DRIFT_WINDOW,
                    "violation_types": list(set(v.violation_type.value for v in recent)),
                },
                recommendation="High violation rate - boundaries may need adjustment",
            )
            self._record_drift_signal(signal)
            return signal

        return None

    def _record_drift_signal(self, signal: DriftSignal) -> None:
        """Record a drift signal."""
        if signal.agent_id not in self._drift_signals:
            self._drift_signals[signal.agent_id] = []
        self._drift_signals[signal.agent_id].append(signal)

        # Persist to database
        self._persist_drift_signal(signal)

        logger.warning(
            "drift_signal_detected",
            extra={
                "agent_id": signal.agent_id,
                "drift_type": signal.drift_type.value,
                "severity": signal.severity,
            },
        )

    def get_drift_signals(
        self,
        agent_id: str,
        unacknowledged_only: bool = False,
    ) -> List[DriftSignal]:
        """Get drift signals for an agent."""
        signals = self._drift_signals.get(agent_id, [])

        if unacknowledged_only:
            signals = [s for s in signals if not s.acknowledged]

        return signals

    def acknowledge_drift(self, signal_id: str) -> bool:
        """Acknowledge a drift signal."""
        for agent_signals in self._drift_signals.values():
            for signal in agent_signals:
                if signal.id == signal_id:
                    signal.acknowledged = True
                    return True
        return False

    def _persist_drift_signal(self, signal: DriftSignal) -> bool:
        """Persist drift signal to database."""
        if not self._db_url:
            return False

        try:
            engine = create_engine(self._db_url)
            with engine.connect() as conn:
                conn.execute(
                    text(
                        """
                        INSERT INTO agents.drift_signals (
                            id, agent_id, drift_type, severity, evidence,
                            recommendation, acknowledged, auto_adjusted, detected_at
                        ) VALUES (
                            CAST(:id AS UUID), :agent_id, :drift_type, :severity,
                            CAST(:evidence AS JSONB), :recommendation,
                            :acknowledged, :auto_adjusted, :detected_at
                        )
                        ON CONFLICT (id) DO NOTHING
                    """
                    ),
                    {
                        "id": signal.id,
                        "agent_id": signal.agent_id,
                        "drift_type": signal.drift_type.value,
                        "severity": signal.severity,
                        "evidence": json.dumps(signal.evidence),
                        "recommendation": signal.recommendation,
                        "acknowledged": signal.acknowledged,
                        "auto_adjusted": signal.auto_adjusted,
                        "detected_at": signal.detected_at,
                    },
                )
                conn.commit()
            engine.dispose()
            return True
        except SQLAlchemyError as e:
            logger.debug(f"Failed to persist drift signal: {e}")
            return False

    # =========================================================================
    # Strategy Adjustment
    # =========================================================================

    def suggest_adjustment(
        self,
        agent_id: str,
        drift_signal: DriftSignal,
        current_sba: Dict[str, Any],
    ) -> Optional[StrategyAdjustment]:
        """
        Suggest a strategy adjustment based on drift signal.

        Args:
            agent_id: Agent to adjust
            drift_signal: The drift that triggered this
            current_sba: Current SBA schema

        Returns:
            Suggested adjustment or None
        """
        # Check cooldown
        last = self._last_adjustment.get(agent_id)
        if last:
            cooldown_end = last + timedelta(seconds=STRATEGY_ADJUSTMENT_COOLDOWN)
            if datetime.now(timezone.utc) < cooldown_end:
                logger.info(f"Agent {agent_id} in adjustment cooldown")
                return None

        # Determine adjustment type based on drift
        adjustment_type = None
        new_strategy = current_sba.copy()

        if drift_signal.drift_type == DriftType.BOUNDARY_DRIFT:
            # Expand boundaries
            adjustment_type = AdjustmentType.BOUNDARY_EXPAND
            where_to_play = new_strategy.get("where_to_play", {})

            # Add note about boundary expansion
            boundaries = where_to_play.get("boundaries", "")
            where_to_play["boundaries"] = f"{boundaries} [Auto-expanded due to drift]"
            new_strategy["where_to_play"] = where_to_play

        elif drift_signal.drift_type == DriftType.BEHAVIOR_DRIFT:
            # Refine strategy steps
            adjustment_type = AdjustmentType.STEP_REFINEMENT
            how_to_win = new_strategy.get("how_to_win", {})

            # Add fallback task
            tasks = how_to_win.get("tasks", [])
            if not any("fallback" in t.lower() for t in tasks):
                tasks.append("Fallback: Handle edge cases gracefully")
                how_to_win["tasks"] = tasks
                new_strategy["how_to_win"] = how_to_win

        elif drift_signal.drift_type == DriftType.DATA_DRIFT:
            # Add fallback strategies
            adjustment_type = AdjustmentType.FALLBACK_ADD
            caps = new_strategy.get("capabilities_capacity", {})
            deps = caps.get("dependencies", [])

            # Suggest adding fallback dependencies
            for dep in deps:
                if isinstance(dep, dict) and not dep.get("fallback"):
                    dep["fallback"] = f"{dep.get('name', 'unknown')}_fallback"

            caps["dependencies"] = deps
            new_strategy["capabilities_capacity"] = caps

        if adjustment_type is None:
            return None

        adjustment = StrategyAdjustment(
            agent_id=agent_id,
            trigger=f"{drift_signal.drift_type.value}: {drift_signal.recommendation}",
            adjustment_type=adjustment_type,
            old_strategy=current_sba,
            new_strategy=new_strategy,
            success_rate_before=drift_signal.evidence.get("current_success_rate"),
        )

        return adjustment

    def apply_adjustment(
        self,
        adjustment: StrategyAdjustment,
    ) -> bool:
        """
        Apply a strategy adjustment.

        This updates the agent's SBA in the database.

        Args:
            adjustment: The adjustment to apply

        Returns:
            True if applied successfully
        """
        if adjustment.agent_id not in self._adjustments:
            self._adjustments[adjustment.agent_id] = []
        self._adjustments[adjustment.agent_id].append(adjustment)
        self._last_adjustment[adjustment.agent_id] = datetime.now(timezone.utc)

        # Persist adjustment record
        self._persist_adjustment(adjustment)

        # Update SBA in database
        if self._db_url:
            try:
                engine = create_engine(self._db_url)
                with engine.connect() as conn:
                    conn.execute(
                        text(
                            """
                            UPDATE agents.agent_registry
                            SET sba = CAST(:sba AS JSONB),
                                updated_at = now()
                            WHERE agent_id = :agent_id
                        """
                        ),
                        {
                            "agent_id": adjustment.agent_id,
                            "sba": json.dumps(adjustment.new_strategy),
                        },
                    )
                    conn.commit()
                engine.dispose()

                logger.info(
                    "strategy_adjustment_applied",
                    extra={
                        "agent_id": adjustment.agent_id,
                        "adjustment_type": adjustment.adjustment_type.value,
                    },
                )
                return True

            except SQLAlchemyError as e:
                logger.error(f"Failed to apply adjustment: {e}")
                return False

        return True

    def get_adjustments(
        self,
        agent_id: str,
        limit: int = 10,
    ) -> List[StrategyAdjustment]:
        """Get adjustment history for an agent."""
        adjustments = self._adjustments.get(agent_id, [])
        return adjustments[-limit:] if limit > 0 else adjustments

    def _persist_adjustment(self, adjustment: StrategyAdjustment) -> bool:
        """Persist adjustment to database."""
        if not self._db_url:
            return False

        try:
            engine = create_engine(self._db_url)
            with engine.connect() as conn:
                conn.execute(
                    text(
                        """
                        INSERT INTO agents.strategy_adjustments (
                            id, agent_id, trigger, adjustment_type,
                            old_strategy, new_strategy,
                            success_rate_before, adjusted_at
                        ) VALUES (
                            CAST(:id AS UUID), :agent_id, :trigger, :adjustment_type,
                            CAST(:old_strategy AS JSONB), CAST(:new_strategy AS JSONB),
                            :success_rate_before, :adjusted_at
                        )
                        ON CONFLICT (id) DO NOTHING
                    """
                    ),
                    {
                        "id": adjustment.id,
                        "agent_id": adjustment.agent_id,
                        "trigger": adjustment.trigger,
                        "adjustment_type": adjustment.adjustment_type.value,
                        "old_strategy": json.dumps(adjustment.old_strategy),
                        "new_strategy": json.dumps(adjustment.new_strategy),
                        "success_rate_before": adjustment.success_rate_before,
                        "adjusted_at": adjustment.adjusted_at,
                    },
                )
                conn.commit()
            engine.dispose()
            return True
        except SQLAlchemyError as e:
            logger.debug(f"Failed to persist adjustment: {e}")
            return False


# =============================================================================
# Singleton
# =============================================================================

_evolution_engine: Optional[SBAEvolutionEngine] = None


def get_evolution_engine() -> SBAEvolutionEngine:
    """Get singleton evolution engine."""
    global _evolution_engine
    if _evolution_engine is None:
        _evolution_engine = SBAEvolutionEngine()
    return _evolution_engine
