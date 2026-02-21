# capability_id: CAP-009
# Layer: L6 -- Driver
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: Data access for killswitch read/write operations (v1_killswitch.py)
# Callers: L4 KillswitchHandler (via registry)
# Allowed Imports: L7 (models), sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-511 (services boundary), L2-L4-L5 topology
#
# GOVERNANCE NOTE:
# This L6 driver provides pure data access for killswitch operations.
# NO business logic - only DB reads and ORM <-> DTO transformation.
# Eliminates session.execute() from L2 v1_killswitch.py.

"""
Killswitch Operations Driver (L6)

Pure data access layer for killswitch endpoint operations.
Provides read operations for:
- Tenant verification
- API key verification
- Killswitch state queries
- Default guardrails listing
- Incident listing and detail
- Incident events (timeline)
- Proxy call lookup

Write operations delegate to existing GuardWriteDriver.

Reference: PIN-511 (no HOC <-> services imports)
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel
from sqlalchemy import and_, desc, select, text
from sqlmodel import Session

from app.models.killswitch import (
    DefaultGuardrail,
    Incident,
    IncidentEvent,
    KillSwitchState,
    ProxyCall,
)


# =============================================================================
# L6 DTOs (Domain-level data transfer objects)
# =============================================================================


class TenantInfoDTO(BaseModel):
    """Minimal tenant info for existence check."""
    id: str
    name: Optional[str] = None


class ApiKeyInfoDTO(BaseModel):
    """API key info for existence check."""
    id: str
    tenant_id: str


class KillswitchStateDTO(BaseModel):
    """Killswitch state data transfer object."""
    id: str
    entity_type: str
    entity_id: str
    tenant_id: str
    is_frozen: bool
    frozen_at: Optional[datetime] = None
    frozen_by: Optional[str] = None
    freeze_reason: Optional[str] = None
    auto_triggered: bool = False
    trigger_type: Optional[str] = None


class GuardrailDTO(BaseModel):
    """Default guardrail summary."""
    id: str
    name: str
    description: Optional[str] = None
    category: str
    action: str
    is_enabled: bool
    priority: int


class IncidentSummaryDTO(BaseModel):
    """Incident list item."""
    id: str
    title: str
    severity: str
    status: str
    trigger_type: str
    calls_affected: int
    cost_delta_cents: float
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None


class IncidentDetailDTO(BaseModel):
    """Full incident detail with timeline."""
    id: str
    title: str
    severity: str
    status: str
    trigger_type: str
    trigger_value: Optional[str] = None
    calls_affected: int
    cost_delta_cents: float
    error_rate: Optional[float] = None
    auto_action: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None


class IncidentEventDTO(BaseModel):
    """Timeline event."""
    id: str
    incident_id: str
    event_type: str
    description: str
    created_at: datetime
    data: Optional[Dict[str, Any]] = None


class ProxyCallDTO(BaseModel):
    """Proxy call data for replay/detail."""
    id: str
    tenant_id: str
    endpoint: str
    model: Optional[str] = None
    request_hash: Optional[str] = None
    request_json: Optional[str] = None
    response_json: Optional[str] = None
    status_code: Optional[int] = None
    error_code: Optional[str] = None
    was_blocked: bool = False
    block_reason: Optional[str] = None
    policy_decisions_json: Optional[str] = None
    cost_cents: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: Optional[int] = None
    replay_eligible: bool = False
    created_at: Optional[datetime] = None


# =============================================================================
# L6 Driver Class
# =============================================================================


class KillswitchOpsDriver:
    """
    L6 driver for killswitch endpoint operations.

    Pure data access - no business logic.
    Sync operations for use with sync session from FastAPI.
    """

    def __init__(self, session: Session):
        """Initialize driver with session."""
        self._session = session

    # =========================================================================
    # Entity Verification
    # =========================================================================

    def verify_tenant_exists(self, tenant_id: str) -> Optional[TenantInfoDTO]:
        """
        Verify a tenant exists and return basic info.

        Returns None if tenant not found.
        """
        result = self._session.execute(
            text("SELECT id, name FROM tenants WHERE id = :id"),
            {"id": tenant_id},
        )
        row = result.mappings().first()
        if not row:
            return None
        return TenantInfoDTO(id=row["id"], name=row.get("name"))

    def verify_api_key_exists(self, key_id: str) -> Optional[ApiKeyInfoDTO]:
        """
        Verify an API key exists and return basic info.

        Returns None if key not found.
        """
        result = self._session.execute(
            text("SELECT id, tenant_id FROM api_keys WHERE id = :id"),
            {"id": key_id},
        )
        row = result.mappings().first()
        if not row:
            return None
        return ApiKeyInfoDTO(id=row["id"], tenant_id=row["tenant_id"])

    # =========================================================================
    # Killswitch State Queries
    # =========================================================================

    def get_killswitch_state(
        self,
        entity_type: str,
        entity_id: str,
    ) -> Optional[KillswitchStateDTO]:
        """
        Get killswitch state for an entity.

        Returns None if no state record exists.
        """
        result = self._session.execute(
            text(
                "SELECT * FROM kill_switch_states "
                "WHERE entity_type = :etype AND entity_id = :eid"
            ),
            {"etype": entity_type, "eid": entity_id},
        )
        row = result.mappings().first()
        if not row:
            return None
        return KillswitchStateDTO(
            id=row["id"],
            entity_type=row["entity_type"],
            entity_id=row["entity_id"],
            tenant_id=row["tenant_id"],
            is_frozen=row["is_frozen"],
            frozen_at=row["frozen_at"],
            frozen_by=row["frozen_by"],
            freeze_reason=row["freeze_reason"],
            auto_triggered=row["auto_triggered"] or False,
            trigger_type=row["trigger_type"],
        )

    def get_key_states_for_tenant(
        self,
        tenant_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get all key killswitch states for a tenant.

        Returns list of raw state dicts for L2 formatting.
        """
        result = self._session.execute(
            text(
                "SELECT * FROM kill_switch_states "
                "WHERE entity_type = :etype AND tenant_id = :tid"
            ),
            {"etype": "key", "tid": tenant_id},
        )
        return [dict(r) for r in result.mappings().all()]

    # =========================================================================
    # Guardrails
    # =========================================================================

    def list_active_guardrails(self) -> List[GuardrailDTO]:
        """
        Get all active (enabled) default guardrails ordered by priority.
        """
        result = self._session.execute(
            text(
                "SELECT * FROM default_guardrails "
                "WHERE is_enabled = true ORDER BY priority"
            ),
        )
        rows = result.mappings().all()
        return [
            GuardrailDTO(
                id=g["id"],
                name=g["name"],
                description=g["description"],
                category=g["category"],
                action=g["action"],
                is_enabled=g["is_enabled"],
                priority=g["priority"],
            )
            for g in rows
        ]

    # =========================================================================
    # Incidents
    # =========================================================================

    def list_incidents(
        self,
        tenant_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[IncidentSummaryDTO]:
        """
        List incidents for a tenant with optional status filter.
        """
        query = "SELECT * FROM incidents WHERE tenant_id = :tenant_id"
        params: Dict[str, Any] = {"tenant_id": tenant_id}

        if status:
            query += " AND status = :status"
            params["status"] = status

        query += " ORDER BY created_at DESC OFFSET :offset LIMIT :lim"
        params["offset"] = offset
        params["lim"] = limit

        result = self._session.execute(text(query), params)
        incidents = result.mappings().all()

        return [
            IncidentSummaryDTO(
                id=i["id"],
                title=i["title"],
                severity=i["severity"],
                status=i["status"],
                trigger_type=i["trigger_type"],
                calls_affected=i["calls_affected"],
                cost_delta_cents=float(i["cost_delta_cents"]),
                started_at=i["started_at"],
                ended_at=i["ended_at"],
                duration_seconds=i["duration_seconds"],
            )
            for i in incidents
        ]

    def get_incident_detail(
        self,
        incident_id: str,
    ) -> Optional[IncidentDetailDTO]:
        """
        Get full incident detail.

        Returns None if incident not found.
        """
        result = self._session.execute(
            text("SELECT * FROM incidents WHERE id = :id"),
            {"id": incident_id},
        )
        incident = result.mappings().first()

        if not incident:
            return None

        return IncidentDetailDTO(
            id=incident["id"],
            title=incident["title"],
            severity=incident["severity"],
            status=incident["status"],
            trigger_type=incident["trigger_type"],
            trigger_value=incident["trigger_value"],
            calls_affected=incident["calls_affected"],
            cost_delta_cents=float(incident["cost_delta_cents"]),
            error_rate=float(incident["error_rate"]) if incident["error_rate"] else None,
            auto_action=incident["auto_action"],
            started_at=incident["started_at"],
            ended_at=incident["ended_at"],
            duration_seconds=incident["duration_seconds"],
        )

    def get_incident_events(
        self,
        incident_id: str,
    ) -> List[IncidentEventDTO]:
        """
        Get timeline events for an incident.
        """
        result = self._session.execute(
            text(
                "SELECT * FROM incident_events "
                "WHERE incident_id = :incident_id ORDER BY created_at"
            ),
            {"incident_id": incident_id},
        )
        events = result.mappings().all()

        return [
            IncidentEventDTO(
                id=e["id"],
                incident_id=e["incident_id"],
                event_type=e["event_type"],
                description=e["description"],
                created_at=e["created_at"],
                data=self._parse_event_data(e.get("data") or e.get("event_data")),
            )
            for e in events
        ]

    def _parse_event_data(self, raw_data: Any) -> Optional[Dict[str, Any]]:
        """Parse event data from JSON string or return as-is."""
        import json

        if raw_data is None:
            return None
        if isinstance(raw_data, dict):
            return raw_data
        try:
            return json.loads(raw_data)
        except (json.JSONDecodeError, TypeError):
            return None

    # =========================================================================
    # Proxy Calls
    # =========================================================================

    def get_proxy_call(
        self,
        call_id: str,
    ) -> Optional[ProxyCallDTO]:
        """
        Get proxy call by ID for replay or detail view.

        Returns None if call not found.
        """
        result = self._session.execute(
            text("SELECT * FROM proxy_calls WHERE id = :id"),
            {"id": call_id},
        )
        call = result.mappings().first()

        if not call:
            return None

        return ProxyCallDTO(
            id=call["id"],
            tenant_id=call["tenant_id"],
            endpoint=call["endpoint"],
            model=call["model"],
            request_hash=call["request_hash"],
            request_json=call["request_json"],
            response_json=call["response_json"],
            status_code=call["status_code"],
            error_code=call["error_code"],
            was_blocked=call["was_blocked"] or False,
            block_reason=call["block_reason"],
            policy_decisions_json=call.get("policy_decisions_json"),
            cost_cents=float(call["cost_cents"]) if call["cost_cents"] else 0.0,
            input_tokens=call["input_tokens"] or 0,
            output_tokens=call["output_tokens"] or 0,
            latency_ms=call["latency_ms"],
            replay_eligible=call["replay_eligible"] or False,
            created_at=call["created_at"],
        )


# =============================================================================
# Factory Function
# =============================================================================


def get_killswitch_ops_driver(session: Session) -> KillswitchOpsDriver:
    """
    Get KillswitchOpsDriver instance.

    Args:
        session: SQLModel session from FastAPI DI

    Returns:
        KillswitchOpsDriver instance
    """
    return KillswitchOpsDriver(session)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "KillswitchOpsDriver",
    "get_killswitch_ops_driver",
    # DTOs
    "TenantInfoDTO",
    "ApiKeyInfoDTO",
    "KillswitchStateDTO",
    "GuardrailDTO",
    "IncidentSummaryDTO",
    "IncidentDetailDTO",
    "IncidentEventDTO",
    "ProxyCallDTO",
]
