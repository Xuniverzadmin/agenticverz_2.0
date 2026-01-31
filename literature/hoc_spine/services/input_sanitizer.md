# input_sanitizer.py

**Path:** `backend/app/hoc/hoc_spine/services/input_sanitizer.py`  
**Layer:** L4 — HOC Spine (Service)  
**Component:** Services

---

## Placement Card

```
File:            input_sanitizer.py
Lives in:        services/
Role:            Services
Inbound:         API routes
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Input sanitization for security (pure regex validation and URL parsing)
Violations:      none
```

## Purpose

Input sanitization for security (pure regex validation and URL parsing)

## Import Analysis

Pure stdlib — no application imports.

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `detect_injection_patterns(text: str) -> List[tuple]`

Detect prompt injection patterns in text.

Returns:
    List of (pattern_name, matched_text) tuples

### `extract_urls(text: str) -> List[str]`

Extract all URLs from text.

### `is_url_safe(url: str) -> tuple[bool, Optional[str]]`

Check if a URL is safe (not targeting internal resources).

Returns:
    Tuple of (is_safe, reason_if_unsafe)

### `sanitize_goal(goal: str) -> SanitizationResult`

Sanitize a goal string before processing.

This is the main entry point for the input sanitizer.

Args:
    goal: The user-provided goal text

Returns:
    SanitizationResult with sanitized text and safety info

### `validate_goal(goal: str) -> tuple[bool, Optional[str], List[str]]`

Convenience function to validate a goal.

Returns:
    Tuple of (is_valid, error_message, warnings)

## Classes

### `SanitizationResult`

Result of input sanitization.

#### Methods

- `__post_init__()` — _No docstring._

## Domain Usage

**Callers:** API routes

## Export Contract

```yaml
exports:
  functions:
    - name: detect_injection_patterns
      signature: "detect_injection_patterns(text: str) -> List[tuple]"
      consumers: ["orchestrator"]
    - name: extract_urls
      signature: "extract_urls(text: str) -> List[str]"
      consumers: ["orchestrator"]
    - name: is_url_safe
      signature: "is_url_safe(url: str) -> tuple[bool, Optional[str]]"
      consumers: ["orchestrator"]
    - name: sanitize_goal
      signature: "sanitize_goal(goal: str) -> SanitizationResult"
      consumers: ["orchestrator"]
    - name: validate_goal
      signature: "validate_goal(goal: str) -> tuple[bool, Optional[str], List[str]]"
      consumers: ["orchestrator"]
  classes:
    - name: SanitizationResult
      methods:
      consumers: ["orchestrator"]
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
    external: []
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

