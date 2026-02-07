# Layer: L4 — hoc_spine Authority
# AUDIENCE: SHARED
# Role: RBAC policy matrix and path-to-policy mapping
# Product: system-wide
# Temporal:
#   Trigger: import
#   Execution: sync
# Callers: auth/rbac_middleware.py (shim), middleware
# Allowed Imports: auth.rbac_rules_loader (YAML loader, no framework)
# Forbidden Imports: FastAPI, Starlette, DB
# Reference: PIN-169, PIN-271/273, PIN-391

"""
RBAC Policy (Canonical)

Defines the RBAC role-resource matrix and path-to-policy mapping.
All path matchers use canonical (unversioned) form.

This module contains NO framework imports — it is pure policy data.
The `enforce()` function (which needs Request) stays in the middleware.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nova.auth.rbac_policy")

# PIN-391: Environment detection for schema-driven RBAC
CURRENT_ENVIRONMENT = os.getenv("AOS_ENVIRONMENT", "preflight")


# ============================================================================
# Policy Objects
# ============================================================================

@dataclass
class PolicyObject:
    """
    Represents an authorization policy for a resource action.

    Attributes:
        resource: Resource type (e.g., "memory_pin", "prometheus")
        action: Action type (e.g., "read", "write", "delete", "admin")
        attrs: Optional additional attributes for context-aware decisions
    """

    resource: str
    action: str
    attrs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Decision:
    """
    Result of an authorization decision.

    Attributes:
        allowed: Whether the action is permitted
        reason: Human-readable reason for the decision
        roles: Roles that contributed to the decision
        policy: The policy that was evaluated
    """

    allowed: bool
    reason: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    policy: Optional[PolicyObject] = None


# ============================================================================
# RBAC Matrix (Role → Resource → Actions)
# ============================================================================
# PIN-169: 14 resources with founder/operator roles.

RBAC_MATRIX: Dict[str, Dict[str, List[str]]] = {
    # =========================================================================
    # FOUNDER-SCOPED ROLES (Isolated — never flow through tenant RBAC)
    # =========================================================================
    "founder": {
        "memory_pin": ["read", "write", "delete", "admin"],
        "prometheus": ["reload", "query"],
        "costsim": ["read", "write", "admin"],
        "policy": ["read", "write", "approve"],
        "agent": ["read", "write", "register", "heartbeat", "delete"],
        "runtime": ["simulate", "query", "capabilities"],
        "recovery": ["read", "write", "execute", "suggest"],
        "worker": ["read", "run", "stream", "cancel"],
        "trace": ["read", "write", "delete", "export"],
        "embedding": ["read", "embed", "query"],
        "killswitch": ["read", "activate", "reset"],
        "integration": ["read", "checkpoint", "resolve"],
        "cost": ["read", "simulate", "forecast"],
        "checkpoint": ["read", "write", "restore"],
        "event": ["read", "subscribe", "publish"],
        "incident": ["read", "write", "resolve"],
        "tenant": ["read", "write", "freeze", "delete"],
        "rbac": ["read", "reload", "audit"],
    },
    "operator": {
        "memory_pin": ["read", "write"],
        "prometheus": ["reload", "query"],
        "costsim": ["read", "write"],
        "policy": ["read", "write"],
        "agent": ["read", "write", "register", "heartbeat"],
        "runtime": ["simulate", "query", "capabilities"],
        "recovery": ["read", "write", "execute"],
        "worker": ["read", "run", "stream"],
        "trace": ["read", "write", "export"],
        "embedding": ["read", "embed", "query"],
        "killswitch": ["read", "activate"],
        "integration": ["read", "checkpoint", "resolve"],
        "cost": ["read", "simulate"],
        "checkpoint": ["read", "write", "restore"],
        "event": ["read", "subscribe"],
        "incident": ["read", "write", "resolve"],
        "tenant": ["read"],
        "rbac": ["read"],
    },
    # =========================================================================
    # TENANT-SCOPED ROLES
    # =========================================================================
    "infra": {
        "memory_pin": ["read", "write", "delete", "admin"],
        "prometheus": ["reload", "query"],
        "costsim": ["read", "write", "admin"],
        "policy": ["read", "write", "approve"],
        "agent": ["read", "write", "register", "heartbeat", "delete"],
        "runtime": ["simulate", "query", "capabilities"],
        "recovery": ["read", "write", "execute", "suggest"],
        "worker": ["read", "run", "stream", "cancel"],
        "trace": ["read", "write", "delete", "export"],
        "embedding": ["read", "embed", "query"],
        "killswitch": ["read", "activate", "reset"],
        "integration": ["read", "checkpoint", "resolve"],
        "cost": ["read", "simulate", "forecast"],
        "checkpoint": ["read", "write", "restore"],
        "event": ["read", "subscribe", "publish"],
        "incident": ["read", "write", "resolve"],
        "rbac": ["read"],
    },
    "admin": {
        "memory_pin": ["read", "write", "delete", "admin"],
        "prometheus": ["reload", "query"],
        "costsim": ["read", "write", "admin"],
        "policy": ["read", "write", "approve"],
        "agent": ["read", "write", "register", "heartbeat"],
        "runtime": ["simulate", "query", "capabilities"],
        "recovery": ["read", "write", "execute"],
        "worker": ["read", "run", "stream"],
        "trace": ["read", "write", "export"],
        "embedding": ["read", "embed", "query"],
        "killswitch": ["read", "activate"],
        "integration": ["read", "checkpoint", "resolve"],
        "cost": ["read", "simulate"],
        "checkpoint": ["read", "write", "restore"],
        "event": ["read", "subscribe"],
        "incident": ["read", "write"],
        "rbac": ["read"],
    },
    "machine": {
        "memory_pin": ["read"],
        "prometheus": ["query"],
        "costsim": ["read"],
        "policy": [],
        "agent": ["read", "heartbeat"],
        "runtime": ["simulate", "query", "capabilities"],
        "recovery": ["read"],
        "worker": ["read", "run", "stream"],
        "trace": ["read", "write"],
        "embedding": ["read", "embed"],
        "killswitch": [],
        "integration": ["read"],
        "cost": ["read"],
        "checkpoint": ["read"],
        "event": ["read", "subscribe"],
        "incident": ["read"],
        "tenant": [],
        "rbac": [],
    },
    "dev": {
        "memory_pin": ["read"],
        "prometheus": ["query"],
        "costsim": ["read"],
        "policy": ["read"],
        "agent": ["read", "register", "heartbeat"],
        "runtime": ["simulate", "query", "capabilities"],
        "recovery": ["read"],
        "worker": ["read", "run", "stream"],
        "trace": ["read"],
        "embedding": ["read", "embed"],
        "killswitch": ["read"],
        "integration": ["read"],
        "cost": ["read"],
        "checkpoint": ["read"],
        "event": ["read", "subscribe"],
        "incident": ["read"],
    },
    "readonly": {
        "memory_pin": ["read"],
        "prometheus": ["query"],
        "costsim": ["read"],
        "policy": ["read"],
        "agent": ["read"],
        "runtime": ["query", "capabilities"],
        "recovery": ["read"],
        "worker": ["read"],
        "trace": ["read"],
        "embedding": ["read"],
        "killswitch": ["read"],
        "integration": ["read"],
        "cost": ["read"],
        "checkpoint": ["read"],
        "event": ["read"],
        "incident": ["read"],
    },
}


# ============================================================================
# Path → Policy Mapping (Canonical Paths)
# ============================================================================

def get_policy_for_path(path: str, method: str) -> Optional[PolicyObject]:
    """
    Map request path and method to a PolicyObject.

    Returns None for explicitly public paths (no RBAC needed).
    All path matchers use canonical (unversioned) form.
    """
    # Schema-driven public paths (PIN-391)
    from app.auth.rbac_rules_loader import get_public_paths

    public_paths = get_public_paths(environment=CURRENT_ENVIRONMENT)

    is_public = any(
        path.startswith(p) or path == p.rstrip("/") for p in public_paths
    )

    if is_public:
        return None

    # =========================================================================
    # MEMORY PINS (/memory/pins)
    # =========================================================================
    if path.startswith("/memory/pins"):
        if path.endswith("/cleanup"):
            return PolicyObject(resource="memory_pin", action="admin")
        elif method == "GET":
            return PolicyObject(resource="memory_pin", action="read")
        elif method in ("POST", "PUT", "PATCH"):
            return PolicyObject(resource="memory_pin", action="write")
        elif method == "DELETE":
            return PolicyObject(resource="memory_pin", action="delete")

    # =========================================================================
    # PROMETHEUS & METRICS
    # =========================================================================
    if path.startswith("/-/reload") or path.startswith("/api/observability/prom-reload"):
        return PolicyObject(resource="prometheus", action="reload")

    if path.startswith("/query") or path.startswith("/api/prometheus"):
        return PolicyObject(resource="prometheus", action="query")

    # =========================================================================
    # COSTSIM (/costsim)
    # =========================================================================
    if path.startswith("/costsim"):
        if method == "GET":
            return PolicyObject(resource="costsim", action="read")
        else:
            return PolicyObject(resource="costsim", action="write")

    # =========================================================================
    # POLICY (/policy)
    # =========================================================================
    if path.startswith("/policy"):
        if "/approve" in path or "/reject" in path:
            return PolicyObject(resource="policy", action="approve")
        elif method == "GET":
            return PolicyObject(resource="policy", action="read")
        else:
            return PolicyObject(resource="policy", action="write")

    # =========================================================================
    # AGENTS (/agents)
    # =========================================================================
    if path.startswith("/agents"):
        if "/heartbeat" in path:
            return PolicyObject(resource="agent", action="heartbeat")
        elif "/register" in path:
            return PolicyObject(resource="agent", action="register")
        elif method == "GET":
            return PolicyObject(resource="agent", action="read")
        elif method == "POST":
            return PolicyObject(resource="agent", action="write")
        elif method in ("PUT", "PATCH"):
            return PolicyObject(resource="agent", action="write")
        elif method == "DELETE":
            return PolicyObject(resource="agent", action="delete")

    # =========================================================================
    # RUNTIME (/runtime)
    # =========================================================================
    if path.startswith("/runtime"):
        if "/simulate" in path:
            return PolicyObject(resource="runtime", action="simulate")
        elif "/capabilities" in path:
            return PolicyObject(resource="runtime", action="capabilities")
        elif "/query" in path or method == "GET":
            return PolicyObject(resource="runtime", action="query")
        else:
            return PolicyObject(resource="runtime", action="query")

    # =========================================================================
    # RECOVERY (/recovery)
    # =========================================================================
    if path.startswith("/recovery"):
        if "/execute" in path or "/apply" in path:
            return PolicyObject(resource="recovery", action="execute")
        elif "/suggest" in path:
            return PolicyObject(resource="recovery", action="suggest")
        elif method == "GET":
            return PolicyObject(resource="recovery", action="read")
        elif method in ("POST", "PUT", "PATCH"):
            return PolicyObject(resource="recovery", action="write")

    # =========================================================================
    # WORKERS (/workers)
    # =========================================================================
    if path.startswith("/workers"):
        if "/run" in path or "/execute" in path:
            return PolicyObject(resource="worker", action="run")
        elif "/stream" in path:
            return PolicyObject(resource="worker", action="stream")
        elif "/cancel" in path or "/stop" in path:
            return PolicyObject(resource="worker", action="cancel")
        elif method == "GET":
            return PolicyObject(resource="worker", action="read")

    # =========================================================================
    # TRACES (/traces)
    # =========================================================================
    if path.startswith("/traces"):
        if "/export" in path:
            return PolicyObject(resource="trace", action="export")
        elif method == "GET":
            return PolicyObject(resource="trace", action="read")
        elif method in ("POST", "PUT", "PATCH"):
            return PolicyObject(resource="trace", action="write")
        elif method == "DELETE":
            return PolicyObject(resource="trace", action="delete")

    # =========================================================================
    # EMBEDDING (/embedding)
    # =========================================================================
    if path.startswith("/embedding"):
        if "/query" in path or "/search" in path:
            return PolicyObject(resource="embedding", action="query")
        elif path.endswith("/embed") and method == "POST":
            return PolicyObject(resource="embedding", action="embed")
        elif method == "GET":
            return PolicyObject(resource="embedding", action="read")
        elif method == "POST":
            return PolicyObject(resource="embedding", action="embed")

    # =========================================================================
    # KILLSWITCH
    # =========================================================================
    if "/killswitch" in path:
        if "/activate" in path or "/engage" in path:
            return PolicyObject(resource="killswitch", action="activate")
        elif "/reset" in path or "/disengage" in path:
            return PolicyObject(resource="killswitch", action="reset")
        else:
            return PolicyObject(resource="killswitch", action="read")

    # =========================================================================
    # INTEGRATION
    # =========================================================================
    if "/integration" in path:
        if "/resolve" in path:
            return PolicyObject(resource="integration", action="resolve")
        elif "/checkpoint" in path:
            return PolicyObject(resource="integration", action="checkpoint")
        elif method == "GET":
            return PolicyObject(resource="integration", action="read")

    # =========================================================================
    # COST
    # =========================================================================
    if "/cost" in path and "/costsim" not in path:
        if "/simulate" in path:
            return PolicyObject(resource="cost", action="simulate")
        elif "/forecast" in path:
            return PolicyObject(resource="cost", action="forecast")
        else:
            return PolicyObject(resource="cost", action="read")

    # =========================================================================
    # CHECKPOINTS (/checkpoints)
    # =========================================================================
    if path.startswith("/checkpoints"):
        if "/restore" in path:
            return PolicyObject(resource="checkpoint", action="restore")
        elif method == "GET":
            return PolicyObject(resource="checkpoint", action="read")
        elif method in ("POST", "PUT", "PATCH"):
            return PolicyObject(resource="checkpoint", action="write")

    # =========================================================================
    # EVENTS (/events)
    # =========================================================================
    if path.startswith("/events"):
        if "/subscribe" in path:
            return PolicyObject(resource="event", action="subscribe")
        elif "/publish" in path and method == "POST":
            return PolicyObject(resource="event", action="publish")
        else:
            return PolicyObject(resource="event", action="read")

    # =========================================================================
    # INCIDENTS (/incidents)
    # =========================================================================
    if path.startswith("/incidents") or "/incidents" in path:
        if "/resolve" in path:
            return PolicyObject(resource="incident", action="resolve")
        elif method == "GET":
            return PolicyObject(resource="incident", action="read")
        elif method in ("POST", "PUT", "PATCH"):
            return PolicyObject(resource="incident", action="write")

    # =========================================================================
    # RBAC (/rbac)
    # =========================================================================
    if path.startswith("/rbac"):
        if "/reload" in path:
            return PolicyObject(resource="rbac", action="reload")
        elif "/audit" in path:
            return PolicyObject(resource="rbac", action="audit")
        else:
            return PolicyObject(resource="rbac", action="read")

    # =========================================================================
    # TENANTS (/tenants)
    # =========================================================================
    if path.startswith("/tenants"):
        if "/freeze" in path:
            return PolicyObject(resource="tenant", action="freeze")
        elif method == "GET":
            return PolicyObject(resource="tenant", action="read")
        elif method == "POST":
            return PolicyObject(resource="tenant", action="write")
        elif method == "DELETE":
            return PolicyObject(resource="tenant", action="delete")

    # =========================================================================
    # RUNS (/runs) — maps to worker resource
    # =========================================================================
    if path.startswith("/runs"):
        if method == "GET":
            return PolicyObject(resource="worker", action="read")
        elif method == "POST":
            return PolicyObject(resource="worker", action="run")

    # =========================================================================
    # V1 PROXY ROUTES (/v1/chat, /v1/embeddings, /v1/status)
    # =========================================================================
    if path.startswith("/v1/"):
        if "/chat" in path or "/completions" in path:
            return PolicyObject(resource="runtime", action="simulate")
        if "/embeddings" in path:
            return PolicyObject(resource="embedding", action="embed")
        if "/status" in path:
            return PolicyObject(resource="runtime", action="query")
        if "/policies" in path:
            return PolicyObject(resource="policy", action="read")
        if "/demo" in path or "/replay" in path:
            return PolicyObject(resource="trace", action="read")

    # =========================================================================
    # CUSTOMER ROUTES (/cus/*)
    # =========================================================================
    if path.startswith("/cus/"):
        if "/pre-run" in path:
            return PolicyObject(resource="runtime", action="query")
        elif "/acknowledge" in path:
            return PolicyObject(resource="runtime", action="query")
        elif "/outcome" in path:
            return PolicyObject(resource="runtime", action="query")
        elif "/declaration" in path:
            return PolicyObject(resource="runtime", action="query")
        else:
            return PolicyObject(resource="runtime", action="query")

    # =========================================================================
    # GUARD ROUTES (/guard/*)
    # =========================================================================
    if path.startswith("/guard/"):
        if "/costs" in path:
            return PolicyObject(resource="cost", action="read")
        elif "/incidents" in path:
            return PolicyObject(resource="incident", action="read")
        else:
            return PolicyObject(resource="runtime", action="query")

    # =========================================================================
    # OPS ROUTES (/ops/*)
    # =========================================================================
    if path.startswith("/ops/"):
        if "/cost" in path:
            return PolicyObject(resource="cost", action="read")
        elif "/customers" in path or "/tenants" in path:
            return PolicyObject(resource="tenant", action="read")
        elif "/incidents" in path:
            return PolicyObject(resource="incident", action="read")
        elif "/actions" in path:
            return PolicyObject(resource="tenant", action="write")
        else:
            return PolicyObject(resource="runtime", action="query")

    # =========================================================================
    # FOUNDER TIMELINE (/fdr/timeline/*)
    # =========================================================================
    if path.startswith("/fdr/timeline"):
        return PolicyObject(resource="runtime", action="query")

    # =========================================================================
    # CATCH-ALL: default to runtime:query
    # =========================================================================
    logger.debug(f"rbac_unknown_path: {path} {method} - defaulting to runtime:query")
    return PolicyObject(resource="runtime", action="query")


__all__ = [
    "PolicyObject",
    "Decision",
    "RBAC_MATRIX",
    "CURRENT_ENVIRONMENT",
    "get_policy_for_path",
]
