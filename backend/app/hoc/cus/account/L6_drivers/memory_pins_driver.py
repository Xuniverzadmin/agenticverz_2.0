# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: system.memory_pins, system.memory_audit
#   Writes: system.memory_pins, system.memory_audit (via session, NO COMMIT)
# Database:
#   Scope: domain (account)
#   Models: system.memory_pins (raw SQL — no ORM model)
# Role: Memory pins data access — pure DB operations for key-value storage
# Callers: memory_pins_engine.py (L5)
# Allowed Imports: L7 (models), sqlalchemy
# Forbidden: session.commit() — L4 coordinator owns transaction boundary
# artifact_class: CODE

"""
Memory Pins Driver (L6)

Pure data access layer for memory pin operations.
Driver instances are session-bound and return raw data.
No business logic — validation, feature flags, and metrics belong in L5.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("nova.hoc.account.L6.memory_pins_driver")


@dataclass
class MemoryPinRow:
    """Snapshot of a memory pin row."""

    id: int
    tenant_id: str
    key: str
    value: Dict[str, Any]
    source: str
    created_at: datetime
    updated_at: datetime
    ttl_seconds: Optional[int]
    expires_at: Optional[datetime]


class MemoryPinsDriver:
    """Pure data access for system.memory_pins table."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_pin(
        self,
        *,
        tenant_id: str,
        key: str,
        value: Dict[str, Any],
        source: str,
        ttl_seconds: Optional[int],
    ) -> MemoryPinRow:
        """Insert or update a memory pin. Returns the resulting row."""
        value_json = json.dumps(value)
        result = await self._session.execute(
            text(
                """
                INSERT INTO system.memory_pins (tenant_id, key, value, source, ttl_seconds)
                VALUES (:tenant_id, :key, CAST(:value AS jsonb), :source, :ttl_seconds)
                ON CONFLICT (tenant_id, key)
                DO UPDATE SET
                    value = EXCLUDED.value,
                    source = EXCLUDED.source,
                    ttl_seconds = EXCLUDED.ttl_seconds,
                    updated_at = now()
                RETURNING id, tenant_id, key, value, source, created_at, updated_at, ttl_seconds, expires_at
                """
            ),
            {
                "tenant_id": tenant_id,
                "key": key,
                "value": value_json,
                "source": source,
                "ttl_seconds": ttl_seconds,
            },
        )
        row = result.fetchone()
        if not row:
            raise RuntimeError("Upsert returned no row")
        return self._row_to_snapshot(row)

    async def get_pin(
        self,
        *,
        tenant_id: str,
        key: str,
    ) -> Optional[MemoryPinRow]:
        """Get a single pin by (tenant_id, key). Returns None if not found or expired."""
        result = await self._session.execute(
            text(
                """
                SELECT id, tenant_id, key, value, source, created_at, updated_at, ttl_seconds, expires_at
                FROM system.memory_pins
                WHERE tenant_id = :tenant_id
                  AND key = :key
                  AND (expires_at IS NULL OR expires_at > now())
                """
            ),
            {"tenant_id": tenant_id, "key": key},
        )
        row = result.fetchone()
        if not row:
            return None
        return self._row_to_snapshot(row)

    async def list_pins(
        self,
        *,
        tenant_id: str,
        prefix: Optional[str] = None,
        include_expired: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[List[MemoryPinRow], int]:
        """List pins for a tenant. Returns (pins, total_count)."""
        where_clauses = ["tenant_id = :tenant_id"]
        params: Dict[str, Any] = {
            "tenant_id": tenant_id,
            "limit": limit,
            "offset": offset,
        }

        if prefix:
            where_clauses.append("key LIKE :prefix")
            params["prefix"] = f"{prefix}%"

        if not include_expired:
            where_clauses.append("(expires_at IS NULL OR expires_at > now())")

        where_sql = " AND ".join(where_clauses)

        count_result = await self._session.execute(
            text(f"SELECT COUNT(*) FROM system.memory_pins WHERE {where_sql}"),
            params,
        )
        total = count_result.scalar() or 0

        result = await self._session.execute(
            text(
                f"""
                SELECT id, tenant_id, key, value, source, created_at, updated_at, ttl_seconds, expires_at
                FROM system.memory_pins
                WHERE {where_sql}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            params,
        )

        pins = [self._row_to_snapshot(row) for row in result]
        return pins, total

    async def delete_pin(
        self,
        *,
        tenant_id: str,
        key: str,
    ) -> bool:
        """Delete a pin. Returns True if deleted, False if not found."""
        result = await self._session.execute(
            text(
                """
                DELETE FROM system.memory_pins
                WHERE tenant_id = :tenant_id AND key = :key
                RETURNING id
                """
            ),
            {"tenant_id": tenant_id, "key": key},
        )
        deleted_row = result.fetchone()
        return deleted_row is not None

    async def cleanup_expired(
        self,
        *,
        tenant_id: Optional[str] = None,
    ) -> int:
        """Delete expired pins. Returns count of deleted rows."""
        if tenant_id:
            result = await self._session.execute(
                text(
                    """
                    DELETE FROM system.memory_pins
                    WHERE tenant_id = :tenant_id
                      AND expires_at IS NOT NULL
                      AND expires_at < now()
                    RETURNING id
                    """
                ),
                {"tenant_id": tenant_id},
            )
        else:
            result = await self._session.execute(
                text(
                    """
                    DELETE FROM system.memory_pins
                    WHERE expires_at IS NOT NULL
                      AND expires_at < now()
                    RETURNING id
                    """
                )
            )
        return len(result.fetchall())

    async def write_audit(
        self,
        *,
        operation: str,
        tenant_id: str,
        key: str,
        success: bool,
        latency_ms: float,
        agent_id: Optional[str] = None,
        source: Optional[str] = None,
        cache_hit: bool = False,
        error_message: Optional[str] = None,
        old_value_hash: Optional[str] = None,
        new_value_hash: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Write an audit entry to system.memory_audit."""
        try:
            await self._session.execute(
                text(
                    """
                    INSERT INTO system.memory_audit
                        (operation, tenant_id, key, agent_id, source, cache_hit,
                         latency_ms, success, error_message, old_value_hash, new_value_hash, extra)
                    VALUES
                        (:operation, :tenant_id, :key, :agent_id, :source, :cache_hit,
                         :latency_ms, :success, :error_message, :old_value_hash, :new_value_hash, :extra)
                    """
                ),
                {
                    "operation": operation,
                    "tenant_id": tenant_id,
                    "key": key,
                    "agent_id": agent_id,
                    "source": source,
                    "cache_hit": cache_hit,
                    "latency_ms": latency_ms,
                    "success": success,
                    "error_message": error_message,
                    "old_value_hash": old_value_hash,
                    "new_value_hash": new_value_hash,
                    "extra": json.dumps(extra) if extra else "{}",
                },
            )
        except Exception as e:
            logger.warning(f"Failed to write memory audit: {e}")

    @staticmethod
    def _row_to_snapshot(row: Any) -> MemoryPinRow:
        """Convert a DB row to a MemoryPinRow snapshot."""
        value = row.value
        if isinstance(value, str):
            value = json.loads(value)
        return MemoryPinRow(
            id=row.id,
            tenant_id=row.tenant_id,
            key=row.key,
            value=value,
            source=row.source,
            created_at=row.created_at,
            updated_at=row.updated_at,
            ttl_seconds=row.ttl_seconds,
            expires_at=row.expires_at,
        )

def get_memory_pins_driver(session: AsyncSession) -> MemoryPinsDriver:
    """Create a session-bound MemoryPinsDriver instance."""
    return MemoryPinsDriver(session)
