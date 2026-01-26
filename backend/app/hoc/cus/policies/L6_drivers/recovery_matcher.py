# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Product: system-wide (NOT console-owned)
# Temporal:
#   Trigger: worker
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: failure_patterns, recovery_suggestions
#   Writes: recovery_candidates (via session.add, NO COMMIT)
# Database:
#   Scope: domain (policies)
#   Models: FailurePattern, RecoverySuggestion, RecoveryCandidate
# Role: Match failure patterns and generate recovery suggestions — L6 DOES NOT COMMIT
# Callers: L5 engines (must provide session, must own transaction boundary)
# Allowed Imports: L6, L7 (models)
# Forbidden: session.commit() — L4 owns commit authority
# Reference: PIN-470, PIN-240, TRANSACTION_BYPASS_REMEDIATION_CHECKLIST.md
# WARNING: If this logic is wrong, ALL products break.
#
# Migration Note:
# This driver has no active HOC callers yet.
# Legacy callers (if any) must provide session explicitly.

from app.infra import FeatureIntent, RetryPolicy

# Phase-2.3: Feature Intent Declaration
# Escalates to LLM for recovery suggestions - external HTTP calls are non-deterministic
# LLM responses cannot be safely retried without semantic duplication
FEATURE_INTENT = FeatureIntent.EXTERNAL_SIDE_EFFECT
RETRY_POLICY = RetryPolicy.NEVER

# app/services/recovery_matcher.py
"""
M10 Recovery Suggestion Engine - Matcher Service

Matches failure entries against historical patterns and generates
recovery suggestions with confidence scoring.

Scoring Algorithm:
- Basic score: matches / occurrences
- Weighted time-decay: exp(-lambda * age_in_days), half-life = 30 days
- Final: alpha * weighted + (1-alpha) * basic, alpha = 0.7

References:
- PIN-033: M8-M14 Machine-Native Realignment
- M10 Blueprint: Recovery Suggestion Engine
"""

import hashlib
import logging
import math
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from app.security.sanitize import sanitize_error_message

if TYPE_CHECKING:
    from sqlmodel import Session

logger = logging.getLogger("nova.services.recovery_matcher")

# Scoring constants
HALF_LIFE_DAYS = 30
EMBEDDING_SIMILARITY_THRESHOLD = 0.85  # Minimum similarity for embedding match
LLM_ESCALATION_THRESHOLD = 0.75  # Below this, escalate to LLM
CACHE_TTL_SECONDS = 3600  # 1 hour cache for recovery suggestions
LAMBDA = math.log(2) / HALF_LIFE_DAYS  # ~0.0231
ALPHA = 0.7  # Weight for time-decayed score
MIN_CONFIDENCE_THRESHOLD = 0.1  # Minimum confidence to store suggestion
NO_HISTORY_CONFIDENCE = 0.2  # Default when no history exists
EXACT_MATCH_CONFIDENCE = 0.95  # Confidence for exact catalog matches


@dataclass
class MatchResult:
    """Result from matching a failure to a recovery suggestion."""

    matched_entry: Optional[Dict[str, Any]]
    suggested_recovery: Optional[str]
    confidence: float
    candidate_id: Optional[int]
    explain: Dict[str, Any]
    failure_match_id: str
    error_code: str
    error_signature: str


