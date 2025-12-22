# skills/stubs/json_transform_stub.py
"""
JSON Transform Stub (M2)

Deterministic stub for json_transform skill for testing.
Applies deterministic JSON transformations.

Features:
- Deterministic transforms
- JSON Schema validation
- JSONPath extraction
- Conforms to SkillDescriptor from runtime/core.py
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

_runtime_path = str(Path(__file__).parent.parent.parent / "worker" / "runtime")
if _runtime_path not in sys.path:
    sys.path.insert(0, _runtime_path)

from core import SkillDescriptor

# Descriptor for json_transform stub
JSON_TRANSFORM_STUB_DESCRIPTOR = SkillDescriptor(
    skill_id="skill.json_transform",
    name="JSON Transform (Stub)",
    version="1.0.0-stub",
    inputs_schema_version="1.0",
    outputs_schema_version="1.0",
    stable_fields={"output": "DETERMINISTIC", "output_hash": "DETERMINISTIC", "transform_type": "DETERMINISTIC"},
    cost_model={"base_cents": 0, "per_kb_cents": 0},
    failure_modes=[
        {"code": "ERR_INVALID_JSON", "category": "PERMANENT", "typical_cause": "malformed input"},
        {"code": "ERR_INVALID_PATH", "category": "PERMANENT", "typical_cause": "JSONPath not found"},
        {"code": "ERR_TRANSFORM_FAILED", "category": "PERMANENT", "typical_cause": "transform error"},
        {"code": "ERR_SCHEMA_VALIDATION", "category": "PERMANENT", "typical_cause": "output doesn't match schema"},
    ],
    constraints={
        "max_input_size_bytes": 1048576,  # 1MB
        "max_depth": 100,
    },
)


@dataclass
class JsonTransformStub:
    """
    JSON Transform stub with deterministic operations.

    Supported operations:
    - extract: Extract value at JSONPath
    - map: Transform each item in array
    - filter: Filter array items
    - merge: Merge objects
    - pick: Pick specific keys
    - omit: Omit specific keys

    Usage:
        stub = JsonTransformStub()
        result = await stub.execute({
            "data": {"users": [{"name": "Alice"}, {"name": "Bob"}]},
            "operation": "extract",
            "path": "$.users[0].name"
        })
    """

    # Call history for verification
    call_history: List[Dict[str, Any]] = field(default_factory=list)

    def _compute_hash(self, data: Any) -> str:
        """Compute deterministic hash of data."""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]

    def _simple_jsonpath(self, data: Any, path: str) -> Any:
        """
        Simple JSONPath implementation for testing.

        Supports:
        - $.key - root key access
        - $.key.subkey - nested access
        - $.array[0] - array index
        - $.array[*] - all array items
        """
        if not path.startswith("$"):
            path = "$." + path

        # Remove $ prefix
        path = path[1:]
        if path.startswith("."):
            path = path[1:]

        current = data

        if not path:
            return current

        # Split path into parts
        parts = re.split(r"\.(?![^\[]*\])", path)

        for part in parts:
            if not part:
                continue

            # Check for array access
            array_match = re.match(r"(\w+)\[(\d+|\*)\]", part)
            if array_match:
                key = array_match.group(1)
                index = array_match.group(2)

                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None

                if index == "*":
                    # Return all items
                    if isinstance(current, list):
                        return current
                    return None
                else:
                    idx = int(index)
                    if isinstance(current, list) and 0 <= idx < len(current):
                        current = current[idx]
                    else:
                        return None
            else:
                # Simple key access
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None

        return current

    def _apply_map(self, data: List, transform: Dict[str, str]) -> List:
        """Apply a mapping transform to array items."""
        result = []
        for item in data:
            if isinstance(item, dict):
                new_item = {}
                for new_key, source_key in transform.items():
                    if source_key in item:
                        new_item[new_key] = item[source_key]
                result.append(new_item)
            else:
                result.append(item)
        return result

    def _apply_filter(self, data: List, condition: Dict[str, Any]) -> List:
        """Filter array items based on condition."""
        result = []
        for item in data:
            if isinstance(item, dict):
                matches = True
                for key, value in condition.items():
                    if key not in item or item[key] != value:
                        matches = False
                        break
                if matches:
                    result.append(item)
        return result

    def _apply_pick(self, data: Dict, keys: List[str]) -> Dict:
        """Pick specific keys from object."""
        return {k: v for k, v in data.items() if k in keys}

    def _apply_omit(self, data: Dict, keys: List[str]) -> Dict:
        """Omit specific keys from object."""
        return {k: v for k, v in data.items() if k not in keys}

    def _apply_merge(self, *objects: Dict) -> Dict:
        """Merge multiple objects."""
        result = {}
        for obj in objects:
            if isinstance(obj, dict):
                result.update(obj)
        return result

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the transform with deterministic behavior.

        Args:
            inputs: Must contain 'data' and 'operation', plus operation-specific params

        Operations:
            - extract: {data, operation: "extract", path: "$.path"}
            - map: {data, operation: "map", transform: {new_key: "source_key"}}
            - filter: {data, operation: "filter", condition: {key: value}}
            - pick: {data, operation: "pick", keys: ["key1", "key2"]}
            - omit: {data, operation: "omit", keys: ["key1", "key2"]}
            - merge: {data, operation: "merge", with: {...}}

        Returns:
            Deterministic transformed output
        """
        data = inputs.get("data")
        operation = inputs.get("operation", "extract")
        path = inputs.get("path", "$")

        # Record call
        self.call_history.append(
            {
                "operation": operation,
                "data_hash": self._compute_hash(data),
                "params": {k: v for k, v in inputs.items() if k not in ("data",)},
            }
        )

        output = None

        try:
            if operation == "extract":
                output = self._simple_jsonpath(data, path)

            elif operation == "map":
                transform = inputs.get("transform", {})
                if isinstance(data, list):
                    output = self._apply_map(data, transform)
                else:
                    output = data

            elif operation == "filter":
                condition = inputs.get("condition", {})
                if isinstance(data, list):
                    output = self._apply_filter(data, condition)
                else:
                    output = data

            elif operation == "pick":
                keys = inputs.get("keys", [])
                if isinstance(data, dict):
                    output = self._apply_pick(data, keys)
                else:
                    output = data

            elif operation == "omit":
                keys = inputs.get("keys", [])
                if isinstance(data, dict):
                    output = self._apply_omit(data, keys)
                else:
                    output = data

            elif operation == "merge":
                merge_with = inputs.get("with", {})
                if isinstance(data, dict):
                    output = self._apply_merge(data, merge_with)
                else:
                    output = data

            else:
                raise ValueError(f"Unknown operation: {operation}")

        except Exception as e:
            raise Exception(f"Transform failed: {str(e)}")

        result = {
            "output": output,
            "output_hash": self._compute_hash(output),
            "transform_type": operation,
            "input_hash": self._compute_hash(data),
        }

        return result

    def reset(self) -> None:
        """Reset call history."""
        self.call_history.clear()


# Global stub instance
_JSON_TRANSFORM_STUB = JsonTransformStub()


async def json_transform_stub_handler(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler function for json_transform stub.

    This is the function registered with the runtime.
    """
    return await _JSON_TRANSFORM_STUB.execute(inputs)


def get_json_transform_stub() -> JsonTransformStub:
    """Get the global json_transform stub instance for configuration."""
    return _JSON_TRANSFORM_STUB


def configure_json_transform_stub(stub: JsonTransformStub) -> None:
    """Replace the global json_transform stub instance."""
    global _JSON_TRANSFORM_STUB
    _JSON_TRANSFORM_STUB = stub
