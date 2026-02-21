# capability_id: CAP-012
# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: worker (run events), incident_engine (failure events)
#   Execution: sync
# Role: Evidence recorder — cross-domain mediation for run evidence (C4 Loop Model)
# Callers: incidents/L5_engines/incident_engine.py (via L4 handler injection)
# Allowed Imports: hoc_spine, hoc.cus.policies (lazy — L4 can import L5/L6)
# Forbidden Imports: L1, L2
# Reference: PIN-504 (Cross-Domain Violation Resolution), PIN-487 (Loop Model)
# artifact_class: CODE

"""
Lessons Coordinator (C4 — Loop Model)

Provides cross-domain evidence recording without domain-specific nouns.
Replaces direct incidents→policies L5 import.

Pattern:
    L4 handler → LessonsCoordinator.record_evidence() → policies L5 engine
"""


class LessonsCoordinator:
    """
    Cross-domain evidence recorder.

    Mediates between incident detection (incidents domain) and
    learning subsystem (policies domain) without either domain
    importing the other directly.

    Rules:
    - No retry logic
    - No decisions
    - No state
    - Neutral naming only (no domain nouns)
    """

    def record_evidence(self, context: dict) -> None:
        """
        Record evidence from a run event into the learning subsystem.

        Args:
            context: Evidence context with keys:
                - run_id: str
                - tenant_id: str
                - error_code: str
                - error_message: str
                - severity: str
                - is_synthetic: bool (optional)
                - synthetic_scenario_id: str (optional)
        """
        from app.hoc.cus.policies.L5_engines.lessons_engine import get_lessons_learned_engine

        engine = get_lessons_learned_engine()

        # Delegate to the learning engine — fail-open for learning
        try:
            engine.detect_lesson_from_failure(
                run_id=context.get("run_id"),
                tenant_id=context.get("tenant_id"),
                error_code=context.get("error_code", "UNKNOWN"),
                error_message=context.get("error_message", ""),
                severity=context.get("severity", "MEDIUM"),
                is_synthetic=context.get("is_synthetic", False),
                synthetic_scenario_id=context.get("synthetic_scenario_id"),
            )
        except Exception:
            # Fail-open: learning must never block incident creation
            pass


# =============================================================================
# Singleton
# =============================================================================

_lessons_coordinator_instance = None


def get_lessons_coordinator() -> LessonsCoordinator:
    """Get the singleton LessonsCoordinator instance."""
    global _lessons_coordinator_instance
    if _lessons_coordinator_instance is None:
        _lessons_coordinator_instance = LessonsCoordinator()
    return _lessons_coordinator_instance


__all__ = [
    "LessonsCoordinator",
    "get_lessons_coordinator",
]
