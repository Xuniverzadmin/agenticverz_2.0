# Layer: L4 — Domain Engine
# AUDIENCE: CUSTOMER
# PHASE: W4
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Controls Facade - Centralized access to control operations
# Callers: L2 controls.py API, SDK
# Allowed Imports: L4 control services, L6 (models, db)
# Forbidden Imports: L1, L2, L3, L5
# Reference: GAP-123 (Controls API)

"""
Controls Facade (L4 Domain Logic)

This facade provides the external interface for control operations.
All control APIs MUST use this facade instead of directly importing
internal control modules.

Why This Facade Exists:
- Prevents L2→L4 layer violations
- Centralizes killswitch and control logic
- Provides unified access to system controls
- Single point for audit emission

L2 API Routes (GAP-123):
- GET /api/v1/controls (list controls)
- GET /api/v1/controls/{id} (get control)
- PUT /api/v1/controls/{id} (update control)
- POST /api/v1/controls/{id}/enable (enable control)
- POST /api/v1/controls/{id}/disable (disable control)
- GET /api/v1/controls/status (overall status)

Usage:
    from app.services.controls.facade import get_controls_facade

    facade = get_controls_facade()

    # Get control status
    status = await facade.get_status(tenant_id="...")
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger("nova.services.controls.facade")


class ControlType(str, Enum):
    """Types of controls."""
    KILLSWITCH = "killswitch"
    CIRCUIT_BREAKER = "circuit_breaker"
    FEATURE_FLAG = "feature_flag"
    THROTTLE = "throttle"
    MAINTENANCE = "maintenance"


class ControlState(str, Enum):
    """Control state."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    AUTO = "auto"


@dataclass
class ControlConfig:
    """Control configuration."""
    id: str
    tenant_id: str
    name: str
    control_type: str
    state: str
    scope: str  # global, tenant, agent, etc.
    conditions: Optional[Dict[str, Any]]
    enabled_at: Optional[str]
    disabled_at: Optional[str]
    enabled_by: Optional[str]
    disabled_by: Optional[str]
    created_at: str
    updated_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "control_type": self.control_type,
            "state": self.state,
            "scope": self.scope,
            "conditions": self.conditions,
            "enabled_at": self.enabled_at,
            "disabled_at": self.disabled_at,
            "enabled_by": self.enabled_by,
            "disabled_by": self.disabled_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }


@dataclass
class ControlStatusSummary:
    """Overall control status summary."""
    tenant_id: str
    total_controls: int
    enabled_count: int
    disabled_count: int
    auto_count: int
    killswitch_active: bool
    maintenance_mode: bool
    as_of: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tenant_id": self.tenant_id,
            "total_controls": self.total_controls,
            "enabled_count": self.enabled_count,
            "disabled_count": self.disabled_count,
            "auto_count": self.auto_count,
            "killswitch_active": self.killswitch_active,
            "maintenance_mode": self.maintenance_mode,
            "as_of": self.as_of,
        }


