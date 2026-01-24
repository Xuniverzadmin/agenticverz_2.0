# Layer: L6 — Driver
# Product: system-wide
# Temporal:
#   Trigger: worker
#   Execution: sync
# Role: Workflow input/output canonicalization
# Callers: workflow engine
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: Workflow System

# Golden File Canonicalization (M4 Hardening)
"""
Canonicalization utilities for deterministic golden file comparison.

Provides:
1. Volatile field removal (timestamps, ephemeral IDs)
2. Float precision normalization
3. Key ordering for deterministic JSON
4. Sensitive field redaction
5. Key normalization (lowercase, collision-safe)

Design Principles:
- Deterministic: Same logical content produces same canonical form
- Configurable: Ignore fields can be customized per use case
- Auditable: Redacted fields are marked, not silently removed
- Case-insensitive: Keys are normalized to lowercase for consistency
"""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set

# Default volatile fields to ignore in golden comparisons
DEFAULT_VOLATILE_FIELDS: Set[str] = {
    "timestamp",
    "ts",
    "created_at",
    "updated_at",
    "started_at",
    "ended_at",
    "duration_ms",
    "latency_ms",
    "request_id",
    "trace_id",
    "span_id",
    "correlation_id",
}

# Fields that may contain sensitive data (exact match or suffix match)
SENSITIVE_FIELDS: Set[str] = {
    "password",
    "api_key",
    "apikey",
    "api_secret",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "auth_token",
    "credential",
    "credentials",
    "private_key",
    "ssn",
    "social_security",
    "credit_card",
    "card_number",
    "cvv",
    "pin",
}

# Patterns that indicate sensitive data (for substring matching)
SENSITIVE_PATTERNS: Set[str] = {
    "_key",
    "_token",
    "_secret",
    "_password",
    "_credential",
}

# Redaction marker
REDACTED_MARKER = "[REDACTED]"

# Key normalization mode
KEY_NORMALIZE_MODE = "lowercase"  # Options: "lowercase", "preserve", "snake_case"


def _normalize_key(key: str, mode: str = KEY_NORMALIZE_MODE) -> str:
    """
    Normalize a key for consistent comparison.

    Args:
        key: Original key name
        mode: Normalization mode (lowercase, preserve, snake_case)

    Returns:
        Normalized key
    """
    if mode == "lowercase":
        return key.lower()
    elif mode == "snake_case":
        # Convert camelCase/PascalCase to snake_case
        import re

        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", key)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
    else:  # preserve
        return key


def _resolve_key_collisions(items: list, mode: str = KEY_NORMALIZE_MODE) -> dict:
    """
    Resolve key collisions when normalizing.

    If two keys normalize to the same value (e.g., "userId" and "userid"),
    we keep the first one encountered (sorted order).

    Args:
        items: List of (key, value) tuples, already sorted
        mode: Normalization mode

    Returns:
        Dict with normalized keys (collision-safe)
    """
    result = {}
    seen_normalized = set()

    for key, value in items:
        normalized = _normalize_key(key, mode)

        if normalized in seen_normalized:
            # Collision detected - skip duplicate
            # This is deterministic because items are sorted
            continue

        seen_normalized.add(normalized)
        result[normalized] = value

    return result


def canonicalize_for_golden(
    obj: Any,
    ignore_fields: Optional[Set[str]] = None,
    redact_sensitive: bool = True,
    float_precision: int = 6,
    include_volatile: bool = False,
) -> Dict[str, Any]:
    """
    Canonicalize an object for golden file comparison.

    Args:
        obj: Object to canonicalize
        ignore_fields: Additional fields to ignore (merged with defaults)
        redact_sensitive: Whether to redact sensitive fields
        float_precision: Decimal places for float normalization
        include_volatile: If True, include volatile fields (for debugging)

    Returns:
        Canonicalized dictionary
    """
    volatile = set() if include_volatile else DEFAULT_VOLATILE_FIELDS.copy()
    if ignore_fields:
        volatile.update(ignore_fields)

    return _canonicalize_value(
        obj,
        volatile_fields=volatile,
        redact_sensitive=redact_sensitive,
        float_precision=float_precision,
    )


