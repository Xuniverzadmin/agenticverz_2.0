# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: ai-console
# Temporal:
#   Trigger: api
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none (in-memory ranking)
#   Writes: none
# Role: Attention ranking engine for activity signals
# Callers: activity_facade.py
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, Activity Domain
# NOTE: Renamed attention_ranking_service.py → attention_ranking_engine.py (2026-01-24)
#       per BANNED_NAMING rule (*_service.py → *_engine.py)
# NOTE: Demoted attention_ranking_engine.py → attention_ranking.py (2026-02-08)
#       Orphan demotion — not an entry module, remove _engine suffix
"""Attention ranking engine for prioritizing signals."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from app.hoc.cus.hoc_spine.services.time import utc_now


@dataclass
class AttentionSignal:
    """A signal in the attention queue."""

    signal_id: str
    signal_type: str
    dimension: str
    title: str
    description: str
    severity: float
    attention_score: float
    attention_reason: str
    created_at: datetime
    source_run_id: Optional[str] = None
    acknowledged: bool = False
    suppressed: bool = False


@dataclass
class AttentionQueueResult:
    """Result of attention queue query."""

    items: list[AttentionSignal]
    total: int
    generated_at: datetime


class AttentionRankingService:
    """
    Service for ranking and prioritizing activity signals.

    Computes attention scores based on:
    - Signal severity
    - Recency
    - Pattern frequency
    - User acknowledgment status
    """

    def __init__(self) -> None:
        pass  # Stub - no DB dependency

    async def get_attention_queue(
        self,
        tenant_id: str,
        *,
        limit: int = 20,
        offset: int = 0,
        min_score: float = 0.0,
    ) -> AttentionQueueResult:
        """Get prioritized attention queue for tenant.

        Args:
            tenant_id: Tenant identifier
            limit: Max items to return
            offset: Pagination offset
            min_score: Minimum attention score threshold (0.0-1.0)
        """
        # Stub implementation - returns empty queue
        # min_score would filter items with score >= min_score when implemented
        _ = min_score  # Reserved for filtering when driver is wired
        return AttentionQueueResult(
            items=[],
            total=0,
            generated_at=utc_now(),
        )

    async def compute_attention_score(
        self,
        signal_type: str,
        severity: float,
        recency_hours: float,
        pattern_frequency: int,
    ) -> float:
        """Compute attention score for a signal."""
        # Simple scoring formula
        base_score = severity * 0.4
        recency_factor = max(0, 1 - (recency_hours / 168))  # Decay over 7 days
        frequency_factor = min(1.0, pattern_frequency / 10)

        return base_score + (recency_factor * 0.3) + (frequency_factor * 0.3)
