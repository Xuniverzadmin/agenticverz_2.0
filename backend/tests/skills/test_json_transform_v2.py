# tests/skills/test_json_transform_v2.py
"""
Tests for JSON Transform Skill v2 (M3)

Tests determinism, canonical output, error handling, and all operations.
"""

import pytest
import sys
from pathlib import Path

# Path setup
_backend = Path(__file__).parent.parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

# Direct import from the module (skills/__init__.py now uses lazy loading)
from app.skills.json_transform_v2 import (
    json_transform_execute,
    json_transform_handler,
    JSON_TRANSFORM_DESCRIPTOR,
    _canonical_json,
    _content_hash,
    _parse_jsonpath,
    _measure_depth,
    OPERATIONS,
)


class TestCanonicalJson:
    """Test canonical JSON utilities."""

    def test_canonical_json_sorted_keys(self):
        """Keys must be sorted alphabetically."""
        data = {"z": 1, "a": 2, "m": 3}
        canonical = _canonical_json(data)
        assert canonical == '{"a":2,"m":3,"z":1}'

    def test_canonical_json_no_whitespace(self):
        """No extra whitespace in output."""
        data = {"key": "value", "nested": {"a": 1}}
        canonical = _canonical_json(data)
        assert ' ' not in canonical
        assert '\n' not in canonical

    def test_canonical_json_nested_sorted(self):
        """Nested objects also have sorted keys."""
        data = {"outer": {"z": 1, "a": 2}}
        canonical = _canonical_json(data)
        assert canonical == '{"outer":{"a":2,"z":1}}'

    def test_content_hash_deterministic(self):
        """Same input produces same hash."""
        data = {"key": "value"}
        hash1 = _content_hash(data)
        hash2 = _content_hash(data)
        assert hash1 == hash2
        assert len(hash1) == 16

    def test_content_hash_different_for_different_data(self):
        """Different input produces different hash."""
        hash1 = _content_hash({"a": 1})
        hash2 = _content_hash({"a": 2})
        assert hash1 != hash2


class TestJsonPath:
    """Test JSONPath parsing and navigation."""

    def test_parse_simple_path(self):
        """Parse simple dot notation."""
        segments = _parse_jsonpath("$.user.name")
        assert segments == ["user", "name"]

    def test_parse_array_index(self):
        """Parse array index."""
        segments = _parse_jsonpath("$.items[0]")
        assert segments == ["items", 0]

    def test_parse_negative_index(self):
        """Parse negative array index."""
        segments = _parse_jsonpath("$.items[-1]")
        assert segments == ["items", -1]

    def test_parse_root_only(self):
        """Parse root path."""
        segments = _parse_jsonpath("$")
        assert segments == []

    def test_parse_bracket_notation(self):
        """Parse bracket notation for keys."""
        segments = _parse_jsonpath("$['user']['name']")
        assert segments == ["user", "name"]

    def test_invalid_path_no_dollar(self):
        """Path must start with $."""
        with pytest.raises(ValueError):
            _parse_jsonpath("user.name")


class TestMeasureDepth:
    """Test depth measurement."""

    def test_flat_object(self):
        """Flat object has depth 1."""
        assert _measure_depth({"a": 1, "b": 2}) == 1

    def test_nested_object(self):
        """Nested object depth."""
        data = {"a": {"b": {"c": 1}}}
        assert _measure_depth(data) == 3

    def test_array_depth(self):
        """Array depth."""
        data = [[[1]]]
        assert _measure_depth(data) == 3

    def test_mixed_depth(self):
        """Mixed object and array."""
        data = {"a": [{"b": 1}]}
        assert _measure_depth(data) == 3


