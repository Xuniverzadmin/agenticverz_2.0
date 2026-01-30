# hoc_cus_policies_L5_engines_runtime_command

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/runtime_command.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Runtime domain commands and query logic (pure logic)

## Intent

**Role:** Runtime domain commands and query logic (pure logic)
**Reference:** PIN-470, PIN-258 Phase F-3 Runtime Cluster
**Callers:** runtime_adapter.py (L3)

## Purpose

Runtime Domain Commands (L4)

---

## Functions

### `get_supported_query_types() -> List[str]`
- **Async:** No
- **Docstring:** Get list of supported query types.  This is an L4 domain decision - defining what queries the system supports.
- **Calls:** copy

### `query_remaining_budget(spent_cents: int, total_cents: int) -> QueryResult`
- **Async:** No
- **Docstring:** Query remaining budget.  L4 domain decision: How to calculate and present budget information.
- **Calls:** QueryResult

### `query_execution_history(history: Optional[List[Dict[str, Any]]]) -> QueryResult`
- **Async:** No
- **Docstring:** Query execution history.  L4 domain decision: How to present execution history.
- **Calls:** QueryResult

### `query_allowed_skills() -> QueryResult`
- **Async:** No
- **Docstring:** Query list of allowed skills.  L4 domain decision: What skills are available.
- **Calls:** QueryResult, keys, len, list

### `query_last_step_outcome(outcome: Optional[Dict[str, Any]]) -> QueryResult`
- **Async:** No
- **Docstring:** Query last step outcome.  L4 domain decision: How to present last outcome.
- **Calls:** QueryResult

### `query_skills_for_goal(goal: str) -> QueryResult`
- **Async:** No
- **Docstring:** Query skills available for a goal.  L4 domain decision: Deterministic skill matching based on goal.
- **Calls:** QueryResult, hash, keys, list, ord, sorted, sum

### `execute_query(query_type: str, params: Optional[Dict[str, Any]]) -> QueryResult`
- **Async:** No
- **Docstring:** Execute a runtime query.  L4 domain command: Routes query to appropriate handler.
- **Calls:** QueryResult, get, query_allowed_skills, query_execution_history, query_last_step_outcome, query_remaining_budget, query_skills_for_goal

### `get_skill_info(skill_id: str) -> Optional[SkillInfo]`
- **Async:** No
- **Docstring:** Get domain information about a skill.  L4 domain decision: Skill metadata and capabilities.
- **Calls:** SkillInfo, get

### `list_skills() -> List[str]`
- **Async:** No
- **Docstring:** List all available skill IDs.  L4 domain decision: What skills are known to the system.
- **Calls:** keys, list

### `get_all_skill_descriptors() -> Dict[str, Dict[str, Any]]`
- **Async:** No
- **Docstring:** Get descriptors for all skills.  L4 domain decision: Comprehensive skill information.
- **Calls:** get

### `get_resource_contract(resource_id: str) -> ResourceContractInfo`
- **Async:** No
- **Docstring:** Get resource contract information.  L4 domain decision: Default resource constraints.
- **Calls:** ResourceContractInfo

### `get_capabilities(agent_id: Optional[str], tenant_id: Optional[str]) -> CapabilitiesInfo`
- **Async:** No
- **Docstring:** Get capabilities for an agent/tenant.  L4 domain decision: What capabilities are available.
- **Calls:** CapabilitiesInfo, get, items

## Classes

### `QueryResult`
- **Docstring:** Result from a runtime query command.
- **Class Variables:** query_type: str, result: Dict[str, Any], supported_queries: List[str]

### `SkillInfo`
- **Docstring:** Domain information about a skill.
- **Class Variables:** skill_id: str, name: str, version: str, description: str, cost_model: Dict[str, Any], latency_ms: int, failure_modes: List[Dict[str, Any]], constraints: Dict[str, Any], composition_hints: Dict[str, Any], inputs_schema: Optional[Dict[str, Any]], outputs_schema: Optional[Dict[str, Any]]

### `ResourceContractInfo`
- **Docstring:** Domain information about a resource contract.
- **Class Variables:** resource_id: str, budget_cents: int, rate_limit_per_minute: int, max_concurrent: int

### `CapabilitiesInfo`
- **Docstring:** Domain information about available capabilities.
- **Class Variables:** agent_id: Optional[str], skills: Dict[str, Dict[str, Any]], budget: Dict[str, Any], rate_limits: Dict[str, Dict[str, Any]], permissions: List[str]

## Attributes

- `DEFAULT_BUDGET_CENTS: int` (line 48)
- `DEFAULT_RATE_LIMIT_PER_MINUTE: int` (line 51)
- `DEFAULT_MAX_CONCURRENT: int` (line 54)
- `SUPPORTED_QUERY_TYPES: List[str]` (line 57)
- `DEFAULT_SKILL_METADATA: Dict[str, Dict[str, Any]]` (line 124)
- `__all__` (line 533)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

runtime_adapter.py (L3)

## Export Contract

```yaml
exports:
  functions:
    - name: get_supported_query_types
      signature: "get_supported_query_types() -> List[str]"
    - name: query_remaining_budget
      signature: "query_remaining_budget(spent_cents: int, total_cents: int) -> QueryResult"
    - name: query_execution_history
      signature: "query_execution_history(history: Optional[List[Dict[str, Any]]]) -> QueryResult"
    - name: query_allowed_skills
      signature: "query_allowed_skills() -> QueryResult"
    - name: query_last_step_outcome
      signature: "query_last_step_outcome(outcome: Optional[Dict[str, Any]]) -> QueryResult"
    - name: query_skills_for_goal
      signature: "query_skills_for_goal(goal: str) -> QueryResult"
    - name: execute_query
      signature: "execute_query(query_type: str, params: Optional[Dict[str, Any]]) -> QueryResult"
    - name: get_skill_info
      signature: "get_skill_info(skill_id: str) -> Optional[SkillInfo]"
    - name: list_skills
      signature: "list_skills() -> List[str]"
    - name: get_all_skill_descriptors
      signature: "get_all_skill_descriptors() -> Dict[str, Dict[str, Any]]"
    - name: get_resource_contract
      signature: "get_resource_contract(resource_id: str) -> ResourceContractInfo"
    - name: get_capabilities
      signature: "get_capabilities(agent_id: Optional[str], tenant_id: Optional[str]) -> CapabilitiesInfo"
  classes:
    - name: QueryResult
      methods: []
    - name: SkillInfo
      methods: []
    - name: ResourceContractInfo
      methods: []
    - name: CapabilitiesInfo
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
