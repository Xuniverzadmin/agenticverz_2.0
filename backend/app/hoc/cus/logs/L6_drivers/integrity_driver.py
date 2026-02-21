# capability_id: CAP-001
# Layer: L6 — Domain Driver
# NOTE: Renamed integrity.py → integrity_driver.py (2026-01-31)
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: worker (via L5 engine)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: Evidence tables
#   Writes: none
# Database:
#   Scope: domain (logs)
#   Models: evidence
# Role: Integrity computation with separated concerns
# Callers: runner.py (at terminal), evidence.capture
# Allowed Imports: L6, L7 (models)
# Reference: PIN-470, Evidence Architecture v1.1

"""
Integrity Computation Module (v1.1)

Separated concerns for integrity evidence:
- IntegrityAssembler: Gathers facts from evidence tables
- IntegrityEvaluator: Applies policy to compute state/grade
- IntegritySerializer: Persists integrity evidence

Design rationale (Category C2 fix):
    compute_integrity() was becoming a god function.
    Split responsibilities enable:
    - Policy-driven integrity (enterprise tiers)
    - Explainable integrity decisions
    - Testable components

State Model (Category B2 fix):
    Execution Status: SUCCEEDED | FAILED | ABORTED (run outcome)
    Integrity State:  PENDING | SEALED (evidence completeness)
    Integrity Grade:  PASS | WARN | FAIL (quality judgment)

    These are distinct axes - do not collapse them.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

import os

logger = logging.getLogger("nova.evidence.integrity")

DATABASE_URL = os.environ.get("DATABASE_URL")


# =============================================================================
# Integrity State Model (Category B2)
# =============================================================================


class IntegrityState(str, Enum):
    """
    Evidence completeness state.

    This is about WHETHER we have evidence, not quality.
    """
    PENDING = "PENDING"      # Evidence collection in progress
    SEALED = "SEALED"        # Evidence collection complete (terminal)


class IntegrityGrade(str, Enum):
    """
    Quality judgment on the evidence.

    This is about HOW GOOD the evidence is.
    """
    PASS = "PASS"    # All expected evidence present, no failures
    WARN = "WARN"    # Some evidence missing or capture failures
    FAIL = "FAIL"    # Critical evidence missing, cannot trust execution


# =============================================================================
# Evidence Class Taxonomy (Category B1)
# =============================================================================


class EvidenceClass(str, Enum):
    """
    Taxonomy of evidence classes.

    Activity Evidence (B) Scope Rule:
        Activity evidence is required only for externally consequential actions
        (e.g., LLM calls, tool invocations), not pure transforms.

        - llm_invoke: REQUIRES activity evidence (decision-bearing)
        - http_call: REQUIRES activity evidence (external effect)
        - json_transform: NO activity evidence (pure transform)
        - postgres_query: OPTIONAL (depends on mutation)
    """
    B_ACTIVITY = "activity_evidence"
    D_DECISION = "policy_decisions"
    G_PROVIDER = "provider_evidence"
    H_ENVIRONMENT = "environment_evidence"
    J_INTEGRITY = "integrity_evidence"

    # Trace evidence (operational layer)
    TRACE = "aos_traces"
    TRACE_STEPS = "aos_trace_steps"


# Evidence that MUST be present for a valid run
REQUIRED_EVIDENCE = [
    EvidenceClass.H_ENVIRONMENT,
    EvidenceClass.TRACE,
    EvidenceClass.TRACE_STEPS,
]

# Evidence that SHOULD be present (warn if missing)
EXPECTED_EVIDENCE = [
    EvidenceClass.B_ACTIVITY,
    EvidenceClass.G_PROVIDER,
    EvidenceClass.D_DECISION,
]


# =============================================================================
# Capture Failure Semantics (Category C3)
# =============================================================================


class FailureResolution(str, Enum):
    """
    Resolution semantics for capture failures.

    Formalizes how to interpret a capture failure for integrity grading.
    """
    TRANSIENT = "transient"      # Temporary failure, may recover (network blip)
    PERMANENT = "permanent"      # Unrecoverable failure (schema mismatch)
    SUPERSEDED = "superseded"    # Later capture succeeded, ignore this failure


@dataclass
class CaptureFailure:
    """
    Structured representation of an evidence capture failure.
    """
    evidence_class: EvidenceClass
    failure_reason: str
    error_message: Optional[str]
    resolution: FailureResolution = FailureResolution.TRANSIENT

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_type": self.evidence_class.value,
            "failure_reason": self.failure_reason,
            "error_message": self.error_message,
            "resolution": self.resolution.value,
        }


# =============================================================================
# IntegrityAssembler - Gathers Facts
# =============================================================================


@dataclass
class IntegrityFacts:
    """
    Raw facts gathered from evidence tables.

    This is pure data gathering - no policy applied.
    """
    run_id: str
    observed_evidence: List[EvidenceClass] = field(default_factory=list)
    missing_evidence: List[EvidenceClass] = field(default_factory=list)
    capture_failures: List[CaptureFailure] = field(default_factory=list)
    evidence_counts: Dict[str, int] = field(default_factory=dict)
    gathered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def has_required_evidence(self) -> bool:
        """Check if all required evidence is present."""
        return all(e in self.observed_evidence for e in REQUIRED_EVIDENCE)

    @property
    def has_capture_failures(self) -> bool:
        """Check if any capture failures were recorded."""
        return len(self.capture_failures) > 0

    @property
    def unresolved_failures(self) -> List[CaptureFailure]:
        """Get failures that are not superseded."""
        return [f for f in self.capture_failures
                if f.resolution != FailureResolution.SUPERSEDED]


class IntegrityAssembler:
    """
    Gathers facts from evidence tables.

    This class only collects data - it does not apply policy.
    """

    EXPECTED_TABLES = [
        "environment_evidence",
        "activity_evidence",
        "provider_evidence",
        "policy_decisions",
        "aos_traces",
        "aos_trace_steps",
    ]

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or DATABASE_URL

    def gather(self, run_id: str) -> IntegrityFacts:
        """
        Gather integrity facts for a run.

        Args:
            run_id: Run identifier

        Returns:
            IntegrityFacts with observed evidence and failures
        """
        facts = IntegrityFacts(run_id=run_id)

        if not self.database_url:
            logger.warning("No DATABASE_URL configured for integrity assembly")
            return facts

        engine = create_engine(self.database_url)

        try:
            with engine.connect() as conn:
                # Gather evidence counts
                for table in self.EXPECTED_TABLES:
                    count = self._count_evidence(conn, run_id, table)
                    facts.evidence_counts[table] = count

                    evidence_class = self._table_to_class(table)
                    if count > 0:
                        facts.observed_evidence.append(evidence_class)
                    else:
                        facts.missing_evidence.append(evidence_class)

                # Gather capture failures
                facts.capture_failures = self._gather_failures(conn, run_id)

                # Mark superseded failures
                self._resolve_superseded(facts)

        except SQLAlchemyError as e:
            logger.warning(f"integrity_assembly_error: {e}")
        finally:
            engine.dispose()

        return facts

    def _count_evidence(self, conn, run_id: str, table: str) -> int:
        """Count evidence records for a table."""
        try:
            if table == "aos_traces":
                result = conn.execute(
                    text("SELECT COUNT(*) FROM aos_traces WHERE run_id = :run_id"),
                    {"run_id": run_id},
                )
            elif table == "aos_trace_steps":
                result = conn.execute(
                    text("""
                        SELECT COUNT(*) FROM aos_trace_steps ts
                        JOIN aos_traces t ON ts.trace_id = t.trace_id
                        WHERE t.run_id = :run_id
                    """),
                    {"run_id": run_id},
                )
            else:
                result = conn.execute(
                    text(f"SELECT COUNT(*) FROM {table} WHERE run_id = :run_id"),
                    {"run_id": run_id},
                )
            return result.scalar() or 0
        except SQLAlchemyError:
            return 0

    def _gather_failures(self, conn, run_id: str) -> List[CaptureFailure]:
        """Gather capture failures from the failures table."""
        failures = []
        try:
            result = conn.execute(
                text("""
                    SELECT evidence_type, failure_reason, error_message
                    FROM evidence_capture_failures
                    WHERE run_id = :run_id
                """),
                {"run_id": run_id},
            )
            for row in result:
                failures.append(CaptureFailure(
                    evidence_class=self._string_to_class(row[0]),
                    failure_reason=row[1],
                    error_message=row[2],
                    resolution=FailureResolution.TRANSIENT,
                ))
        except SQLAlchemyError:
            pass
        return failures

    def _resolve_superseded(self, facts: IntegrityFacts) -> None:
        """Mark failures as superseded if evidence was later captured."""
        for failure in facts.capture_failures:
            if failure.evidence_class in facts.observed_evidence:
                failure.resolution = FailureResolution.SUPERSEDED

    def _table_to_class(self, table: str) -> EvidenceClass:
        """Map table name to EvidenceClass."""
        mapping = {
            "environment_evidence": EvidenceClass.H_ENVIRONMENT,
            "activity_evidence": EvidenceClass.B_ACTIVITY,
            "provider_evidence": EvidenceClass.G_PROVIDER,
            "policy_decisions": EvidenceClass.D_DECISION,
            "aos_traces": EvidenceClass.TRACE,
            "aos_trace_steps": EvidenceClass.TRACE_STEPS,
        }
        return mapping.get(table, EvidenceClass.B_ACTIVITY)

    def _string_to_class(self, value: str) -> EvidenceClass:
        """Convert string to EvidenceClass."""
        for cls in EvidenceClass:
            if cls.value == value:
                return cls
        return EvidenceClass.B_ACTIVITY


# =============================================================================
# IntegrityEvaluator - Applies Policy
# =============================================================================


@dataclass
class IntegrityEvaluation:
    """
    Result of integrity policy evaluation.
    """
    state: IntegrityState
    grade: IntegrityGrade
    score: float  # 0.0 to 1.0
    missing_reasons: Dict[str, str]
    explanation: str

    # Legacy compatibility
    @property
    def integrity_status(self) -> str:
        """Legacy status for backward compatibility."""
        if self.grade == IntegrityGrade.PASS:
            return "VALID"
        elif self.grade == IntegrityGrade.WARN:
            return "DEGRADED"
        else:
            return "FAILED"


class IntegrityEvaluator:
    """
    Applies policy to integrity facts.

    This class makes quality judgments based on collected facts.
    Policy can be customized for enterprise tiers.
    """

    # Policy thresholds (can be made configurable)
    PASS_THRESHOLD = 0.8
    WARN_THRESHOLD = 0.5

    def evaluate(self, facts: IntegrityFacts) -> IntegrityEvaluation:
        """
        Evaluate integrity facts and produce a grade.

        Args:
            facts: IntegrityFacts from assembler

        Returns:
            IntegrityEvaluation with state, grade, and explanation
        """
        # Calculate score
        total_expected = len(self.EXPECTED_TABLES)
        observed_count = len(facts.observed_evidence)
        score = observed_count / total_expected if total_expected > 0 else 0.0

        # Build missing reasons
        missing_reasons = {}
        for evidence_class in facts.missing_evidence:
            # Check if there's a recorded failure for this
            failure = self._find_failure(facts, evidence_class)
            if failure:
                missing_reasons[evidence_class.value] = failure.failure_reason
            else:
                missing_reasons[evidence_class.value] = "no_records_found"

        # Include unresolved failures in reasons
        if facts.unresolved_failures:
            missing_reasons["_capture_failures"] = [
                f.to_dict() for f in facts.unresolved_failures
            ]

        # Determine state (is evidence collection complete?)
        state = IntegrityState.SEALED  # Assume sealed at evaluation time

        # Determine grade based on policy
        grade = self._compute_grade(facts, score)

        # Build explanation
        explanation = self._build_explanation(facts, grade)

        return IntegrityEvaluation(
            state=state,
            grade=grade,
            score=score,
            missing_reasons=missing_reasons,
            explanation=explanation,
        )

    EXPECTED_TABLES = IntegrityAssembler.EXPECTED_TABLES

    def _find_failure(self, facts: IntegrityFacts,
                      evidence_class: EvidenceClass) -> Optional[CaptureFailure]:
        """Find a capture failure for an evidence class."""
        for failure in facts.capture_failures:
            if failure.evidence_class == evidence_class:
                return failure
        return None

    def _compute_grade(self, facts: IntegrityFacts, score: float) -> IntegrityGrade:
        """
        Compute integrity grade based on policy.

        Policy:
        - FAIL if required evidence missing
        - FAIL if unresolved permanent failures
        - WARN if any capture failures (even if superseded)
        - WARN if score < PASS_THRESHOLD
        - PASS otherwise
        """
        # Check for required evidence
        if not facts.has_required_evidence:
            return IntegrityGrade.FAIL

        # Check for unresolved permanent failures
        permanent_failures = [
            f for f in facts.unresolved_failures
            if f.resolution == FailureResolution.PERMANENT
        ]
        if permanent_failures:
            return IntegrityGrade.FAIL

        # Degrade if any capture failures occurred
        if facts.has_capture_failures:
            return IntegrityGrade.WARN

        # Score-based grading
        if score >= self.PASS_THRESHOLD:
            return IntegrityGrade.PASS
        elif score >= self.WARN_THRESHOLD:
            return IntegrityGrade.WARN
        else:
            return IntegrityGrade.FAIL

    def _build_explanation(self, facts: IntegrityFacts,
                           grade: IntegrityGrade) -> str:
        """Build human-readable explanation."""
        observed = len(facts.observed_evidence)
        expected = len(self.EXPECTED_TABLES)
        failures = len(facts.capture_failures)

        if grade == IntegrityGrade.PASS:
            return f"All evidence present ({observed}/{expected})"
        elif grade == IntegrityGrade.WARN:
            parts = []
            if observed < expected:
                parts.append(f"{expected - observed} evidence types missing")
            if failures > 0:
                parts.append(f"{failures} capture failures recorded")
            return "; ".join(parts)
        else:
            missing = [e.value for e in facts.missing_evidence if e in REQUIRED_EVIDENCE]
            return f"Critical evidence missing: {', '.join(missing)}"


# =============================================================================
# Backward Compatibility - compute_integrity()
# =============================================================================


def compute_integrity_v2(run_id: str) -> Dict[str, Any]:
    """
    Compute integrity using the new split architecture.

    Returns dict compatible with the original compute_integrity().
    """
    assembler = IntegrityAssembler()
    evaluator = IntegrityEvaluator()

    facts = assembler.gather(run_id)
    evaluation = evaluator.evaluate(facts)

    return {
        "expected_artifacts": [e.value for e in EvidenceClass if e != EvidenceClass.J_INTEGRITY],
        "observed_artifacts": [e.value for e in facts.observed_evidence],
        "missing_artifacts": [e.value for e in facts.missing_evidence],
        "missing_reasons": evaluation.missing_reasons,
        "capture_failures": [f.to_dict() for f in facts.capture_failures],
        "integrity_score": evaluation.score,
        "integrity_status": evaluation.integrity_status,
        "integrity_state": evaluation.state.value,
        "integrity_grade": evaluation.grade.value,
        "explanation": evaluation.explanation,
    }
