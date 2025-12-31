# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Role: RBAC authorization engine with policy evaluation
# Callers: API routes, middleware, services
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: Auth System

"""
Enhanced RBAC Engine - M7 Implementation

Provides PolicyObject-based authorization with:
- Hot-reloadable policies from JSON file
- Prometheus metrics
- Database audit logging
- Fail-open/fail-closed modes

Usage:
    from app.auth.rbac_engine import RBACEngine, PolicyObject

    engine = RBACEngine()
    decision = engine.check(PolicyObject("memory_pin", "write"), request)
"""

import hashlib
import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import jwt
from fastapi import Request

from ..utils.metrics_helpers import get_or_create_counter, get_or_create_gauge, get_or_create_histogram

logger = logging.getLogger("nova.auth.rbac_engine")

# =============================================================================
# Configuration
# =============================================================================

RBAC_ENFORCE = os.getenv("RBAC_ENFORCE", "false").lower() == "true"
RBAC_FAIL_OPEN = os.getenv("RBAC_FAIL_OPEN", "false").lower() == "true"
RBAC_AUDIT_ENABLED = os.getenv("RBAC_AUDIT_ENABLED", "true").lower() == "true"
MACHINE_SECRET_TOKEN = os.getenv("MACHINE_SECRET_TOKEN", "")
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_VERIFY_SIGNATURE = os.getenv("JWT_VERIFY_SIGNATURE", "false").lower() == "true"

# Policy file path (can be reloaded at runtime)
POLICY_FILE = os.getenv("RBAC_POLICY_FILE", str(Path(__file__).parent.parent / "config" / "rbac_policies.json"))


# =============================================================================
# Prometheus Metrics
# =============================================================================

RBAC_ENGINE_DECISIONS = get_or_create_counter(
    "rbac_engine_decisions_total", "RBAC engine authorization decisions", ["resource", "action", "decision", "reason"]
)

RBAC_ENGINE_LATENCY = get_or_create_histogram(
    "rbac_engine_latency_seconds",
    "RBAC engine decision latency",
    buckets=[0.0005, 0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1],
)

RBAC_POLICY_LOADS = get_or_create_counter("rbac_policy_loads_total", "Policy file reload attempts", ["status"])

RBAC_POLICY_VERSION = get_or_create_gauge("rbac_policy_version_info", "Current policy version (hash as integer)")

RBAC_AUDIT_WRITES = get_or_create_counter("rbac_audit_writes_total", "Audit log writes", ["status"])


# =============================================================================
# L4 Domain Authority: Role Mapping Rules
# =============================================================================
# B03/B04 FIX: Role-to-level and role classification logic moved from L3 adapters
# Reference: PIN-254 Phase B Fix

# Role-to-approval-level mapping (L4 domain authority)
# Clerk adapter and other auth sources must delegate to this
ROLE_APPROVAL_LEVELS: Dict[str, int] = {
    # Level 5 - Full administrative access
    "owner": 5,
    "admin": 5,
    "realm-admin": 5,
    "aos-admin": 5,
    # Level 4 - Policy and management access
    "manager": 4,
    "policy_admin": 4,
    "director": 4,
    # Level 3 - Team leadership access
    "team_lead": 3,
    "senior_engineer": 3,
    "tech_lead": 3,
    # Level 2 - Standard member access
    "team_member": 2,
    "engineer": 2,
    "developer": 2,
    "dev": 2,
    # Level 1 - Minimal access
    "guest": 1,
    "readonly": 1,
    "viewer": 1,
}

# External provider role mappings (L4 domain authority)
# Keycloak/OIDC provider roles to AOS internal roles
EXTERNAL_TO_AOS_ROLE_MAP: Dict[str, str] = {
    # Admin roles
    "admin": "admin",
    "realm-admin": "admin",
    "aos-admin": "admin",
    # Infrastructure roles
    "infra": "infra",
    "infrastructure": "infra",
    "platform": "infra",
    # Developer roles
    "developer": "dev",
    "dev": "dev",
    "engineer": "dev",
    # Machine/service roles
    "machine": "machine",
    "service": "machine",
    "service-account": "machine",
    # Readonly roles
    "readonly": "readonly",
    "viewer": "readonly",
    "guest": "readonly",
}


