# canonical_json.py

**Path:** `backend/app/hoc/cus/hoc_spine/services/canonical_json.py`  
**Layer:** L4 — HOC Spine (Service)  
**Component:** Services

---

## Placement Card

```
File:            canonical_json.py
Lives in:        services/
Role:            Services
Inbound:         SDK, trace system
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Canonical JSON serialization for AOS.
Violations:      none
```

## Purpose

Canonical JSON serialization for AOS.

Ensures deterministic JSON output for:
- Replay testing
- Content hashing
- Golden file comparison

See: app/specs/canonical_json.md for full specification.

## Import Analysis

**External:**
- `__future__`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `canonical_json(obj: Any, exclude_fields: Optional[Set[str]]) -> str`

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

### `canonical_json_bytes(obj: Any, exclude_fields: Optional[Set[str]]) -> bytes`

Serialize object to canonical JSON bytes (UTF-8).

Args:
    obj: Object to serialize
    exclude_fields: Optional set of field names to exclude

Returns:
    UTF-8 encoded canonical JSON bytes

### `content_hash(obj: Any, exclude_fields: Optional[Set[str]], length: int) -> str`

Compute deterministic content hash.

Args:
    obj: Object to hash
    exclude_fields: Fields to exclude from hash (e.g., timestamps)
    length: Length of hash to return (default 16 hex chars)

Returns:
    Hex string of SHA-256 hash (truncated to length)

### `content_hash_full(obj: Any, exclude_fields: Optional[Set[str]]) -> str`

Compute full SHA-256 content hash.

Args:
    obj: Object to hash
    exclude_fields: Fields to exclude from hash

Returns:
    Full 64-character hex hash

### `deterministic_hash(obj: Any, length: int) -> str`

Compute hash excluding allowed variance fields.

This is the standard hashing function for replay comparisons.

Args:
    obj: Object to hash
    length: Length of hash to return

Returns:
    Hex hash string

### `_json_serializer(obj: Any) -> Any`

Custom JSON serializer for non-standard types.

Handles:
- datetime/date → ISO format string
- UUID → string
- Enum → value
- bytes → base64 string (if needed)
- Objects with to_dict() method
- Objects with __dict__ attribute

### `_filter_fields(obj: Any, exclude: Set[str]) -> Any`

Recursively filter out excluded fields from an object.

Args:
    obj: Object to filter
    exclude: Set of field names to exclude

Returns:
    Filtered object

### `is_canonical(json_str: str) -> bool`

Check if a JSON string is in canonical format.

Args:
    json_str: JSON string to check

Returns:
    True if canonical, False otherwise

### `canonicalize_file(filepath: str) -> None`

Rewrite a JSON file in canonical format.

Args:
    filepath: Path to JSON file

Raises:
    ValueError: If file is not valid JSON

### `assert_canonical(filepath: str) -> None`

Assert that a JSON file is in canonical format.

Args:
    filepath: Path to JSON file

Raises:
    AssertionError: If file is not canonical

### `compare_deterministic(actual: Dict[str, Any], expected: Dict[str, Any], deterministic_fields: Optional[List[str]]) -> Dict[str, Any]`

Compare two outputs, checking only deterministic fields.

Args:
    actual: Actual output
    expected: Expected output
    deterministic_fields: List of fields that must match exactly

Returns:
    Dict with 'match' (bool) and 'differences' (list)

### `_get_nested(obj: Dict[str, Any], path: str) -> Any`

Get nested value using dot notation.

## Domain Usage

**Callers:** SDK, trace system

## Export Contract

```yaml
exports:
  functions:
    - name: canonical_json
      signature: "canonical_json(obj: Any, exclude_fields: Optional[Set[str]]) -> str"
      consumers: ["orchestrator"]
    - name: canonical_json_bytes
      signature: "canonical_json_bytes(obj: Any, exclude_fields: Optional[Set[str]]) -> bytes"
      consumers: ["orchestrator"]
    - name: content_hash
      signature: "content_hash(obj: Any, exclude_fields: Optional[Set[str]], length: int) -> str"
      consumers: ["orchestrator"]
    - name: content_hash_full
      signature: "content_hash_full(obj: Any, exclude_fields: Optional[Set[str]]) -> str"
      consumers: ["orchestrator"]
    - name: deterministic_hash
      signature: "deterministic_hash(obj: Any, length: int) -> str"
      consumers: ["orchestrator"]
    - name: _json_serializer
      signature: "_json_serializer(obj: Any) -> Any"
      consumers: ["orchestrator"]
    - name: _filter_fields
      signature: "_filter_fields(obj: Any, exclude: Set[str]) -> Any"
      consumers: ["orchestrator"]
    - name: is_canonical
      signature: "is_canonical(json_str: str) -> bool"
      consumers: ["orchestrator"]
    - name: canonicalize_file
      signature: "canonicalize_file(filepath: str) -> None"
      consumers: ["orchestrator"]
    - name: assert_canonical
      signature: "assert_canonical(filepath: str) -> None"
      consumers: ["orchestrator"]
    - name: compare_deterministic
      signature: "compare_deterministic(actual: Dict[str, Any], expected: Dict[str, Any], deterministic_fields: Optional[List[str]]) -> Dict[str, Any]"
      consumers: ["orchestrator"]
    - name: _get_nested
      signature: "_get_nested(obj: Dict[str, Any], path: str) -> Any"
      consumers: ["orchestrator"]
  classes: []
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.orchestrator.*"
    - "hoc_spine.authority.*"
    - "hoc_spine.consequences.*"
    - "hoc_spine.drivers.*"
  forbidden_inbound:
    - "hoc.cus.*"
    - "hoc.api.*"
  actual_imports:
    spine_internal: []
    l7_model: []
    external: ['__future__']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

