# Layer: L5 — Domain Engine
# AUDIENCE: INTERNAL
# Role: A single transformation mapping.
# JSON Transform Skill
# Safe, deterministic JSON transformation using dot-path mapping

import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .registry import skill

logger = logging.getLogger("nova.skills.json_transform")


class TransformMapping(BaseModel):
    """A single transformation mapping."""

    target: str = Field(description="Target key in output")
    source: str = Field(description="Dot-path to source value (e.g., 'data.items[0].name')")
    default: Optional[Any] = Field(default=None, description="Default value if source not found")


class JsonTransformInput(BaseModel):
    """Input schema for json_transform skill."""

    payload: Dict[str, Any] = Field(description="Input JSON payload to transform")
    mapping: Dict[str, str] = Field(
        description="Mapping of output keys to source paths (e.g., {'name': 'data.user.name'})"
    )
    defaults: Optional[Dict[str, Any]] = Field(
        default=None, description="Default values for keys if source path not found"
    )


class JsonTransformOutput(BaseModel):
    """Output schema for json_transform skill."""

    status: str = Field(description="'ok' or 'error'")
    result: Dict[str, Any] = Field(default_factory=dict, description="Transformed output")
    errors: List[str] = Field(default_factory=list, description="Any errors during transformation")


def _get_path(data: Any, path: str) -> tuple[Any, bool]:
    """Get value at dot-path from nested structure.

    Supports:
    - Dot notation: 'data.user.name'
    - Array indexing: 'items[0]', 'items[-1]'
    - Combined: 'data.items[0].name'

    Returns:
        Tuple of (value, found: bool)
    """
    if not path:
        return data, True

    # Parse path into segments
    import re

    # Split on dots, but handle array brackets
    segments = re.split(r"\.(?![^\[]*\])", path)

    current = data
    for segment in segments:
        if current is None:
            return None, False

        # Check for array index
        match = re.match(r"^([^\[]*)\[(-?\d+)\]$", segment)
        if match:
            key, idx_str = match.groups()
            idx = int(idx_str)

            # Get the key first if present
            if key:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None, False

            # Then index into array
            if isinstance(current, (list, tuple)):
                try:
                    current = current[idx]
                except IndexError:
                    return None, False
            else:
                return None, False
        else:
            # Simple key access
            if isinstance(current, dict) and segment in current:
                current = current[segment]
            else:
                return None, False

    return current, True


def transform_json(
    payload: Dict[str, Any], mapping: Dict[str, str], defaults: Optional[Dict[str, Any]] = None
) -> tuple[Dict[str, Any], List[str]]:
    """Transform JSON payload using mapping.

    Args:
        payload: Input data
        mapping: Dict of {output_key: source_path}
        defaults: Optional default values

    Returns:
        Tuple of (result_dict, errors_list)
    """
    result = {}
    errors = []
    defaults = defaults or {}

    for output_key, source_path in mapping.items():
        value, found = _get_path(payload, source_path)

        if found:
            result[output_key] = value
        elif output_key in defaults:
            result[output_key] = defaults[output_key]
        else:
            result[output_key] = None
            errors.append(f"Path '{source_path}' not found for key '{output_key}'")

    return result, errors


@skill(
    name="json_transform",
    input_schema=JsonTransformInput,
    output_schema=JsonTransformOutput,
    tags=["transform", "json", "data"],
)
class JsonTransformSkill:
    """Transform JSON payloads using dot-path mapping.

    This skill provides safe, deterministic JSON transformation without
    arbitrary code execution. Useful for:
    - Extracting fields from API responses
    - Reshaping data between steps
    - Normalizing data structures
    """

    def __init__(self, **kwargs):
        pass

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the JSON transformation.

        Args:
            params: Must contain 'payload' and 'mapping'

        Returns:
            Skill result dict with status and transformed result
        """
        logger.info("skill_execution_start", extra={"skill": "json_transform"})

        try:
            payload = params.get("payload", {})
            mapping = params.get("mapping", {})
            defaults = params.get("defaults")

            if not isinstance(payload, dict):
                return {
                    "skill": "json_transform",
                    "skill_version": "1.0.0",
                    "result": {
                        "status": "error",
                        "result": {},
                        "errors": ["payload must be a dictionary"],
                    },
                    "side_effects": {},
                }

            if not isinstance(mapping, dict):
                return {
                    "skill": "json_transform",
                    "skill_version": "1.0.0",
                    "result": {
                        "status": "error",
                        "result": {},
                        "errors": ["mapping must be a dictionary"],
                    },
                    "side_effects": {},
                }

            result, errors = transform_json(payload, mapping, defaults)

            logger.info(
                "skill_execution_end",
                extra={
                    "skill": "json_transform",
                    "status": "ok" if not errors else "partial",
                    "output_keys": list(result.keys()),
                    "error_count": len(errors),
                },
            )

            return {
                "skill": "json_transform",
                "skill_version": "1.0.0",
                "result": {
                    "status": "ok" if not errors else "partial",
                    "result": result,
                    "errors": errors,
                },
                "side_effects": {},
            }

        except Exception as e:
            logger.exception("skill_execution_error", extra={"skill": "json_transform", "error": str(e)})
            return {
                "skill": "json_transform",
                "skill_version": "1.0.0",
                "result": {
                    "status": "error",
                    "result": {},
                    "errors": [str(e)],
                },
                "side_effects": {},
            }
