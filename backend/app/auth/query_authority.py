# Layer: L4 — Domain Engines (Authorization)
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Query authority enforcement for data access
# Reference: PIN-392
"""
Query Authority Enforcement

Enforces data query constraints declared in RBAC_RULES.yaml.
Controls WHAT KIND OF DATA a request may ask for.

Usage:
    from app.auth.query_authority import (
        enforce_query_authority,
        QueryAuthorityViolation,
    )

    # In your endpoint
    rule = resolve_rbac_rule(path, method, console, env, strict=True)
    enforce_query_authority(
        rule.query_authority,
        include_synthetic=request.query.get("include_synthetic", False),
        max_rows=request.query.get("limit", 100),
        time_range_days=calculate_time_range(request),
    )
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .rbac_rules_loader import AggregationLevel, QueryAuthority

# =============================================================================
# EXCEPTIONS
# =============================================================================


class QueryAuthorityViolation(Exception):
    """
    Raised when a query exceeds its declared authority.

    This exception enforces the PIN-392 invariant:
    "Data queries are privileges. They must be declared, not inferred."

    The caller must handle this exception explicitly.
    """

    def __init__(
        self,
        constraint: str,
        requested: Any,
        allowed: Any,
        message: str | None = None,
    ):
        self.constraint = constraint
        self.requested = requested
        self.allowed = allowed
        if message is None:
            message = (
                f"QUERY AUTHORITY VIOLATION: {constraint} exceeded. "
                f"Requested: {requested}, Allowed: {allowed}. "
                f"Update query_authority in RBAC_RULES.yaml to change limits (PIN-392)"
            )
        super().__init__(message)


# =============================================================================
# ENFORCEMENT FUNCTIONS
# =============================================================================


def enforce_query_authority(
    qa: QueryAuthority,
    *,
    include_synthetic: bool = False,
    include_deleted: bool = False,
    include_internal: bool = False,
    requested_rows: int | None = None,
    time_range_days: int | None = None,
    aggregation: str | AggregationLevel | None = None,
    export_requested: bool = False,
) -> None:
    """
    Enforce query authority constraints.

    Args:
        qa: QueryAuthority from the resolved RBAC rule
        include_synthetic: Whether synthetic data was requested
        include_deleted: Whether deleted records were requested
        include_internal: Whether internal records were requested
        requested_rows: Number of rows requested
        time_range_days: Time range in days being queried
        aggregation: Aggregation level requested
        export_requested: Whether export was requested

    Raises:
        QueryAuthorityViolation: If any constraint is exceeded

    Example:
        rule = resolve_rbac_rule("/api/v1/incidents/", "GET", "customer", "preflight", strict=True)
        enforce_query_authority(
            rule.query_authority,
            include_synthetic=True,
            requested_rows=500,
        )
    """
    # Check include_synthetic
    if include_synthetic and not qa.include_synthetic:
        raise QueryAuthorityViolation(
            constraint="include_synthetic",
            requested=True,
            allowed=False,
        )

    # Check include_deleted
    if include_deleted and not qa.include_deleted:
        raise QueryAuthorityViolation(
            constraint="include_deleted",
            requested=True,
            allowed=False,
        )

    # Check include_internal
    if include_internal and not qa.include_internal:
        raise QueryAuthorityViolation(
            constraint="include_internal",
            requested=True,
            allowed=False,
        )

    # Check row limit
    if requested_rows is not None and requested_rows > qa.max_rows:
        raise QueryAuthorityViolation(
            constraint="max_rows",
            requested=requested_rows,
            allowed=qa.max_rows,
        )

    # Check time range
    if time_range_days is not None and time_range_days > qa.max_time_range_days:
        raise QueryAuthorityViolation(
            constraint="max_time_range_days",
            requested=time_range_days,
            allowed=qa.max_time_range_days,
        )

    # Check aggregation level
    if aggregation is not None:
        requested_level = AggregationLevel(aggregation) if isinstance(aggregation, str) else aggregation
        if not _aggregation_permitted(requested_level, qa.aggregation):
            raise QueryAuthorityViolation(
                constraint="aggregation",
                requested=requested_level.value,
                allowed=qa.aggregation.value,
            )

    # Check export
    if export_requested and not qa.export_allowed:
        raise QueryAuthorityViolation(
            constraint="export_allowed",
            requested=True,
            allowed=False,
        )


def _aggregation_permitted(
    requested: AggregationLevel,
    allowed: AggregationLevel,
) -> bool:
    """Check if requested aggregation level is permitted."""
    # Aggregation hierarchy: NONE < BASIC < FULL
    hierarchy = {
        AggregationLevel.NONE: 0,
        AggregationLevel.BASIC: 1,
        AggregationLevel.FULL: 2,
    }
    return hierarchy.get(requested, 0) <= hierarchy.get(allowed, 0)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def calculate_time_range_days(
    start_date: datetime | str | None,
    end_date: datetime | str | None = None,
) -> int | None:
    """
    Calculate the time range in days between two dates.

    Args:
        start_date: Start of the time range
        end_date: End of the time range (defaults to now)

    Returns:
        Number of days, or None if start_date is None
    """
    if start_date is None:
        return None

    if isinstance(start_date, str):
        start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))

    if end_date is None:
        end_date = datetime.now(start_date.tzinfo)
    elif isinstance(end_date, str):
        end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

    delta = abs(end_date - start_date)
    return delta.days + 1  # Include both endpoints


@dataclass
class QueryConstraints:
    """
    Extracted query constraints from request parameters.

    Helper for collecting all constraints before enforcement.
    """

    include_synthetic: bool = False
    include_deleted: bool = False
    include_internal: bool = False
    requested_rows: int | None = None
    time_range_days: int | None = None
    aggregation: AggregationLevel | None = None
    export_requested: bool = False

    def enforce(self, qa: QueryAuthority) -> None:
        """Enforce these constraints against the given authority."""
        enforce_query_authority(
            qa,
            include_synthetic=self.include_synthetic,
            include_deleted=self.include_deleted,
            include_internal=self.include_internal,
            requested_rows=self.requested_rows,
            time_range_days=self.time_range_days,
            aggregation=self.aggregation,
            export_requested=self.export_requested,
        )


def extract_query_constraints(
    query_params: dict[str, Any],
    start_date_param: str = "start_date",
    end_date_param: str = "end_date",
    limit_param: str = "limit",
) -> QueryConstraints:
    """
    Extract query constraints from request query parameters.

    Args:
        query_params: Dictionary of query parameters
        start_date_param: Name of the start date parameter
        end_date_param: Name of the end date parameter
        limit_param: Name of the limit parameter

    Returns:
        QueryConstraints object ready for enforcement
    """
    # Parse boolean flags
    include_synthetic = _parse_bool(query_params.get("include_synthetic", False))
    include_deleted = _parse_bool(query_params.get("include_deleted", False))
    include_internal = _parse_bool(query_params.get("include_internal", False))
    export_requested = _parse_bool(query_params.get("export", False))

    # Parse row limit
    limit = query_params.get(limit_param)
    requested_rows = int(limit) if limit is not None else None

    # Parse time range
    start_date = query_params.get(start_date_param)
    end_date = query_params.get(end_date_param)
    time_range_days = calculate_time_range_days(start_date, end_date)

    # Parse aggregation
    agg = query_params.get("aggregation")
    aggregation = AggregationLevel(agg) if agg else None

    return QueryConstraints(
        include_synthetic=include_synthetic,
        include_deleted=include_deleted,
        include_internal=include_internal,
        requested_rows=requested_rows,
        time_range_days=time_range_days,
        aggregation=aggregation,
        export_requested=export_requested,
    )


def _parse_bool(value: Any) -> bool:
    """Parse a boolean value from query parameter."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    return bool(value)