def _canonicalize_value(
    value: Any,
    volatile_fields: Set[str],
    redact_sensitive: bool,
    float_precision: int,
    current_key: str = "",
) -> Any:
    """Recursively canonicalize a value."""
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        # Normalize floats to fixed precision
        return round(value, float_precision)

    if isinstance(value, Decimal):
        return float(round(value, float_precision))

    if isinstance(value, str):
        # Check if current key is sensitive
        if redact_sensitive and _is_sensitive_key(current_key):
            return REDACTED_MARKER
        return value

    if isinstance(value, datetime):
        # Convert datetimes to ISO format for non-volatile fields
        return value.isoformat()

    if isinstance(value, bytes):
        # Hash bytes for deterministic comparison
        return f"[BYTES:{hashlib.sha256(value).hexdigest()[:16]}]"

    if isinstance(value, (list, tuple)):
        return [
            _canonicalize_value(
                item,
                volatile_fields,
                redact_sensitive,
                float_precision,
            )
            for item in value
        ]

    if isinstance(value, dict):
        result = {}
        # Sort keys for determinism before processing
        sorted_items = sorted(value.items())

        for k, v in sorted_items:
            # Normalize key for comparison (lowercase by default)
            normalized_key = _normalize_key(k)

            # Skip volatile fields (check both original and normalized)
            if k.lower() in volatile_fields or normalized_key in volatile_fields:
                continue
            # Skip None values for cleaner output
            if v is None:
                continue
            # Skip if we already have this normalized key (collision resolution)
            if normalized_key in result:
                continue
            # Redact sensitive fields
            if redact_sensitive and _is_sensitive_key(k):
                result[normalized_key] = REDACTED_MARKER
            else:
                result[normalized_key] = _canonicalize_value(
                    v,
                    volatile_fields,
                    redact_sensitive,
                    float_precision,
                    current_key=k,
                )
        return result

    # For objects with to_dict method
    if hasattr(value, "to_dict"):
        return _canonicalize_value(
            value.to_dict(),
            volatile_fields,
            redact_sensitive,
            float_precision,
        )

    # For objects with __dict__
    if hasattr(value, "__dict__"):
        return _canonicalize_value(
            {k: v for k, v in value.__dict__.items() if not k.startswith("_")},
            volatile_fields,
            redact_sensitive,
            float_precision,
        )

    # Fallback: convert to string
    return str(value)


def _is_sensitive_key(key: str) -> bool:
    """Check if a key name indicates sensitive data."""
    key_lower = key.lower()
    # Exact match
    if key_lower in SENSITIVE_FIELDS:
        return True
    # Pattern match (suffix)
    for pattern in SENSITIVE_PATTERNS:
        if key_lower.endswith(pattern):
            return True
    return False


def canonical_json(
    obj: Any,
    ignore_fields: Optional[Set[str]] = None,
    redact_sensitive: bool = True,
    float_precision: int = 6,
) -> str:
    """
    Produce canonical JSON string for deterministic comparison.

    Args:
        obj: Object to serialize
        ignore_fields: Fields to ignore
        redact_sensitive: Whether to redact sensitive fields
        float_precision: Decimal places for floats

    Returns:
        Canonical JSON string (sorted keys, no extra whitespace)
    """
    canonical = canonicalize_for_golden(
        obj,
        ignore_fields=ignore_fields,
        redact_sensitive=redact_sensitive,
        float_precision=float_precision,
    )
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"))


def canonical_hash(
    obj: Any,
    ignore_fields: Optional[Set[str]] = None,
    redact_sensitive: bool = True,
) -> str:
    """
    Compute deterministic hash of an object.

    Args:
        obj: Object to hash
        ignore_fields: Fields to ignore
        redact_sensitive: Whether to redact sensitive fields

    Returns:
        SHA256 hash (first 16 characters)
    """
    json_str = canonical_json(
        obj,
        ignore_fields=ignore_fields,
        redact_sensitive=redact_sensitive,
    )
    return hashlib.sha256(json_str.encode()).hexdigest()[:16]


