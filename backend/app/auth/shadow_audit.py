# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Role: Shadow audit logging for auth decisions
# Callers: RBAC engine, middleware
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: Auth System

"""
Shadow Audit Logging - M7-M28 RBAC Integration (PIN-169)

Logs RBAC decisions WITHOUT enforcing them.
Used during Phase 1-3 to collect real-world decision data before enforcement.

Usage:
    RBAC_SHADOW_AUDIT=true  # Enable shadow audit logging
    RBAC_ENFORCE=false      # Disable enforcement (log only)

ROLLOUT GATES (must pass before enforcement):
    - READ would-block rate < 0.1%
    - WRITE would-block rate < 0.01%
    - Founder-tenant violations = 0 (ever)
    - Shadow audit running >= 24h

Created: 2025-12-25
"""

import json
import logging
import os
import threading
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("nova.auth.shadow_audit")

# Configuration
SHADOW_AUDIT_ENABLED = os.getenv("RBAC_SHADOW_AUDIT", "true").lower() == "true"
SHADOW_AUDIT_LOG_LEVEL = os.getenv("RBAC_SHADOW_AUDIT_LEVEL", "INFO").upper()

# ============================================================================
# Rollout Gates - EXPLICIT THRESHOLDS
# ============================================================================

ROLLOUT_GATES = {
    "read_would_block_rate": 0.001,  # < 0.1% would-block on READ
    "write_would_block_rate": 0.0001,  # < 0.01% would-block on WRITE
    "founder_tenant_violations": 0,  # Zero tolerance
    "min_observation_hours": 24,  # Minimum 24h of shadow audit data
}

READ_ACTIONS = {"read", "query", "capabilities", "export", "stream", "checkpoint", "forecast"}
WRITE_ACTIONS = {
    "write",
    "delete",
    "admin",
    "simulate",
    "run",
    "cancel",
    "activate",
    "reset",
    "resolve",
    "reload",
    "freeze",
    "register",
    "heartbeat",
    "embed",
    "suggest",
    "execute",
}


@dataclass
class ShadowAuditEvent:
    """
    Shadow audit event for RBAC decisions.

    Captures what WOULD have happened if enforcement was enabled.
    """

    # Timestamp
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_type: str = "rbac_shadow_audit"

    # Request context
    path: str = ""
    method: str = ""
    client_ip: str = ""

    # Principal (Phase 2.5)
    principal_id: str = ""
    principal_type: str = ""  # console, fops, machine, anonymous
    tenant_id: Optional[str] = None
    source_token_type: str = ""  # jwt, api_key, machine_token

    # Role mapping (Phase 1)
    original_role: str = ""
    mapped_rbac_roles: List[str] = field(default_factory=list)
    mapping_source: str = ""  # console_auth, fops_auth, machine_token, x_roles

    # Policy evaluation (Phase 2)
    resource: str = ""
    action: str = ""
    policy_attrs: Dict[str, Any] = field(default_factory=dict)

    # Decision
    decision: str = ""  # allowed, denied
    decision_reason: str = ""
    would_block: bool = False  # True if this would be blocked under enforcement

    # Latency
    evaluation_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string for structured logging."""
        return json.dumps(self.to_dict(), default=str)


class ShadowAuditLogger:
    """
    Shadow audit logger for RBAC decisions.

    Logs to structured JSON format for easy parsing and analysis.
    """

    def __init__(self, enabled: bool = SHADOW_AUDIT_ENABLED):
        self.enabled = enabled
        self._audit_logger = logging.getLogger("nova.auth.shadow_audit.events")

        # Configure audit logger level
        level = getattr(logging, SHADOW_AUDIT_LOG_LEVEL, logging.INFO)
        self._audit_logger.setLevel(level)

    def log_decision(
        self,
        path: str,
        method: str,
        resource: str,
        action: str,
        decision: str,
        reason: str,
        roles: List[str],
        would_block: bool,
        principal_id: str = "",
        principal_type: str = "",
        tenant_id: Optional[str] = None,
        original_role: str = "",
        mapping_source: str = "",
        source_token_type: str = "",
        client_ip: str = "",
        evaluation_ms: float = 0.0,
        policy_attrs: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log a shadow audit event.

        Args:
            path: Request path
            method: HTTP method
            resource: RBAC resource
            action: RBAC action
            decision: "allowed" or "denied"
            reason: Decision reason
            roles: Effective RBAC roles
            would_block: True if this would be blocked under enforcement
            principal_id: Principal identifier
            principal_type: Type of principal
            tenant_id: Tenant ID (None for founders)
            original_role: Original console role before mapping
            mapping_source: Where the role came from
            source_token_type: Type of auth token
            client_ip: Client IP address
            evaluation_ms: Evaluation time in milliseconds
            policy_attrs: Additional policy attributes
        """
        if not self.enabled:
            return

        event = ShadowAuditEvent(
            path=path,
            method=method,
            client_ip=client_ip,
            principal_id=principal_id,
            principal_type=principal_type,
            tenant_id=tenant_id,
            source_token_type=source_token_type,
            original_role=original_role,
            mapped_rbac_roles=roles,
            mapping_source=mapping_source,
            resource=resource,
            action=action,
            policy_attrs=policy_attrs or {},
            decision=decision,
            decision_reason=reason,
            would_block=would_block,
            evaluation_ms=evaluation_ms,
        )

        # Log as structured JSON
        if would_block:
            self._audit_logger.warning(
                "shadow_audit_would_block",
                extra={"shadow_audit": event.to_dict()},
            )
        else:
            self._audit_logger.info(
                "shadow_audit_allowed",
                extra={"shadow_audit": event.to_dict()},
            )

        # Also log to main logger for visibility
        if would_block:
            logger.info(
                f"SHADOW_AUDIT [WOULD_BLOCK] {method} {path} - "
                f"resource={resource} action={action} roles={roles} reason={reason}"
            )
        else:
            logger.debug(
                f"SHADOW_AUDIT [allowed] {method} {path} - " f"resource={resource} action={action} roles={roles}"
            )

    def log_role_mapping(
        self,
        original_role: str,
        mapped_role: str,
        principal_type: str,
        source: str,
    ) -> None:
        """
        Log a role mapping event.

        Useful for tracking how console roles map to RBAC roles.
        """
        if not self.enabled:
            return

        logger.info(
            f"SHADOW_AUDIT [role_mapping] {original_role} -> {mapped_role} "
            f"(principal_type={principal_type}, source={source})"
        )

    def log_founder_isolation_check(
        self,
        principal_id: str,
        tenant_id: Optional[str],
        passed: bool,
    ) -> None:
        """
        Log a founder isolation check.

        Tracks whether founder isolation guard would pass or fail.
        """
        if not self.enabled:
            return

        if not passed:
            logger.error(
                f"SHADOW_AUDIT [FOUNDER_ISOLATION_FAIL] principal={principal_id} "
                f"tenant_id={tenant_id} - SECURITY VIOLATION WOULD OCCUR"
            )
        else:
            logger.debug(f"SHADOW_AUDIT [founder_isolation_pass] principal={principal_id} " f"tenant_id={tenant_id}")


