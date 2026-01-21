# Layer: L4 — Domain Engines (Authorization)
# Product: system-wide
# Temporal:
#   Trigger: import
#   Execution: sync
# Role: Load RBAC rules from canonical YAML schema
# Reference: PIN-391
"""
RBAC Rules Loader

Loads authorization rules from the canonical RBAC_RULES.yaml schema.
This is the bridge between the declarative schema and runtime enforcement.

Usage:
    from app.auth.rbac_rules_loader import (
        load_rbac_rules,
        resolve_rbac_rule,
        get_public_paths,
        RBACRule,
    )

    # Get all rules
    rules = load_rbac_rules()

    # Resolve a specific request (raises RBACSchemaViolation if no rule)
    rule = resolve_rbac_rule("/api/v1/incidents/", "GET", "customer", "preflight")

    # Get PUBLIC paths for backward compatibility
    public_paths = get_public_paths()
"""

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml

# =============================================================================
# EXCEPTIONS
# =============================================================================


class RBACSchemaViolation(Exception):
    """
    Raised when an RBAC rule is missing for a given request context.

    This exception enforces the PIN-391 invariant:
    "If a rule is missing, access is DENIED."

    The caller must handle this exception explicitly.
    Catching and ignoring it is a governance violation.
    """

    def __init__(
        self,
        path: str,
        method: str,
        console_kind: str,
        environment: str,
        message: str | None = None,
    ):
        self.path = path
        self.method = method
        self.console_kind = console_kind
        self.environment = environment
        if message is None:
            message = (
                f"RBAC RULE MISSING: No rule covers {method} {path} "
                f"for console={console_kind}, env={environment}. "
                f"Add rule to design/auth/RBAC_RULES.yaml (PIN-391)"
            )
        super().__init__(message)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Path to canonical RBAC rules (relative to repo root)
RBAC_RULES_PATH = Path(__file__).parent.parent.parent.parent / "design/auth/RBAC_RULES.yaml"


# =============================================================================
# ENUMS
# =============================================================================


class AccessTier(str, Enum):
    """Authorization access tiers.

    PIN-440: MACHINE tier added for SDK/CLI machine-to-machine authentication.
    Machine callers use API keys (X-AOS-Key) and have capabilities, not roles.
    """

    PUBLIC = "PUBLIC"
    SESSION = "SESSION"
    PRIVILEGED = "PRIVILEGED"
    MACHINE = "MACHINE"  # PIN-440: For SDK/CLI with X-AOS-Key auth
    SYSTEM = "SYSTEM"


class ConsoleKind(str, Enum):
    """Console types."""

    CUSTOMER = "customer"
    FOUNDER = "founder"


class Environment(str, Enum):
    """Deployment environments."""

    PREFLIGHT = "preflight"
    PRODUCTION = "production"


class AggregationLevel(str, Enum):
    """Query aggregation levels (PIN-392)."""

    NONE = "NONE"  # No aggregation, raw records only
    BASIC = "BASIC"  # Count, sum, avg on non-sensitive fields
    FULL = "FULL"  # All aggregations including sensitive metrics


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass(frozen=True)
class QueryAuthority:
    """
    Query authority constraints for data access (PIN-392).

    Controls WHAT KIND OF DATA a request may ask for.
    Orthogonal to route access (WHO may touch WHAT).

    INVARIANT: Data queries are privileges.
               They must be declared, authorized, constrained — not inferred.
    """

    include_synthetic: bool = False
    include_deleted: bool = False
    include_internal: bool = False
    max_rows: int = 100
    max_time_range_days: int = 7
    aggregation: AggregationLevel = AggregationLevel.NONE
    export_allowed: bool = False

    @classmethod
    def from_dict(cls, data: dict | None, defaults: dict | None = None) -> "QueryAuthority":
        """Create QueryAuthority from YAML dict, merging with defaults."""
        if data is None and defaults is None:
            return cls()

        merged = {}
        if defaults:
            merged.update(defaults)
        if data:
            merged.update(data)

        aggregation = merged.get("aggregation", "NONE")
        if isinstance(aggregation, str):
            aggregation = AggregationLevel(aggregation)

        return cls(
            include_synthetic=merged.get("include_synthetic", False),
            include_deleted=merged.get("include_deleted", False),
            include_internal=merged.get("include_internal", False),
            max_rows=merged.get("max_rows", 100),
            max_time_range_days=merged.get("max_time_range_days", 7),
            aggregation=aggregation,
            export_allowed=merged.get("export_allowed", False),
        )