class TestExtractOperation:
    """Test extract operation."""

    @pytest.mark.asyncio
    async def test_extract_simple(self):
        """Extract simple nested value."""
        result = await json_transform_execute({
            "data": {"user": {"name": "Alice"}},
            "operation": "extract",
            "path": "$.user.name"
        })

        assert result.ok is True
        assert result.result["result"] == "Alice"
        assert result.result["canonical"] is True

    @pytest.mark.asyncio
    async def test_extract_array_index(self):
        """Extract array element."""
        result = await json_transform_execute({
            "data": {"items": ["a", "b", "c"]},
            "operation": "extract",
            "path": "$.items[1]"
        })

        assert result.ok is True
        assert result.result["result"] == "b"

    @pytest.mark.asyncio
    async def test_extract_path_not_found(self):
        """Error when path doesn't exist."""
        result = await json_transform_execute({
            "data": {"user": {}},
            "operation": "extract",
            "path": "$.user.name"
        })

        assert result.ok is False
        assert result.error["code"] == "ERR_JSON_PATH_NOT_FOUND"
        assert result.error["retryable"] is False


class TestPickOperation:
    """Test pick operation."""

    @pytest.mark.asyncio
    async def test_pick_keys(self):
        """Pick specific keys."""
        result = await json_transform_execute({
            "data": {"a": 1, "b": 2, "c": 3},
            "operation": "pick",
            "keys": ["a", "c"]
        })

        assert result.ok is True
        assert result.result["result"] == {"a": 1, "c": 3}

    @pytest.mark.asyncio
    async def test_pick_missing_keys(self):
        """Pick with some missing keys."""
        result = await json_transform_execute({
            "data": {"a": 1},
            "operation": "pick",
            "keys": ["a", "b"]
        })

        assert result.ok is True
        assert result.result["result"] == {"a": 1}

    @pytest.mark.asyncio
    async def test_pick_requires_object(self):
        """Pick fails on non-object."""
        result = await json_transform_execute({
            "data": [1, 2, 3],
            "operation": "pick",
            "keys": ["a"]
        })

        assert result.ok is False


class TestOmitOperation:
    """Test omit operation."""

    @pytest.mark.asyncio
    async def test_omit_keys(self):
        """Omit specific keys."""
        result = await json_transform_execute({
            "data": {"a": 1, "b": 2, "c": 3},
            "operation": "omit",
            "keys": ["b"]
        })

        assert result.ok is True
        assert result.result["result"] == {"a": 1, "c": 3}


class TestFilterOperation:
    """Test filter operation."""

    @pytest.mark.asyncio
    async def test_filter_eq(self):
        """Filter with equality condition."""
        result = await json_transform_execute({
            "data": [
                {"id": 1, "status": "active"},
                {"id": 2, "status": "inactive"},
                {"id": 3, "status": "active"}
            ],
            "operation": "filter",
            "condition": {"field": "status", "operator": "eq", "value": "active"}
        })

        assert result.ok is True
        assert len(result.result["result"]) == 2
        assert all(item["status"] == "active" for item in result.result["result"])

    @pytest.mark.asyncio
    async def test_filter_gt(self):
        """Filter with greater than."""
        result = await json_transform_execute({
            "data": [{"val": 1}, {"val": 5}, {"val": 10}],
            "operation": "filter",
            "condition": {"field": "val", "operator": "gt", "value": 3}
        })

        assert result.ok is True
        assert len(result.result["result"]) == 2


class TestMergeOperation:
    """Test merge operation."""

    @pytest.mark.asyncio
    async def test_merge_objects(self):
        """Merge two objects."""
        result = await json_transform_execute({
            "data": {"a": 1, "b": 2},
            "operation": "merge",
            "merge_with": {"c": 3}
        })

        assert result.ok is True
        assert result.result["result"] == {"a": 1, "b": 2, "c": 3}

    @pytest.mark.asyncio
    async def test_merge_override(self):
        """Merge with override."""
        result = await json_transform_execute({
            "data": {"a": 1},
            "operation": "merge",
            "merge_with": {"a": 2, "b": 3}
        })

        assert result.ok is True
        assert result.result["result"]["a"] == 2


class TestSortOperation:
    """Test sort operation."""

    @pytest.mark.asyncio
    async def test_sort_asc(self):
        """Sort ascending."""
        result = await json_transform_execute({
            "data": [3, 1, 2],
            "operation": "sort"
        })

        assert result.ok is True
        assert result.result["result"] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_sort_desc(self):
        """Sort descending."""
        result = await json_transform_execute({
            "data": [1, 3, 2],
            "operation": "sort",
            "sort_order": "desc"
        })

        assert result.ok is True
        assert result.result["result"] == [3, 2, 1]

    @pytest.mark.asyncio
    async def test_sort_by_key(self):
        """Sort by object key."""
        result = await json_transform_execute({
            "data": [{"name": "Charlie"}, {"name": "Alice"}, {"name": "Bob"}],
            "operation": "sort",
            "sort_key": "name"
        })

        assert result.ok is True
        assert result.result["result"][0]["name"] == "Alice"