def get_role_approval_level(role: str) -> int:
    """
    Get approval level for a role (L4 domain decision).

    L3 adapters must NOT hardcode role-to-level mappings.
    This function is the authoritative source.

    Args:
        role: Role name (case-insensitive)

    Returns:
        Approval level (1-5), defaults to 1 for unknown roles
    """
    return ROLE_APPROVAL_LEVELS.get(role.lower(), 1)


def get_max_approval_level(roles: List[str]) -> int:
    """
    Get maximum approval level from a list of roles (L4 domain decision).

    Args:
        roles: List of role names

    Returns:
        Maximum approval level (1-5)
    """
    if not roles:
        return 1
    return max(get_role_approval_level(role) for role in roles)


def map_external_role_to_aos(external_role: str) -> str:
    """
    Map external provider role to AOS internal role (L4 domain decision).

    L3 adapters (OIDC, Clerk) must NOT hardcode role mappings.
    This function is the authoritative source.

    Args:
        external_role: Role from external provider (Keycloak, Clerk, etc.)

    Returns:
        AOS internal role name
    """
    role_lower = external_role.lower()
    return EXTERNAL_TO_AOS_ROLE_MAP.get(role_lower, role_lower)


def map_external_roles_to_aos(external_roles: List[str]) -> List[str]:
    """
    Map list of external roles to AOS internal roles (L4 domain decision).

    Args:
        external_roles: List of roles from external provider

    Returns:
        List of AOS internal roles (deduplicated)
    """
    aos_roles = set()
    for role in external_roles:
        aos_roles.add(map_external_role_to_aos(role))
    return list(aos_roles)


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class PolicyObject:
    """
    Represents an authorization request.

    Attributes:
        resource: Resource type (e.g., "memory_pin", "prometheus")
        action: Action type (e.g., "read", "write", "delete", "admin")
        attrs: Optional additional attributes for context-aware decisions
    """

    resource: str
    action: str
    attrs: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash((self.resource, self.action))


@dataclass
class Decision:
    """
    Result of an authorization decision.

    Attributes:
        allowed: Whether the action is permitted
        reason: Human-readable reason for the decision
        roles: Roles that contributed to the decision
        policy: The policy that was evaluated
        latency_ms: Decision latency in milliseconds
    """

    allowed: bool
    reason: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    policy: Optional[PolicyObject] = None
    latency_ms: float = 0.0


@dataclass
class PolicyConfig:
    """Loaded policy configuration."""

    version: str
    matrix: Dict[str, Dict[str, List[str]]]
    path_mappings: List[Dict[str, Any]]
    loaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    hash: str = ""


# =============================================================================
# RBAC Engine
# =============================================================================


