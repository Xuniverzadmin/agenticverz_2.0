# capability_id: CAP-018
# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api (via L2 proxy endpoints)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: api_keys, tenants, killswitch_state, default_guardrails, proxy_calls, incidents
#   Writes: api_keys (usage), proxy_calls
# Database:
#   Scope: domain (integrations/proxy)
#   Models: api_keys, tenants, killswitch_state, default_guardrails, proxy_calls, incidents
# Role: OpenAI proxy persistence driver — pure DB operations for v1_proxy.py
# Callers: L2 proxy (hoc/api/cus/integrations/v1_proxy.py)
# Allowed Imports: L6, L7 (models), sqlalchemy
# Reference: PIN-484 HOC Layer Topology V2.0.0
# artifact_class: CODE

"""Proxy Driver - Pure persistence layer for OpenAI proxy operations.

L6 driver for proxy-related database operations.

Pure persistence - no business logic, no HTTP calls.
All methods accept primitive parameters and return raw facts.

Encapsulates all session.execute() calls that were previously in v1_proxy.py (L2).
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlmodel import Session

logger = logging.getLogger(__name__)


# =============================================================================
# Data Transfer Objects (Frozen Dataclasses)
# =============================================================================


@dataclass(frozen=True)
class ApiKeyRow:
    """Immutable DTO for API key database row."""

    id: str
    tenant_id: str
    key_hash: str
    name: Optional[str]
    status: str
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    total_requests: int
    created_at: datetime
    # Include full row data as dict for backwards compatibility
    raw: Dict[str, Any]


@dataclass(frozen=True)
class TenantRow:
    """Immutable DTO for tenant database row."""

    id: str
    name: Optional[str]
    status: Optional[str]
    created_at: Optional[datetime]
    # Include full row data as dict for backwards compatibility
    raw: Dict[str, Any]


@dataclass(frozen=True)
class KillSwitchStateRow:
    """Immutable DTO for killswitch state database row."""

    frozen_at: Optional[datetime]
    freeze_reason: Optional[str]


@dataclass(frozen=True)
class GuardrailRow:
    """Immutable DTO for default guardrail database row."""

    id: str
    name: str
    category: str
    rule_type: str
    rule_config_json: str
    action: str
    is_enabled: bool
    priority: int


@dataclass(frozen=True)
class LatencyStats:
    """Immutable DTO for latency statistics."""

    latencies: List[int]
    p95_ms: Optional[int]
    calls_count: int


@dataclass(frozen=True)
class IncidentRow:
    """Immutable DTO for incident database row."""

    id: str
    title: Optional[str]
    severity: Optional[str]
    created_at: Optional[datetime]
    status: Optional[str]


# =============================================================================
# Proxy Driver (L6 - Pure CRUD)
# =============================================================================


class ProxyDriver:
    """L6 driver for OpenAI proxy persistence.

    Pure CRUD operations only. No business logic.

    Provides all database operations needed by v1_proxy.py:
    - API key lookup and usage recording
    - Tenant lookup
    - KillSwitch state checks
    - Guardrails fetch
    - Proxy call logging
    - Status endpoint queries (latency stats, blocked counts, incidents)
    """

    def __init__(self, session: Session):
        """Initialize driver with sync session.

        Args:
            session: SQLModel sync session for DB operations.
        """
        self._session = session

    # =========================================================================
    # API Key Operations
    # =========================================================================

    def get_api_key_by_hash(self, key_hash: str) -> Optional[ApiKeyRow]:
        """Get API key by hash.

        Args:
            key_hash: SHA256 hash of the API key.

        Returns:
            ApiKeyRow or None if not found.
        """
        result = self._session.execute(
            text("SELECT * FROM api_keys WHERE key_hash = :key_hash"),
            {"key_hash": key_hash},
        )
        row = result.mappings().first()
        if not row:
            return None

        return ApiKeyRow(
            id=row["id"],
            tenant_id=row["tenant_id"],
            key_hash=row["key_hash"],
            name=row.get("name"),
            status=row["status"],
            expires_at=row.get("expires_at"),
            last_used_at=row.get("last_used_at"),
            total_requests=row.get("total_requests", 0),
            created_at=row.get("created_at"),
            raw=dict(row),
        )

    def get_api_key_id_and_tenant(self, key_hash: str) -> Optional[Dict[str, str]]:
        """Get API key ID and tenant ID by hash (lightweight lookup for status endpoint).

        Args:
            key_hash: SHA256 hash of the API key.

        Returns:
            Dict with id and tenant_id, or None if not found.
        """
        result = self._session.execute(
            text("SELECT id, tenant_id FROM api_keys WHERE key_hash = :key_hash"),
            {"key_hash": key_hash},
        )
        row = result.mappings().first()
        if not row:
            return None

        return {"id": row["id"], "tenant_id": row["tenant_id"]}

    def record_api_key_usage(self, key_id: str, now: datetime) -> None:
        """Record API key usage (last_used_at and increment total_requests).

        Args:
            key_id: API key ID.
            now: Current timestamp.
        """
        self._session.execute(
            text(
                "UPDATE api_keys SET last_used_at = :now, total_requests = total_requests + 1 "
                "WHERE id = :key_id"
            ),
            {"now": now, "key_id": key_id},
        )
        # L6 does NOT commit — L4 handler owns transaction boundary

    # =========================================================================
    # Tenant Operations
    # =========================================================================

    def get_tenant_by_id(self, tenant_id: str) -> Optional[TenantRow]:
        """Get tenant by ID.

        Args:
            tenant_id: Tenant ID.

        Returns:
            TenantRow or None if not found.
        """
        result = self._session.execute(
            text("SELECT * FROM tenants WHERE id = :tenant_id"),
            {"tenant_id": tenant_id},
        )
        row = result.mappings().first()
        if not row:
            return None

        return TenantRow(
            id=row["id"],
            name=row.get("name"),
            status=row.get("status"),
            created_at=row.get("created_at"),
            raw=dict(row),
        )

    # =========================================================================
    # KillSwitch Operations
    # =========================================================================

    def get_killswitch_state(
        self, entity_type: str, entity_id: str
    ) -> Optional[KillSwitchStateRow]:
        """Get killswitch state for an entity.

        Args:
            entity_type: Entity type ('tenant' or 'key').
            entity_id: Entity ID.

        Returns:
            KillSwitchStateRow if frozen, None if not frozen.
        """
        result = self._session.execute(
            text(
                "SELECT frozen_at, freeze_reason FROM killswitch_state "
                "WHERE entity_type = :entity_type AND entity_id = :entity_id AND is_frozen = true"
            ),
            {"entity_type": entity_type, "entity_id": entity_id},
        )
        row = result.mappings().first()
        if not row:
            return None

        return KillSwitchStateRow(
            frozen_at=row.get("frozen_at"),
            freeze_reason=row.get("freeze_reason"),
        )

    # =========================================================================
    # Guardrail Operations
    # =========================================================================

    def get_enabled_guardrails(self) -> List[GuardrailRow]:
        """Get all enabled guardrails ordered by priority.

        Returns:
            List of GuardrailRow.
        """
        result = self._session.execute(
            text(
                "SELECT id, name, category, rule_type, rule_config_json, action, is_enabled, priority "
                "FROM default_guardrails WHERE is_enabled = true ORDER BY priority"
            ),
        )
        rows = result.mappings().all()

        return [
            GuardrailRow(
                id=row["id"],
                name=row["name"],
                category=row["category"],
                rule_type=row["rule_type"],
                rule_config_json=row["rule_config_json"],
                action=row["action"],
                is_enabled=row["is_enabled"],
                priority=row["priority"],
            )
            for row in rows
        ]

    # =========================================================================
    # Proxy Call Logging
    # =========================================================================

    def log_proxy_call(
        self,
        call_id: str,
        tenant_id: str,
        api_key_id: str,
        user_id: Optional[str],
        endpoint: str,
        model: str,
        request_hash: str,
        request_json: str,
        response_hash: Optional[str],
        response_json: Optional[str],
        status_code: int,
        error_code: Optional[str],
        input_tokens: int,
        output_tokens: int,
        cost_cents: Decimal,
        policy_decisions_json: str,
        was_blocked: bool,
        block_reason: Optional[str],
        latency_ms: int,
        upstream_latency_ms: Optional[int],
        replay_eligible: bool,
        created_at: datetime,
    ) -> None:
        """Insert a proxy call record.

        Args:
            All fields for the proxy_calls table.
        """
        self._session.execute(
            text(
                "INSERT INTO proxy_calls "
                "(id, tenant_id, api_key_id, user_id, endpoint, model, request_hash, request_json, "
                "response_hash, response_json, status_code, error_code, input_tokens, output_tokens, "
                "cost_cents, policy_decisions_json, was_blocked, block_reason, latency_ms, "
                "upstream_latency_ms, replay_eligible, created_at) "
                "VALUES (:id, :tenant_id, :api_key_id, :user_id, :endpoint, :model, :request_hash, "
                ":request_json, :response_hash, :response_json, :status_code, :error_code, "
                ":input_tokens, :output_tokens, :cost_cents, :policy_decisions_json, :was_blocked, "
                ":block_reason, :latency_ms, :upstream_latency_ms, :replay_eligible, :created_at)"
            ),
            {
                "id": call_id,
                "tenant_id": tenant_id,
                "api_key_id": api_key_id,
                "user_id": user_id,
                "endpoint": endpoint,
                "model": model,
                "request_hash": request_hash,
                "request_json": request_json,
                "response_hash": response_hash,
                "response_json": response_json,
                "status_code": status_code,
                "error_code": error_code,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_cents": cost_cents,
                "policy_decisions_json": policy_decisions_json,
                "was_blocked": was_blocked,
                "block_reason": block_reason,
                "latency_ms": latency_ms,
                "upstream_latency_ms": upstream_latency_ms,
                "replay_eligible": replay_eligible,
                "created_at": created_at,
            },
        )
        # L6 does NOT commit — L4 handler owns transaction boundary

    # =========================================================================
    # Status Endpoint Operations
    # =========================================================================

    def get_latency_stats(
        self,
        since: datetime,
        tenant_id: Optional[str] = None,
        limit: int = 1000,
    ) -> LatencyStats:
        """Get latency statistics from recent proxy calls.

        Args:
            since: Fetch calls since this timestamp.
            tenant_id: Optional tenant ID filter.
            limit: Max rows to fetch.

        Returns:
            LatencyStats with latencies list, p95, and count.
        """
        if tenant_id:
            result = self._session.execute(
                text(
                    "SELECT latency_ms FROM proxy_calls "
                    "WHERE tenant_id = :tenant_id AND created_at >= :since "
                    "ORDER BY created_at DESC LIMIT :limit"
                ),
                {"tenant_id": tenant_id, "since": since, "limit": limit},
            )
        else:
            result = self._session.execute(
                text(
                    "SELECT latency_ms FROM proxy_calls "
                    "WHERE created_at >= :since "
                    "ORDER BY created_at DESC LIMIT :limit"
                ),
                {"since": since, "limit": limit},
            )

        latencies = [
            row["latency_ms"]
            for row in result.mappings().all()
            if row["latency_ms"]
        ]

        p95_ms = None
        if latencies:
            latencies.sort()
            p95_idx = int(len(latencies) * 0.95)
            p95_ms = latencies[p95_idx] if p95_idx < len(latencies) else latencies[-1]

        return LatencyStats(
            latencies=latencies,
            p95_ms=p95_ms,
            calls_count=len(latencies),
        )

    def get_blocked_call_count(
        self,
        since: datetime,
        tenant_id: Optional[str] = None,
    ) -> int:
        """Get count of blocked proxy calls.

        Args:
            since: Count calls since this timestamp.
            tenant_id: Optional tenant ID filter.

        Returns:
            Count of blocked calls.
        """
        if tenant_id:
            result = self._session.execute(
                text(
                    "SELECT COUNT(*) FROM proxy_calls "
                    "WHERE tenant_id = :tenant_id AND was_blocked = true AND created_at >= :since"
                ),
                {"tenant_id": tenant_id, "since": since},
            )
        else:
            result = self._session.execute(
                text(
                    "SELECT COUNT(*) FROM proxy_calls "
                    "WHERE was_blocked = true AND created_at >= :since"
                ),
                {"since": since},
            )
        return result.scalar() or 0

    def get_last_incident(
        self, tenant_id: Optional[str] = None
    ) -> Optional[IncidentRow]:
        """Get most recent incident.

        Args:
            tenant_id: Optional tenant ID filter.

        Returns:
            IncidentRow or None if no incidents found.
        """
        if tenant_id:
            result = self._session.execute(
                text(
                    "SELECT id, title, severity, created_at, status FROM incidents "
                    "WHERE tenant_id = :tenant_id ORDER BY created_at DESC LIMIT 1"
                ),
                {"tenant_id": tenant_id},
            )
        else:
            result = self._session.execute(
                text(
                    "SELECT id, title, severity, created_at, status FROM incidents "
                    "ORDER BY created_at DESC LIMIT 1"
                ),
            )

        row = result.mappings().first()
        if not row:
            return None

        return IncidentRow(
            id=row["id"],
            title=row.get("title"),
            severity=row.get("severity"),
            created_at=row.get("created_at"),
            status=row.get("status"),
        )


# =============================================================================
# Factory Function
# =============================================================================


def get_proxy_driver(session: Session) -> ProxyDriver:
    """Get ProxyDriver instance.

    Args:
        session: SQLModel sync session.

    Returns:
        ProxyDriver instance.
    """
    return ProxyDriver(session=session)
