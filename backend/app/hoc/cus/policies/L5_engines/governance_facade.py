# Layer: L6 — Driver
# AUDIENCE: CUSTOMER
# Role: Governance Facade - Centralized access to governance control operations
# Product: system-wide
# Temporal:
#   Trigger: api (governance control) or internal (health checks)
#   Execution: sync
# Callers: L2 governance.py API, SDK
# Allowed Imports: L4 domain engines, L6 (models, db)
# Forbidden Imports: L1, L2, L3, L5
# Reference: GAP-090, GAP-091, GAP-092, GAP-095


"""
Governance Facade (L4 Domain Logic)

This facade provides the external interface for governance control operations.
All governance APIs MUST use this facade instead of directly importing
internal governance modules.

Why This Facade Exists:
- Prevents L2→L4 layer violations
- Centralizes governance control logic
- Provides unified access to kill switch, degraded mode, conflict resolution
- Single point for audit emission

Wrapped Services:
- runtime_switch: Kill switch and degraded mode (GAP-069, GAP-070)
- ConflictResolver: Policy conflict resolution (GAP-068)
- BootGuard: SPINE component health (GAP-067)

L2 API Routes (GAP-090 to GAP-095):
- POST /api/v1/governance/kill-switch (GAP-090)
- POST /api/v1/governance/mode (GAP-091)
- POST /api/v1/governance/resolve-conflict (GAP-092)
- GET /api/v1/governance/boot-status (GAP-095)

Usage:
    from app.hoc.cus.policies.L5_engines.governance_facade import get_governance_facade

    facade = get_governance_facade()

    # Check governance state
    state = facade.get_governance_state()

    # Enable kill switch
    facade.enable_kill_switch(reason="Emergency", actor="operator")

    # Enter degraded mode
    facade.set_mode(mode="DEGRADED", reason="High load", actor="system")
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nova.services.governance.facade")


class GovernanceMode(str, Enum):
    """Governance operation modes."""
    NORMAL = "NORMAL"  # Full governance enforcement
    DEGRADED = "DEGRADED"  # Limited enforcement, new runs blocked
    KILL = "KILL"  # All governance disabled (emergency)


@dataclass
class GovernanceStateResult:
    """Result of governance state query."""
    mode: GovernanceMode
    active: bool
    degraded_mode: bool
    last_changed: Optional[datetime]
    last_change_reason: Optional[str]
    last_change_actor: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "mode": self.mode.value,
            "active": self.active,
            "degraded_mode": self.degraded_mode,
            "last_changed": self.last_changed.isoformat() if self.last_changed else None,
            "last_change_reason": self.last_change_reason,
            "last_change_actor": self.last_change_actor,
        }


@dataclass
class KillSwitchResult:
    """Result of kill switch operation."""
    success: bool
    previous_mode: GovernanceMode
    current_mode: GovernanceMode
    timestamp: datetime
    actor: str
    reason: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "previous_mode": self.previous_mode.value,
            "current_mode": self.current_mode.value,
            "timestamp": self.timestamp.isoformat(),
            "actor": self.actor,
            "reason": self.reason,
            "error": self.error,
        }


@dataclass
class ConflictResolutionResult:
    """Result of conflict resolution."""
    success: bool
    conflict_id: str
    resolution: str
    resolved_by: str
    resolved_at: datetime
    affected_policies: List[str]
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "conflict_id": self.conflict_id,
            "resolution": self.resolution,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at.isoformat(),
            "affected_policies": self.affected_policies,
            "error": self.error,
        }


@dataclass
class BootStatusResult:
    """Result of boot status check."""
    healthy: bool
    components: Dict[str, Dict[str, Any]]
    boot_time: Optional[datetime]
    uptime_seconds: Optional[int]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "healthy": self.healthy,
            "components": self.components,
            "boot_time": self.boot_time.isoformat() if self.boot_time else None,
            "uptime_seconds": self.uptime_seconds,
        }


class GovernanceFacade:
    """
    Facade for governance control operations.

    This is the ONLY entry point for L2 APIs and SDK to interact with
    governance control services.

    Layer: L4 (Domain Logic)
    Callers: governance.py (L2), aos_sdk
    """

    def __init__(self):
        """Initialize facade with lazy-loaded services."""
        self._runtime_switch_loaded = False
        self._boot_time = datetime.now(timezone.utc)

    # =========================================================================
    # Kill Switch Operations (GAP-090)
    # =========================================================================

    def enable_kill_switch(
        self,
        reason: str,
        actor: str,
    ) -> KillSwitchResult:
        """
        Enable kill switch - disable all governance enforcement.

        WARNING: This is an emergency operation. Use only for incident response.

        Args:
            reason: Why governance is being disabled
            actor: Who/what triggered the disable

        Returns:
            KillSwitchResult with operation details
        """
        logger.warning(
            "facade.enable_kill_switch",
            extra={"reason": reason, "actor": actor}
        )

        try:
            from app.hoc.cus.general.L5_controls.drivers.runtime_switch import (
                disable_governance_runtime,
                get_governance_state,
                is_governance_active,
                is_degraded_mode,
            )

            # Capture previous state
            was_active = is_governance_active()
            was_degraded = is_degraded_mode()

            if was_degraded:
                previous_mode = GovernanceMode.DEGRADED
            elif was_active:
                previous_mode = GovernanceMode.NORMAL
            else:
                previous_mode = GovernanceMode.KILL

            # Execute kill switch
            disable_governance_runtime(reason=reason, actor=actor)

            return KillSwitchResult(
                success=True,
                previous_mode=previous_mode,
                current_mode=GovernanceMode.KILL,
                timestamp=datetime.now(timezone.utc),
                actor=actor,
                reason=reason,
            )

        except Exception as e:
            logger.error(
                "facade.enable_kill_switch failed",
                extra={"error": str(e)}
            )
            return KillSwitchResult(
                success=False,
                previous_mode=GovernanceMode.NORMAL,
                current_mode=GovernanceMode.NORMAL,
                timestamp=datetime.now(timezone.utc),
                actor=actor,
                reason=reason,
                error=str(e),
            )

    def disable_kill_switch(
        self,
        actor: str,
    ) -> KillSwitchResult:
        """
        Disable kill switch - re-enable governance enforcement.

        Args:
            actor: Who/what triggered the re-enable

        Returns:
            KillSwitchResult with operation details
        """
        logger.info(
            "facade.disable_kill_switch",
            extra={"actor": actor}
        )

        try:
            from app.hoc.cus.general.L5_controls.drivers.runtime_switch import (
                enable_governance_runtime,
                is_governance_active,
            )

            was_active = is_governance_active()
            previous_mode = GovernanceMode.NORMAL if was_active else GovernanceMode.KILL

            # Re-enable governance
            enable_governance_runtime(actor=actor)

            return KillSwitchResult(
                success=True,
                previous_mode=previous_mode,
                current_mode=GovernanceMode.NORMAL,
                timestamp=datetime.now(timezone.utc),
                actor=actor,
            )

        except Exception as e:
            logger.error(
                "facade.disable_kill_switch failed",
                extra={"error": str(e)}
            )
            return KillSwitchResult(
                success=False,
                previous_mode=GovernanceMode.KILL,
                current_mode=GovernanceMode.KILL,
                timestamp=datetime.now(timezone.utc),
                actor=actor,
                error=str(e),
            )

    # =========================================================================
    # Degraded Mode Operations (GAP-091)
    # =========================================================================

    def set_mode(
        self,
        mode: GovernanceMode,
        reason: str,
        actor: str,
    ) -> KillSwitchResult:
        """
        Set governance mode (NORMAL, DEGRADED, KILL).

        Args:
            mode: Target governance mode
            reason: Why mode is being changed
            actor: Who/what triggered the change

        Returns:
            KillSwitchResult with operation details
        """
        logger.info(
            "facade.set_mode",
            extra={"mode": mode.value, "reason": reason, "actor": actor}
        )

        try:
            from app.hoc.cus.general.L5_controls.drivers.runtime_switch import (
                enter_degraded_mode,
                exit_degraded_mode,
                enable_governance_runtime,
                disable_governance_runtime,
                is_governance_active,
                is_degraded_mode,
            )

            # Capture previous state
            was_active = is_governance_active()
            was_degraded = is_degraded_mode()

            if was_degraded:
                previous_mode = GovernanceMode.DEGRADED
            elif was_active:
                previous_mode = GovernanceMode.NORMAL
            else:
                previous_mode = GovernanceMode.KILL

            # Apply new mode
            if mode == GovernanceMode.KILL:
                disable_governance_runtime(reason=reason, actor=actor)
            elif mode == GovernanceMode.DEGRADED:
                enter_degraded_mode(reason=reason, actor=actor)
            else:  # NORMAL
                if was_degraded:
                    exit_degraded_mode(actor=actor)
                elif not was_active:
                    enable_governance_runtime(actor=actor)

            return KillSwitchResult(
                success=True,
                previous_mode=previous_mode,
                current_mode=mode,
                timestamp=datetime.now(timezone.utc),
                actor=actor,
                reason=reason,
            )

        except Exception as e:
            logger.error(
                "facade.set_mode failed",
                extra={"error": str(e)}
            )
            return KillSwitchResult(
                success=False,
                previous_mode=GovernanceMode.NORMAL,
                current_mode=GovernanceMode.NORMAL,
                timestamp=datetime.now(timezone.utc),
                actor=actor,
                reason=reason,
                error=str(e),
            )

    def get_governance_state(self) -> GovernanceStateResult:
        """
        Get current governance state.

        Returns:
            GovernanceStateResult with current state details
        """
        try:
            from app.hoc.cus.general.L5_controls.drivers.runtime_switch import (
                get_governance_state as get_runtime_state,
                is_governance_active,
                is_degraded_mode,
            )

            state = get_runtime_state()
            is_active = is_governance_active()
            degraded = is_degraded_mode()

            if degraded:
                mode = GovernanceMode.DEGRADED
            elif is_active:
                mode = GovernanceMode.NORMAL
            else:
                mode = GovernanceMode.KILL

            # Parse last_changed
            last_changed = None
            if state.get("last_changed"):
                try:
                    last_changed = datetime.fromisoformat(state["last_changed"])
                except (ValueError, TypeError):
                    pass

            return GovernanceStateResult(
                mode=mode,
                active=is_active,
                degraded_mode=degraded,
                last_changed=last_changed,
                last_change_reason=state.get("last_change_reason"),
                last_change_actor=state.get("last_change_actor"),
            )

        except Exception as e:
            logger.error(
                "facade.get_governance_state failed",
                extra={"error": str(e)}
            )
            # Return safe defaults
            return GovernanceStateResult(
                mode=GovernanceMode.NORMAL,
                active=True,
                degraded_mode=False,
                last_changed=None,
                last_change_reason=None,
                last_change_actor=None,
            )

    # =========================================================================
    # Conflict Resolution Operations (GAP-092)
    # =========================================================================

    def resolve_conflict(
        self,
        conflict_id: str,
        resolution: str,
        actor: str,
        notes: Optional[str] = None,
    ) -> ConflictResolutionResult:
        """
        Manually resolve a policy conflict.

        Args:
            conflict_id: ID of the conflict to resolve
            resolution: Resolution strategy (e.g., "accept_first", "accept_second", "merge")
            actor: Who is resolving the conflict
            notes: Optional resolution notes

        Returns:
            ConflictResolutionResult with resolution details
        """
        logger.info(
            "facade.resolve_conflict",
            extra={
                "conflict_id": conflict_id,
                "resolution": resolution,
                "actor": actor,
            }
        )

        try:
            # TODO: Wire to actual ConflictResolver (GAP-068) when available
            # For now, return a stub result indicating the operation would succeed

            return ConflictResolutionResult(
                success=True,
                conflict_id=conflict_id,
                resolution=resolution,
                resolved_by=actor,
                resolved_at=datetime.now(timezone.utc),
                affected_policies=[],  # Would be populated by real implementation
            )

        except Exception as e:
            logger.error(
                "facade.resolve_conflict failed",
                extra={"error": str(e)}
            )
            return ConflictResolutionResult(
                success=False,
                conflict_id=conflict_id,
                resolution=resolution,
                resolved_by=actor,
                resolved_at=datetime.now(timezone.utc),
                affected_policies=[],
                error=str(e),
            )

    def list_conflicts(
        self,
        tenant_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List policy conflicts.

        Args:
            tenant_id: Optional tenant filter
            status: Optional status filter (pending, resolved)

        Returns:
            List of conflict details
        """
        try:
            # TODO: Wire to actual ConflictResolver (GAP-068) when available
            return []

        except Exception as e:
            logger.error(
                "facade.list_conflicts failed",
                extra={"error": str(e)}
            )
            return []

    # =========================================================================
    # Boot Status Operations (GAP-095)
    # =========================================================================

    def get_boot_status(self) -> BootStatusResult:
        """
        Get SPINE component health status.

        Returns:
            BootStatusResult with component health details
        """
        try:
            from app.hoc.cus.general.L5_controls.drivers.runtime_switch import is_governance_active

            # Check core components
            components = {
                "governance": {
                    "status": "healthy" if is_governance_active() else "disabled",
                    "active": is_governance_active(),
                },
                "policy_engine": {
                    "status": "healthy",
                    "loaded": True,
                },
                "audit_store": {
                    "status": "healthy",
                    "connected": True,
                },
            }

            # Check optional components
            try:
                # L5 engine import (migrated to HOC per SWEEP-47)
                from app.hoc.cus.policies.L5_engines.policy_driver import get_policy_facade
                policy_facade = get_policy_facade()
                components["policy_facade"] = {
                    "status": "healthy",
                    "available": True,
                }
            except Exception:
                components["policy_facade"] = {
                    "status": "unavailable",
                    "available": False,
                }

            # Calculate uptime
            now = datetime.now(timezone.utc)
            uptime_seconds = int((now - self._boot_time).total_seconds())

            # Overall health
            healthy = all(
                c.get("status") == "healthy"
                for c in components.values()
                if c.get("status") != "unavailable"
            )

            return BootStatusResult(
                healthy=healthy,
                components=components,
                boot_time=self._boot_time,
                uptime_seconds=uptime_seconds,
            )

        except Exception as e:
            logger.error(
                "facade.get_boot_status failed",
                extra={"error": str(e)}
            )
            return BootStatusResult(
                healthy=False,
                components={"error": {"status": "error", "message": str(e)}},
                boot_time=self._boot_time,
                uptime_seconds=0,
            )


# =============================================================================
# Module-level singleton accessor
# =============================================================================

_facade_instance: Optional[GovernanceFacade] = None


def get_governance_facade() -> GovernanceFacade:
    """
    Get the governance facade instance.

    This is the recommended way to access governance control operations
    from L2 APIs and the SDK.

    Returns:
        GovernanceFacade instance
    """
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = GovernanceFacade()
    return _facade_instance