class RecoveryMatcher:
    """
    Matches failures to recovery suggestions using pattern matching
    and confidence scoring.

    Transaction Boundary: L6 drivers DO NOT commit.
    The caller (L5 engine or L4 coordinator) owns the transaction.
    This driver only calls session.add()/session.execute() — never session.commit().
    """

    def __init__(self, session: "Session"):
        """
        Initialize matcher with required database session.

        Args:
            session: SQLModel session (REQUIRED — caller owns transaction)
        """
        self._session = session

    def _normalize_error(self, payload: Dict[str, Any]) -> Tuple[str, str]:
        """
        Normalize failure payload for matching.

        Returns:
            Tuple of (error_code, error_signature)
        """
        error_type = payload.get("error_type", payload.get("error_code", "UNKNOWN"))
        raw = payload.get("raw", payload.get("error_message", ""))

        # Sanitize error message to prevent secrets in signatures (PIN-052)
        sanitized_raw = sanitize_error_message(str(raw))

        # Normalize: lowercase, strip whitespace, truncate
        normalized = sanitized_raw.lower().strip()[:500]

        # Generate signature hash
        signature_input = f"{error_type}:{normalized}"
        signature = hashlib.sha256(signature_input.encode()).hexdigest()[:16]

        return error_type, signature

    def _calculate_time_weight(self, age_days: float) -> float:
        """Calculate time decay weight using exponential decay."""
        return math.exp(-LAMBDA * age_days)

    def _compute_confidence(
        self, matches: List[Dict[str, Any]], occurrences: int, has_exact_match: bool = False
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Compute confidence score using weighted time-decay algorithm.

        Args:
            matches: List of historical matches with timestamps
            occurrences: Total occurrences of this failure pattern
            has_exact_match: Whether there's an exact catalog match

        Returns:
            Tuple of (confidence, explain_dict)
        """
        if has_exact_match:
            return EXACT_MATCH_CONFIDENCE, {
                "method": "exact_match",
                "confidence": EXACT_MATCH_CONFIDENCE,
            }

        if not matches or occurrences == 0:
            return NO_HISTORY_CONFIDENCE, {
                "method": "no_history",
                "confidence": NO_HISTORY_CONFIDENCE,
            }

        now = datetime.now(timezone.utc)

        # Calculate basic score
        score_basic = min(1.0, len(matches) / occurrences)

        # Calculate weighted score with time decay
        weighted_matches = 0.0
        weighted_occurrences = 0.0

        for match in matches:
            created_at = match.get("created_at")
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            elif created_at is None:
                continue

            age_days = (now - created_at).total_seconds() / 86400
            weight = self._calculate_time_weight(age_days)
            weighted_matches += weight

        # Weight all occurrences (assume uniform distribution for simplicity)
        weighted_occurrences = occurrences * self._calculate_time_weight(7)  # Avg age ~7 days

        if weighted_occurrences > 0:
            score_weighted = weighted_matches / weighted_occurrences
        else:
            score_weighted = score_basic

        # Blend scores
        confidence = ALPHA * score_weighted + (1 - ALPHA) * score_basic
        confidence = min(1.0, max(0.0, confidence))

        explain = {
            "method": "weighted_time_decay",
            "matches": len(matches),
            "occurrences": occurrences,
            "score_basic": round(score_basic, 4),
            "score_weighted": round(score_weighted, 4),
            "alpha": ALPHA,
            "half_life_days": HALF_LIFE_DAYS,
            "confidence": round(confidence, 4),
        }

        return confidence, explain

    def _generate_suggestion(self, error_code: str, error_message: str, similar_recoveries: List[str]) -> str:
        """Generate recovery suggestion text."""
        if similar_recoveries:
            # Use most common recovery from history
            return similar_recoveries[0]

        # Default suggestions by error type
        defaults = {
            "TIMEOUT": "Increase timeout threshold or implement retry with exponential backoff",
            "HTTP_5XX": "Check service health, implement circuit breaker, retry with backoff",
            "RATE_LIMITED": "Implement rate limiting with jitter, queue requests",
            "BUDGET_EXCEEDED": "Check budget allocation, consider cost optimization",
            "PERMISSION_DENIED": "Verify credentials and permissions configuration",
            "PARSE_ERROR": "Validate input format, check schema compatibility",
            "CONNECTION_ERROR": "Check network connectivity, implement retry logic",
        }

        for code_prefix, suggestion in defaults.items():
            if error_code.upper().startswith(code_prefix):
                return suggestion

        return f"Review error '{error_code}' and implement appropriate error handling"

    def _find_similar_failures(self, error_code: str, error_signature: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find similar failures from history."""
        try:
            from sqlalchemy import text

            session = self._session

            # Query for similar failures by error_code
            result = session.execute(
                text(
                    """
                SELECT
                    id,
                    error_code,
                    error_message,
                    recovery_suggestion,
                    recovery_succeeded,
                    category,
                    created_at
                FROM failure_matches
                WHERE error_code = :error_code
                  AND recovery_suggestion IS NOT NULL
                ORDER BY created_at DESC
                LIMIT :limit
                """
                ),
                {"error_code": error_code, "limit": limit},
            )

            rows = result.fetchall()
            return [
                {
                    "id": str(row[0]),
                    "error_code": row[1],
                    "error_message": row[2],
                    "recovery_suggestion": row[3],
                    "recovery_succeeded": row[4],
                    "category": row[5],
                    "created_at": row[6],
                }
                for row in rows
            ]
        except Exception as e:
            logger.warning(f"Failed to find similar failures: {e}")
            return []

    def _count_occurrences(self, error_code: str, days: int = 7) -> int:
        """Count occurrences of error code in recent history."""
        try:
            from sqlalchemy import text

            session = self._session

            result = session.execute(
                text(
                    f"""
                SELECT COUNT(*)
                FROM failure_matches
                WHERE error_code = :error_code
                  AND created_at > now() - interval '{days} days'
                """
                ),
                {"error_code": error_code},
            )

            return result.scalar() or 0
        except Exception as e:
            logger.warning(f"Failed to count occurrences: {e}")
            return 0

    # =========================================================================
    # Hybrid ML Recovery (PIN-050)
    # 3-layer lookup: cache → embedding → LLM
    # =========================================================================

    def _get_cached_recovery(self, error_signature: str) -> Optional[Dict[str, Any]]:
        """
        Layer 1: Check in-memory/Redis cache for recovery suggestion.

        Fast O(1) lookup for recently seen error patterns.
        """
        try:
            import redis

            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            r = redis.from_url(redis_url, decode_responses=True)

            cache_key = f"recovery:cache:{error_signature}"
            cached = r.get(cache_key)

            if cached:
                import json

                logger.debug(f"Cache hit for error_signature={error_signature[:8]}")
                return json.loads(cached)

            return None
        except Exception as e:
            logger.debug(f"Cache lookup failed (non-fatal): {e}")
            return None

    def _set_cached_recovery(self, error_signature: str, recovery: Dict[str, Any]) -> None:
        """Store recovery suggestion in cache."""
        try:
            import json

            import redis

            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            r = redis.from_url(redis_url, decode_responses=True)

            cache_key = f"recovery:cache:{error_signature}"
            r.setex(cache_key, CACHE_TTL_SECONDS, json.dumps(recovery))
        except Exception as e:
            logger.debug(f"Cache set failed (non-fatal): {e}")

    async def _find_similar_by_embedding(self, error_message: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Layer 2: Vector similarity search for similar failures.

        Uses pgvector to find semantically similar error messages
        even if error_code differs.

        Args:
            error_message: Sanitized error message to match
            limit: Maximum results

        Returns:
            List of similar failures with similarity scores
        """
        try:
            from app.memory.vector_store import get_embedding

            # Get embedding for the error message
            sanitized = sanitize_error_message(error_message)
            embedding = await get_embedding(sanitized[:500])  # Truncate for embedding

            from sqlalchemy import text

            session = self._session

            # Vector similarity search on failure_catalog (if embeddings exist)
            result = session.execute(
                text(
                    """
                    SELECT
                        id,
                        error_code,
                        error_pattern,
                        recovery_action,
                        success_rate,
                        1 - (embedding <=> CAST(:embedding AS vector)) as similarity
                    FROM failure_catalog
                    WHERE embedding IS NOT NULL
                      AND 1 - (embedding <=> CAST(:embedding AS vector)) >= :threshold
                    ORDER BY embedding <=> CAST(:embedding AS vector)
                    LIMIT :limit
                """
                ),
                {
                    "embedding": f"[{','.join(str(x) for x in embedding)}]",
                    "threshold": EMBEDDING_SIMILARITY_THRESHOLD,
                    "limit": limit,
                },
            )

            rows = result.fetchall()

            similar = [
                {
                    "id": str(row[0]),
                    "error_code": row[1],
                    "error_pattern": row[2],
                    "recovery_action": row[3],
                    "success_rate": float(row[4]) if row[4] else 0.0,
                    "similarity": float(row[5]),
                    "source": "embedding",
                }
                for row in rows
            ]

            logger.info(f"Embedding search found {len(similar)} similar failures")
            return similar

        except Exception as e:
            logger.warning(f"Embedding search failed: {e}")
            return []

    async def _escalate_to_llm(
        self, error_code: str, error_message: str, context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Layer 3: LLM reasoning for complex/novel failures.

        Only called when:
        - No cache hit
        - No embedding match above threshold
        - Error is complex or novel

        Uses structured output for recovery suggestion.
        """
        try:
            import httpx

            anthropic_key = os.getenv("ANTHROPIC_API_KEY")
            if not anthropic_key:
                logger.warning("ANTHROPIC_API_KEY not set, skipping LLM escalation")
                return None

            # Build prompt
            prompt = f"""Analyze this error and suggest a recovery action.

Error Code: {error_code}
Error Message: {sanitize_error_message(error_message)[:500]}

Provide a JSON response with:
- suggested_action: string (concise recovery action, max 200 chars)
- confidence: float (0.0-1.0)
- reasoning: string (brief explanation)
- requires_human: boolean (true if needs manual intervention)
"""

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": anthropic_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-sonnet-4-20250514",
                        "max_tokens": 500,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )

                if response.status_code != 200:
                    logger.warning(f"LLM API error: {response.status_code}")
                    return None

                data = response.json()
                content = data.get("content", [{}])[0].get("text", "")

                # Parse JSON response
                import json
                import re

                # Extract JSON from response
                json_match = re.search(r"\{[^{}]*\}", content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    result["source"] = "llm"
                    logger.info(f"LLM suggested recovery with confidence={result.get('confidence', 0):.2f}")
                    return result

                return None

        except Exception as e:
            logger.warning(f"LLM escalation failed: {e}")
            return None

    async def suggest_hybrid(self, request: Dict[str, Any]) -> MatchResult:
        """
        Hybrid ML recovery suggestion using 3-layer lookup.

        Layer 1: Cache (fast, O(1))
        Layer 2: Embedding similarity (semantic match)
        Layer 3: LLM reasoning (complex/novel failures)

        Args:
            request: Dict with failure_match_id, failure_payload, source

        Returns:
            MatchResult with suggestion and confidence
        """
        failure_match_id = str(request.get("failure_match_id", ""))
        payload = request.get("failure_payload", {})
        source = request.get("source", "unknown")

        # Normalize and sanitize
        error_code, error_signature = self._normalize_error(payload)
        error_message = payload.get("raw", payload.get("error_message", ""))

        logger.info(f"Hybrid recovery for failure_match_id={failure_match_id}, error_code={error_code}")

        # Layer 1: Cache lookup
        cached = self._get_cached_recovery(error_signature)
        if cached:
            return MatchResult(
                matched_entry=cached.get("matched_entry"),
                suggested_recovery=cached.get("suggestion"),
                confidence=cached.get("confidence", 0.8),
                candidate_id=None,
                explain={"method": "cache", "cache_hit": True},
                failure_match_id=failure_match_id,
                error_code=error_code,
                error_signature=error_signature,
            )

        # Layer 2: Embedding similarity search
        similar_by_embedding = await self._find_similar_by_embedding(error_message)

        if similar_by_embedding:
            best_match = similar_by_embedding[0]
            similarity = best_match.get("similarity", 0)

            if similarity >= EMBEDDING_SIMILARITY_THRESHOLD:
                suggestion = best_match.get("recovery_action", "")
                confidence = min(0.95, similarity * best_match.get("success_rate", 0.8))

                # Cache for future lookups
                self._set_cached_recovery(
                    error_signature,
                    {
                        "suggestion": suggestion,
                        "confidence": confidence,
                        "matched_entry": best_match,
                    },
                )

                return MatchResult(
                    matched_entry=best_match,
                    suggested_recovery=suggestion,
                    confidence=confidence,
                    candidate_id=None,
                    explain={
                        "method": "embedding",
                        "similarity": similarity,
                        "catalog_id": best_match.get("id"),
                    },
                    failure_match_id=failure_match_id,
                    error_code=error_code,
                    error_signature=error_signature,
                )

        # Layer 3: LLM escalation for complex/novel failures
        llm_result = await self._escalate_to_llm(error_code, error_message)

        if llm_result:
            suggestion = llm_result.get("suggested_action", "")
            confidence = llm_result.get("confidence", 0.5)

            # Cache LLM results too (shorter TTL could be configured)
            self._set_cached_recovery(
                error_signature,
                {
                    "suggestion": suggestion,
                    "confidence": confidence,
                    "matched_entry": {"source": "llm", "reasoning": llm_result.get("reasoning")},
                },
            )

            return MatchResult(
                matched_entry={"source": "llm", "reasoning": llm_result.get("reasoning")},
                suggested_recovery=suggestion,
                confidence=confidence,
                candidate_id=None,
                explain={
                    "method": "llm",
                    "requires_human": llm_result.get("requires_human", False),
                },
                failure_match_id=failure_match_id,
                error_code=error_code,
                error_signature=error_signature,
            )

        # Fallback: Use error_code matching (original behavior)
        return self.suggest(request)

    def _upsert_candidate(
        self,
        failure_match_id: str,
        suggestion: str,
        confidence: float,
        explain: Dict[str, Any],
        error_code: str,
        error_signature: str,
        matched_entry: Optional[Dict[str, Any]] = None,
        source: str = "matcher",
    ) -> int:
        """
        Upsert recovery candidate with occurrence counting.

        Returns:
            candidate_id
        """
        import json

        from sqlalchemy import text

        session = self._session

        # Check if candidate exists
        result = session.execute(
            text(
                """
            SELECT id, occurrence_count FROM recovery_candidates
            WHERE failure_match_id = CAST(:failure_match_id AS uuid)
            """
            ),
            {"failure_match_id": failure_match_id},
        )
        existing = result.fetchone()

        if existing:
            # Update existing candidate
            candidate_id = existing[0]
            session.execute(
                text(
                    """
                UPDATE recovery_candidates
                SET
                    suggestion = :suggestion,
                    confidence = :confidence,
                    explain = CAST(:explain AS jsonb),
                    occurrence_count = occurrence_count + 1,
                    last_occurrence_at = now(),
                    matched_catalog_entry = CAST(:matched_entry AS jsonb)
                WHERE id = :id
                """
                ),
                {
                    "id": candidate_id,
                    "suggestion": suggestion,
                    "confidence": confidence,
                    "explain": json.dumps(explain),
                    "matched_entry": json.dumps(matched_entry) if matched_entry else None,
                },
            )
        else:
            # Insert new candidate
            result = session.execute(
                text(
                    """
                INSERT INTO recovery_candidates (
                    failure_match_id, suggestion, confidence, explain,
                    matched_catalog_entry, error_code, error_signature,
                    source, created_by
                ) VALUES (
                    CAST(:failure_match_id AS uuid), :suggestion, :confidence, CAST(:explain AS jsonb),
                    CAST(:matched_entry AS jsonb), :error_code, :error_signature,
                    :source, :created_by
                )
                RETURNING id
                """
                ),
                {
                    "failure_match_id": failure_match_id,
                    "suggestion": suggestion,
                    "confidence": confidence,
                    "explain": json.dumps(explain),
                    "matched_entry": json.dumps(matched_entry) if matched_entry else None,
                    "error_code": error_code,
                    "error_signature": error_signature,
                    "source": source,
                    "created_by": "recovery_matcher",
                },
            )
            candidate_id = result.scalar()

        # NO COMMIT — L4 coordinator owns transaction boundary
        # Caller must commit after all operations complete
        return int(candidate_id) if candidate_id else 0

    def suggest(self, request: Dict[str, Any]) -> MatchResult:
        """
        Generate recovery suggestion for a failure.

        Args:
            request: Dict with keys:
                - failure_match_id: ID of the failure match
                - failure_payload: Error details (error_type, raw, meta)
                - source: Source system (optional)
                - occurred_at: When failure occurred (optional)

        Returns:
            MatchResult with suggestion and confidence
        """
        failure_match_id = str(request.get("failure_match_id", ""))
        payload = request.get("failure_payload", {})
        source = request.get("source", "unknown")

        # Normalize error
        error_code, error_signature = self._normalize_error(payload)
        error_message = payload.get("raw", payload.get("error_message", ""))

        logger.info(f"Processing recovery suggestion for failure_match_id={failure_match_id}, error_code={error_code}")

        # Find similar failures
        similar = self._find_similar_failures(error_code, error_signature)
        occurrences = self._count_occurrences(error_code)

        # Extract successful recovery suggestions
        successful_recoveries = [
            f["recovery_suggestion"] for f in similar if f.get("recovery_succeeded") and f.get("recovery_suggestion")
        ]

        # Check for exact catalog match
        matched_entry = None
        has_exact_match = False
        if similar:
            for s in similar:
                if s.get("category"):  # Has catalog match
                    matched_entry = {
                        "catalog_id": s.get("id"),
                        "error_code": s.get("error_code"),
                        "category": s.get("category"),
                    }
                    has_exact_match = True
                    break

        # Compute confidence
        confidence, explain = self._compute_confidence(similar, occurrences, has_exact_match)

        # Generate suggestion
        suggestion = self._generate_suggestion(error_code, error_message, successful_recoveries)

        # Upsert candidate if confidence meets threshold
        candidate_id = None
        if confidence >= MIN_CONFIDENCE_THRESHOLD:
            try:
                candidate_id = self._upsert_candidate(
                    failure_match_id=failure_match_id,
                    suggestion=suggestion,
                    confidence=confidence,
                    explain=explain,
                    error_code=error_code,
                    error_signature=error_signature,
                    matched_entry=matched_entry,
                    source=source,
                )
            except Exception as e:
                logger.error(f"Failed to upsert candidate: {e}")

        result = MatchResult(
            matched_entry=matched_entry,
            suggested_recovery=suggestion,
            confidence=confidence,
            candidate_id=candidate_id,
            explain=explain,
            failure_match_id=failure_match_id,
            error_code=error_code,
            error_signature=error_signature,
        )

        logger.info(f"Generated suggestion: confidence={confidence:.2f}, candidate_id={candidate_id}")

        return result

    def get_candidates(self, status: str = "pending", limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List recovery candidates by status.

        Args:
            status: Filter by decision status (pending, approved, rejected, all)
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of candidate dicts
        """
        import json

        from sqlalchemy import text

        session = self._session

        query = """
            SELECT
                id, failure_match_id, suggestion, confidence,
                explain, decision, occurrence_count, last_occurrence_at,
                created_at, approved_by_human, approved_at, review_note,
                error_code, source
            FROM recovery_candidates
        """

        if status != "all":
            query += " WHERE decision = :status"

        query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"

        params = {"limit": limit, "offset": offset}
        if status != "all":
            params["status"] = status

        result = session.execute(text(query), params)
        rows = result.fetchall()

        return [
            {
                "id": row[0],
                "failure_match_id": str(row[1]),
                "suggestion": row[2],
                "confidence": row[3],
                "explain": json.loads(row[4]) if isinstance(row[4], str) else (row[4] or {}),
                "decision": row[5],
                "occurrence_count": row[6],
                "last_occurrence_at": row[7].isoformat() if row[7] else None,
                "created_at": row[8].isoformat() if row[8] else None,
                "approved_by_human": row[9],
                "approved_at": row[10].isoformat() if row[10] else None,
                "review_note": row[11],
                "error_code": row[12],
                "source": row[13],
            }
            for row in rows
        ]

    def approve_candidate(
        self, candidate_id: int, approved_by: str, decision: str = "approved", note: str = ""
    ) -> Dict[str, Any]:
        """
        Approve or reject a recovery candidate.

        Args:
            candidate_id: ID of candidate to approve
            approved_by: User making the decision
            decision: 'approved' or 'rejected'
            note: Optional review note

        Returns:
            Updated candidate dict
        """
        from sqlalchemy import text

        if decision not in ("approved", "rejected"):
            raise ValueError("decision must be 'approved' or 'rejected'")

        session = self._session

        # Get current state for audit
        result = session.execute(text("SELECT decision FROM recovery_candidates WHERE id = :id"), {"id": candidate_id})
        row = result.fetchone()
        if not row:
            raise ValueError(f"Candidate {candidate_id} not found")

        old_decision = row[0]

        # Update candidate
        session.execute(
            text(
                """
            UPDATE recovery_candidates
            SET
                decision = :decision,
                approved_by_human = :approved_by,
                approved_at = now(),
                review_note = :note
            WHERE id = :id
            """
            ),
            {
                "id": candidate_id,
                "decision": decision,
                "approved_by": approved_by,
                "note": note,
            },
        )

        # Create audit record
        session.execute(
            text(
                """
            INSERT INTO recovery_candidates_audit (
                candidate_id, action, actor, old_decision, new_decision, note
            ) VALUES (
                :candidate_id, :action, :actor, :old_decision, :new_decision, :note
            )
            """
            ),
            {
                "candidate_id": candidate_id,
                "action": decision,
                "actor": approved_by,
                "old_decision": old_decision,
                "new_decision": decision,
                "note": note,
            },
        )

        # NO COMMIT — L4 coordinator owns transaction boundary
        # Caller must commit after all operations complete

        # Return updated candidate by querying directly
        result = session.execute(
            text(
                """
            SELECT
                id, failure_match_id, suggestion, confidence,
                explain, decision, occurrence_count, last_occurrence_at,
                created_at, approved_by_human, approved_at, review_note,
                error_code, source
            FROM recovery_candidates
            WHERE id = :id
            """
            ),
            {"id": candidate_id},
        )
        row = result.fetchone()

        import json

        if row:
            return {
                "id": row[0],
                "failure_match_id": str(row[1]),
                "suggestion": row[2],
                "confidence": row[3],
                "explain": json.loads(row[4]) if isinstance(row[4], str) else (row[4] or {}),
                "decision": row[5],
                "occurrence_count": row[6],
                "last_occurrence_at": row[7].isoformat() if row[7] else None,
                "created_at": row[8].isoformat() if row[8] else None,
                "approved_by_human": row[9],
                "approved_at": row[10].isoformat() if row[10] else None,
                "review_note": row[11],
                "error_code": row[12],
                "source": row[13],
            }

        return {"id": candidate_id, "decision": decision}
