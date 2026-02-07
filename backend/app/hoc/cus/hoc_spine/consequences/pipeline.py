# Layer: L4 — HOC Spine (Consequences)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (post-dispatch, every operation)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: DispatchRecord from OperationRegistry._audit_dispatch()
# Data Access:
#   Reads: none
#   Writes: none (delegates to adapters)
# Role: Post-dispatch consequences pipeline — runs adapters after audit persistence
# Callers: OperationRegistry._audit_dispatch()
# Allowed Imports: hoc_spine/consequences (ports, adapters), hoc_spine/services (dispatch_audit)
# Forbidden Imports: L1, L2, L5, L6, sqlalchemy, app.db
# Reference: Constitution §2.3, Gap G4 consequences expansion
# artifact_class: CODE

"""
Consequences Pipeline.

Entry point for post-dispatch consequences. Runs registered adapters
against each DispatchRecord after audit store persistence.

Constitution §2.3: Consequences are post-commit only. They never
participate in the operation's transaction. Adapter failures are
logged but never propagate — the operation result is already final.

Usage (from OperationRegistry._audit_dispatch):
    from app.hoc.cus.hoc_spine.consequences.pipeline import get_consequence_pipeline
    get_consequence_pipeline().run(record)
"""

import logging
from typing import Optional

from app.hoc.cus.hoc_spine.consequences.ports import ConsequenceAdapter
from app.hoc.cus.hoc_spine.services.dispatch_audit import DispatchRecord

logger = logging.getLogger("nova.hoc_spine.consequences.pipeline")


class ConsequencePipeline:
    """
    Post-dispatch consequence pipeline.

    Adapters are registered at startup and run synchronously for each
    dispatch. Each adapter is wrapped in try/except — a failing adapter
    never blocks other adapters or the dispatch response.
    """

    def __init__(self) -> None:
        self._adapters: list[ConsequenceAdapter] = []
        self._frozen: bool = False

    def register(self, adapter: ConsequenceAdapter) -> None:
        """
        Register a consequence adapter.

        Must be called before freeze(). Typically during bootstrap_hoc_spine().

        Args:
            adapter: ConsequenceAdapter implementation

        Raises:
            RuntimeError: If pipeline is frozen
        """
        if self._frozen:
            raise RuntimeError(
                f"ConsequencePipeline is frozen — cannot register adapter '{adapter.name}'"
            )
        self._adapters.append(adapter)
        logger.info(
            "consequence.adapter_registered",
            extra={"adapter": adapter.name},
        )

    def freeze(self) -> None:
        """Freeze the pipeline — no more adapter registrations."""
        self._frozen = True
        logger.info(
            "consequence.pipeline_frozen",
            extra={"adapter_count": len(self._adapters)},
        )

    @property
    def is_frozen(self) -> bool:
        return self._frozen

    @property
    def adapter_count(self) -> int:
        return len(self._adapters)

    @property
    def adapter_names(self) -> list[str]:
        return [a.name for a in self._adapters]

    def run(self, record: DispatchRecord) -> None:
        """
        Run all registered adapters against a dispatch record.

        Non-blocking: each adapter is wrapped in try/except.
        A failing adapter is logged but never propagates.

        Args:
            record: Frozen DispatchRecord from build_dispatch_record()
        """
        for adapter in self._adapters:
            try:
                adapter.handle(record)
            except Exception:
                logger.warning(
                    "consequence.adapter_failed",
                    extra={
                        "adapter": adapter.name,
                        "operation": record.operation,
                    },
                    exc_info=True,
                )


# =============================================================================
# Module-level singleton
# =============================================================================

_pipeline_instance: Optional[ConsequencePipeline] = None


def get_consequence_pipeline() -> ConsequencePipeline:
    """
    Get the consequence pipeline singleton.

    Returns:
        ConsequencePipeline instance
    """
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = ConsequencePipeline()
    return _pipeline_instance