def redact_sensitive_fields(
    obj: Any,
    additional_fields: Optional[Set[str]] = None,
) -> Any:
    """
    Redact sensitive fields from an object (in-place safe copy).

    Args:
        obj: Object to redact
        additional_fields: Additional field names to redact

    Returns:
        Copy of object with sensitive fields redacted
    """
    sensitive = SENSITIVE_FIELDS.copy()
    if additional_fields:
        sensitive.update(additional_fields)

    return _redact_recursive(copy.deepcopy(obj), sensitive)


def _redact_recursive(obj: Any, sensitive_fields: Set[str]) -> Any:
    """Recursively redact sensitive fields."""
    if isinstance(obj, dict):
        for key in list(obj.keys()):
            if _is_sensitive_key(key) or key.lower() in sensitive_fields:
                obj[key] = REDACTED_MARKER
            else:
                obj[key] = _redact_recursive(obj[key], sensitive_fields)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            obj[i] = _redact_recursive(item, sensitive_fields)
    return obj


def compare_canonical(
    actual: Any,
    expected: Any,
    ignore_fields: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """
    Compare two objects after canonicalization.

    Args:
        actual: Actual value
        expected: Expected value
        ignore_fields: Fields to ignore in comparison

    Returns:
        Dict with 'match' boolean and 'diffs' list
    """
    actual_canonical = canonicalize_for_golden(actual, ignore_fields=ignore_fields)
    expected_canonical = canonicalize_for_golden(expected, ignore_fields=ignore_fields)

    if actual_canonical == expected_canonical:
        return {"match": True, "diffs": []}

    diffs = _find_diffs(actual_canonical, expected_canonical, path="")
    return {"match": False, "diffs": diffs}


def _find_diffs(actual: Any, expected: Any, path: str) -> List[Dict[str, Any]]:
    """Find differences between two canonicalized objects."""
    diffs = []

    if type(actual) != type(expected):
        diffs.append(
            {
                "path": path or "root",
                "type": "type_mismatch",
                "actual_type": type(actual).__name__,
                "expected_type": type(expected).__name__,
            }
        )
        return diffs

    if isinstance(actual, dict):
        all_keys = set(actual.keys()) | set(expected.keys())
        for key in sorted(all_keys):
            key_path = f"{path}.{key}" if path else key
            if key not in actual:
                diffs.append(
                    {
                        "path": key_path,
                        "type": "missing_in_actual",
                        "expected": expected[key],
                    }
                )
            elif key not in expected:
                diffs.append(
                    {
                        "path": key_path,
                        "type": "extra_in_actual",
                        "actual": actual[key],
                    }
                )
            else:
                diffs.extend(_find_diffs(actual[key], expected[key], key_path))

    elif isinstance(actual, list):
        if len(actual) != len(expected):
            diffs.append(
                {
                    "path": path or "root",
                    "type": "length_mismatch",
                    "actual_length": len(actual),
                    "expected_length": len(expected),
                }
            )
        for i, (a, e) in enumerate(zip(actual, expected)):
            diffs.extend(_find_diffs(a, e, f"{path}[{i}]"))

    else:
        if actual != expected:
            diffs.append(
                {
                    "path": path or "root",
                    "type": "value_mismatch",
                    "actual": actual,
                    "expected": expected,
                }
            )

    return diffs


def strip_volatile_from_events(
    events: List[Dict[str, Any]],
    ignore_fields: Optional[Set[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Strip volatile fields from a list of golden events.

    Args:
        events: List of event dictionaries
        ignore_fields: Additional fields to strip

    Returns:
        List of events with volatile fields removed
    """
    return [canonicalize_for_golden(event, ignore_fields=ignore_fields, redact_sensitive=False) for event in events]