class RBACEngine:
    """
    Core RBAC authorization engine.

    Features:
    - Hot-reloadable policies
    - Thread-safe policy access
    - Prometheus metrics integration
    - Database audit logging
    """

    _instance: Optional["RBACEngine"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Singleton pattern for consistent policy state."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db_session_factory: Optional[Callable] = None, policy_file: Optional[str] = None):
        # Only initialize once
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._initialized = True
        self._policy_lock = threading.RLock()
        self._db_session_factory = db_session_factory
        self._policy_file = policy_file or POLICY_FILE
        self._policy: Optional[PolicyConfig] = None
        self._default_matrix = self._get_default_matrix()

        # Load initial policy
        self.reload_policy()

    def _get_default_matrix(self) -> Dict[str, Dict[str, List[str]]]:
        """Default RBAC matrix (used if policy file not found)."""
        return {
            "infra": {
                "memory_pin": ["read", "write", "delete", "admin"],
                "prometheus": ["reload", "query"],
                "costsim": ["read", "write", "admin"],
                "policy": ["read", "write", "approve"],
                "rbac": ["reload", "read"],
            },
            "admin": {
                "memory_pin": ["read", "write", "delete", "admin"],
                "prometheus": ["reload", "query"],
                "costsim": ["read", "write", "admin"],
                "policy": ["read", "write", "approve"],
                "rbac": ["reload", "read"],
            },
            "machine": {
                "memory_pin": ["read", "write"],
                "prometheus": ["reload"],
                "costsim": ["read"],
                "policy": ["read"],
                "rbac": ["read"],
            },
            "dev": {
                "memory_pin": ["read"],
                "prometheus": ["query"],
                "costsim": ["read"],
                "policy": ["read"],
                "rbac": ["read"],
            },
            "readonly": {
                "memory_pin": ["read"],
                "prometheus": ["query"],
                "costsim": ["read"],
                "policy": ["read"],
                "rbac": ["read"],
            },
        }

    def reload_policy(self) -> Tuple[bool, str]:
        """
        Reload policies from JSON file.

        Returns:
            Tuple of (success, message)
        """
        try:
            policy_path = Path(self._policy_file)
            if not policy_path.exists():
                logger.warning(f"Policy file not found: {policy_path}, using defaults")
                RBAC_POLICY_LOADS.labels(status="default").inc()
                with self._policy_lock:
                    self._policy = PolicyConfig(
                        version="default", matrix=self._default_matrix, path_mappings=[], hash="default"
                    )
                return True, "Using default policies"

            with open(policy_path, "r") as f:
                data = json.load(f)

            # Compute hash for versioning
            policy_hash = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]

            with self._policy_lock:
                self._policy = PolicyConfig(
                    version=data.get("version", "unknown"),
                    matrix=data.get("matrix", self._default_matrix),
                    path_mappings=data.get("path_mappings", []),
                    hash=policy_hash,
                )
                RBAC_POLICY_VERSION.set(int(policy_hash[:8], 16))

            RBAC_POLICY_LOADS.labels(status="success").inc()
            logger.info(f"RBAC policies reloaded: version={self._policy.version}, hash={policy_hash}")
            return True, f"Policies reloaded: {policy_hash}"

        except json.JSONDecodeError as e:
            RBAC_POLICY_LOADS.labels(status="parse_error").inc()
            logger.error(f"Failed to parse policy file: {e}")
            return False, f"JSON parse error: {e}"
        except Exception as e:
            RBAC_POLICY_LOADS.labels(status="error").inc()
            logger.error(f"Failed to reload policies: {e}")
            return False, str(e)

    def get_policy_info(self) -> Dict[str, Any]:
        """Get current policy information."""
        with self._policy_lock:
            if self._policy:
                return {
                    "version": self._policy.version,
                    "hash": self._policy.hash,
                    "loaded_at": self._policy.loaded_at.isoformat(),
                    "roles": list(self._policy.matrix.keys()),
                    "resources": list(set(r for perms in self._policy.matrix.values() for r in perms.keys())),
                }
            return {"version": "none", "hash": "none"}

    def check(self, policy: PolicyObject, request: Request, tenant_id: Optional[str] = None) -> Decision:
        """
        Check authorization for a policy.

        Args:
            policy: The policy to check
            request: The incoming request
            tenant_id: Optional tenant context

        Returns:
            Decision with allowed status and reason
        """
        start_time = time.time()

        try:
            # Extract roles from request
            roles = self._extract_roles(request)

            # If RBAC not enforced, allow with reason
            if not RBAC_ENFORCE:
                decision = Decision(allowed=True, reason="rbac-disabled", roles=roles, policy=policy)
                self._record_metrics(policy, decision, start_time)
                return decision

            # No credentials
            if not roles:
                decision = Decision(
                    allowed=RBAC_FAIL_OPEN,
                    reason="no-credentials" if not RBAC_FAIL_OPEN else "fail-open-no-credentials",
                    roles=[],
                    policy=policy,
                )
                self._record_metrics(policy, decision, start_time)
                self._audit(decision, request, tenant_id)
                return decision

            # Check permissions
            with self._policy_lock:
                matrix = self._policy.matrix if self._policy else self._default_matrix

            for role in roles:
                role_perms = matrix.get(role, {})
                allowed_actions = role_perms.get(policy.resource, [])

                if policy.action in allowed_actions:
                    decision = Decision(allowed=True, reason=f"role:{role}", roles=roles, policy=policy)
                    self._record_metrics(policy, decision, start_time)
                    self._audit(decision, request, tenant_id)
                    return decision

            # No matching permission
            decision = Decision(
                allowed=RBAC_FAIL_OPEN,
                reason="insufficient-permissions" if not RBAC_FAIL_OPEN else "fail-open-insufficient",
                roles=roles,
                policy=policy,
            )
            self._record_metrics(policy, decision, start_time)
            self._audit(decision, request, tenant_id)
            return decision

        except Exception as e:
            logger.error(f"RBAC check error: {e}")
            decision = Decision(
                allowed=RBAC_FAIL_OPEN, reason=f"error:{e}" if RBAC_FAIL_OPEN else "error", roles=[], policy=policy
            )
            self._record_metrics(policy, decision, start_time)
            return decision

    def _extract_roles(self, request: Request) -> List[str]:
        """Extract roles from request headers."""
        # Check machine token
        machine_token = request.headers.get("X-Machine-Token") or request.headers.get("Authorization-Machine")
        if machine_token and MACHINE_SECRET_TOKEN and machine_token == MACHINE_SECRET_TOKEN:
            return ["machine"]

        # Check JWT
        auth_header = request.headers.get("Authorization", "") or ""
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            try:
                if JWT_VERIFY_SIGNATURE and JWT_SECRET:
                    payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
                else:
                    payload = jwt.decode(token, options={"verify_signature": False})

                roles = payload.get("roles", [])
                if isinstance(roles, str):
                    roles = [roles]
                return roles

            except jwt.ExpiredSignatureError:
                logger.debug("JWT token expired")
                return []
            except jwt.InvalidTokenError as e:
                logger.debug(f"Invalid JWT token: {e}")
                return []

        # Check X-Roles header (for testing/dev)
        roles_header = request.headers.get("X-Roles", "")
        if roles_header:
            return [r.strip() for r in roles_header.split(",") if r.strip()]

        return []

    def _record_metrics(self, policy: PolicyObject, decision: Decision, start_time: float) -> None:
        """Record Prometheus metrics."""
        latency = time.time() - start_time
        decision.latency_ms = latency * 1000

        RBAC_ENGINE_DECISIONS.labels(
            resource=policy.resource,
            action=policy.action,
            decision="allowed" if decision.allowed else "denied",
            reason=decision.reason or "unknown",
        ).inc()
        RBAC_ENGINE_LATENCY.observe(latency)

    def _audit(self, decision: Decision, request: Request, tenant_id: Optional[str] = None) -> None:
        """Write audit log to database (async-safe)."""
        if not RBAC_AUDIT_ENABLED or not self._db_session_factory:
            return

        try:
            # Extract subject identifier
            subject = "unknown"
            if decision.roles:
                subject = ",".join(decision.roles)
            elif request.headers.get("X-Request-ID"):
                subject = f"req:{request.headers.get('X-Request-ID')}"

            # Get request ID if available
            request_id = request.headers.get("X-Request-ID")

            # Insert audit record (fire and forget for performance)
            # Handle both generator-based and regular session factories
            session_gen = self._db_session_factory()
            if hasattr(session_gen, "__next__"):
                # Generator-based factory (e.g., FastAPI dependency)
                session = next(session_gen)
            else:
                # Regular factory that returns session directly
                session = session_gen

            try:
                from sqlalchemy import text

                session.execute(
                    text(
                        """
                        INSERT INTO system.rbac_audit
                        (subject, resource, action, allowed, reason, roles, path, method, tenant_id, request_id, latency_ms)
                        VALUES (:subject, :resource, :action, :allowed, :reason, :roles, :path, :method, :tenant_id, :request_id, :latency_ms)
                    """
                    ),
                    {
                        "subject": subject,
                        "resource": decision.policy.resource if decision.policy else "unknown",
                        "action": decision.policy.action if decision.policy else "unknown",
                        "allowed": decision.allowed,
                        "reason": decision.reason,
                        "roles": decision.roles,
                        "path": str(request.url.path),
                        "method": request.method,
                        "tenant_id": tenant_id,
                        "request_id": request_id,
                        "latency_ms": decision.latency_ms,
                    },
                )
                session.commit()
                RBAC_AUDIT_WRITES.labels(status="success").inc()
            finally:
                session.close()
                # Clean up generator if applicable
                if hasattr(session_gen, "__next__"):
                    try:
                        next(session_gen)
                    except StopIteration:
                        pass

        except Exception as e:
            RBAC_AUDIT_WRITES.labels(status="error").inc()
            logger.warning(f"Failed to write audit log: {e}")


