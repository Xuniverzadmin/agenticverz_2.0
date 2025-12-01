# utils/canonical_json.py
"""
Canonical JSON serialization for AOS.

Ensures deterministic JSON output for:
- Replay testing
- Content hashing
- Golden file comparison

See: app/specs/canonical_json.md for full specification.
"""

from __future__ import annotations
import json
import hashlib
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Set, Union
from uuid import UUID
from enum import Enum


def canonical_json(obj: Any, exclude_fields: Optional[Set[str]] = None) -> str:
    """
    Serialize object to canonical JSON format.

    Rules:
    - Keys sorted alphabetically
    - No whitespace
    - UTF-8 encoding
    - Minimal escaping

    Args:
        obj: Object to serialize
        exclude_fields: Optional set of field names to exclude (for variance fields)

    Returns:
        Canonical JSON string
    """
    if exclude_fields:
        obj = _filter_fields(obj, exclude_fields)

    return json.dumps(
        obj,
        sort_keys=True,
        ensure_ascii=False,
        separators=(',', ':'),
        default=_json_serializer
    )


def canonical_json_bytes(obj: Any, exclude_fields: Optional[Set[str]] = None) -> bytes:
    """
    Serialize object to canonical JSON bytes (UTF-8).

    Args:
        obj: Object to serialize
        exclude_fields: Optional set of field names to exclude

    Returns:
        UTF-8 encoded canonical JSON bytes
    """
    return canonical_json(obj, exclude_fields).encode('utf-8')


def content_hash(obj: Any, exclude_fields: Optional[Set[str]] = None, length: int = 16) -> str:
    """
    Compute deterministic content hash.

    Args:
        obj: Object to hash
        exclude_fields: Fields to exclude from hash (e.g., timestamps)
        length: Length of hash to return (default 16 hex chars)

    Returns:
        Hex string of SHA-256 hash (truncated to length)
    """
    canonical = canonical_json_bytes(obj, exclude_fields)
    full_hash = hashlib.sha256(canonical).hexdigest()
    return full_hash[:length]


def content_hash_full(obj: Any, exclude_fields: Optional[Set[str]] = None) -> str:
    """
    Compute full SHA-256 content hash.

    Args:
        obj: Object to hash
        exclude_fields: Fields to exclude from hash

    Returns:
        Full 64-character hex hash
    """
    canonical = canonical_json_bytes(obj, exclude_fields)
    return hashlib.sha256(canonical).hexdigest()


# Default fields to exclude from deterministic comparisons
ALLOWED_VARIANCE_FIELDS = frozenset({
    'id',
    'created_at',
    'started_at',
    'completed_at',
    'updated_at',
    'duration_ms',
    'duration',
    'trace_id',
    'span_id',
    'request_id',
    'timestamp',
    'ts',
})


def deterministic_hash(obj: Any, length: int = 16) -> str:
    """
    Compute hash excluding allowed variance fields.

    This is the standard hashing function for replay comparisons.

    Args:
        obj: Object to hash
        length: Length of hash to return

    Returns:
        Hex hash string
    """
    return content_hash(obj, ALLOWED_VARIANCE_FIELDS, length)


def _json_serializer(obj: Any) -> Any:
    """
    Custom JSON serializer for non-standard types.

    Handles:
    - datetime/date → ISO format string
    - UUID → string
    - Enum → value
    - bytes → base64 string (if needed)
    - Objects with to_dict() method
    - Objects with __dict__ attribute
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, bytes):
        import base64
        return base64.b64encode(obj).decode('ascii')
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    if hasattr(obj, 'model_dump'):
        return obj.model_dump()
    if hasattr(obj, '__dict__'):
        return obj.__dict__

    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _filter_fields(obj: Any, exclude: Set[str]) -> Any:
    """
    Recursively filter out excluded fields from an object.

    Args:
        obj: Object to filter
        exclude: Set of field names to exclude

    Returns:
        Filtered object
    """
    if isinstance(obj, dict):
        return {
            k: _filter_fields(v, exclude)
            for k, v in obj.items()
            if k not in exclude
        }
    if isinstance(obj, list):
        return [_filter_fields(item, exclude) for item in obj]
    return obj


def is_canonical(json_str: str) -> bool:
    """
    Check if a JSON string is in canonical format.

    Args:
        json_str: JSON string to check

    Returns:
        True if canonical, False otherwise
    """
    try:
        obj = json.loads(json_str)
        canonical = canonical_json(obj)
        return json_str.strip() == canonical
    except json.JSONDecodeError:
        return False


def canonicalize_file(filepath: str) -> None:
    """
    Rewrite a JSON file in canonical format.

    Args:
        filepath: Path to JSON file

    Raises:
        ValueError: If file is not valid JSON
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    canonical = canonical_json(data)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(canonical)


def assert_canonical(filepath: str) -> None:
    """
    Assert that a JSON file is in canonical format.

    Args:
        filepath: Path to JSON file

    Raises:
        AssertionError: If file is not canonical
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if not is_canonical(content):
        raise AssertionError(f"File {filepath} is not in canonical JSON format")


# Comparison helpers for replay tests

def compare_deterministic(
    actual: Dict[str, Any],
    expected: Dict[str, Any],
    deterministic_fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Compare two outputs, checking only deterministic fields.

    Args:
        actual: Actual output
        expected: Expected output
        deterministic_fields: List of fields that must match exactly

    Returns:
        Dict with 'match' (bool) and 'differences' (list)
    """
    differences = []

    if deterministic_fields:
        for field in deterministic_fields:
            actual_val = _get_nested(actual, field)
            expected_val = _get_nested(expected, field)
            if actual_val != expected_val:
                differences.append({
                    'field': field,
                    'expected': expected_val,
                    'actual': actual_val
                })
    else:
        # Compare full content hash excluding variance fields
        actual_hash = deterministic_hash(actual)
        expected_hash = deterministic_hash(expected)
        if actual_hash != expected_hash:
            differences.append({
                'field': '_content_hash',
                'expected': expected_hash,
                'actual': actual_hash
            })

    return {
        'match': len(differences) == 0,
        'differences': differences
    }


def _get_nested(obj: Dict[str, Any], path: str) -> Any:
    """Get nested value using dot notation."""
    parts = path.split('.')
    current = obj
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current