class ControlsFacade:
    """
    Facade for control operations.

    This is the ONLY entry point for L2 APIs and SDK to interact with
    control services.

    Layer: L4 (Domain Logic)
    Callers: controls.py (L2), aos_sdk
    """

    def __init__(self):
        """Initialize facade with default controls."""
        self._controls: Dict[str, ControlConfig] = {}

    def _ensure_default_controls(self, tenant_id: str) -> None:
        """Ensure default controls exist for tenant."""
        now = datetime.now(timezone.utc)

        default_controls = [
            ("Global Killswitch", ControlType.KILLSWITCH.value, "global"),
            ("API Circuit Breaker", ControlType.CIRCUIT_BREAKER.value, "api"),
            ("Execution Throttle", ControlType.THROTTLE.value, "executions"),
            ("Maintenance Mode", ControlType.MAINTENANCE.value, "global"),
        ]

        for name, control_type, scope in default_controls:
            key = f"{tenant_id}:{name}"
            if key not in self._controls:
                self._controls[key] = ControlConfig(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    name=name,
                    control_type=control_type,
                    state=ControlState.DISABLED.value,
                    scope=scope,
                    conditions=None,
                    enabled_at=None,
                    disabled_at=None,
                    enabled_by=None,
                    disabled_by=None,
                    created_at=now.isoformat(),
                )

    # =========================================================================
    # Control Operations (GAP-123)
    # =========================================================================

    async def list_controls(
        self,
        tenant_id: str,
        control_type: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ControlConfig]:
        """
        List controls for a tenant.

        Args:
            tenant_id: Tenant ID
            control_type: Optional filter by type
            state: Optional filter by state
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of ControlConfig
        """
        self._ensure_default_controls(tenant_id)

        results = []
        for control in self._controls.values():
            if control.tenant_id != tenant_id:
                continue
            if control_type and control.control_type != control_type:
                continue
            if state and control.state != state:
                continue
            results.append(control)

        results.sort(key=lambda c: c.name)
        return results[offset:offset + limit]

    async def get_control(
        self,
        control_id: str,
        tenant_id: str,
    ) -> Optional[ControlConfig]:
        """
        Get a specific control.

        Args:
            control_id: Control ID
            tenant_id: Tenant ID for authorization

        Returns:
            ControlConfig or None if not found
        """
        self._ensure_default_controls(tenant_id)

        for control in self._controls.values():
            if control.id == control_id and control.tenant_id == tenant_id:
                return control
        return None

    async def update_control(
        self,
        control_id: str,
        tenant_id: str,
        conditions: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[ControlConfig]:
        """
        Update a control.

        Args:
            control_id: Control ID
            tenant_id: Tenant ID for authorization
            conditions: New conditions
            metadata: New metadata

        Returns:
            Updated ControlConfig or None if not found
        """
        self._ensure_default_controls(tenant_id)

        control = None
        for c in self._controls.values():
            if c.id == control_id and c.tenant_id == tenant_id:
                control = c
                break

        if not control:
            return None

        now = datetime.now(timezone.utc)

        if conditions is not None:
            control.conditions = conditions
        if metadata:
            control.metadata.update(metadata)

        control.updated_at = now.isoformat()
        return control

    async def enable_control(
        self,
        control_id: str,
        tenant_id: str,
        actor: str,
    ) -> Optional[ControlConfig]:
        """
        Enable a control.

        Args:
            control_id: Control ID
            tenant_id: Tenant ID for authorization
            actor: Who is enabling

        Returns:
            Updated ControlConfig or None if not found
        """
        self._ensure_default_controls(tenant_id)

        control = None
        for c in self._controls.values():
            if c.id == control_id and c.tenant_id == tenant_id:
                control = c
                break

        if not control:
            return None

        now = datetime.now(timezone.utc)
        control.state = ControlState.ENABLED.value
        control.enabled_at = now.isoformat()
        control.enabled_by = actor
        control.updated_at = now.isoformat()

        logger.info(
            "facade.enable_control",
            extra={"control_id": control_id, "actor": actor, "name": control.name}
        )

        return control

    async def disable_control(
        self,
        control_id: str,
        tenant_id: str,
        actor: str,
    ) -> Optional[ControlConfig]:
        """
        Disable a control.

        Args:
            control_id: Control ID
            tenant_id: Tenant ID for authorization
            actor: Who is disabling

        Returns:
            Updated ControlConfig or None if not found
        """
        self._ensure_default_controls(tenant_id)

        control = None
        for c in self._controls.values():
            if c.id == control_id and c.tenant_id == tenant_id:
                control = c
                break

        if not control:
            return None

        now = datetime.now(timezone.utc)
        control.state = ControlState.DISABLED.value
        control.disabled_at = now.isoformat()
        control.disabled_by = actor
        control.updated_at = now.isoformat()

        logger.info(
            "facade.disable_control",
            extra={"control_id": control_id, "actor": actor, "name": control.name}
        )

        return control

    async def get_status(
        self,
        tenant_id: str,
    ) -> ControlStatusSummary:
        """
        Get overall control status.

        Args:
            tenant_id: Tenant ID

        Returns:
            ControlStatusSummary
        """
        self._ensure_default_controls(tenant_id)

        now = datetime.now(timezone.utc)
        total = 0
        enabled = 0
        disabled = 0
        auto = 0
        killswitch_active = False
        maintenance_mode = False

        for control in self._controls.values():
            if control.tenant_id != tenant_id:
                continue
            total += 1
            if control.state == ControlState.ENABLED.value:
                enabled += 1
                if control.control_type == ControlType.KILLSWITCH.value:
                    killswitch_active = True
                if control.control_type == ControlType.MAINTENANCE.value:
                    maintenance_mode = True
            elif control.state == ControlState.DISABLED.value:
                disabled += 1
            else:
                auto += 1

        return ControlStatusSummary(
            tenant_id=tenant_id,
            total_controls=total,
            enabled_count=enabled,
            disabled_count=disabled,
            auto_count=auto,
            killswitch_active=killswitch_active,
            maintenance_mode=maintenance_mode,
            as_of=now.isoformat(),
        )


# =============================================================================
# Module-level singleton accessor
# =============================================================================

_facade_instance: Optional[ControlsFacade] = None


def get_controls_facade() -> ControlsFacade:
    """
    Get the controls facade instance.

    This is the recommended way to access control operations
    from L2 APIs and the SDK.

    Returns:
        ControlsFacade instance
    """
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = ControlsFacade()
    return _facade_instance
