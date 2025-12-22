# json_transform_v2.py
"""
JSON Transform Skill v2 (M3)

Deterministic, contract-compliant JSON transformation skill.
Returns StructuredOutcome for all operations.
Produces canonical JSON for replay compatibility.

See: app/skills/contracts/json_transform.contract.yaml
"""

import hashlib
import json
import logging
import re
import sys

# Path setup for imports
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

_backend = Path(__file__).parent.parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from app.worker.runtime.core import SkillDescriptor, StructuredOutcome

logger = logging.getLogger("nova.skills.json_transform_v2")


# =============================================================================
# Canonical JSON Utilities
# =============================================================================


def _canonical_json(obj: Any) -> str:
    """Produce canonical JSON (sorted keys, no whitespace)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _content_hash(obj: Any, length: int = 16) -> str:
    """Compute SHA256 hash of canonical JSON representation."""
    canonical = _canonical_json(obj).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()[:length]


def _measure_depth(obj: Any, current: int = 0) -> int:
    """Measure maximum nesting depth of JSON structure."""
    if isinstance(obj, dict):
        if not obj:
            return current + 1
        return max(_measure_depth(v, current + 1) for v in obj.values())
    elif isinstance(obj, list):
        if not obj:
            return current + 1
        return max(_measure_depth(item, current + 1) for item in obj)
    return current


# =============================================================================
# Path Extraction
# =============================================================================


def _parse_jsonpath(path: str) -> List[Union[str, int]]:
    """
    Parse JSONPath-like expression into segments.

    Supports:
    - Root: $
    - Dot notation: $.user.name
    - Bracket notation: $['user']['name']
    - Array index: $.items[0], $.items[-1]

    Returns:
        List of segments (strings for keys, ints for array indices)
    """
    if not path.startswith("$"):
        raise ValueError(f"Path must start with '$': {path}")

    # Remove leading $
    path = path[1:]
    if not path:
        return []

    # Remove leading dot if present
    if path.startswith("."):
        path = path[1:]

    if not path:
        return []

    segments = []
    i = 0

    while i < len(path):
        if path[i] == ".":
            i += 1
            continue

        # Bracket notation: ['key'] or [0]
        if path[i] == "[":
            end = path.index("]", i)
            content = path[i + 1 : end]

            # String key: ['key'] or ["key"]
            if content.startswith("'") or content.startswith('"'):
                segments.append(content[1:-1])
            else:
                # Array index
                segments.append(int(content))

            i = end + 1
        else:
            # Dot notation: find next . or [
            end = len(path)
            for j in range(i, len(path)):
                if path[j] in ".[]":
                    end = j
                    break

            key = path[i:end]

            # Check for array index attached to key: items[0]
            bracket_match = re.match(r"^([^\[]+)\[(-?\d+)\]$", key)
            if bracket_match:
                key_part, idx = bracket_match.groups()
                segments.append(key_part)
                segments.append(int(idx))
            elif key:
                segments.append(key)

            i = end

    return segments


def _get_at_path(data: Any, segments: List[Union[str, int]]) -> tuple[Any, bool]:
    """
    Navigate to value at path.

    Returns:
        (value, found)
    """
    current = data

    for segment in segments:
        if current is None:
            return None, False

        if isinstance(segment, int):
            # Array index
            if isinstance(current, (list, tuple)):
                try:
                    current = current[segment]
                except IndexError:
                    return None, False
            else:
                return None, False
        else:
            # String key
            if isinstance(current, dict) and segment in current:
                current = current[segment]
            else:
                return None, False

    return current, True


# =============================================================================
# Transform Operations
# =============================================================================


def _op_extract(data: Any, params: Dict[str, Any]) -> tuple[Any, Optional[str]]:
    """Extract value at path."""
    path = params.get("path")
    if not path:
        return None, "Missing 'path' parameter for extract operation"

    try:
        segments = _parse_jsonpath(path)
    except (ValueError, IndexError) as e:
        return None, f"Invalid path: {e}"

    value, found = _get_at_path(data, segments)
    if not found:
        return None, f"Path not found: {path}"

    return value, None


def _op_pick(data: Any, params: Dict[str, Any]) -> tuple[Any, Optional[str]]:
    """Pick specific keys from object."""
    if not isinstance(data, dict):
        return None, "pick operation requires object input"

    keys = params.get("keys", [])
    if not keys:
        return None, "Missing 'keys' parameter for pick operation"

    result = {k: data[k] for k in keys if k in data}
    return result, None


def _op_omit(data: Any, params: Dict[str, Any]) -> tuple[Any, Optional[str]]:
    """Omit specific keys from object."""
    if not isinstance(data, dict):
        return None, "omit operation requires object input"

    keys = set(params.get("keys", []))
    if not keys:
        return None, "Missing 'keys' parameter for omit operation"

    result = {k: v for k, v in data.items() if k not in keys}
    return result, None


def _op_filter(data: Any, params: Dict[str, Any]) -> tuple[Any, Optional[str]]:
    """Filter array by condition."""
    if not isinstance(data, list):
        return None, "filter operation requires array input"

    condition = params.get("condition")
    if not condition:
        return None, "Missing 'condition' parameter for filter operation"

    field_name = condition.get("field")
    operator = condition.get("operator", "eq")
    value = condition.get("value")

    if not field_name:
        return None, "Missing 'field' in condition"

    def matches(item: Any) -> bool:
        if not isinstance(item, dict):
            return False

        item_value = item.get(field_name)

        if operator == "eq":
            return item_value == value
        elif operator == "ne":
            return item_value != value
        elif operator == "gt":
            return item_value > value
        elif operator == "gte":
            return item_value >= value
        elif operator == "lt":
            return item_value < value
        elif operator == "lte":
            return item_value <= value
        elif operator == "contains":
            return isinstance(item_value, str) and value in item_value
        elif operator == "startswith":
            return isinstance(item_value, str) and item_value.startswith(value)
        elif operator == "endswith":
            return isinstance(item_value, str) and item_value.endswith(value)
        elif operator == "exists":
            return field_name in item
        else:
            return False

    result = [item for item in data if matches(item)]
    return result, None


def _op_merge(data: Any, params: Dict[str, Any]) -> tuple[Any, Optional[str]]:
    """Merge two objects."""
    if not isinstance(data, dict):
        return None, "merge operation requires object input"

    merge_with = params.get("merge_with", {})
    if not isinstance(merge_with, dict):
        return None, "'merge_with' must be an object"

    result = {**data, **merge_with}
    return result, None


def _op_flatten(data: Any, params: Dict[str, Any]) -> tuple[Any, Optional[str]]:
    """Flatten nested arrays."""
    if not isinstance(data, list):
        return None, "flatten operation requires array input"

    def flatten(arr: list, depth: int = 1) -> list:
        result = []
        for item in arr:
            if isinstance(item, list) and depth > 0:
                result.extend(flatten(item, depth - 1))
            else:
                result.append(item)
        return result

    depth = params.get("depth", 1)
    return flatten(data, depth), None


def _op_sort(data: Any, params: Dict[str, Any]) -> tuple[Any, Optional[str]]:
    """Sort array."""
    if not isinstance(data, list):
        return None, "sort operation requires array input"

    sort_key = params.get("sort_key")
    sort_order = params.get("sort_order", "asc")
    reverse = sort_order == "desc"

    try:
        if sort_key:
            result = sorted(data, key=lambda x: x.get(sort_key) if isinstance(x, dict) else x, reverse=reverse)
        else:
            result = sorted(data, reverse=reverse)
        return result, None
    except TypeError as e:
        return None, f"Cannot sort: {e}"


def _op_map(data: Any, params: Dict[str, Any]) -> tuple[Any, Optional[str]]:
    """Map over array, extracting path from each element."""
    if not isinstance(data, list):
        return None, "map operation requires array input"

    path = params.get("path")
    if not path:
        return None, "Missing 'path' parameter for map operation"

    try:
        segments = _parse_jsonpath(path)
    except (ValueError, IndexError) as e:
        return None, f"Invalid path: {e}"

    result = []
    for item in data:
        value, found = _get_at_path(item, segments)
        result.append(value if found else None)

    return result, None


# Operation dispatcher
OPERATIONS = {
    "extract": _op_extract,
    "pick": _op_pick,
    "omit": _op_omit,
    "filter": _op_filter,
    "merge": _op_merge,
    "flatten": _op_flatten,
    "sort": _op_sort,
    "map": _op_map,
}

FORBIDDEN_OPERATIONS = {"eval", "exec", "__import__"}


# =============================================================================
# Skill Descriptor
# =============================================================================

JSON_TRANSFORM_DESCRIPTOR = SkillDescriptor(
    skill_id="skill.json_transform",
    name="JSON Transform",
    version="2.0.0",  # M3 version
    description="Deterministic JSON transformation with canonical output",
    inputs_schema={
        "type": "object",
        "required": ["data", "operation"],
        "properties": {
            "data": {"description": "Input data to transform"},
            "operation": {"type": "string", "enum": list(OPERATIONS.keys())},
            "path": {"type": "string"},
            "keys": {"type": "array", "items": {"type": "string"}},
            "condition": {"type": "object"},
            "merge_with": {"type": "object"},
            "sort_key": {"type": "string"},
            "sort_order": {"type": "string", "enum": ["asc", "desc"]},
        },
    },
    outputs_schema={
        "type": "object",
        "required": ["result", "result_hash", "canonical"],
        "properties": {
            "result": {},
            "result_hash": {"type": "string"},
            "canonical": {"type": "boolean"},
            "operation": {"type": "string"},
            "input_size": {"type": "integer"},
            "output_size": {"type": "integer"},
        },
    },
    stable_fields=["result", "result_hash", "operation", "canonical"],
    idempotent=True,
    cost_model={"base_cents": 0, "per_kb_cents": 0.001},
    failure_modes=[
        "ERR_JSON_INVALID",
        "ERR_JSON_PATH_INVALID",
        "ERR_JSON_PATH_NOT_FOUND",
        "ERR_JSON_TRANSFORM_FAILED",
        "ERR_JSON_DEPTH_EXCEEDED",
        "ERR_JSON_SIZE_EXCEEDED",
        "ERR_JSON_OPERATION_INVALID",
    ],
    constraints={
        "max_input_size_bytes": 10485760,  # 10MB
        "max_depth": 100,
        "max_array_length": 100000,
    },
)


# =============================================================================
# Main Execute Function
# =============================================================================


def _generate_call_id(params: Dict[str, Any]) -> str:
    """Generate deterministic call ID from params."""
    # Use content hash of params for deterministic ID
    return f"jt_{_content_hash(params, 12)}"


async def json_transform_execute(params: Dict[str, Any]) -> StructuredOutcome:
    """
    Execute JSON transformation.

    Args:
        params: Must contain 'data' and 'operation'

    Returns:
        StructuredOutcome with transformed result or error
    """
    call_id = _generate_call_id(params)

    # Parse input data
    data = params.get("data")
    operation = params.get("operation")

    # Handle string input (parse as JSON)
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError as e:
            return StructuredOutcome.failure(
                call_id=call_id,
                code="ERR_JSON_INVALID",
                message=f"Invalid JSON input: {e}",
                category="VALIDATION",
                retryable=False,
                details={"error": str(e), "input_preview": data[:100] if len(data) > 100 else data},
            )

    # Validate operation
    if not operation:
        return StructuredOutcome.failure(
            call_id=call_id,
            code="ERR_JSON_OPERATION_INVALID",
            message="Missing 'operation' parameter",
            category="VALIDATION",
            retryable=False,
        )

    if operation in FORBIDDEN_OPERATIONS:
        return StructuredOutcome.failure(
            call_id=call_id,
            code="ERR_JSON_OPERATION_INVALID",
            message=f"Forbidden operation: {operation}",
            category="VALIDATION",
            retryable=False,
            details={"operation": operation},
        )

    if operation not in OPERATIONS:
        return StructuredOutcome.failure(
            call_id=call_id,
            code="ERR_JSON_OPERATION_INVALID",
            message=f"Unknown operation: {operation}. Valid: {list(OPERATIONS.keys())}",
            category="VALIDATION",
            retryable=False,
            details={"operation": operation, "valid_operations": list(OPERATIONS.keys())},
        )

    # Validate input size
    input_size = len(_canonical_json(data)) if data else 0
    max_size = JSON_TRANSFORM_DESCRIPTOR.constraints.get("max_input_size_bytes", 10485760)
    if input_size > max_size:
        return StructuredOutcome.failure(
            call_id=call_id,
            code="ERR_JSON_SIZE_EXCEEDED",
            message=f"Input size {input_size} exceeds limit {max_size}",
            category="VALIDATION",
            retryable=False,
            details={"input_size": input_size, "max_size": max_size},
        )

    # Validate depth
    depth = _measure_depth(data) if data else 0
    max_depth = JSON_TRANSFORM_DESCRIPTOR.constraints.get("max_depth", 100)
    if depth > max_depth:
        return StructuredOutcome.failure(
            call_id=call_id,
            code="ERR_JSON_DEPTH_EXCEEDED",
            message=f"Input depth {depth} exceeds limit {max_depth}",
            category="VALIDATION",
            retryable=False,
            details={"depth": depth, "max_depth": max_depth},
        )

    # Execute operation
    try:
        op_func = OPERATIONS[operation]
        result, error = op_func(data, params)

        if error:
            # Determine error code based on error message
            if "path" in error.lower() and "not found" in error.lower():
                code = "ERR_JSON_PATH_NOT_FOUND"
            elif "path" in error.lower():
                code = "ERR_JSON_PATH_INVALID"
            else:
                code = "ERR_JSON_TRANSFORM_FAILED"

            return StructuredOutcome.failure(
                call_id=call_id,
                code=code,
                message=error,
                category="VALIDATION" if code != "ERR_JSON_TRANSFORM_FAILED" else "PERMANENT",
                retryable=False,
                details={"operation": operation},
            )

        # Compute result hash (canonical)
        result_hash = _content_hash(result)
        output_size = len(_canonical_json(result)) if result else 0

        return StructuredOutcome.success(
            call_id=call_id,
            result={
                "result": result,
                "result_hash": result_hash,
                "canonical": True,
                "operation": operation,
                "input_size": input_size,
                "output_size": output_size,
            },
            meta={
                "skill_id": JSON_TRANSFORM_DESCRIPTOR.skill_id,
                "skill_version": JSON_TRANSFORM_DESCRIPTOR.version,
                "deterministic": True,
            },
        )

    except Exception as e:
        logger.exception("json_transform execution error", extra={"error": str(e)})
        return StructuredOutcome.failure(
            call_id=call_id,
            code="ERR_JSON_TRANSFORM_FAILED",
            message=f"Transform failed: {e}",
            category="PERMANENT",
            retryable=False,
            details={"operation": operation, "error_type": type(e).__name__},
        )


# Handler for registry
async def json_transform_handler(params: Dict[str, Any]) -> StructuredOutcome:
    """Handler function for skill registry."""
    return await json_transform_execute(params)


# =============================================================================
# Registration Helper
# =============================================================================


def register_json_transform(registry) -> None:
    """Register json_transform skill with registry."""
    registry.register(
        descriptor=JSON_TRANSFORM_DESCRIPTOR,
        handler=json_transform_handler,
        is_stub=False,
        tags=["transform", "json", "data", "m3"],
    )