@dataclass(frozen=True)
class RBACRule:
    """Immutable RBAC rule from schema."""

    rule_id: str
    path_prefix: str
    methods: tuple[str, ...]
    access_tier: AccessTier
    allow_console: tuple[str, ...]
    allow_environment: tuple[str, ...]
    pin: Optional[str] = None
    required_permissions: tuple[str, ...] = ()
    required_roles: tuple[str, ...] = ()
    description: str = ""
    temporary: bool = False
    expires: Optional[str] = None
    query_authority: QueryAuthority = None  # type: ignore[assignment]

    def __post_init__(self):
        # Ensure query_authority is never None
        if self.query_authority is None:
            object.__setattr__(self, "query_authority", QueryAuthority())

    @classmethod
    def from_dict(cls, data: dict, qa_defaults: dict | None = None) -> "RBACRule":
        """Create RBACRule from YAML dict."""
        qa_data = data.get("query_authority")
        query_authority = QueryAuthority.from_dict(qa_data, qa_defaults)

        return cls(
            rule_id=data["rule_id"],
            path_prefix=data["path_prefix"],
            methods=tuple(data.get("methods", [])),
            access_tier=AccessTier(data["access_tier"]),
            allow_console=tuple(data.get("allow_console", [])),
            allow_environment=tuple(data.get("allow_environment", [])),
            pin=data.get("pin"),
            required_permissions=tuple(data.get("required_permissions", [])),
            required_roles=tuple(data.get("required_roles", [])),
            description=data.get("description", ""),
            temporary=data.get("temporary", False),
            expires=data.get("expires"),
            query_authority=query_authority,
        )


# =============================================================================
# LOADER FUNCTIONS
# =============================================================================


@lru_cache(maxsize=1)
def load_rbac_rules() -> tuple[RBACRule, ...]:
    """
    Load RBAC rules from canonical YAML schema.

    Returns:
        Tuple of RBACRule objects (immutable, cached).

    Raises:
        FileNotFoundError: If RBAC_RULES.yaml does not exist.
        yaml.YAMLError: If YAML is malformed.
    """
    if not RBAC_RULES_PATH.exists():
        # Fail-closed: no rules = no access
        raise FileNotFoundError(
            f"RBAC_RULES.yaml not found at {RBAC_RULES_PATH}. Authorization cannot proceed without canonical rules."
        )

    with RBAC_RULES_PATH.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Load query_authority_defaults (PIN-392)
    qa_defaults = data.get("query_authority_defaults")

    rules = data.get("rules", [])
    return tuple(RBACRule.from_dict(rule, qa_defaults) for rule in rules)


def reload_rbac_rules() -> tuple[RBACRule, ...]:
    """
    Force reload of RBAC rules (clears cache).

    Use sparingly - mainly for testing or hot-reload scenarios.
    """
    load_rbac_rules.cache_clear()
    return load_rbac_rules()


# =============================================================================
# RESOLUTION FUNCTIONS
# =============================================================================


def resolve_rbac_rule(
    path: str,
    method: str,
    console_kind: str,
    environment: str,
    *,
    strict: bool = True,
) -> Optional[RBACRule]:
    """
    Find the RBAC rule that matches the given request context.

    Args:
        path: Request path (e.g., "/api/v1/incidents/")
        method: HTTP method (e.g., "GET")
        console_kind: Console type ("customer" or "founder")
        environment: Environment ("preflight" or "production")
        strict: If True (default), raise RBACSchemaViolation when no rule matches.
                If False, return None for backward compatibility with legacy code.

    Returns:
        Matching RBACRule or None if no rule matches (and strict=False).

    Raises:
        RBACSchemaViolation: If strict=True and no rule matches.

    Note:
        First matching rule wins. Rules are evaluated in order.
        More specific rules should be defined before general ones.

        INVARIANT (PIN-391): strict=True is the default. Missing rules are
        governance violations, not silent failures. Use strict=False only
        during migration or in explicitly backward-compatible code paths.

    Example:
        # Default behavior (raises exception if no rule)
        rule = resolve_rbac_rule("/api/v1/foo/", "GET", "customer", "preflight")

        # Legacy behavior (returns None for backward compatibility)
        rule = resolve_rbac_rule("/api/v1/foo/", "GET", "customer", "preflight", strict=False)
    """
    rules = load_rbac_rules()
    method_upper = method.upper()

    for rule in rules:
        # Path prefix match
        if not path.startswith(rule.path_prefix):
            continue

        # Method match
        if method_upper not in rule.methods:
            continue

        # Console kind match
        if console_kind not in rule.allow_console:
            continue

        # Environment match
        if environment not in rule.allow_environment:
            continue

        return rule

    # No rule matched
    if strict:
        raise RBACSchemaViolation(path, method, console_kind, environment)

    return None


