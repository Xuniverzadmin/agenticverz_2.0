# hoc_cus_policies_L5_engines_policy_mapper

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/policy_mapper.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Map MCP tool invocations to policy gates

## Intent

**Role:** Map MCP tool invocations to policy gates
**Reference:** PIN-470, GAP-142
**Callers:** Runner, skill executor

## Purpose

Module: policy_mapper
Purpose: Map MCP tool invocations to policy gates.

---

## Functions

### `get_mcp_policy_mapper() -> MCPPolicyMapper`
- **Async:** No
- **Docstring:** Get or create the singleton MCPPolicyMapper.  Returns:
- **Calls:** MCPPolicyMapper, info

### `configure_mcp_policy_mapper(policy_engine: Optional[Any]) -> MCPPolicyMapper`
- **Async:** No
- **Docstring:** Configure the singleton MCPPolicyMapper.  Args:
- **Calls:** MCPPolicyMapper, info

### `reset_mcp_policy_mapper() -> None`
- **Async:** No
- **Docstring:** Reset the singleton (for testing).

## Classes

### `MCPPolicyDecisionType(str, Enum)`
- **Docstring:** Types of policy decisions for MCP tools.

### `MCPDenyReason(str, Enum)`
- **Docstring:** Reasons for denying MCP tool invocation.

### `MCPPolicyDecision`
- **Docstring:** Policy decision for MCP tool invocation.
- **Methods:** to_dict, allow, deny
- **Class Variables:** tool_name: str, server_id: str, decision: MCPPolicyDecisionType, deny_reason: Optional[MCPDenyReason], policy_id: Optional[str], message: Optional[str], checked_at: str

### `MCPToolPolicy`
- **Docstring:** Policy configuration for an MCP tool.
- **Class Variables:** tool_name: str, server_id: str, required_permissions: List[str], is_enabled: bool, is_dangerous: bool, requires_explicit_allow: bool, max_calls_per_minute: Optional[int], metadata: Optional[Dict[str, Any]]

### `MCPPolicyMapper`
- **Docstring:** Maps MCP tool invocations to policy gates.
- **Methods:** __init__, check_tool_invocation, register_tool_policy, _evaluate_policy, _check_explicit_allow, _check_rate_limit, _get_policy_engine

## Attributes

- `logger` (line 51)
- `_mcp_policy_mapper: Optional[MCPPolicyMapper]` (line 444)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L5 Engine | `app.hoc.cus.policies.L5_engines.engine` |

## Callers

Runner, skill executor

## Export Contract

```yaml
exports:
  functions:
    - name: get_mcp_policy_mapper
      signature: "get_mcp_policy_mapper() -> MCPPolicyMapper"
    - name: configure_mcp_policy_mapper
      signature: "configure_mcp_policy_mapper(policy_engine: Optional[Any]) -> MCPPolicyMapper"
    - name: reset_mcp_policy_mapper
      signature: "reset_mcp_policy_mapper() -> None"
  classes:
    - name: MCPPolicyDecisionType
      methods: []
    - name: MCPDenyReason
      methods: []
    - name: MCPPolicyDecision
      methods: [to_dict, allow, deny]
    - name: MCPToolPolicy
      methods: []
    - name: MCPPolicyMapper
      methods: [check_tool_invocation, register_tool_policy]
```

## PIN-520 Dead Code Rewiring Updates

- **Change Date:** 2026-02-03
- **Change Type:** Documentation — Dead Code Rewiring
- **Details:** Wired `tool_key` and `max_per_minute` parameters during PIN-520 phase 3 dead code rewiring
- **Impact:** No code changes; enhanced documentation of existing parameters

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