class TestMapOperation:
    """Test map operation."""

    @pytest.mark.asyncio
    async def test_map_extract_field(self):
        """Map to extract field from each element."""
        result = await json_transform_execute({
            "data": [{"name": "Alice"}, {"name": "Bob"}],
            "operation": "map",
            "path": "$.name"
        })

        assert result.ok is True
        assert result.result["result"] == ["Alice", "Bob"]


class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_invalid_json_string(self):
        """Invalid JSON string input."""
        result = await json_transform_execute({
            "data": "not valid json {",
            "operation": "extract",
            "path": "$.x"
        })

        assert result.ok is False
        assert result.error["code"] == "ERR_JSON_INVALID"
        assert result.error["category"] == "VALIDATION"
        assert result.error["retryable"] is False

    @pytest.mark.asyncio
    async def test_missing_operation(self):
        """Missing operation parameter."""
        result = await json_transform_execute({
            "data": {"a": 1}
        })

        assert result.ok is False
        assert result.error["code"] == "ERR_JSON_OPERATION_INVALID"

    @pytest.mark.asyncio
    async def test_forbidden_operation(self):
        """Forbidden operation rejected."""
        result = await json_transform_execute({
            "data": {"a": 1},
            "operation": "eval"
        })

        assert result.ok is False
        assert result.error["code"] == "ERR_JSON_OPERATION_INVALID"
        assert "Forbidden" in result.error["message"]

    @pytest.mark.asyncio
    async def test_unknown_operation(self):
        """Unknown operation rejected."""
        result = await json_transform_execute({
            "data": {"a": 1},
            "operation": "nonexistent"
        })

        assert result.ok is False
        assert result.error["code"] == "ERR_JSON_OPERATION_INVALID"


class TestDeterminism:
    """Test deterministic behavior."""

    @pytest.mark.asyncio
    async def test_same_input_same_output(self):
        """Same input produces identical output."""
        params = {
            "data": {"users": [{"name": "Alice"}, {"name": "Bob"}]},
            "operation": "extract",
            "path": "$.users"
        }

        results = [await json_transform_execute(params) for _ in range(10)]

        # All results should be identical
        first_hash = results[0].result["result_hash"]
        for r in results[1:]:
            assert r.result["result_hash"] == first_hash

    @pytest.mark.asyncio
    async def test_canonical_output_consistent(self):
        """Canonical output is consistent across runs."""
        params = {
            "data": {"z": 1, "a": 2, "m": 3},
            "operation": "pick",
            "keys": ["z", "a", "m"]
        }

        results = [await json_transform_execute(params) for _ in range(5)]

        # All should produce same canonical form
        canonical_forms = set()
        for r in results:
            canonical = _canonical_json(r.result["result"])
            canonical_forms.add(canonical)

        assert len(canonical_forms) == 1


class TestDescriptor:
    """Test skill descriptor."""

    def test_descriptor_fields(self):
        """Descriptor has required fields."""
        d = JSON_TRANSFORM_DESCRIPTOR
        assert d.skill_id == "skill.json_transform"
        assert d.version == "2.0.0"
        assert d.idempotent is True
        assert "result" in d.stable_fields
        assert "result_hash" in d.stable_fields

    def test_failure_modes_defined(self):
        """Failure modes are defined."""
        d = JSON_TRANSFORM_DESCRIPTOR
        assert "ERR_JSON_INVALID" in d.failure_modes
        assert "ERR_JSON_PATH_INVALID" in d.failure_modes

    def test_constraints_defined(self):
        """Constraints are defined."""
        d = JSON_TRANSFORM_DESCRIPTOR
        assert d.constraints["max_input_size_bytes"] == 10485760
        assert d.constraints["max_depth"] == 100


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