def is_path_public(
    path: str,
    method: str = "GET",
    console_kind: str = "customer",
    environment: str = "preflight",
) -> bool:
    """
    Check if a path is publicly accessible for the given context.

    Args:
        path: Request path
        method: HTTP method (default: GET)
        console_kind: Console type (default: customer)
        environment: Environment (default: preflight)

    Returns:
        True if the path is PUBLIC tier, False otherwise.
        Unknown paths return False (not an exception).
    """
    # Use strict=False because unknown paths should return False, not raise
    rule = resolve_rbac_rule(path, method, console_kind, environment, strict=False)
    if rule is None:
        return False
    return rule.access_tier == AccessTier.PUBLIC


# =============================================================================
# BACKWARD COMPATIBILITY
# =============================================================================


def get_public_paths(environment: str = "preflight") -> list[str]:
    """
    Get list of PUBLIC path prefixes for backward compatibility.

    This function exists to support the transition from hardcoded
    PUBLIC_PATHS to schema-driven RBAC_RULES.

    Args:
        environment: Environment to check ("preflight" or "production")

    Returns:
        List of path prefixes that are PUBLIC in the given environment.
    """
    rules = load_rbac_rules()
    public_paths: list[str] = []

    for rule in rules:
        if rule.access_tier != AccessTier.PUBLIC:
            continue
        if environment not in rule.allow_environment:
            continue
        if rule.path_prefix not in public_paths:
            public_paths.append(rule.path_prefix)

    return public_paths


def get_temporary_rules() -> list[RBACRule]:
    """
    Get all temporary RBAC rules.

    These rules are marked for review/removal and should be
    audited regularly.

    Returns:
        List of temporary RBACRule objects.
    """
    rules = load_rbac_rules()
    return [rule for rule in rules if rule.temporary]


# =============================================================================
# VALIDATION
# =============================================================================


def validate_rbac_rules() -> list[str]:
    """
    Validate RBAC rules for consistency issues.

    Returns:
        List of validation errors (empty if valid).
    """
    errors: list[str] = []
    rules = load_rbac_rules()
    rule_ids = set()

    for rule in rules:
        # Check for duplicate rule IDs
        if rule.rule_id in rule_ids:
            errors.append(f"Duplicate rule_id: {rule.rule_id}")
        rule_ids.add(rule.rule_id)

        # Check PRIVILEGED rules have permissions
        if rule.access_tier == AccessTier.PRIVILEGED:
            if not rule.required_permissions and not rule.required_roles:
                errors.append(f"PRIVILEGED rule {rule.rule_id} has no required_permissions or required_roles")

        # Check temporary rules have expiry
        if rule.temporary and not rule.expires:
            errors.append(f"Temporary rule {rule.rule_id} has no expires date")

    return errors


# =============================================================================
# CLI INTERFACE
# =============================================================================

if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("RBAC Rules Loader - Validation Report")
    print("=" * 60)

    try:
        rules = load_rbac_rules()
        print(f"\nLoaded {len(rules)} rules from {RBAC_RULES_PATH}")

        # Validation
        errors = validate_rbac_rules()
        if errors:
            print("\nValidation Errors:")
            for err in errors:
                print(f"  - {err}")
            sys.exit(1)
        else:
            print("\nValidation: PASSED")

        # Summary by tier
        print("\nRules by Access Tier:")
        tier_counts = {}
        for rule in rules:
            tier = rule.access_tier.value
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
        for tier, count in sorted(tier_counts.items()):
            print(f"  {tier}: {count}")

        # Temporary rules
        temp_rules = get_temporary_rules()
        if temp_rules:
            print(f"\nTemporary Rules ({len(temp_rules)}):")
            for rule in temp_rules:
                print(f"  - {rule.rule_id} (expires: {rule.expires})")

        # Public paths
        print("\nPublic Paths (preflight):")
        for path in get_public_paths("preflight"):
            print(f"  - {path}")

        print("\n" + "=" * 60)
        sys.exit(0)

    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(2)
