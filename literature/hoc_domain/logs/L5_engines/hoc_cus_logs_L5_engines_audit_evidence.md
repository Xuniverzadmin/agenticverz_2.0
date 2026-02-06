# hoc_cus_logs_L5_engines_audit_evidence

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L5_engines/audit_evidence.py` |
| Layer | L5 — Domain Engine |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Emit compliance-grade audit for MCP tool calls

## Intent

**Role:** Emit compliance-grade audit for MCP tool calls
**Reference:** PIN-470, GAP-143
**Callers:** Runner, skill executor

## Purpose

Module: audit_evidence
Purpose: Emit compliance-grade audit for MCP tool calls.

---

## Functions

### `_hash_value(value: Any) -> str`
- **Async:** No
- **Docstring:** Hash a value for audit purposes.
- **Calls:** encode, hexdigest, sha256, str

### `_contains_sensitive(key: str) -> bool`
- **Async:** No
- **Docstring:** Check if key name suggests sensitive data.
- **Calls:** any, lower

### `_redact_sensitive(data: Dict[str, Any]) -> Dict[str, Any]`
- **Async:** No
- **Docstring:** Redact sensitive fields from data for logging.
- **Calls:** _contains_sensitive, _redact_sensitive, isinstance, items

### `get_mcp_audit_emitter() -> MCPAuditEmitter`
- **Async:** No
- **Docstring:** Get or create the singleton MCPAuditEmitter.  Returns:
- **Calls:** MCPAuditEmitter, info

### `configure_mcp_audit_emitter(publisher: Optional[Any]) -> MCPAuditEmitter`
- **Async:** No
- **Docstring:** Configure the singleton MCPAuditEmitter.  Args:
- **Calls:** MCPAuditEmitter, info

### `reset_mcp_audit_emitter() -> None`
- **Async:** No
- **Docstring:** Reset the singleton (for testing).

## Classes

### `MCPAuditEventType(str, Enum)`
- **Docstring:** Types of MCP audit events.

### `MCPAuditEvent`
- **Docstring:** Compliance-grade audit event for MCP operations.
- **Methods:** __post_init__, _compute_integrity_hash, to_dict, verify_integrity
- **Class Variables:** event_id: str, event_type: MCPAuditEventType, tenant_id: str, run_id: Optional[str], server_id: Optional[str], tool_name: Optional[str], timestamp: str, policy_decision: Optional[str], policy_id: Optional[str], deny_reason: Optional[str], input_hash: Optional[str], output_hash: Optional[str], duration_ms: Optional[float], error_message: Optional[str], trace_id: Optional[str], span_id: Optional[str], parent_span_id: Optional[str], integrity_hash: Optional[str], previous_event_hash: Optional[str], metadata: Optional[Dict[str, Any]]

### `MCPAuditEmitter`
- **Docstring:** Emitter for compliance-grade MCP audit events.
- **Methods:** __init__, _generate_event_id, emit_tool_requested, emit_tool_allowed, emit_tool_denied, emit_tool_started, emit_tool_completed, emit_tool_failed, emit_server_registered, emit_server_unregistered, _emit, _get_publisher

## Attributes

- `logger` (line 53)
- `SENSITIVE_PATTERNS` (line 153)
- `_mcp_audit_emitter: Optional[MCPAuditEmitter]` (line 625)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.events` |

## Callers

Runner, skill executor

## Export Contract

```yaml
exports:
  functions:
    - name: get_mcp_audit_emitter
      signature: "get_mcp_audit_emitter() -> MCPAuditEmitter"
    - name: configure_mcp_audit_emitter
      signature: "configure_mcp_audit_emitter(publisher: Optional[Any]) -> MCPAuditEmitter"
    - name: reset_mcp_audit_emitter
      signature: "reset_mcp_audit_emitter() -> None"
  classes:
    - name: MCPAuditEventType
      methods: []
    - name: MCPAuditEvent
      methods: [to_dict, verify_integrity]
    - name: MCPAuditEmitter
      methods: [emit_tool_requested, emit_tool_allowed, emit_tool_denied, emit_tool_started, emit_tool_completed, emit_tool_failed, emit_server_registered, emit_server_unregistered]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