# ============================================================================
# Shadow Audit Aggregator - In-Memory Stats for Quick Queries
# ============================================================================


class ShadowAuditAggregator:
    """
    In-memory aggregation for shadow audit events.

    Answers "who would be blocked and why" in < 10 seconds.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._start_time = datetime.now(timezone.utc)

        # Counters by action type
        self._read_total = 0
        self._read_would_block = 0
        self._write_total = 0
        self._write_would_block = 0

        # Founder isolation violations (ZERO TOLERANCE)
        self._founder_tenant_violations = 0
        self._founder_violation_details: List[Dict[str, Any]] = []

        # Who would be blocked (top offenders)
        # Key: (principal_type, role, resource, action)
        self._would_block_by_principal: Dict[Tuple[str, str, str, str], int] = defaultdict(int)
        self._would_block_details: List[Dict[str, Any]] = []  # Last N events
        self._max_detail_events = 100

    def record_decision(
        self,
        principal_type: str,
        role: str,
        resource: str,
        action: str,
        would_block: bool,
        tenant_id: Optional[str] = None,
        principal_id: str = "",
        reason: str = "",
    ) -> None:
        """Record a shadow audit decision for aggregation."""
        with self._lock:
            # Categorize as READ or WRITE
            if action in READ_ACTIONS:
                self._read_total += 1
                if would_block:
                    self._read_would_block += 1
            elif action in WRITE_ACTIONS:
                self._write_total += 1
                if would_block:
                    self._write_would_block += 1

            # Track who would be blocked
            if would_block:
                key = (principal_type, role, resource, action)
                self._would_block_by_principal[key] += 1

                # Keep last N detail events
                if len(self._would_block_details) >= self._max_detail_events:
                    self._would_block_details.pop(0)
                self._would_block_details.append(
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "principal_type": principal_type,
                        "principal_id": principal_id,
                        "role": role,
                        "resource": resource,
                        "action": action,
                        "tenant_id": tenant_id,
                        "reason": reason,
                    }
                )

    def record_founder_violation(
        self,
        principal_id: str,
        tenant_id: str,
    ) -> None:
        """Record a founder-tenant isolation violation (CRITICAL)."""
        with self._lock:
            self._founder_tenant_violations += 1
            self._founder_violation_details.append(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "principal_id": principal_id,
                    "tenant_id": tenant_id,
                }
            )
            logger.critical(
                f"FOUNDER_TENANT_VIOLATION #{self._founder_tenant_violations}: "
                f"principal={principal_id} tenant={tenant_id}"
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get current aggregated statistics."""
        with self._lock:
            hours_running = (datetime.now(timezone.utc) - self._start_time).total_seconds() / 3600

            read_block_rate = self._read_would_block / self._read_total if self._read_total > 0 else 0.0
            write_block_rate = self._write_would_block / self._write_total if self._write_total > 0 else 0.0

            return {
                "start_time": self._start_time.isoformat(),
                "hours_running": round(hours_running, 2),
                "read": {
                    "total": self._read_total,
                    "would_block": self._read_would_block,
                    "block_rate": round(read_block_rate, 6),
                    "block_rate_pct": f"{read_block_rate * 100:.4f}%",
                },
                "write": {
                    "total": self._write_total,
                    "would_block": self._write_would_block,
                    "block_rate": round(write_block_rate, 6),
                    "block_rate_pct": f"{write_block_rate * 100:.4f}%",
                },
                "founder_tenant_violations": self._founder_tenant_violations,
            }

    def check_rollout_gates(self) -> Dict[str, Any]:
        """
        Check if rollout gates are met for enforcement.

        Returns dict with gate status and readiness.
        """
        stats = self.get_stats()
        hours = stats["hours_running"]

        gates = {
            "read_would_block_rate": {
                "threshold": ROLLOUT_GATES["read_would_block_rate"],
                "actual": stats["read"]["block_rate"],
                "passed": stats["read"]["block_rate"] < ROLLOUT_GATES["read_would_block_rate"],
            },
            "write_would_block_rate": {
                "threshold": ROLLOUT_GATES["write_would_block_rate"],
                "actual": stats["write"]["block_rate"],
                "passed": stats["write"]["block_rate"] < ROLLOUT_GATES["write_would_block_rate"],
            },
            "founder_tenant_violations": {
                "threshold": ROLLOUT_GATES["founder_tenant_violations"],
                "actual": stats["founder_tenant_violations"],
                "passed": stats["founder_tenant_violations"] == 0,
            },
            "min_observation_hours": {
                "threshold": ROLLOUT_GATES["min_observation_hours"],
                "actual": hours,
                "passed": hours >= ROLLOUT_GATES["min_observation_hours"],
            },
        }

        all_passed = all(g["passed"] for g in gates.values())

        return {
            "ready_for_enforcement": all_passed,
            "gates": gates,
            "stats": stats,
        }

    def get_who_would_be_blocked(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Answer: "Who would be blocked and why?"

        Returns top offenders sorted by count.
        """
        with self._lock:
            sorted_offenders = sorted(
                self._would_block_by_principal.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:limit]

            return [
                {
                    "principal_type": key[0],
                    "role": key[1],
                    "resource": key[2],
                    "action": key[3],
                    "count": count,
                }
                for key, count in sorted_offenders
            ]

    def get_recent_blocks(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent would-block events with details."""
        with self._lock:
            return list(reversed(self._would_block_details[-limit:]))

    def get_founder_violations(self) -> List[Dict[str, Any]]:
        """Get all founder-tenant violations (should always be empty)."""
        with self._lock:
            return list(self._founder_violation_details)


# Global aggregator instance
shadow_aggregator = ShadowAuditAggregator()


# Global shadow audit logger instance
shadow_audit = ShadowAuditLogger()


# ============================================================================
# Metrics for shadow audit
# ============================================================================

try:
    from ..utils.metrics_helpers import get_or_create_counter

    SHADOW_AUDIT_DECISIONS = get_or_create_counter(
        "rbac_shadow_audit_total",
        "Shadow audit RBAC decisions (what would happen under enforcement)",
        ["resource", "action", "decision", "would_block"],
    )
except ImportError:
    SHADOW_AUDIT_DECISIONS = None


def record_shadow_audit_metric(resource: str, action: str, decision: str, would_block: bool) -> None:
    """Record shadow audit decision in Prometheus."""
    if SHADOW_AUDIT_DECISIONS:
        SHADOW_AUDIT_DECISIONS.labels(
            resource=resource,
            action=action,
            decision=decision,
            would_block=str(would_block).lower(),
        ).inc()


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "ShadowAuditEvent",
    "ShadowAuditLogger",
    "ShadowAuditAggregator",
    "shadow_audit",
    "shadow_aggregator",
    "SHADOW_AUDIT_ENABLED",
    "ROLLOUT_GATES",
    "record_shadow_audit_metric",
]