# =============================================================================
# PROMOTION VALIDATION
# =============================================================================


def validate_promotion_safety(
    preflight_qa: QueryAuthority,
    production_qa: QueryAuthority,
) -> list[str]:
    """
    Validate that production query authority is not more permissive than preflight.

    INVARIANT: Production can only be more restrictive, never looser.

    Args:
        preflight_qa: QueryAuthority from preflight rule
        production_qa: QueryAuthority from production rule

    Returns:
        List of violations (empty if safe to promote)
    """
    violations = []

    # Production must not allow synthetic if preflight doesn't
    if production_qa.include_synthetic and not preflight_qa.include_synthetic:
        violations.append("include_synthetic: production allows synthetic but preflight doesn't")

    # Production must have same or fewer rows
    if production_qa.max_rows > preflight_qa.max_rows:
        violations.append(f"max_rows: production ({production_qa.max_rows}) > preflight ({preflight_qa.max_rows})")

    # Production must have same or shorter time range
    if production_qa.max_time_range_days > preflight_qa.max_time_range_days:
        violations.append(
            f"max_time_range_days: production ({production_qa.max_time_range_days}) > "
            f"preflight ({preflight_qa.max_time_range_days})"
        )

    # Production must have same or lower aggregation
    hierarchy = {
        AggregationLevel.NONE: 0,
        AggregationLevel.BASIC: 1,
        AggregationLevel.FULL: 2,
    }
    if hierarchy[production_qa.aggregation] > hierarchy[preflight_qa.aggregation]:
        violations.append(
            f"aggregation: production ({production_qa.aggregation.value}) > "
            f"preflight ({preflight_qa.aggregation.value})"
        )

    # Production synthetic must be false (critical safety check)
    if production_qa.include_synthetic:
        violations.append("CRITICAL: include_synthetic must be false in production")

    return violations
