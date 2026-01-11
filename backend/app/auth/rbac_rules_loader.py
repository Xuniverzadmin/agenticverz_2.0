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

    # Resolve a specific request
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
# CONFIGURATION
# =============================================================================

# Path to canonical RBAC rules (relative to repo root)
RBAC_RULES_PATH = Path(__file__).parent.parent.parent.parent / "design/auth/RBAC_RULES.yaml"


# =============================================================================
# ENUMS
# =============================================================================


class AccessTier(str, Enum):
    """Authorization access tiers."""

    PUBLIC = "PUBLIC"
    SESSION = "SESSION"
    PRIVILEGED = "PRIVILEGED"
    SYSTEM = "SYSTEM"


class ConsoleKind(str, Enum):
    """Console types."""

    CUSTOMER = "customer"
    FOUNDER = "founder"


class Environment(str, Enum):
    """Deployment environments."""

    PREFLIGHT = "preflight"
    PRODUCTION = "production"


# =============================================================================
# DATA CLASSES
# =============================================================================


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

    @classmethod
    def from_dict(cls, data: dict) -> "RBACRule":
        """Create RBACRule from YAML dict."""
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

    rules = data.get("rules", [])
    return tuple(RBACRule.from_dict(rule) for rule in rules)


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
) -> Optional[RBACRule]:
    """
    Find the RBAC rule that matches the given request context.

    Args:
        path: Request path (e.g., "/api/v1/incidents/")
        method: HTTP method (e.g., "GET")
        console_kind: Console type ("customer" or "founder")
        environment: Environment ("preflight" or "production")

    Returns:
        Matching RBACRule or None if no rule matches.

    Note:
        First matching rule wins. Rules are evaluated in order.
        More specific rules should be defined before general ones.
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
    """
    rule = resolve_rbac_rule(path, method, console_kind, environment)
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