# =============================================================================
# Path to Policy Mapping
# =============================================================================


def get_policy_for_path(path: str, method: str) -> Optional[PolicyObject]:
    """
    Map request path and method to a PolicyObject.

    Returns None for paths that don't require RBAC.
    """
    # Memory pins
    if path.startswith("/api/v1/memory/pins"):
        if path.endswith("/cleanup"):
            return PolicyObject(resource="memory_pin", action="admin")
        elif method == "GET":
            return PolicyObject(resource="memory_pin", action="read")
        elif method in ("POST", "PUT", "PATCH"):
            return PolicyObject(resource="memory_pin", action="write")
        elif method == "DELETE":
            return PolicyObject(resource="memory_pin", action="delete")

    # RBAC management
    if path.startswith("/api/v1/rbac"):
        if "/reload" in path:
            return PolicyObject(resource="rbac", action="reload")
        return PolicyObject(resource="rbac", action="read")

    # Prometheus reload
    if path.startswith("/-/reload") or path.startswith("/api/observability/prom-reload"):
        return PolicyObject(resource="prometheus", action="reload")

    # Prometheus query
    if path.startswith("/api/v1/query") or path.startswith("/api/prometheus"):
        return PolicyObject(resource="prometheus", action="query")

    # CostSim
    if path.startswith("/api/v1/costsim"):
        if method == "GET":
            return PolicyObject(resource="costsim", action="read")
        else:
            return PolicyObject(resource="costsim", action="write")

    # Policy API
    if path.startswith("/api/v1/policy"):
        if "/approve" in path or "/reject" in path:
            return PolicyObject(resource="policy", action="approve")
        elif method == "GET":
            return PolicyObject(resource="policy", action="read")
        else:
            return PolicyObject(resource="policy", action="write")

    return None


