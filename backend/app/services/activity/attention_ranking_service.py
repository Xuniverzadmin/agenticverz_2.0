# Layer: L4 — Domain Engines
# Product: ai-console
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Composite attention scoring for runs
# Callers: Activity API (L2)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: docs/architecture/activity/ACTIVITY_DOMAIN_SQL.md#6-sig-o5

"""
Attention Ranking Service

Combines multiple signals into a single attention score:
- risk_level (35%)
- impact (25%)
- latency (15%)
- recency (15%)
- evidence (10%)

Design Rules:
- Weights are FROZEN (governance approval required to change)
- Ranking only (no signal recomputation)
- Read-only (no writes)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


# ============================================================================
# FROZEN WEIGHTS - DO NOT MODIFY WITHOUT GOVERNANCE APPROVAL
# Reference: docs/architecture/activity/ACTIVITY_DOMAIN_CONTRACT.md
# ============================================================================

ATTENTION_WEIGHTS = {
    "risk": 0.35,
    "impact": 0.25,
    "latency": 0.15,
    "recency": 0.15,
    "evidence": 0.10,
}

# Verify weights sum to 1.0
assert abs(sum(ATTENTION_WEIGHTS.values()) - 1.0) < 0.001, "Weights must sum to 1.0"

WEIGHTS_VERSION = "1.0"

# ============================================================================
# FROZEN DAMPENING CONSTANT - DO NOT MODIFY WITHOUT GOVERNANCE APPROVAL
# Reference: ATTN-DAMP-001 (Idempotent Dampening)
# ============================================================================

ACK_DAMPENER = 0.6  # Acknowledged signals receive 0.6x attention score


@dataclass
class AttentionItem:
    """An item in the attention queue."""
    run_id: str
    attention_score: float
    effective_attention_score: float  # After dampening if acknowledged
    reasons: list[str]
    state: str
    status: str
    started_at: Optional[datetime]
    # Feedback fields
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    suppressed_until: Optional[datetime] = None


@dataclass
class AttentionQueueResult:
    """Result of attention queue computation."""
    queue: list[AttentionItem]
    total_attention_items: int
    weights_version: str
    generated_at: datetime


class AttentionRankingService:
    """
    Composite attention scoring for runs.

    RESPONSIBILITIES:
    - Combine signals into attention score
    - Apply frozen weights
    - Return ranked queue with reasons

    FORBIDDEN:
    - Recompute underlying signals
    - Apply policy actions
    - Modify weights at runtime
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_attention_queue(
        self,
        tenant_id: str,
        limit: int = 20,
        include_suppressed: bool = False,
    ) -> AttentionQueueResult:
        """
        Get the attention queue ranked by composite score.

        Applies feedback from audit_ledger:
        - Suppressed signals are filtered out (unless include_suppressed=True)
        - Acknowledged signals receive 0.6x dampening (ATTN-DAMP-001)

        Args:
            tenant_id: Tenant scope
            limit: Max items to return (max 100)
            include_suppressed: If True, include suppressed items (for admin view)

        Returns:
            AttentionQueueResult with ranked items
        """
        limit = min(limit, 100)

        # Weights for SQL
        w_risk = ATTENTION_WEIGHTS["risk"]
        w_impact = ATTENTION_WEIGHTS["impact"]
        w_latency = ATTENTION_WEIGHTS["latency"]
        w_recency = ATTENTION_WEIGHTS["recency"]
        w_evidence = ATTENTION_WEIGHTS["evidence"]

        # Import here to avoid circular imports
        from app.services.activity.signal_identity import compute_signal_fingerprint_from_row

        sql = text("""
            WITH run_signals AS (
                SELECT
                    run_id,
                    tenant_id,
                    state,
                    status,
                    started_at,
                    risk_type,
                    evaluation_outcome,
                    -- Risk score (0-1)
                    CASE risk_level
                        WHEN 'VIOLATED' THEN 1.0
                        WHEN 'AT_RISK' THEN 0.8
                        WHEN 'NEAR_THRESHOLD' THEN 0.5
                        ELSE 0.0
                    END as risk_score,
                    -- Latency score (0-1)
                    CASE latency_bucket
                        WHEN 'STALLED' THEN 1.0
                        WHEN 'SLOW' THEN 0.5
                        ELSE 0.0
                    END as latency_score,
                    -- Evidence health score (0-1)
                    CASE evidence_health
                        WHEN 'MISSING' THEN 1.0
                        WHEN 'DEGRADED' THEN 0.5
                        ELSE 0.0
                    END as evidence_score,
                    -- Impact score (0-1)
                    CASE
                        WHEN policy_violation THEN 0.8
                        WHEN incident_count > 0 THEN 0.6
                        ELSE 0.0
                    END as impact_score,
                    -- Recency score (0-1, decays over 24h)
                    GREATEST(0, 1 - EXTRACT(EPOCH FROM (NOW() - started_at)) / 86400) as recency_score
                FROM v_runs_o2
                WHERE tenant_id = :tenant_id
                  AND (state = 'LIVE' OR completed_at >= NOW() - INTERVAL '24 hours')
            )
            SELECT
                run_id,
                state,
                status,
                started_at,
                risk_type,
                evaluation_outcome,
                risk_score,
                latency_score,
                evidence_score,
                impact_score,
                recency_score,
                -- Composite score with frozen weights
                (
                    risk_score * :w_risk +
                    latency_score * :w_latency +
                    evidence_score * :w_evidence +
                    impact_score * :w_impact +
                    recency_score * :w_recency
                ) as attention_score
            FROM run_signals
            WHERE (
                risk_score > 0 OR
                latency_score > 0 OR
                evidence_score > 0 OR
                impact_score > 0
            )
            ORDER BY attention_score DESC
            LIMIT :limit
        """)

        result = await self.session.execute(sql, {
            "tenant_id": tenant_id,
            "w_risk": w_risk,
            "w_impact": w_impact,
            "w_latency": w_latency,
            "w_recency": w_recency,
            "w_evidence": w_evidence,
            "limit": limit,
        })

        rows = result.mappings().all()

        # Compute fingerprints for all rows to enable feedback lookup
        fingerprints: list[str] = []
        for row in rows:
            # Derive signal type from row
            signal_type = f"{row.get('risk_type', 'UNKNOWN')}_RISK" if row.get("risk_type") else "UNKNOWN"
            signal_row = {
                "run_id": row["run_id"],
                "signal_type": signal_type,
                "risk_type": row.get("risk_type") or "UNKNOWN",
                "evaluation_outcome": row.get("evaluation_outcome") or "UNKNOWN",
            }
            fingerprints.append(compute_signal_fingerprint_from_row(signal_row))

        # Fetch feedback for all signals in bulk
        feedback_map = await self._get_bulk_feedback(tenant_id, fingerprints)

        queue: list[AttentionItem] = []
        now = datetime.utcnow()

        for i, row in enumerate(rows):
            fingerprint = fingerprints[i]
            feedback = feedback_map.get(fingerprint)

            # Check suppression (SIGNAL-SUPPRESS-001)
            if feedback and feedback.get("suppress_until"):
                suppress_until = feedback["suppress_until"]
                if suppress_until > now and not include_suppressed:
                    # Skip suppressed signals
                    continue

            # Build reason codes
            reasons = []
            if row["risk_score"] > 0:
                reasons.append("risk")
            if row["impact_score"] > 0:
                reasons.append("impact")
            if row["latency_score"] > 0:
                reasons.append("latency")
            if row["evidence_score"] > 0:
                reasons.append("evidence")

            base_score = round(float(row["attention_score"]), 3)

            # Apply acknowledgement dampening (ATTN-DAMP-001)
            # Idempotent: apply ONCE if acknowledged
            is_acknowledged = bool(feedback and feedback.get("event_type") == "SignalAcknowledged")
            if is_acknowledged:
                effective_score = round(base_score * ACK_DAMPENER, 3)
            else:
                effective_score = base_score

            queue.append(AttentionItem(
                run_id=row["run_id"],
                attention_score=base_score,
                effective_attention_score=effective_score,
                reasons=reasons,
                state=row["state"],
                status=row["status"],
                started_at=row["started_at"],
                acknowledged=is_acknowledged,
                acknowledged_by=feedback["actor_id"] if is_acknowledged and feedback else None,
                acknowledged_at=feedback["created_at"] if is_acknowledged and feedback else None,
                suppressed_until=feedback["suppress_until"] if feedback else None,
            ))

        # Re-sort by effective_attention_score (dampening may change order)
        queue.sort(key=lambda x: x.effective_attention_score, reverse=True)

        return AttentionQueueResult(
            queue=queue,
            total_attention_items=len(queue),
            weights_version=WEIGHTS_VERSION,
            generated_at=datetime.utcnow(),
        )

    async def _get_bulk_feedback(
        self,
        tenant_id: str,
        fingerprints: list[str],
    ) -> dict[str, dict]:
        """
        Get feedback state for multiple signals efficiently.

        Args:
            tenant_id: Tenant scope
            fingerprints: List of signal fingerprints to query

        Returns:
            Dict mapping fingerprint to feedback dict with:
            - event_type: SignalAcknowledged or SignalSuppressed
            - actor_id: Who created the feedback
            - created_at: When feedback was created
            - suppress_until: Expiry time if suppressed
        """
        if not fingerprints:
            return {}

        sql = text("""
            SELECT DISTINCT ON (entity_id)
                entity_id AS fingerprint,
                event_type,
                actor_id,
                created_at,
                (after_state->>'suppress_until')::timestamptz AS suppress_until
            FROM audit_ledger
            WHERE tenant_id = :tenant_id
              AND entity_type = 'SIGNAL'
              AND entity_id = ANY(:fingerprints)
            ORDER BY entity_id, created_at DESC
        """)

        result = await self.session.execute(sql, {
            "tenant_id": tenant_id,
            "fingerprints": fingerprints,
        })

        feedback_map: dict[str, dict] = {}
        for row in result.mappings():
            feedback_map[row["fingerprint"]] = {
                "event_type": row["event_type"],
                "actor_id": row["actor_id"],
                "created_at": row["created_at"],
                "suppress_until": row["suppress_until"],
            }

        return feedback_map