# =============================================================================
# Global Engine Instance
# =============================================================================

_engine: Optional[RBACEngine] = None


def get_rbac_engine() -> RBACEngine:
    """Get or create global RBAC engine instance."""
    global _engine
    if _engine is None:
        _engine = RBACEngine()
    return _engine


def init_rbac_engine(db_session_factory: Callable) -> RBACEngine:
    """Initialize RBAC engine with database session factory."""
    global _engine
    _engine = RBACEngine(db_session_factory=db_session_factory)
    return _engine


# =============================================================================
# Convenience Functions
# =============================================================================


def check_permission(resource: str, action: str, request: Request, attrs: Optional[Dict[str, Any]] = None) -> Decision:
    """
    Programmatic permission check.

    Example:
        decision = check_permission("memory_pin", "write", request)
        if not decision.allowed:
            raise HTTPException(status_code=403, detail=decision.reason)
    """
    engine = get_rbac_engine()
    policy = PolicyObject(resource=resource, action=action, attrs=attrs or {})
    return engine.check(policy, request)


def require_permission(resource: str, action: str):
    """
    Decorator for requiring specific permissions.

    Example:
        @require_permission("memory_pin", "admin")
        async def admin_endpoint(request: Request):
            ...
    """
    from fastapi.responses import JSONResponse

    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            decision = check_permission(resource, action, request)
            if not decision.allowed:
                return JSONResponse(status_code=403, content={"error": "forbidden", "reason": decision.reason})
            return await func(request, *args, **kwargs)

        return wrapper

    return decorator
